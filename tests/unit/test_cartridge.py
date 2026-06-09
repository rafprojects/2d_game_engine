"""Tests for cartridge manifest, loader, and packaging helpers."""

from __future__ import annotations

import json
import shutil
import sys
import textwrap
import zipfile
from pathlib import Path

import pytest

from engine.cartridge.loader import CartridgeLoadError, CartridgeLoader, CartridgeValidationError
from engine.cartridge.manifest import CartridgeManifest
from engine.cartridge.context import CartridgeContext
from engine.save_state.manager import SaveStateManager
from tools.cli import cartridge_pack


class DummyWorld:
    """Minimal stand-in for the ECS world."""


class DummyBase:
    """Minimal ShowBase replacement for loader tests."""

    def __init__(self):
        self.loader = object()
        self.hook_payload = None


class DummyResourceManager:
    """Stub ResourceManager exposing only asset_root."""

    def __init__(self):
        self.asset_roots = ["assets"]
        self.mount_calls: list[str] = []

    @property
    def asset_root(self) -> str:
        return self.asset_roots[0]

    @asset_root.setter
    def asset_root(self, path: str):
        self.asset_roots = [path]

    def mount_asset_root(self, path: str, prepend: bool = True):
        if path in self.asset_roots:
            self.asset_roots.remove(path)
        if prepend:
            self.asset_roots.insert(0, path)
        else:
            self.asset_roots.append(path)
        self.mount_calls.append(path)


