import math
from typing import Tuple, Optional

from panda3d.core import Vec2

from engine.core.system import System
from engine.graphics import TransformComponent
from engine.physics import ColliderComponent
from engine.physics import ColliderType
from engine.core.events import Event

class CollisionEvent(Event):
    """Event fired when collision is detected between two entities."""
    def __init__(self, entity_a_id, entity_b_id, collision_normal: Vec2):
        self.entity_a_id = entity_a_id
        self.entity_b_id = entity_b_id
        self.collision_normal = collision_normal

class TriggerEnterEvent(Event):
    """Event fired when an entity enters a trigger."""
    def __init__(self, trigger_entity_id, other_entity_id):
        self.trigger_entity_id = trigger_entity_id
        self.other_entity_id = other_entity_id

class TriggerExitEvent(Event):
    """Event fired when an entity exits a trigger."""
    def __init__(self, trigger_entity_id, other_entity_id):
        self.trigger_entity_id = trigger_entity_id
        self.other_entity_id = other_entity_id

class CollisionSystem(System):
    """
    System for collision detection and response.
    Handles both solid collisions and trigger events.
    """
    
    def __init__(self, world):
        super().__init__(world)
        
    def update(self, dt: float):
        """Update collision detection for all entities with colliders."""
        # Get all entities with colliders and transforms
        entities_with_colliders = self.world.get_entities_with_components(
            TransformComponent, ColliderComponent
        )
        
        # Update collision states
        for entity in entities_with_colliders:
            collider = self.world.get_component(entity.id, ColliderComponent)
            if collider:
                collider.was_colliding_entities = collider.colliding_entities.copy()
                collider.colliding_entities.clear()
        
        # Check all collision pairs
        for i, entity_a in enumerate(entities_with_colliders):
            for entity_b in entities_with_colliders[i+1:]:
                self._check_collision_pair(entity_a, entity_b)
        
        # Fire trigger events
        self._fire_trigger_events(entities_with_colliders)
    
    def _check_collision_pair(self, entity_a, entity_b):
        """Check collision between two entities."""
        transform_a = self.world.get_component(entity_a.id, TransformComponent)
        transform_b = self.world.get_component(entity_b.id, TransformComponent)
        collider_a = self.world.get_component(entity_a.id, ColliderComponent)
        collider_b = self.world.get_component(entity_b.id, ColliderComponent)
        
        if not all([transform_a, transform_b, collider_a, collider_b]):
            return
        
        # Check layer collision
        if not (collider_a.can_collide_with_layer(collider_b.collision_layer) or
                collider_b.can_collide_with_layer(collider_a.collision_layer)):
            return
        
        # Get collision info
        pos_a = Vec2(transform_a.x, transform_a.y)
        pos_b = Vec2(transform_b.x, transform_b.y)
        collision_info = self._detect_collision(
            pos_a, collider_a,
            pos_b, collider_b
        )
        
        if collision_info:
            is_colliding, normal, penetration = collision_info
            
            # Update collision sets
            collider_a.colliding_entities.add(entity_b.id)
            collider_b.colliding_entities.add(entity_a.id)
            
            # Fire collision event if not triggers
            if not collider_a.is_trigger and not collider_b.is_trigger:
                self.world.event_manager.publish(
                    CollisionEvent(entity_a.id, entity_b.id, normal)
                )
    
    def _detect_collision(self, pos_a: Vec2, collider_a: ColliderComponent,
                         pos_b: Vec2, collider_b: ColliderComponent) -> Optional[Tuple[bool, Vec2, float]]:
        """
        Detect collision between two colliders.
        
        Returns:
            (is_colliding, normal, penetration_depth) or None if no collision
        """
        bounds_a = collider_a.get_bounds(pos_a)
        bounds_b = collider_b.get_bounds(pos_b)
        
        # Rectangle vs Rectangle
        if (collider_a.collider_type == ColliderType.RECTANGLE and 
            collider_b.collider_type == ColliderType.RECTANGLE):
            return self._rect_vs_rect_collision(bounds_a, bounds_b)
        
        # Circle vs Circle (also handles Sphere vs Sphere, Circle vs Sphere, etc.)
        elif ((collider_a.collider_type in [ColliderType.CIRCLE, ColliderType.SPHERE] and 
              collider_b.collider_type in [ColliderType.CIRCLE, ColliderType.SPHERE])):
            return self._circle_vs_circle_collision(bounds_a, bounds_b)
        
        # Rectangle vs Circle/Sphere (or Circle/Sphere vs Rectangle)
        else:
            if collider_a.collider_type == ColliderType.RECTANGLE:
                return self._rect_vs_circle_collision(bounds_a, bounds_b)
            elif collider_b.collider_type == ColliderType.RECTANGLE:
                result = self._rect_vs_circle_collision(bounds_b, bounds_a)
                if result:
                    is_colliding, normal, penetration = result
                    return is_colliding, -normal, penetration
                return None
            else:
                # Both are circles/spheres - handle as circle vs circle
                return self._circle_vs_circle_collision(bounds_a, bounds_b)
    
    def _rect_vs_rect_collision(self, rect_a, rect_b) -> Optional[Tuple[bool, Vec2, float]]:
        """Check collision between two rectangles."""
        min_x_a, min_y_a, max_x_a, max_y_a = rect_a
        min_x_b, min_y_b, max_x_b, max_y_b = rect_b
        
        # Check for overlap
        if (max_x_a < min_x_b or max_x_b < min_x_a or
            max_y_a < min_y_b or max_y_b < min_y_a):
            return None
        
        # Calculate overlap amounts
        overlap_x = min(max_x_a, max_x_b) - max(min_x_a, min_x_b)
        overlap_y = min(max_y_a, max_y_b) - max(min_y_a, min_y_b)
        
        # Find minimum translation vector
        if overlap_x < overlap_y:
            # Separate horizontally
            center_a_x = (min_x_a + max_x_a) / 2
            center_b_x = (min_x_b + max_x_b) / 2
            normal = Vec2(1, 0) if center_a_x < center_b_x else Vec2(-1, 0)
            penetration = overlap_x
        else:
            # Separate vertically
            center_a_y = (min_y_a + max_y_a) / 2
            center_b_y = (min_y_b + max_y_b) / 2
            normal = Vec2(0, 1) if center_a_y < center_b_y else Vec2(0, -1)
            penetration = overlap_y
        
        return True, normal, penetration
    
    def _circle_vs_circle_collision(self, circle_a, circle_b) -> Optional[Tuple[bool, Vec2, float]]:
        """Check collision between two circles."""
        center_a_x, center_a_y, radius_a = circle_a
        center_b_x, center_b_y, radius_b = circle_b
        
        # Calculate distance between centers
        dx = center_b_x - center_a_x
        dy = center_b_y - center_a_y
        distance = math.sqrt(dx * dx + dy * dy)
        
        # Check if circles overlap
        combined_radius = radius_a + radius_b
        if distance >= combined_radius:
            return None
        
        # Calculate collision normal
        if distance > 0:
            normal = Vec2(dx / distance, dy / distance)
        else:
            normal = Vec2(1, 0)  # Arbitrary direction for identical centers
        
        penetration = combined_radius - distance
        return True, normal, penetration
    
    def _rect_vs_circle_collision(self, rect, circle) -> Optional[Tuple[bool, Vec2, float]]:
        """Check collision between rectangle and circle."""
        min_x, min_y, max_x, max_y = rect
        center_x, center_y, radius = circle
        
        # Find closest point on rectangle to circle center
        closest_x = max(min_x, min(center_x, max_x))
        closest_y = max(min_y, min(center_y, max_y))
        
        # Calculate distance from circle center to closest point
        dx = center_x - closest_x
        dy = center_y - closest_y
        distance = math.sqrt(dx * dx + dy * dy)
        
        # Check if circle overlaps with rectangle
        if distance >= radius:
            return None
        
        # Calculate collision normal
        if distance > 0:
            normal = Vec2(dx / distance, dy / distance)
        else:
            # Circle center is inside rectangle
            # Find normal based on closest edge
            left_dist = center_x - min_x
            right_dist = max_x - center_x
            top_dist = max_y - center_y
            bottom_dist = center_y - min_y
            
            min_dist = min(left_dist, right_dist, top_dist, bottom_dist)
            
            if min_dist == left_dist:
                normal = Vec2(-1, 0)
            elif min_dist == right_dist:
                normal = Vec2(1, 0)
            elif min_dist == top_dist:
                normal = Vec2(0, 1)
            else:
                normal = Vec2(0, -1)
        
        penetration = radius - distance
        return True, normal, penetration
    
    def _fire_trigger_events(self, entities_with_colliders):
        """Fire trigger enter/exit events."""
        for entity in entities_with_colliders:
            collider = self.world.get_component(entity.id, ColliderComponent)
            if not collider or not collider.is_trigger:
                continue
            
            # Check for new collisions (trigger enter)
            new_collisions = collider.colliding_entities - collider.was_colliding_entities
            for other_entity_id in new_collisions:
                self.world.event_manager.publish(
                    TriggerEnterEvent(entity.id, other_entity_id)
                )
            
            # Check for ended collisions (trigger exit)
            ended_collisions = collider.was_colliding_entities - collider.colliding_entities
            for other_entity_id in ended_collisions:
                self.world.event_manager.publish(
                    TriggerExitEvent(entity.id, other_entity_id)
                )
