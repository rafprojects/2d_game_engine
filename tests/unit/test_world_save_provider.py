"""Unit tests for the built-in WorldSaveProvider (ECS world serialization)."""

from __future__ import annotations

from engine.combat.components.health_component import HealthComponent
from engine.core.system import World
from engine.graphics.components.transform_component import TransformComponent
from engine.save_state.manager import SaveStateManager
from engine.save_state.world_provider import WorldSaveProvider


def _populated_world() -> World:
    world = World()
    player = world.create_entity("player")
    world.add_component(player.id, TransformComponent(x=12.5, y=-3.0, rotation=90.0))
    world.add_component(
        player.id, HealthComponent(max_health=100.0, current_health=42.0, team="blue")
    )
    enemy = world.create_entity("enemy")
    world.add_component(enemy.id, TransformComponent(x=1.0, y=2.0))
    return world


def test_capture_restore_round_trip():
    world = _populated_world()
    player_id = world.get_entity_by_name("player").id
    provider = WorldSaveProvider()

    payload = provider.capture(world)
    world.get_component(player_id, TransformComponent).x = 0.0  # mutate after capture
    provider.restore(world, payload)

    assert len(world.entities) == 2
    restored = world.get_entity_by_name("player")
    transform = world.get_component(restored.id, TransformComponent)
    health = world.get_component(restored.id, HealthComponent)
    assert (transform.x, transform.y, transform.rotation) == (12.5, -3.0, 90.0)
    assert health.current_health == 42.0
    assert health.team == "blue"


def test_restore_into_fresh_world_preserves_ids_and_names():
    source = _populated_world()
    original_player_id = str(source.get_entity_by_name("player").id)
    payload = WorldSaveProvider().capture(source)

    target = World()
    WorldSaveProvider().restore(target, payload)

    player = target.get_entity_by_name("player")
    assert player is not None
    assert str(player.id) == original_player_id
    assert {e.name for e in target.entities.values()} == {"player", "enemy"}


def test_end_to_end_through_save_state_manager(tmp_path):
    world = _populated_world()
    manager = SaveStateManager(world, storage_root=tmp_path / "saves")
    manager.register_provider("world", WorldSaveProvider())

    manager.save("slot1")
    enemy_id = world.get_entity_by_name("enemy").id
    world.get_component(enemy_id, TransformComponent).x = 999.0  # mutate after save
    manager.restore("slot1")

    enemy = world.get_entity_by_name("enemy")
    assert world.get_component(enemy.id, TransformComponent).x == 1.0


def test_skips_non_serializable_and_panda_node():
    class Widget:  # non-dataclass component with mixed field types
        def __init__(self):
            self.label = "hp"
            self.value = 3
            self.panda_node = object()  # runtime handle -> always skipped
            self.callback = lambda: None  # non-serializable -> skipped

    world = World()
    entity = world.create_entity("w")
    world.add_component(entity.id, Widget())

    record = WorldSaveProvider().capture(world)["entities"][0]["components"][0]
    assert record["data"] == {"label": "hp", "value": 3}


def test_to_dict_from_dict_override():
    class Packed:
        def __init__(self, blob="x"):
            self.blob = blob
            self.from_dict_used = False

        def to_dict(self):
            return {"blob": self.blob, "packed": True}

        @classmethod
        def from_dict(cls, data):
            inst = cls(blob=data["blob"])
            inst.from_dict_used = bool(data.get("packed"))
            return inst

    source = World()
    entity = source.create_entity("p")
    source.add_component(entity.id, Packed(blob="hello"))
    payload = WorldSaveProvider().capture(source)

    target = World()
    provider = WorldSaveProvider()
    # Packed is defined locally, so it is not importable by module:qualname.
    provider.register_component(
        Packed, key=f"{Packed.__module__}:{Packed.__qualname__}"
    )
    provider.restore(target, payload)

    restored = target.components[target.get_entity_by_name("p").id][Packed]
    assert restored.blob == "hello"
    assert restored.from_dict_used is True