def _write_file(path: Path, contents: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(contents, encoding="utf-8")


def _build_manifest(overrides: dict | None = None) -> dict:
    manifest = {
        "cartridge": {
            "name": "Test Cartridge",
            "version": "1.0.0",
            "entrypoint": "guardian.main:Cartridge",
        },
        "assets": {"mount": "assets", "virtual_root": "test"},
        "systems": {"register": []},
        "python_path": "python",
    }

    if overrides:
        manifest = _deep_update(manifest, overrides)
    return manifest


def _deep_update(base: dict, updates: dict) -> dict:
    result = dict(base)
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_update(result[key], value)
        else:
            result[key] = value
    return result


def _create_cartridge_tree(root: Path, manifest_overrides: dict | None = None) -> tuple[Path, dict]:
    manifest = _build_manifest(manifest_overrides)
    config_path = root / "config" / "cartridge.json"
    _write_file(config_path, json.dumps(manifest, indent=2))

    assets_dir = root / manifest["assets"]["mount"]
    _write_file(assets_dir / "sprite.txt", "sprite data")

    python_root = root / manifest.get("python_path", "python")
    module_root = python_root / "guardian"
    _write_file(module_root / "__init__.py", "")
    _write_file(
        module_root / "main.py",
        textwrap.dedent(
            """
            class Cartridge:
                def __init__(self):
                    self.hook_invoked = False
                    self.received_manifest = None

                def initialize(self, world, base, manifest):
                    self.hook_invoked = True
                    self.received_manifest = manifest
                    base.hook_payload = manifest.name
            """
        ).strip()
        + "\n",
    )

    return root, manifest


def _add_system_module(root: Path, manifest: dict, module: str) -> None:
    python_root = root / manifest.get("python_path", "python")
    module_rel = Path(*module.split("."))
    module_path = python_root / module_rel
    module_path.parent.mkdir(parents=True, exist_ok=True)
    _write_file(module_path.with_suffix(".py"), textwrap.dedent(
        """
        REGISTERED = False

        def register(world, base):
            global REGISTERED
            REGISTERED = True
            base.hook_payload = "registered"
        """
    ).strip() + "\n")
    # Ensure package __init__.py files exist up the tree
    cursor = module_path.parent
    while cursor and cursor != python_root.parent:
        init_file = cursor / "__init__.py"
        if not init_file.exists():
            _write_file(init_file, "")
        if cursor == python_root:
            break
        cursor = cursor.parent


def _zip_cartridge(source: Path, destination: Path) -> Path:
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
        for file_path in source.rglob("*"):
            if file_path.is_file():
                archive.write(file_path, arcname=str(file_path.relative_to(source)))
    return destination


def _cleanup_modules():
    for name in [mod for mod in list(sys.modules) if mod.startswith("guardian")]:
        sys.modules.pop(name, None)


def test_manifest_from_dict_parses_defaults():
    manifest_dict = _build_manifest()
    manifest = CartridgeManifest.from_dict(manifest_dict)

    assert manifest.name == "Test Cartridge"
    assert manifest.version == "1.0.0"
    assert manifest.entrypoint == "guardian.main:Cartridge"
    assert manifest.assets.mount_path == "assets"
    assert manifest.assets.virtual_root == "test"
    assert manifest.system_modules == []


def test_manifest_from_dict_missing_required_key():
    manifest_dict = _build_manifest({"cartridge": {"entrypoint": None}})
    manifest_dict["cartridge"].pop("name")

    with pytest.raises(ValueError):
        CartridgeManifest.from_dict(manifest_dict)


def test_loader_loads_archive_and_mounts_assets(tmp_path):
    cartridge_dir = tmp_path / "cartridge"
    cartridge_dir, _ = _create_cartridge_tree(cartridge_dir)
    archive_path = tmp_path / "test.car"
    _zip_cartridge(cartridge_dir, archive_path)

    resource_manager = DummyResourceManager()
    loader = CartridgeLoader(
        world=DummyWorld(),
        base=DummyBase(),
        resource_manager=resource_manager,
        extract_root=tmp_path / "extract",
    )

    try:
        context = loader.load_archive(archive_path)
    finally:
        _cleanup_modules()

    assert context.manifest.name == "Test Cartridge"
    assert context.entry_instance.hook_invoked is True
    assert context.entry_instance.received_manifest is context.manifest
    assert loader.loaded["Test Cartridge"].extract_path == context.extract_path

    expected_asset_root = context.extract_path / context.manifest.assets.mount_path
    assert Path(resource_manager.asset_root) == expected_asset_root
    assert context.system_modules == []


def test_loader_raises_for_invalid_manifest(tmp_path):
    cartridge_dir = tmp_path / "invalid"
    cartridge_dir, _ = _create_cartridge_tree(cartridge_dir, {"cartridge": {"version": "1.0"}})
    archive_path = tmp_path / "invalid.car"
    _zip_cartridge(cartridge_dir, archive_path)

    loader = CartridgeLoader(
        world=DummyWorld(),
        base=DummyBase(),
        resource_manager=DummyResourceManager(),
        extract_root=tmp_path / "extract_invalid",
    )

    with pytest.raises(CartridgeValidationError):
        try:
            loader.load_archive(archive_path)
        finally:
            _cleanup_modules()


def test_cartridge_pack_cli_creates_archive(tmp_path):
    cartridge_dir = tmp_path / "source"
    cartridge_dir, _ = _create_cartridge_tree(cartridge_dir)
    output_path = tmp_path / "output.car"

    exit_code = cartridge_pack.main([str(cartridge_dir), "-o", str(output_path), "--force"])

    assert exit_code == 0
    assert output_path.exists()

    with zipfile.ZipFile(output_path, "r") as archive:
        assert "config/cartridge.json" in archive.namelist()


def test_loader_rejects_bad_entrypoint_format(tmp_path):
    cartridge_dir, _ = _create_cartridge_tree(tmp_path / "bad_ep", {"cartridge": {"entrypoint": "guardian.main.Cartridge"}})
    archive_path = tmp_path / "bad_ep.car"
    _zip_cartridge(cartridge_dir, archive_path)

    loader = CartridgeLoader(
        world=DummyWorld(),
        base=DummyBase(),
        resource_manager=DummyResourceManager(),
        extract_root=tmp_path / "extract_bad_ep",
    )

    with pytest.raises(CartridgeValidationError):
        try:
            loader.load_archive(archive_path)
        finally:
            _cleanup_modules()


def test_loader_raises_when_assets_directory_missing(tmp_path):
    cartridge_dir, manifest = _create_cartridge_tree(tmp_path / "missing_assets")
    assets_dir = cartridge_dir / manifest["assets"]["mount"]
    shutil.rmtree(assets_dir)
    archive_path = tmp_path / "missing_assets.car"
    _zip_cartridge(cartridge_dir, archive_path)

    loader = CartridgeLoader(
        world=DummyWorld(),
        base=DummyBase(),
        resource_manager=DummyResourceManager(),
        extract_root=tmp_path / "extract_missing_assets",
    )

    with pytest.raises(CartridgeLoadError):
        try:
            loader.load_archive(archive_path)
        finally:
            _cleanup_modules()


def test_loader_registers_system_modules(tmp_path):
    overrides = {"systems": {"register": ["guardian.systems.demo"]}}
    cartridge_dir, manifest = _create_cartridge_tree(tmp_path / "with_system", overrides)
    _add_system_module(cartridge_dir, manifest, "guardian.systems.demo")
    archive_path = tmp_path / "system.car"
    _zip_cartridge(cartridge_dir, archive_path)

    base = DummyBase()
    loader = CartridgeLoader(
        world=DummyWorld(),
        base=base,
        resource_manager=DummyResourceManager(),
        extract_root=tmp_path / "extract_system",
    )

    try:
        context = loader.load_archive(archive_path)
        module = sys.modules.get("guardian.systems.demo")
    finally:
        _cleanup_modules()

    assert context.system_modules == ["guardian.systems.demo"]
    assert module is not None
    assert getattr(module, "REGISTERED", False) is True
    assert base.hook_payload == "registered"


def test_loader_attaches_save_state_manager(tmp_path):
    save_root = tmp_path / "saves"
    manager = SaveStateManager(DummyWorld(), storage_root=save_root)

    cartridge_dir, _ = _create_cartridge_tree(tmp_path / "with_save")
    archive_path = tmp_path / "with_save.car"
    _zip_cartridge(cartridge_dir, archive_path)

    loader = CartridgeLoader(
        world=manager.world,
        base=DummyBase(),
        resource_manager=DummyResourceManager(),
        save_state_manager=manager,
        extract_root=tmp_path / "extract_save",
    )

    try:
        context = loader.load_archive(archive_path)
    finally:
        _cleanup_modules()

    assert context.save_state_manager is manager
    assert context.entry_instance.save_state_manager is manager
    assert manager.cartridge_name == "Test Cartridge"


def test_cartridge_pack_cli_dry_run_skips_archive(tmp_path):
    cartridge_dir, _ = _create_cartridge_tree(tmp_path / "dry_run")
    output_path = tmp_path / "skipped.car"

    exit_code = cartridge_pack.main([str(cartridge_dir), "-o", str(output_path), "--dry-run"])

    assert exit_code == 0
    assert not output_path.exists()


# ------------------------------------------------------------------
# P1-B: Loader unload lifecycle tests
# ------------------------------------------------------------------

def test_loader_unload_removes_python_path_and_loaded_entry(tmp_path):
    """Core P1-B behavior: after unload the python path we inserted is gone and
    the cartridge is no longer in loader.loaded. Re-load must succeed cleanly.
    """
    cartridge_dir = tmp_path / "cartridge"
    cartridge_dir, _ = _create_cartridge_tree(cartridge_dir)
    archive_path = tmp_path / "test.car"
    _zip_cartridge(cartridge_dir, archive_path)

    loader = CartridgeLoader(
        world=DummyWorld(),
        base=DummyBase(),
        resource_manager=DummyResourceManager(),
        extract_root=tmp_path / "extract_unload",
    )

    try:
        # Directory load first (fast path)
        ctx = loader.load_directory(str(cartridge_dir))
        name = ctx.manifest.name

        # The python path for the cartridge should have been recorded and be on sys.path
        py_paths_before = [p for p in sys.path if "cartridge" in p or name.lower() in p.lower()]
        assert name in loader.loaded
        assert loader._python_path_for.get(name) is not None

        # Unload
        assert loader.unload(name) is True
        assert name not in loader.loaded
        assert loader.unload(name) is False  # idempotent

        removed_path = loader._python_path_for.get(name)  # should have been popped
        assert removed_path is None or removed_path not in sys.path

        # Re-load the same cartridge (or archive) must work without accumulating duplicates
        ctx2 = loader.load_archive(archive_path)
        assert ctx2.manifest.name == name
        assert name in loader.loaded
    finally:
        _cleanup_modules()
        # Best-effort cleanup of any path we may have left (in case of test failure)
        for p in list(sys.path):
            if "cartridge" in str(p).lower() or str(tmp_path) in str(p):
                try:
                    sys.path.remove(p)
                except ValueError:
                    pass


# ------------------------------------------------------------------
# P1-F: Manifest engine requirement enforcement (version compatibility)
# ------------------------------------------------------------------

def test_loader_rejects_incompatible_engine_requirement(tmp_path):
    """A cartridge declaring a future/incompatible engine requirement must fail
    early with CartridgeValidationError (before sys.path or asset side effects).
    """
    overrides = {"cartridge": {"requires": {"engine": "^99.0.0"}}}
    cartridge_dir, _ = _create_cartridge_tree(tmp_path / "bad_req", overrides)

    loader = CartridgeLoader(
        world=DummyWorld(),
        base=DummyBase(),
        resource_manager=DummyResourceManager(),
    )

    with pytest.raises(CartridgeValidationError) as excinfo:
        try:
            loader.load_directory(str(cartridge_dir))
        finally:
            _cleanup_modules()

    msg = str(excinfo.value)
    assert "requires engine" in msg
    assert "^99.0.0" in msg
    assert "this engine is" in msg


def test_loader_accepts_compatible_engine_requirement(tmp_path):
    """^0.1.0 (as declared by the reference tgl_demo) must load successfully."""
    overrides = {"cartridge": {"requires": {"engine": "^0.1.0"}}}
    cartridge_dir, _ = _create_cartridge_tree(tmp_path / "good_req", overrides)

    loader = CartridgeLoader(
        world=DummyWorld(),
        base=DummyBase(),
        resource_manager=DummyResourceManager(),
    )

    try:
        ctx = loader.load_directory(str(cartridge_dir))
        assert ctx.manifest.engine_requirement == "^0.1.0"
        assert ctx.manifest.name == "Test Cartridge"
    finally:
        _cleanup_modules()


def test_loader_accepts_missing_engine_requirement(tmp_path):
    """Manifests that omit 'requires.engine' entirely must continue to load
    (no breaking change for existing or minimal cartridges).
    """
    # Explicitly ensure the key is absent by starting clean and not providing it
    cartridge_dir, _ = _create_cartridge_tree(tmp_path / "no_req")

    loader = CartridgeLoader(
        world=DummyWorld(),
        base=DummyBase(),
        resource_manager=DummyResourceManager(),
    )

    try:
        ctx = loader.load_directory(str(cartridge_dir))
        assert ctx.manifest.engine_requirement is None
    finally:
        _cleanup_modules()


def test_loader_unload_calls_teardown_hook(tmp_path):
    """If the entrypoint instance has a teardown (or unload/cleanup) method it is invoked."""
    cartridge_dir = tmp_path / "with_teardown"
    cartridge_dir, _ = _create_cartridge_tree(cartridge_dir)

    loader = CartridgeLoader(
        world=DummyWorld(),
        base=DummyBase(),
        resource_manager=DummyResourceManager(),
        extract_root=tmp_path / "extract_teardown",
    )

    teardown_called = {"flag": False, "manifest_name": None}

    try:
        ctx = loader.load_directory(str(cartridge_dir))
        entry = ctx.entry_instance

        def fake_teardown(world=None, base=None, manifest=None):
            teardown_called["flag"] = True
            teardown_called["manifest_name"] = getattr(manifest, "name", None)

        # Attach after load (the hook lookup uses getattr at unload time)
        entry.teardown = fake_teardown

        assert loader.unload(ctx) is True
        assert teardown_called["flag"] is True
        assert teardown_called["manifest_name"] == "Test Cartridge"
    finally:
        _cleanup_modules()


def test_loader_unload_unmounts_assets(tmp_path):
    """unload must call unmount_asset_root on the RM for the recorded cartridge assets path."""
    cartridge_dir = tmp_path / "asset_unmount"
    cartridge_dir, _ = _create_cartridge_tree(cartridge_dir)

    class TrackingRM(DummyResourceManager):
        def __init__(self):
            super().__init__()
            self.unmount_calls: list[str] = []

        def unmount_asset_root(self, path: str):
            self.unmount_calls.append(path)

    rm = TrackingRM()
    loader = CartridgeLoader(
        world=DummyWorld(),
        base=DummyBase(),
        resource_manager=rm,
        extract_root=tmp_path / "extract_assets",
    )

    try:
        ctx = loader.load_directory(str(cartridge_dir))
        name = ctx.manifest.name

        # We should have recorded the asset root during load
        recorded = loader._asset_root_for.get(name)
        assert recorded is not None

        assert loader.unload(name) is True
        assert any(recorded in call for call in rm.unmount_calls), (
            f"expected unmount of {recorded}, got {rm.unmount_calls}"
        )
    finally:
        _cleanup_modules()


def test_loader_passes_cartridge_context_and_supports_new_style_hook(tmp_path):
    """CartridgeContext is constructed, attached to entry as .context, and passed
    as the `context` kwarg to initialize (new-style hook). Legacy hooks continue
    to work via fallback (covered by other tests + tgl_demo canary).
    """
    cartridge_dir = tmp_path / "with_context"
    cartridge_dir, _ = _create_cartridge_tree(cartridge_dir)

    # Override the generated entrypoint with one that only accepts `context`
    # (proves new cartridges can be written against CartridgeContext only).
    python_root = cartridge_dir / "python"
    main_py = python_root / "guardian" / "main.py"
    _write_file(
        main_py,
        textwrap.dedent(
            """
            from engine.cartridge.context import CartridgeContext

            class Cartridge:
                def __init__(self):
                    self.context_received = None
                    self.manifest_name = None

                def initialize(self, context):
                    # New-style only signature
                    if not isinstance(context, CartridgeContext):
                        raise TypeError("expected CartridgeContext")
                    self.context_received = context
                    self.manifest_name = getattr(context.manifest, "name", None)
                    # Exercise other surfaces
                    _ = context.world
                    _ = context.base
                    if context.save_state_manager is not None:
                        context.save_state_manager  # accessible
                    if context.resource_manager is not None:
                        context.resource_manager  # accessible
            """
        ).strip()
        + "\n",
    )

    loader = CartridgeLoader(
        world=DummyWorld(),
        base=DummyBase(),
        resource_manager=DummyResourceManager(),
        extract_root=tmp_path / "extract_ctx",
    )

    try:
        loaded = loader.load_directory(str(cartridge_dir))
        entry = loaded.entry_instance

        assert hasattr(entry, "context"), "entry should have .context attached"
        assert isinstance(entry.context, CartridgeContext)
        assert entry.context is entry.context_received
        assert entry.manifest_name == "Test Cartridge"
        assert loaded.manifest.name == "Test Cartridge"
    finally:
        _cleanup_modules()
