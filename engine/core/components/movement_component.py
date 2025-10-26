from panda3d.core import Vec2
from engine.core.component import Component
from typing import Dict

class MovementComponent(Component):
    """
    Handles movement properties for entities including base speed, acceleration,
    and dynamic speed modifiers for status effects.
    """
    def __init__(self, 
                 base_speed: float = 1.0,
                 acceleration: float = 10.0,
                 deceleration: float = 10.0,
                 max_speed_multiplier: float = 3.0):
        # Base movement properties
        self.base_speed = base_speed
        self.acceleration = acceleration  # How quickly to reach target speed
        self.deceleration = deceleration  # How quickly to stop when no input
        self.max_speed_multiplier = max_speed_multiplier  # Maximum speed boost allowed
        
        # Current movement state
        self.current_velocity = Vec2(0, 0)
        self.target_velocity = Vec2(0, 0)
        
        # Speed modifiers (multiplicative effects)
        # Key: effect name, Value: (multiplier, duration_remaining)
        # Example: {"slowdown": (0.5, 3.0), "speed_boost": (2.0, 5.0)}
        self.speed_modifiers: Dict[str, tuple[float, float]] = {}
        
        # Movement state flags
        self.is_moving = False
        self.can_move = True  # Can be set to False to disable movement entirely
        
    def add_speed_modifier(self, effect_name: str, multiplier: float, duration: float):
        """
        Add a temporary speed modifier effect.
        
        Args:
            effect_name: Unique name for the effect (e.g., "slowdown", "speed_boost")
            multiplier: Speed multiplier (0.5 = half speed, 2.0 = double speed)
            duration: How long the effect lasts in seconds
        """
        self.speed_modifiers[effect_name] = (multiplier, duration)
        print(f"Applied {effect_name} effect: {multiplier}x speed for {duration}s")
    
    def remove_speed_modifier(self, effect_name: str):
        """Remove a specific speed modifier effect."""
        if effect_name in self.speed_modifiers:
            del self.speed_modifiers[effect_name]
            print(f"Removed {effect_name} effect")
    
    def get_effective_speed(self) -> float:
        """
        Calculate the current effective speed including all modifiers.
        """
        if not self.can_move:
            return 0.0
            
        # Start with base speed
        effective_speed = self.base_speed
        
        # Apply all active speed modifiers
        total_multiplier = 1.0
        for _, (multiplier, _) in self.speed_modifiers.items():
            total_multiplier *= multiplier
        
        effective_speed *= total_multiplier
        
        # Clamp to reasonable limits
        max_speed = self.base_speed * self.max_speed_multiplier
        effective_speed = min(effective_speed, max_speed)
        effective_speed = max(effective_speed, 0.0)  # Can't go negative
        
        return effective_speed
    
    def update_modifiers(self, dt: float):
        """
        Update speed modifier durations and remove expired effects.
        Call this every frame.
        """
        expired_effects = []
        
        for effect_name, (multiplier, duration) in self.speed_modifiers.items():
            new_duration = duration - dt
            if new_duration <= 0:
                expired_effects.append(effect_name)
            else:
                self.speed_modifiers[effect_name] = (multiplier, new_duration)
        
        # Remove expired effects
        for effect_name in expired_effects:
            self.remove_speed_modifier(effect_name)
    
    def set_target_direction(self, direction: Vec2):
        """
        Set the target movement direction. The actual velocity will smoothly
        interpolate toward this target based on acceleration.
        """
        if not self.can_move:
            self.target_velocity = Vec2(0, 0)
            return
            
        # Normalize direction and apply current effective speed
        if direction.length() > 0:
            direction.normalize()
            effective_speed = self.get_effective_speed()
            self.target_velocity = direction * effective_speed
            self.is_moving = True
        else:
            self.target_velocity = Vec2(0, 0)
            self.is_moving = False
    
    def update_velocity(self, dt: float):
        """
        Update the current velocity toward the target velocity using acceleration.
        """
        if not self.can_move:
            self.current_velocity = Vec2(0, 0)
            return
            
        # Choose acceleration or deceleration
        accel_rate = self.acceleration if self.is_moving else self.deceleration
        
        # Smooth interpolation toward target velocity
        velocity_diff = self.target_velocity - self.current_velocity
        accel_amount = velocity_diff * accel_rate * dt
        
        # Clamp acceleration to prevent overshooting
        if accel_amount.length() > velocity_diff.length():
            self.current_velocity = self.target_velocity
        else:
            self.current_velocity += accel_amount
        
        # Apply very small threshold to stop micro-movements
        if self.current_velocity.length() < 0.01:
            self.current_velocity = Vec2(0, 0)
            self.is_moving = False
