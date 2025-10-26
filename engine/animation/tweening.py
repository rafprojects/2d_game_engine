"""
Tweening and Easing System for smooth animations and movement effects.

This module provides various easing functions and a tween manager for creating
smooth animations and visual effects.
"""
import math
from typing import Callable, Any, Dict, List, Optional

from panda3d.core import Vec2, Vec3

from engine.animation.typesg.animation import EasingType

class EasingFunctions:
    """Collection of easing functions for smooth animations."""
    
    @staticmethod
    def linear(t: float) -> float:
        """Linear interpolation (no easing)."""
        return t
    
    @staticmethod
    def ease_in_quad(t: float) -> float:
        """Quadratic ease-in."""
        return t * t
    
    @staticmethod
    def ease_out_quad(t: float) -> float:
        """Quadratic ease-out."""
        return 1 - (1 - t) * (1 - t)
    
    @staticmethod
    def ease_in_out_quad(t: float) -> float:
        """Quadratic ease-in-out."""
        return 2 * t * t if t < 0.5 else 1 - pow(-2 * t + 2, 2) / 2
    
    @staticmethod
    def ease_in_cubic(t: float) -> float:
        """Cubic ease-in."""
        return t * t * t
    
    @staticmethod
    def ease_out_cubic(t: float) -> float:
        """Cubic ease-out."""
        return 1 - pow(1 - t, 3)
    
    @staticmethod
    def ease_in_out_cubic(t: float) -> float:
        """Cubic ease-in-out."""
        return 4 * t * t * t if t < 0.5 else 1 - pow(-2 * t + 2, 3) / 2
    
    @staticmethod
    def ease_in_quart(t: float) -> float:
        """Quartic ease-in."""
        return t * t * t * t
    
    @staticmethod
    def ease_out_quart(t: float) -> float:
        """Quartic ease-out."""
        return 1 - pow(1 - t, 4)
    
    @staticmethod
    def ease_in_out_quart(t: float) -> float:
        """Quartic ease-in-out."""
        return 8 * t * t * t * t if t < 0.5 else 1 - pow(-2 * t + 2, 4) / 2
    
    @staticmethod
    def ease_in_sine(t: float) -> float:
        """Sine ease-in."""
        return 1 - math.cos((t * math.pi) / 2)
    
    @staticmethod
    def ease_out_sine(t: float) -> float:
        """Sine ease-out."""
        return math.sin((t * math.pi) / 2)
    
    @staticmethod
    def ease_in_out_sine(t: float) -> float:
        """Sine ease-in-out."""
        return -(math.cos(math.pi * t) - 1) / 2
    
    @staticmethod
    def ease_in_expo(t: float) -> float:
        """Exponential ease-in."""
        return 0 if t == 0 else pow(2, 10 * (t - 1))
    
    @staticmethod
    def ease_out_expo(t: float) -> float:
        """Exponential ease-out."""
        return 1 if t == 1 else 1 - pow(2, -10 * t)
    
    @staticmethod
    def ease_in_out_expo(t: float) -> float:
        """Exponential ease-in-out."""
        if t == 0:
            return 0
        elif t == 1:
            return 1
        elif t < 0.5:
            return pow(2, 20 * t - 10) / 2
        else:
            return (2 - pow(2, -20 * t + 10)) / 2
    
    @staticmethod
    def ease_out_bounce(t: float) -> float:
        """Bounce ease-out."""
        n1 = 7.5625
        d1 = 2.75
        
        if t < 1 / d1:
            return n1 * t * t
        elif t < 2 / d1:
            t -= 1.5 / d1
            return n1 * t * t + 0.75
        elif t < 2.5 / d1:
            t -= 2.25 / d1
            return n1 * t * t + 0.9375
        else:
            t -= 2.625 / d1
            return n1 * t * t + 0.984375
    
    @staticmethod
    def ease_in_bounce(t: float) -> float:
        """Bounce ease-in."""
        return 1 - EasingFunctions.ease_out_bounce(1 - t)
    
    @staticmethod
    def ease_in_out_bounce(t: float) -> float:
        """Bounce ease-in-out."""
        return (1 - EasingFunctions.ease_out_bounce(1 - 2 * t)) / 2 if t < 0.5 else (1 + EasingFunctions.ease_out_bounce(2 * t - 1)) / 2
    
    @staticmethod
    def ease_out_elastic(t: float) -> float:
        """Elastic ease-out."""
        c4 = (2 * math.pi) / 3
        
        if t == 0:
            return 0
        elif t == 1:
            return 1
        else:
            return pow(2, -10 * t) * math.sin((t * 10 - 0.75) * c4) + 1
    
    @staticmethod
    def ease_in_elastic(t: float) -> float:
        """Elastic ease-in."""
        c4 = (2 * math.pi) / 3
        
        if t == 0:
            return 0
        elif t == 1:
            return 1
        else:
            return -pow(2, 10 * t - 10) * math.sin((t * 10 - 10.75) * c4)
    
    @staticmethod
    def ease_in_out_elastic(t: float) -> float:
        """Elastic ease-in-out."""
        c5 = (2 * math.pi) / 4.5
        
        if t == 0:
            return 0
        elif t == 1:
            return 1
        elif t < 0.5:
            return -(pow(2, 20 * t - 10) * math.sin((20 * t - 11.125) * c5)) / 2
        else:
            return (pow(2, -20 * t + 10) * math.sin((20 * t - 11.125) * c5)) / 2 + 1

    @staticmethod
    def get_easing_function(easing_type: EasingType) -> Callable[[float], float]:
        """Get the easing function for a given type."""
        mapping = {
            EasingType.LINEAR: EasingFunctions.linear,
            EasingType.EASE_IN_QUAD: EasingFunctions.ease_in_quad,
            EasingType.EASE_OUT_QUAD: EasingFunctions.ease_out_quad,
            EasingType.EASE_IN_OUT_QUAD: EasingFunctions.ease_in_out_quad,
            EasingType.EASE_IN_CUBIC: EasingFunctions.ease_in_cubic,
            EasingType.EASE_OUT_CUBIC: EasingFunctions.ease_out_cubic,
            EasingType.EASE_IN_OUT_CUBIC: EasingFunctions.ease_in_out_cubic,
            EasingType.EASE_IN_QUART: EasingFunctions.ease_in_quart,
            EasingType.EASE_OUT_QUART: EasingFunctions.ease_out_quart,
            EasingType.EASE_IN_OUT_QUART: EasingFunctions.ease_in_out_quart,
            EasingType.EASE_IN_SINE: EasingFunctions.ease_in_sine,
            EasingType.EASE_OUT_SINE: EasingFunctions.ease_out_sine,
            EasingType.EASE_IN_OUT_SINE: EasingFunctions.ease_in_out_sine,
            EasingType.EASE_IN_EXPO: EasingFunctions.ease_in_expo,
            EasingType.EASE_OUT_EXPO: EasingFunctions.ease_out_expo,
            EasingType.EASE_IN_OUT_EXPO: EasingFunctions.ease_in_out_expo,
            EasingType.EASE_IN_BOUNCE: EasingFunctions.ease_in_bounce,
            EasingType.EASE_OUT_BOUNCE: EasingFunctions.ease_out_bounce,
            EasingType.EASE_IN_OUT_BOUNCE: EasingFunctions.ease_in_out_bounce,
            EasingType.EASE_IN_ELASTIC: EasingFunctions.ease_in_elastic,
            EasingType.EASE_OUT_ELASTIC: EasingFunctions.ease_out_elastic,
            EasingType.EASE_IN_OUT_ELASTIC: EasingFunctions.ease_in_out_elastic,
        }
        return mapping.get(easing_type, EasingFunctions.linear)

