"""Utilities for loading cartridge archives."""

from __future__ import annotations

import importlib
import json
import os
import shutil
import sys
import tempfile
import uuid
import zipfile
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from jsonschema import Draft202012Validator

from .errors import CartridgeLoadError, CartridgeValidationError
from .manifest import CartridgeManifest
from .context import CartridgeContext

if TYPE_CHECKING:  # pragma: no cover
    from engine.save_state.manager import SaveStateManager


@dataclass
class LoadedCartridge:
    manifest: CartridgeManifest
    archive_path: Path
    extract_path: Path
    entry_instance: Any
    system_modules: List[str]
    save_state_manager: Optional["SaveStateManager"] = None


class CartridgeLoader:
    def __init__(
        self,
        world,
        base,
        resource_manager=None,
        save_state_manager: Optional["SaveStateManager"] = None,
        extract_root: Optional[Path] = None,
    ):
        self.world = world
        self.base = base
        self.resource_manager = resource_manager
        self.save_state_manager = save_state_manager
        self.extract_root = Path(extract_root) if extract_root else Path(tempfile.gettempdir()) / "2dge_cartridges"
        self.extract_root.mkdir(parents=True, exist_ok=True)
        self.loaded: Dict[str, LoadedCartridge] = {}
        # Track what *we* inserted so unload can cleanly reverse sys.path and asset mounts.
        # Keyed by cartridge manifest.name for reliable lookup regardless of how unload is called.
        self._python_path_for: Dict[str, Optional[str]] = {}
        self._asset_root_for: Dict[str, Optional[str]] = {}
        self._manifest_schema: Optional[Dict[str, Any]] = None
        self._validator: Optional[Draft202012Validator] = None

    def load_directory(self, directory_path: str | os.PathLike[str]) -> LoadedCartridge:
        """Load a cartridge from an unpacked directory (dev mode — no ZIP required)."""
        directory_path = Path(directory_path)
        if not directory_path.is_dir():
            raise CartridgeLoadError(f"Cartridge directory not found: {directory_path}")

        manifest_file = directory_path / "config" / "cartridge.json"
        try:
            with manifest_file.open() as fp:
                manifest_data = json.load(fp)
        except FileNotFoundError as exc:
            raise CartridgeValidationError("config/cartridge.json missing from cartridge directory") from exc
        except json.JSONDecodeError as exc:
            raise CartridgeValidationError(f"Invalid JSON in config/cartridge.json: {exc}") from exc

        self._validate_manifest(manifest_data)
        try:
            manifest = CartridgeManifest.from_dict(manifest_data)
        except ValueError as exc:
            raise CartridgeValidationError(str(exc)) from exc

        self._check_engine_requirement(manifest)

        python_path = directory_path / manifest.python_path
        inserted_py = None
        if python_path.exists() and python_path.is_dir():
            path_str = str(python_path)
            if path_str not in sys.path:
                sys.path.insert(0, path_str)
                inserted_py = path_str
        self._python_path_for[manifest.name] = inserted_py

        # Assets are optional in directory mode — sprites may be served from CWD.
        assets_path = directory_path / manifest.assets.mount_path
        mounted_asset = None
        if assets_path.exists():
            self._mount_assets(assets_path)
            mounted_asset = str(assets_path)
        self._asset_root_for[manifest.name] = mounted_asset

        if self.save_state_manager:
            self.save_state_manager.attach_manifest(manifest)

        entry_instance = self._instantiate_entrypoint(manifest)
        ctx = self._make_context(manifest)
        setattr(entry_instance, "context", ctx)
        if self.save_state_manager:
            setattr(entry_instance, "save_state_manager", self.save_state_manager)
        self._run_entry_hook(entry_instance, manifest, ctx)
        loaded_modules = self._register_system_modules(manifest)

        context = LoadedCartridge(
            manifest=manifest,
            archive_path=directory_path,
            extract_path=directory_path,
            entry_instance=entry_instance,
            system_modules=loaded_modules,
            save_state_manager=self.save_state_manager,
        )

        self.loaded[manifest.name] = context
        return context

    def load_archive(self, archive_path: str | os.PathLike[str]) -> LoadedCartridge:
        archive_path = Path(archive_path)
        if not archive_path.exists():
            raise CartridgeLoadError(f"Cartridge archive not found: {archive_path}")

        with zipfile.ZipFile(archive_path, "r") as zf:
            manifest = self._read_manifest(zf)
            extract_dir = self._extract_archive(zf, manifest)

        self._check_engine_requirement(manifest)

        python_path = extract_dir / manifest.python_path
        inserted_py = None
        if python_path.exists() and python_path.is_dir():
            path_str = str(python_path)
            if path_str not in sys.path:
                sys.path.insert(0, path_str)
                inserted_py = path_str
        self._python_path_for[manifest.name] = inserted_py

        assets_path = extract_dir / manifest.assets.mount_path
        if assets_path.exists():
            self._mount_assets(assets_path)
            self._asset_root_for[manifest.name] = str(assets_path)
        else:
            raise CartridgeLoadError(f"Cartridge assets directory missing: {assets_path}")

        if self.save_state_manager:
            self.save_state_manager.attach_manifest(manifest)

        entry_instance = self._instantiate_entrypoint(manifest)
        ctx = self._make_context(manifest)
        setattr(entry_instance, "context", ctx)
        if self.save_state_manager:
            setattr(entry_instance, "save_state_manager", self.save_state_manager)
        self._run_entry_hook(entry_instance, manifest, ctx)
        loaded_modules = self._register_system_modules(manifest)

        context = LoadedCartridge(
            manifest=manifest,
            archive_path=archive_path,
            extract_path=extract_dir,
            entry_instance=entry_instance,
            system_modules=loaded_modules,
            save_state_manager=self.save_state_manager,
        )

        self.loaded[manifest.name] = context
        return context

    def unload(self, name_or_context: str | LoadedCartridge | None = None) -> bool:
        """Unload a previously loaded cartridge by name or LoadedCartridge instance.

        - Removes any python_path we inserted from sys.path (if present).
        - Calls an optional `teardown` / `unload` / `cleanup` hook on the entry instance
          (first match wins), passing the same (world, base, manifest) style as initialize hooks.
        - Unmounts the cartridge's asset root via ResourceManager (if recorded and supported).
        - Removes the entry from self.loaded.
        - Extract directories for archives are left in place (conservative; caller can clean
          the extract_root if desired).

        Returns True if a cartridge was unloaded, False if nothing matched (idempotent/safe).
        """
        if not self.loaded:
            return False

        name: Optional[str]
        if name_or_context is None:
            if len(self.loaded) == 1:
                name = next(iter(self.loaded.keys()))
            else:
                # Future multi-cartridge hosts will need to be explicit.
                raise ValueError(
                    "Multiple cartridges loaded; specify a name or LoadedCartridge to unload"
                )
        elif isinstance(name_or_context, LoadedCartridge):
            name = name_or_context.manifest.name
        elif isinstance(name_or_context, str):
            name = name_or_context
        else:
            raise TypeError("name_or_context must be str, LoadedCartridge, or None")

        if name not in self.loaded:
            return False

        loaded = self.loaded[name]
        entry = loaded.entry_instance

        # 1. Optional teardown hook (symmetric naming to the load-side hooks)
        # Use the same context-first + legacy fallback as load hooks (P1-C).
        teardown_ctx = self._make_context(loaded.manifest)
        for hook_name in ("teardown", "unload", "cleanup"):
            hook = getattr(entry, hook_name, None)
            if callable(hook):
                try:
                    try:
                        hook(context=teardown_ctx)
                    except TypeError:
                        hook(world=self.world, base=self.base, manifest=loaded.manifest)
                except Exception as e:
                    print(f"⚠️  {hook_name} hook for cartridge '{name}' raised: {e}")
                break

        # 2. Unmount assets (RM.unmount_asset_root is already implemented and used by P1-A fixes)
        asset_path = self._asset_root_for.pop(name, None)
        if asset_path and self.resource_manager is not None:
            try:
                if hasattr(self.resource_manager, "unmount_asset_root"):
                    self.resource_manager.unmount_asset_root(asset_path)
            except Exception as e:
                print(f"⚠️  Failed to unmount assets for '{name}': {e}")

        # 3. Remove the python path we inserted (only the exact one we own)
        py_path = self._python_path_for.pop(name, None)
        if py_path and py_path in sys.path:
            try:
                sys.path.remove(py_path)
            except ValueError:
                pass  # Already gone or was never there

        # 4. Drop the record
        del self.loaded[name]

        print(f"🧹 Unloaded cartridge '{name}'")
        return True

    def _read_manifest(self, zf: zipfile.ZipFile) -> CartridgeManifest:
        try:
            with zf.open("config/cartridge.json") as fp:
                manifest_data = json.load(fp)
        except KeyError as exc:
            raise CartridgeValidationError("config/cartridge.json missing from archive") from exc
        except json.JSONDecodeError as exc:
            raise CartridgeValidationError(f"Invalid JSON in config/cartridge.json: {exc}") from exc

        self._validate_manifest(manifest_data)

        try:
            return CartridgeManifest.from_dict(manifest_data)
        except ValueError as exc:
            raise CartridgeValidationError(str(exc)) from exc

    def _validate_manifest(self, manifest_data: Dict[str, Any]):
        validator = self._get_validator()
        errors = sorted(validator.iter_errors(manifest_data), key=lambda err: err.path)
        if errors:
            formatted = "; ".join(
                f"{'/'.join(str(p) for p in error.path) or '<root>'}: {error.message}" for error in errors
            )
            raise CartridgeValidationError(f"Manifest validation failed: {formatted}")

    def _get_validator(self) -> Draft202012Validator:
        if self._validator is None:
            schema = self._get_manifest_schema()
            self._validator = Draft202012Validator(schema)
        return self._validator

    def _get_manifest_schema(self) -> Dict[str, Any]:
        if self._manifest_schema is None:
            schema_text = resources.files("engine.cartridge").joinpath("schema.json").read_text(encoding="utf-8")
            self._manifest_schema = json.loads(schema_text)
        assert self._manifest_schema is not None
        return self._manifest_schema

    def _extract_archive(self, zf: zipfile.ZipFile, manifest: CartridgeManifest) -> Path:
        unique_id = uuid.uuid4().hex[:8]
        extract_dir = self.extract_root / f"{manifest.name}-{manifest.version}-{unique_id}"
        if extract_dir.exists():
            shutil.rmtree(extract_dir)
        extract_dir.mkdir(parents=True, exist_ok=True)
        zf.extractall(extract_dir)
        return extract_dir

    def _mount_assets(self, assets_path: Path):
        if self.resource_manager is None:
            return
        # Mount cartridge assets as highest-priority root while keeping existing mounts available.
        if hasattr(self.resource_manager, "mount_asset_root"):
            self.resource_manager.mount_asset_root(str(assets_path), prepend=True)
        else:
            self.resource_manager.asset_root = str(assets_path)

    def _instantiate_entrypoint(self, manifest: CartridgeManifest):
        module_name, _, attr = manifest.entrypoint.partition(":")
        if not module_name or not attr:
            raise CartridgeValidationError("entrypoint must be in 'module:Class' format")
        try:
            module = importlib.import_module(module_name)
        except ImportError as exc:
            raise CartridgeLoadError(f"Failed to import cartridge module '{module_name}': {exc}") from exc

        try:
            entry_cls = getattr(module, attr)
        except AttributeError as exc:
            raise CartridgeLoadError(f"Entrypoint '{attr}' not found in module '{module_name}'") from exc

        try:
            instance = entry_cls()
        except Exception as exc:
            raise CartridgeLoadError(f"Failed to instantiate entrypoint '{manifest.entrypoint}': {exc}") from exc
        return instance

    def _make_context(self, manifest: CartridgeManifest) -> CartridgeContext:
        """Construct a CartridgeContext for the current load state.

        This centralizes exposure of world/base + the managers the loader was
        constructed with (RM for assets, SaveStateManager, and self for future
        self-unload).
        """
        return CartridgeContext(
            world=self.world,
            base=self.base,
            manifest=manifest,
            resource_manager=self.resource_manager,
            save_state_manager=self.save_state_manager,
            loader=self,
        )

    def _check_engine_requirement(self, manifest: CartridgeManifest) -> None:
        """Enforce manifest 'cartridge.requires.engine' if present (P1-F).

        Called immediately after manifest parsing in both load_directory and
        load_archive, before any side effects (sys.path, asset mounts, hooks).
        Uses CartridgeValidationError for consistency with other manifest issues.
        """
        if not getattr(manifest, "engine_requirement", None):
            return

        current = self._get_current_engine_version()
        if not self._requirement_satisfied(current, manifest.engine_requirement):
            raise CartridgeValidationError(
                f"Cartridge '{manifest.name}' requires engine "
                f"{manifest.engine_requirement} but this engine is {current}"
            )

    def _get_current_engine_version(self) -> str:
        """Best-effort engine version for requirement checks.

        Prefers installed distribution metadata; falls back to the module attr
        we expose (engine.__version__) and finally a safe default.
        """
        try:
            import importlib.metadata

            return importlib.metadata.version("py2d-game-engine")
        except Exception:
            pass

        # Fallback to the attribute we maintain on the engine package (P1-F).
        try:
            import engine

            return getattr(engine, "__version__", "0.1.0")
        except Exception:
            return "0.1.0"

    def _requirement_satisfied(self, current_version: str, requirement: str) -> bool:
        """Return True if current_version satisfies the declared requirement string.

        Primary path uses 'packaging' (SpecifierSet) when available (rich semver,
        caret ranges, etc.). Falls back to a conservative heuristic sufficient
        for the current 0.1.x world and common "^0.1.0" style declarations.
        """
        req = (requirement or "").strip()
        if not req:
            return True

        # Preferred: full semver support via packaging (transitive in most envs)
        try:
            from packaging.specifiers import SpecifierSet
            from packaging.version import parse as parse_version

            spec = SpecifierSet(req)
            return parse_version(current_version) in spec
        except Exception:
            pass

        # Conservative fallback (no 'packaging' or parse error).
        # Handle common caret ranges ^X.Y.Z for the 0.x series explicitly,
        # otherwise do a loose "base appears in current or current starts with base".
        if req.startswith("^"):
            base = req[1:].strip().split()[0]
            try:
                base_parts = [int(x) for x in base.split(".")[:2] if x.isdigit()]
                cur_parts = [int(x) for x in current_version.split(".")[:2] if x.isdigit()]
                if len(base_parts) >= 2 and len(cur_parts) >= 2:
                    if base_parts[0] == 0:
                        # ^0.1.0 intent: same major 0, minor >= base minor
                        return cur_parts[0] == 0 and cur_parts[1] >= base_parts[1]
                    return cur_parts[0] >= base_parts[0]
            except Exception:
                pass
            base = base  # fall through to contains check below

        base = req.lstrip("^~>=< ").strip().split()[0]
        if not base:
            return True
        return base in current_version or current_version.startswith(base)

    def _run_entry_hook(
        self,
        entry_instance,
        manifest: CartridgeManifest,
        context: CartridgeContext | None = None,
    ):
        ctx = context or self._make_context(manifest)
        for hook_name in ("mount", "load", "initialize"):
            hook = getattr(entry_instance, hook_name, None)
            if callable(hook):
                # Transition strategy (P1-C): prefer context= (new cartridges can
                # implement `def initialize(self, context): ...` only). Fall back to
                # the legacy three-kw call so existing cartridges (e.g. tgl_demo)
                # continue to work unchanged during the short transition.
                try:
                    hook(context=ctx)
                except TypeError:
                    hook(world=self.world, base=self.base, manifest=manifest)
                break

    def _register_system_modules(self, manifest: CartridgeManifest) -> List[str]:
        loaded = []
        # Build once for the cartridge; all its system register fns share the same context.
        ctx = self._make_context(manifest)
        for dotted in manifest.system_modules:
            try:
                module = importlib.import_module(dotted)
            except ImportError as exc:
                raise CartridgeLoadError(f"Failed to import system module '{dotted}': {exc}") from exc

            register_fn = getattr(module, "register", None)
            if callable(register_fn):
                # Same transition support as entry hooks: context-first then legacy.
                try:
                    register_fn(context=ctx)
                except TypeError:
                    register_fn(world=self.world, base=self.base)
            loaded.append(dotted)
        return loaded
