"""Unit tests for SaveStateManager serialization and persistence."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from engine.save_state.errors import SaveStateError
from engine.save_state.manager import SaveStateManager, SaveStateProvider


class DummyWorld:
    def __init__(self):
        self.value = 0


class MockProvider(SaveStateProvider):
    def __init__(self):
        self.last_restored = None

    def capture(self, world):
        return {"value": world.value}

    def restore(self, world, payload):
        world.value = payload.get("value", 0)
        self.last_restored = payload


@dataclass
class Manifest:
    name: str
    version: str


def test_capture_state_collects_provider_payload(tmp_path):
    world = DummyWorld()
    world.value = 42
    provider = MockProvider()
    manager = SaveStateManager(world, storage_root=tmp_path / "root")
    manager.register_provider("mock", provider)

    state = manager.capture_state("slot_a")

    assert state.payload["mock"] == {"value": 42}
    assert state.metadata.slot == "slot_a"
    assert state.metadata.version == manager.serializer_version


def test_save_and_load_msgpack(tmp_path):
    world = DummyWorld()
    world.value = 7
    provider = MockProvider()
    manager = SaveStateManager(world, storage_root=tmp_path / "saves")
    manager.attach_manifest(Manifest(name="CartridgeA", version="0.1"))
    manager.register_provider("mock", provider)

    save_path = manager.save("slot1")
    assert save_path.exists()
    assert save_path.suffix == ".sav"
    assert manager.list_saves() == ["slot1"]

    world.value = 0
    loaded_state = manager.restore("slot1")

    assert world.value == 7
    assert provider.last_restored == {"value": 7}
    assert loaded_state.metadata.cartridge == "CartridgeA"


def test_json_format_export(tmp_path):
    world = DummyWorld()
    world.value = 13
    provider = MockProvider()
    manager = SaveStateManager(world, storage_root=tmp_path / "json_saves")
    manager.register_provider("mock", provider)

    path = manager.save("slot_json", fmt="json")
    assert path.exists()
    assert path.suffix == ".json"

    world.value = 0
    manager.restore("slot_json", fmt="json")
    assert world.value == 13


def test_delete_removes_save(tmp_path):
    world = DummyWorld()
    provider = MockProvider()
    manager = SaveStateManager(world, storage_root=tmp_path / "saves_del")
    manager.register_provider("mock", provider)

    manager.save("slot_x")
    assert manager.list_saves() == ["slot_x"]
    manager.delete("slot_x")
    assert list(manager.list_saves()) == []


def test_duplicate_provider_name_errors():
    world = DummyWorld()
    provider = MockProvider()
    manager = SaveStateManager(world)
    manager.register_provider("mock", provider)

    with pytest.raises(SaveStateError):
        manager.register_provider("mock", provider)