class Tween:
    """A single tween animation."""
    
    def __init__(self, target: Any, property_name: str, start_value: Any, end_value: Any, 
                 duration: float, easing: EasingType = EasingType.LINEAR, 
                 on_complete: Optional[Callable] = None, on_update: Optional[Callable] = None):
        self.target = target
        self.property_name = property_name
        self.start_value = start_value
        self.end_value = end_value
        self.duration = duration
        self.elapsed_time = 0.0
        self.easing_function = EasingFunctions.get_easing_function(easing)
        self.on_complete = on_complete
        self.on_update = on_update
        self.is_active = True
        self.is_complete = False
    
    def update(self, dt: float) -> bool:
        """Update the tween. Returns False if tween is complete."""
        if not self.is_active or self.is_complete:
            return False
        
        self.elapsed_time += dt
        progress = min(self.elapsed_time / self.duration, 1.0)
        eased_progress = self.easing_function(progress)
        
        # Interpolate the value
        current_value = self._interpolate(self.start_value, self.end_value, eased_progress)
        
        # Set the property on the target
        setattr(self.target, self.property_name, current_value)
        
        # Call update callback
        if self.on_update:
            self.on_update(current_value, progress)
        
        # Check if complete
        if progress >= 1.0:
            self.is_complete = True
            if self.on_complete:
                self.on_complete()
            return False
        
        return True
    
    def _interpolate(self, start: Any, end: Any, t: float) -> Any:
        """Interpolate between start and end values."""
        if isinstance(start, (int, float)):
            return start + (end - start) * t
        elif isinstance(start, Vec2):
            return Vec2(
                start.x + (end.x - start.x) * t,
                start.y + (end.y - start.y) * t
            )
        elif isinstance(start, Vec3):
            return Vec3(
                start.x + (end.x - start.x) * t,
                start.y + (end.y - start.y) * t,
                start.z + (end.z - start.z) * t
            )
        else:
            # For other types, just return the end value when t >= 1
            return end if t >= 1.0 else start
    
    def stop(self):
        """Stop the tween."""
        self.is_active = False
    
    def restart(self):
        """Restart the tween from the beginning."""
        self.elapsed_time = 0.0
        self.is_active = True
        self.is_complete = False

