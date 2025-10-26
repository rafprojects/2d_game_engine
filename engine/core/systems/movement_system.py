from panda3d.core import Vec2

from engine.core.system import System
from engine.core.components.movement_component import MovementComponent
from engine.input.components.input_component import InputComponent
from engine.graphics.components.transform_component import TransformComponent

# Optional import for tweening effects
try:
    from engine.animation.movement_tweening import MovementTweenComponent
    TWEENING_AVAILABLE = True
except ImportError:
    TWEENING_AVAILABLE = False
    MovementTweenComponent = None

class MovementSystem(System):
    """
    Handles entity movement based on MovementComponent and input.
    Supports smooth acceleration, deceleration, and speed modifiers.
    """
    
    def __init__(self, world):
        super().__init__(world)
    
    def update(self, dt: float):
        """Update movement for all entities with MovementComponent."""
        
        # Update all entities with movement components
        movement_entities = self.world.get_entities_with_components(MovementComponent, TransformComponent)
        
        for entity in movement_entities:
            movement = self.world.get_component(entity.id, MovementComponent)
            transform = self.world.get_component(entity.id, TransformComponent)
            
            if not movement or not transform:
                continue
            
            # Update speed modifier durations
            movement.update_modifiers(dt)
            
            # Handle input-based movement
            input_comp = self.world.get_component(entity.id, InputComponent)
            if input_comp:
                self._handle_input_movement(input_comp, movement)
            
            # Update velocity based on acceleration
            movement.update_velocity(dt)
            
            # Apply movement to transform
            transform.position += movement.current_velocity * dt
            
            # Update tweening effects if available
            if TWEENING_AVAILABLE:
                tween_comp = self.world.get_component(entity.id, MovementTweenComponent)
                if tween_comp:
                    # Update visual effects based on movement
                    tween_comp.update_visual_position(transform.position, dt)
                    tween_comp.update_movement_effects(movement.current_velocity, movement.is_moving, dt)
                    
                    # Apply visual transform to the actual transform for rendering
                    # Note: This creates a separation between physics position and visual position
                    transform.position = Vec2(tween_comp.visual_position)
                    transform.scale = Vec2(tween_comp.visual_scale)
                    transform.rotation = tween_comp.visual_rotation
            
            # Optional: Clamp to screen bounds (adjust these values as needed)
            # self._clamp_to_bounds(transform)
    
    def _handle_input_movement(self, input_comp: InputComponent, movement: MovementComponent):
        """Process input and set target movement direction."""
        direction = Vec2(0, 0)
        
        # Gather input from all directions
        if input_comp.action_active.get("move_left", False):
            direction.x -= 1
        if input_comp.action_active.get("move_right", False):
            direction.x += 1
        if input_comp.action_active.get("move_up", False):
            direction.y += 1
        if input_comp.action_active.get("move_down", False):
            direction.y -= 1
        
        # Set the target direction for the movement component
        movement.set_target_direction(direction)
    
    def _clamp_to_bounds(self, transform: TransformComponent):
        """Optional: Keep entities within screen bounds."""
        # For aspect2d coordinate system
        min_x, max_x = -1.5, 1.5  # Adjust based on your screen aspect ratio
        min_y, max_y = -1.0, 1.0
        
        transform.position.x = max(min_x, min(max_x, transform.position.x))
        transform.position.y = max(min_y, min(max_y, transform.position.y))
    
    def apply_speed_effect(self, entity_id, effect_name: str, multiplier: float, duration: float):
        """
        Apply a speed effect to a specific entity.
        
        Args:
            entity_id: The entity to apply the effect to
            effect_name: Unique name for the effect
            multiplier: Speed multiplier (0.5 = half speed, 2.0 = double speed)
            duration: How long the effect lasts in seconds
        """
        movement = self.world.get_component(entity_id, MovementComponent)
        if movement:
            movement.add_speed_modifier(effect_name, multiplier, duration)
    
    def remove_speed_effect(self, entity_id, effect_name: str):
        """Remove a specific speed effect from an entity."""
        movement = self.world.get_component(entity_id, MovementComponent)
        if movement:
            movement.remove_speed_modifier(effect_name)
    
    def set_movement_enabled(self, entity_id, enabled: bool):
        """Enable or disable movement for an entity (useful for stunned/frozen states)."""
        movement = self.world.get_component(entity_id, MovementComponent)
        if movement:
            movement.can_move = enabled
