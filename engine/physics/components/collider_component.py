from typing import Set

from panda3d.core import Vec2

from engine.core.component import Component
from engine.physics.typesg import ColliderType

class ColliderComponent(Component):
    """
    Component for collision detection.
    Defines the shape and properties for collision detection.
    """
    
    def __init__(self, 
                 collider_type: ColliderType = ColliderType.RECTANGLE,
                 size: Vec2 = Vec2(1, 1),
                 radius: float = 0.5,
                 offset: Vec2 = Vec2(0, 0),
                 is_trigger: bool = False,
                 collision_layer: int = 1,
                 collision_mask: int = 1,
                 use_panda_collision: bool = True):
        """
        Initialize a collider component.
        
        Args:
            collider_type: Type of collider (rectangle, circle, sphere, box, capsule, polygon)
            size: Size for rectangle/box colliders (width, height)
            radius: Radius for circle/sphere/capsule colliders
            offset: Offset from entity position
            is_trigger: If True, generates collision events but doesn't block movement
            collision_layer: Layer this collider belongs to (1-32)
            collision_mask: Layers this collider can collide with (bitwise)
            use_panda_collision: Whether to use Panda3D collision system (default: True)
        """
        self.collider_type = collider_type
        self.size = size
        self.radius = radius
        self.offset = offset
        self.is_trigger = is_trigger
        self.collision_layer = collision_layer
        self.collision_mask = collision_mask
        self.use_panda_collision = use_panda_collision
        
        # Additional properties for 3D shapes
        self.depth = 1.0  # For box colliders
        self.height = size.y  # For capsule colliders
        
        # Runtime collision state
        self.colliding_entities: Set = set()
        self.was_colliding_entities: Set = set()
        
    def get_bounds(self, position: Vec2) -> tuple:
        """
        Get the collision bounds for this collider.
        
        Args:
            position: World position of the entity
            
        Returns:
            For rectangle: (min_x, min_y, max_x, max_y)
            For circle: (center_x, center_y, radius)
        """
        actual_pos = position + self.offset
        
        if self.collider_type == ColliderType.RECTANGLE:
            half_width = self.size.x / 2
            half_height = self.size.y / 2
            return (
                actual_pos.x - half_width,
                actual_pos.y - half_height,
                actual_pos.x + half_width,
                actual_pos.y + half_height
            )
        else:  # CIRCLE
            return (actual_pos.x, actual_pos.y, self.radius)
    
    def can_collide_with_layer(self, layer: int) -> bool:
        """Check if this collider can collide with the given layer."""
        return bool(self.collision_mask & (1 << (layer - 1)))