class TweenManager:
    """Manages multiple tweens and provides convenience methods."""
    
    def __init__(self):
        self.tweens: List[Tween] = []
    
    def update(self, dt: float):
        """Update all active tweens."""
        # Update tweens and remove completed ones
        active_tweens = []
        for tween in self.tweens:
            if tween.update(dt):
                active_tweens.append(tween)
        self.tweens = active_tweens
    
    def add_tween(self, tween: Tween) -> Tween:
        """Add a tween to be managed."""
        self.tweens.append(tween)
        return tween
    
    def tween_to(self, target: Any, property_name: str, end_value: Any, duration: float,
                 easing: EasingType = EasingType.LINEAR,
                 on_complete: Optional[Callable] = None,
                 on_update: Optional[Callable] = None) -> Tween:
        """Create and add a tween to animate a property to a target value."""
        start_value = getattr(target, property_name)
        tween = Tween(target, property_name, start_value, end_value, duration, 
                     easing, on_complete, on_update)
        return self.add_tween(tween)
    
    def tween_from(self, target: Any, property_name: str, start_value: Any, duration: float,
                   easing: EasingType = EasingType.LINEAR,
                   on_complete: Optional[Callable] = None,
                   on_update: Optional[Callable] = None) -> Tween:
        """Create and add a tween to animate a property from a start value to current value."""
        end_value = getattr(target, property_name)
        setattr(target, property_name, start_value)  # Set initial value
        tween = Tween(target, property_name, start_value, end_value, duration,
                     easing, on_complete, on_update)
        return self.add_tween(tween)
    
    def stop_all_tweens(self, target: Any = None):
        """Stop all tweens, optionally filtering by target."""
        if target is None:
            for tween in self.tweens:
                tween.stop()
        else:
            for tween in self.tweens:
                if tween.target == target:
                    tween.stop()
    
    def get_active_count(self) -> int:
        """Get the number of active tweens."""
        return len([t for t in self.tweens if t.is_active and not t.is_complete])

# Global tween manager instance
global_tween_manager = TweenManager()
