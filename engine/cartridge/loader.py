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
        self._manifest_schema: Optional[Dict[str, Any]] = None
        self._validator: Optional[Draft202012Validator] = None

    def load_archive(self, archive_path: str | os.PathLike[str]) -> LoadedCartridge:
        archive_path = Path(archive_path)
        if not archive_path.exists():
            raise CartridgeLoadError(f"Cartridge archive not found: {archive_path}")

        with zipfile.ZipFile(archive_path, "r") as zf:
            manifest = self._read_manifest(zf)
            extract_dir = self._extract_archive(zf, manifest)

        python_path = extract_dir / manifest.python_path
        if python_path.exists() and python_path.is_dir():
            path_str = str(python_path)
            if path_str not in sys.path:
                sys.path.insert(0, path_str)

        assets_path = extract_dir / manifest.assets.mount_path
        if assets_path.exists():
            self._mount_assets(assets_path)
        else:
            raise CartridgeLoadError(f"Cartridge assets directory missing: {assets_path}")

        if self.save_state_manager:
            self.save_state_manager.attach_manifest(manifest)

        entry_instance = self._instantiate_entrypoint(manifest)
        if self.save_state_manager:
            setattr(entry_instance, "save_state_manager", self.save_state_manager)
        self._run_entry_hook(entry_instance, manifest)
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

    def _run_entry_hook(self, entry_instance, manifest: CartridgeManifest):
        for hook_name in ("mount", "load", "initialize"):
            hook = getattr(entry_instance, hook_name, None)
            if callable(hook):
                hook(world=self.world, base=self.base, manifest=manifest)
                break

    def _register_system_modules(self, manifest: CartridgeManifest) -> List[str]:
        loaded = []
        for dotted in manifest.system_modules:
            try:
                module = importlib.import_module(dotted)
            except ImportError as exc:
                raise CartridgeLoadError(f"Failed to import system module '{dotted}': {exc}") from exc

            register_fn = getattr(module, "register", None)
            if callable(register_fn):
                register_fn(world=self.world, base=self.base)
            loaded.append(dotted)
        return loaded
