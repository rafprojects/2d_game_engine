"""Tests for ResourceManager layered asset mounts."""

from __future__ import annotations

import json
import os
from pathlib import Path

from engine.assets.resource_manager import ResourceManager
from engine.core.system import World


class NullLoader:
    """Loader stub that satisfies ResourceManager expectations."""

    def loadTexture(self, path):  # pragma: no cover - not used in these tests
        return path

    def loadSfx(self, path):  # pragma: no cover - not used in these tests
        return path

    def loadFont(self, path):  # pragma: no cover - not used in these tests
        return path

    def loadModel(self, path):  # pragma: no cover - not used in these tests
        return path


class DummyBase:
    def __init__(self):
        self.loader = NullLoader()


def _normalized(path: Path) -> str:
    return os.path.normpath(os.path.abspath(path))


def _build_resource_manager(base_root: Path) -> ResourceManager:
    manager = ResourceManager(World(), DummyBase())
    manager.asset_root = str(base_root)
    return manager


def _write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")



def test_layered_mount_prefers_overlay(tmp_path):
    base_dir = tmp_path / "base"
    overlay_dir = tmp_path / "overlay"
    _write_json(base_dir / "shared" / "data.json", {"source": "base"})
    _write_json(overlay_dir / "shared" / "data.json", {"source": "overlay"})

    manager = _build_resource_manager(base_dir)
    assert manager.register_asset("shared/data.json")

    manager.mount_asset_root(str(overlay_dir))
    data = manager.load_asset("shared/data.json", force_reload=True)

    assert data is not None
    assert data["source"] == "overlay"
    assert manager.asset_root == _normalized(overlay_dir)


def test_layered_mount_falls_back_to_base(tmp_path):
    base_dir = tmp_path / "base"
    overlay_dir = tmp_path / "overlay"
    _write_json(base_dir / "solo.json", {"present": "base_only"})

    manager = _build_resource_manager(base_dir)
    manager.mount_asset_root(str(overlay_dir))

    assert manager.validate_asset("solo.json")

    manager.unmount_asset_root(str(overlay_dir))
    data = manager.load_asset("solo.json", force_reload=True)

    assert data is not None
    assert data["present"] == "base_only"
    assert manager.asset_root == _normalized(base_dir)


def test_resolve_asset_path_prefers_overlay(tmp_path):
    """New coverage for the public resolve hook used by RenderSystem (P1-A).

    Cartridge mounts (prepended) must win for relative paths, matching the
    contract used by load_asset and now by sprite/egg loading in RenderSystem.
    """
    base_dir = tmp_path / "base"
    overlay_dir = tmp_path / "overlay"
    _write_json(base_dir / "shared" / "data.json", {"source": "base"})
    _write_json(overlay_dir / "shared" / "data.json", {"source": "overlay"})

    manager = _build_resource_manager(base_dir)
    manager.mount_asset_root(str(overlay_dir))

    resolved = manager.resolve_asset_path("shared/data.json")
    assert resolved is not None
    assert "overlay" in resolved, f"expected overlay to win, got {resolved}"

    # Nonexistent falls back to None (no error)
    assert manager.resolve_asset_path("does/not/exist.png") is None

    # After unmount, base wins again
    manager.unmount_asset_root(str(overlay_dir))
    resolved_base = manager.resolve_asset_path("shared/data.json")
    assert resolved_base is not None
    assert "base" in resolved_base
