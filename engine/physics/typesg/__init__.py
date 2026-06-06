"""Types and helpers for physics type definitions."""

from engine.physics.typesg.collider_type import ColliderType
import importlib as _importlib

# Dynamically import to avoid static analysis resolution issues
_cl = _importlib.import_module(__name__ + ".collision_layers")
CollisionLayer = _cl.CollisionLayer
mask_of = _cl.mask_of
mask_from_names = _cl.mask_from_names
layer_bit = _cl.layer_bit

__all__ = [
	'ColliderType',
	'CollisionLayer', 'mask_of', 'mask_from_names', 'layer_bit',
]