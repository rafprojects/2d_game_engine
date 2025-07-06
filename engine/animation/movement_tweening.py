"""
Movement Tweening Component - Adds visual tweening effects to movement.

This component works alongside MovementComponent to provide smooth visual
animations and effects that enhance the feel of movement without affecting
the core movement logic.
"""

import math
from panda3d.core import Vec2
from engine.core.component import Component
from engine.animation.tweening import EasingType, TweenManager
from typing import Optional, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from engine.animation.tweening import Tween

class MovementTweenComponent(Component):
    """
    Provides visual tweening effects for movement including:
    - Smooth visual position interpolation separate from physics
    - Acceleration/deceleration visual effects
    - Bounce effects on direction changes
    - Scale effects during movement
    - Rotation effects during movement
    """
    
    def __init__(self):
        # Visual position (separate from physics position)
        self.visual_position = Vec2(0, 0)
        self.visual_scale = Vec2(1, 1)
        self.visual_rotation = 0.0
        
        # Tweening settings
        self.position_smoothing = True
        self.position_easing = EasingType.EASE_OUT_CUBIC
        self.position_lag = 0.1  # How much the visual lags behind actual position
        
        # Movement effects
        self.bounce_on_direction_change = True
        self.bounce_scale = 0.15  # How much to scale during bounce
        self.bounce_duration = 0.2
        
        self.scale_on_movement = True
        self.movement_scale_factor = 0.1  # How much to scale when moving
        self.scale_easing = EasingType.EASE_OUT_BOUNCE
        
        self.rotate_on_movement = False
        self.rotation_speed = 180.0  # Degrees per second when moving
        self.rotation_easing = EasingType.EASE_IN_OUT_SINE
        
        # Internal state
        self._last_direction = Vec2(0, 0)
        self._is_moving = False
        self._tween_manager = TweenManager()
        self._current_scale_target = Vec2(1, 1)  # Track current scale target
        
        # Base values (set from transform component)
        self._base_scale = Vec2(1, 1)
        self._base_rotation = 0.0
    
    def set_base_transform(self, position: Vec2, scale: Vec2, rotation: float):
        """Set the base transform values from the TransformComponent."""
        self.visual_position = Vec2(position)
        self.visual_scale = Vec2(scale)
        self.visual_rotation = rotation
        self._base_scale = Vec2(scale)
        self._base_rotation = rotation
    
    def update_visual_position(self, target_position: Vec2, dt: float):
        """Update visual position with smooth interpolation."""
        if not self.position_smoothing:
            self.visual_position = Vec2(target_position)
            return
        
        # Smooth interpolation to target position
        distance = target_position - self.visual_position
        if distance.length() > 0.001:  # Only move if there's significant distance
            # Use exponential smoothing for natural feel
            smoothing_factor = 1.0 - pow(self.position_lag, dt)
            self.visual_position += distance * smoothing_factor
    
    def update_movement_effects(self, current_velocity: Vec2, is_moving: bool, dt: float):
        """Update visual effects based on movement state."""
        direction = Vec2(0, 0)
        if current_velocity.length() > 0.01:
            direction = Vec2(current_velocity)
            direction.normalize()
        
        # Check for direction change
        if self.bounce_on_direction_change and is_moving:
            direction_change = (direction - self._last_direction).length()
            if direction_change > 1.5 and self._is_moving:  # Significant direction change
                self._trigger_bounce_effect()
        
        # Update movement scale effect
        if self.scale_on_movement:
            self._update_movement_scale(is_moving)
        
        # Update rotation effect
        if self.rotate_on_movement:
            self._update_movement_rotation(current_velocity, dt)
        
        self._last_direction = direction
        self._is_moving = is_moving
        
        # Update all tweens
        self._tween_manager.update(dt)
    
    def _trigger_bounce_effect(self):
        """Trigger a bounce effect on direction change."""
        # Stop existing scale tweens
        self._tween_manager.stop_all_tweens(self)
        
        # Scale up then back down for bounce effect
        bounce_scale = self._base_scale * (1.0 + self.bounce_scale)
        
        # Tween to bounce scale
        self._tween_manager.tween_to(
            self, 'visual_scale', bounce_scale, 
            self.bounce_duration * 0.3, 
            EasingType.EASE_OUT_CUBIC,
            on_complete=lambda: self._tween_manager.tween_to(
                self, 'visual_scale', self._base_scale,
                self.bounce_duration * 0.7,
                EasingType.EASE_OUT_BOUNCE
            )
        )
    
    def _update_movement_scale(self, is_moving: bool):
        """Update scale based on movement state."""
        target_scale = self._base_scale
        if is_moving:
            # Slightly larger when moving
            scale_multiplier = 1.0 + self.movement_scale_factor
            target_scale = self._base_scale * scale_multiplier
        
        # Check if we need to start a new tween
        current_target = getattr(self, '_current_scale_target', None)
        if current_target != target_scale:
            self._current_scale_target = target_scale
            
            # Stop existing scale tweens for movement (not bounce)
            for tween in self._tween_manager.tweens:
                if (tween.target == self and tween.property_name == 'visual_scale' 
                    and not hasattr(tween, '_is_bounce')):
                    tween.stop()
            
            # Tween to new scale
            self._tween_manager.tween_to(
                self, 'visual_scale', target_scale,
                0.2, self.scale_easing
            )
    
    def _update_movement_rotation(self, velocity: Vec2, dt: float):
        """Update rotation based on movement direction."""
        if velocity.length() > 0.01:
            self._rotate_towards_movement(velocity, dt)
        else:
            self._rotate_to_base(dt)
    
    def _rotate_towards_movement(self, velocity: Vec2, dt: float):
        """Rotate towards movement direction."""
        target_rotation = math.atan2(velocity.y, velocity.x) * 180.0 / math.pi
        self._smooth_rotate_to(target_rotation, dt, self.rotation_speed)
    
    def _rotate_to_base(self, dt: float):
        """Rotate back to base rotation when not moving."""
        self._smooth_rotate_to(self._base_rotation, dt, self.rotation_speed * 0.5)
    
    def _smooth_rotate_to(self, target_rotation: float, dt: float, speed: float):
        """Smoothly rotate to target rotation."""
        rotation_diff = target_rotation - self.visual_rotation
        
        # Handle angle wrapping
        while rotation_diff > 180:
            rotation_diff -= 360
        while rotation_diff < -180:
            rotation_diff += 360
        
        # Apply rotation smoothing
        rotation_speed = speed * dt
        if abs(rotation_diff) < rotation_speed:
            self.visual_rotation = target_rotation
        else:
            self.visual_rotation += rotation_speed * (1 if rotation_diff > 0 else -1)
    
    def create_custom_effect(self, property_name: str, end_value, duration: float,
                           easing: EasingType = EasingType.LINEAR,
                           on_complete: Optional[Callable] = None):
        """Create a custom tween effect on any property of this component."""
        return self._tween_manager.tween_to(
            self, property_name, end_value, duration, easing, on_complete
        )
    
    def stop_all_effects(self):
        """Stop all active tween effects."""
        self._tween_manager.stop_all_tweens(self)
    
    def enable_juice_effects(self):
        """Enable all 'juice' effects for maximum visual appeal."""
        self.position_smoothing = True
        self.bounce_on_direction_change = True
        self.scale_on_movement = True
        self.position_lag = 0.15
        self.bounce_scale = 0.2
        self.movement_scale_factor = 0.15
        self.position_easing = EasingType.EASE_OUT_CUBIC
        self.scale_easing = EasingType.EASE_OUT_BOUNCE
    
    def disable_all_effects(self):
        """Disable all visual effects for direct 1:1 movement."""
        self.position_smoothing = False
        self.bounce_on_direction_change = False
        self.scale_on_movement = False
        self.rotate_on_movement = False
        self.stop_all_effects()
    
    def set_preset(self, preset_name: str):
        """Set predefined effect presets."""
        if preset_name == "snappy":
            self.position_lag = 0.05
            self.bounce_scale = 0.25
            self.movement_scale_factor = 0.2
            self.position_easing = EasingType.EASE_OUT_QUART
            self.scale_easing = EasingType.EASE_OUT_BOUNCE
        elif preset_name == "smooth":
            self.position_lag = 0.2
            self.bounce_scale = 0.1
            self.movement_scale_factor = 0.05
            self.position_easing = EasingType.EASE_OUT_SINE
            self.scale_easing = EasingType.EASE_IN_OUT_CUBIC
        elif preset_name == "bouncy":
            self.position_lag = 0.1
            self.bounce_scale = 0.3
            self.movement_scale_factor = 0.25
            self.bounce_duration = 0.3
            self.position_easing = EasingType.EASE_OUT_BOUNCE
            self.scale_easing = EasingType.EASE_OUT_BOUNCE
        elif preset_name == "elastic":
            self.position_lag = 0.15
            self.bounce_scale = 0.2
            self.movement_scale_factor = 0.15
            self.position_easing = EasingType.EASE_OUT_ELASTIC
            self.scale_easing = EasingType.EASE_OUT_ELASTIC
