# Collision layers, masks, and playfield bounds

This engine supports two collision backends:

- Generic AABB/circle CollisionSystem (pure Python, simple)
- Panda3D-backed PandaCollisionSystem (fast, feature-rich, with debug viz)

For 2D games with Panda3D rendering, prefer PandaCollisionSystem. It maps 2D to the Panda X/Z plane (Y is depth) and reparents its collision root to `aspect2d` so debug geometry aligns with sprites.

## Layers and masks

- A collision layer is a 1–32 index that an entity “is”.
- A collision mask is a bitfield of layers an entity can hit.
- Triggers set `ColliderComponent.is_trigger = True` to get enter/exit events without physical blocking.

Helpers live in `engine.physics.typesg`:

- `CollisionLayer` enum with common presets (PLAYER, ENEMY, PLAYER_BULLET, ENEMY_BULLET, BOUNDARY)
- `mask_of(*layers)` to build a mask
- `layer_bit(layer)` and `mask_from_names(names)` for dynamic cases

Example:

```python
from engine.physics.typesg import CollisionLayer, mask_of
from engine.physics.components import ColliderComponent

col = ColliderComponent(
    collider_type=ColliderType.RECTANGLE,
    size=Vec2(0.5, 0.5),
    collision_layer=int(CollisionLayer.PLAYER),
    collision_mask=mask_of(CollisionLayer.ENEMY, CollisionLayer.BOUNDARY),
)
```

## Playfield bounds

Use PandaCollisionSystem to quickly add screen-edge walls in `aspect2d` units:

```python
panda_col.set_playfield_bounds(min_x=-1.1, min_y=-0.8, max_x=1.1, max_y=0.8)
# later
panda_col.remove_playfield_bounds()
```

Bounds are static, into-only colliders on the `BOUNDARY` layer. Tune extents for your scene.

## Debug visualization

- `panda_col.show_collision_nodes(True|False)` to show/hide collision solids
- `panda_col.is_collision_nodes_visible()` to query state
- `panda_col.highlight_collision(entity_id)` to briefly tint a collider on impact

The demo `examples/demos/panda_collision_minimal_demo.py` shows a simple setup, playfield bounds, and a burst of bullets colliding with an enemy and the bounds. Press `V` to toggle visualization.
