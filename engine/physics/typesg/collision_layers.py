from enum import IntEnum
from typing import Iterable, Union


class CollisionLayer(IntEnum):
    """Common collision layers used across demos/games (1-based)."""
    PLAYER = 1
    ENEMY = 2
    PLAYER_BULLET = 3
    ENEMY_BULLET = 4
    BOUNDARY = 5


LayerLike = Union["CollisionLayer", int]


def layer_bit(layer: LayerLike) -> int:
    """Return the bit for a given 1-based layer value."""
    value = int(layer)
    if value < 1 or value > 32:
        raise ValueError("Layer value must be in 1..32")
    return 1 << (value - 1)


def mask_of(*layers: LayerLike) -> int:
    """Compose a bitmask from multiple 1-based layers."""
    m = 0
    for layer in layers:
        m |= layer_bit(layer)
    return m


def mask_from_names(names: Iterable[str]) -> int:
    """Compose a mask from string names (case-insensitive) matching CollisionLayer enum."""
    name_to_layer = {name.lower(): member for name, member in CollisionLayer.__members__.items()}
    m = 0
    for name in names:
        key = name.lower()
        if key not in name_to_layer:
            raise KeyError(f"Unknown collision layer name: {name}")
        m |= layer_bit(name_to_layer[key])
    return m
