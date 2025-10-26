from engine.core.component import Component
from typing import Optional, Dict, Any, Callable
from panda3d.core import Vec2, Vec4

from engine.scene.typeg.scene_transition_types import TransitionType

class SceneTransitionComponent(Component):
    """
    Component for scene transition effects and management.
    
    Features:
    - Multiple transition types (fade, slide, wipe, etc.)
    - Customizable timing and easing
    - Transition callbacks and events
    - Progress tracking
    - Custom transition effects
    """
    
    def __init__(self,
                 transition_type: TransitionType = TransitionType.FADE,
                 duration: float = 1.0,
                 delay: float = 0.0,
                 easing: str = "ease_in_out",
                 reverse_on_exit: bool = False):
        """
        Initialize SceneTransitionComponent.
        
        Args:
            transition_type: Type of transition effect
            duration: Transition duration in seconds
            delay: Delay before transition starts
            easing: Easing function name
            reverse_on_exit: Whether to reverse transition when exiting
        """
        super().__init__()
        
        self.transition_type = transition_type
        self.duration = duration
        self.delay = delay
        self.easing = easing
        self.reverse_on_exit = reverse_on_exit
        
        # Transition state
        self.is_transitioning = False
        self.transition_direction = 1  # 1 for in, -1 for out
        self.current_time = 0.0
        self.progress = 0.0  # 0.0 to 1.0
        
        # Transition properties
        self.fade_color = Vec4(0, 0, 0, 1)  # Black by default
        self.slide_distance = Vec2(800, 600)  # Screen distance
        self.circle_center = Vec2(0.5, 0.5)  # Normalized screen position
        self.circle_max_radius = 1.0  # Normalized radius
        
        # Custom transition
        self.custom_transition_func: Optional[Callable] = None
        self.custom_transition_data: Dict[str, Any] = {}
        
        # Callbacks
        self.on_transition_start: Optional[Callable] = None
        self.on_transition_update: Optional[Callable] = None
        self.on_transition_complete: Optional[Callable] = None
        self.on_transition_interrupt: Optional[Callable] = None
        
        # Visual elements (managed by transition system)
        self.overlay_node = None  # Panda3D node for transition overlay
        self.transition_texture = None  # Custom transition texture
        
        # Performance settings
        self.use_shader_effects = True  # Use GPU shaders if available
        self.update_frequency = 60.0  # Updates per second
        self.skip_frames = False  # Skip intermediate frames for performance
    
    def start_transition_in(self):
        """Start transition into the scene."""
        self.is_transitioning = True
        self.transition_direction = 1
        self.current_time = 0.0
        self.progress = 0.0
        
        if self.on_transition_start:
            self.on_transition_start(self, "in")
    
    def start_transition_out(self):
        """Start transition out of the scene."""
        self.is_transitioning = True
        self.transition_direction = -1 if self.reverse_on_exit else 1
        self.current_time = 0.0
        self.progress = 0.0
        
        if self.on_transition_start:
            self.on_transition_start(self, "out")
    
    def update_transition(self, dt: float):
        """Update transition progress."""
        if not self.is_transitioning:
            return
        
        # Handle delay
        if self.current_time < self.delay:
            self.current_time += dt
            return
        
        # Update progress
        transition_time = self.current_time - self.delay
        raw_progress = min(transition_time / self.duration, 1.0)
        
        # Apply easing
        self.progress = self._apply_easing(raw_progress)
        
        # Update callback
        if self.on_transition_update:
            self.on_transition_update(self, self.progress)
        
        # Update timer
        self.current_time += dt
        
        # Check completion
        if raw_progress >= 1.0:
            self.complete_transition()
    
    def complete_transition(self):
        """Complete the current transition."""
        self.is_transitioning = False
        self.progress = 1.0
        
        if self.on_transition_complete:
            direction = "in" if self.transition_direction == 1 else "out"
            self.on_transition_complete(self, direction)
    
    def interrupt_transition(self):
        """Interrupt the current transition."""
        if self.is_transitioning:
            self.is_transitioning = False
            
            if self.on_transition_interrupt:
                self.on_transition_interrupt(self)
    
    def set_custom_transition(self, func: Callable, data: Optional[Dict[str, Any]] = None):
        """Set a custom transition function."""
        self.transition_type = TransitionType.CUSTOM
        self.custom_transition_func = func
        self.custom_transition_data = data or {}
    
    def set_fade_color(self, color: Vec4):
        """Set the fade transition color."""
        self.fade_color = color
    
    def set_slide_distance(self, distance: Vec2):
        """Set the slide transition distance."""
        self.slide_distance = distance
    
    def set_circle_properties(self, center: Vec2, max_radius: float):
        """Set circle transition properties."""
        self.circle_center = center
        self.circle_max_radius = max_radius
    
    def get_current_alpha(self) -> float:
        """Get current alpha value for fade transitions."""
        if self.transition_type in [TransitionType.FADE, TransitionType.FADE_THROUGH_COLOR]:
            if self.transition_direction == 1:  # Transitioning in
                return 1.0 - self.progress  # Start opaque, end transparent
            else:  # Transitioning out
                return self.progress  # Start transparent, end opaque
        return 0.0
    
    def get_current_offset(self) -> Vec2:
        """Get current offset for slide transitions."""
        if self.transition_type in [
            TransitionType.SLIDE_LEFT, TransitionType.SLIDE_RIGHT,
            TransitionType.SLIDE_UP, TransitionType.SLIDE_DOWN,
            TransitionType.PUSH_LEFT, TransitionType.PUSH_RIGHT
        ]:
            # Calculate offset based on direction and progress
            offset_multiplier = 1.0 - self.progress if self.transition_direction == 1 else self.progress
            
            if self.transition_type in [TransitionType.SLIDE_LEFT, TransitionType.PUSH_LEFT]:
                return Vec2(-self.slide_distance.x * offset_multiplier, 0)
            elif self.transition_type in [TransitionType.SLIDE_RIGHT, TransitionType.PUSH_RIGHT]:
                return Vec2(self.slide_distance.x * offset_multiplier, 0)
            elif self.transition_type == TransitionType.SLIDE_UP:
                return Vec2(0, self.slide_distance.y * offset_multiplier)
            elif self.transition_type == TransitionType.SLIDE_DOWN:
                return Vec2(0, -self.slide_distance.y * offset_multiplier)
        
        return Vec2(0, 0)
    
    def get_current_circle_radius(self) -> float:
        """Get current radius for circle transitions."""
        if self.transition_type in [TransitionType.CIRCLE_CLOSE, TransitionType.CIRCLE_OPEN]:
            if self.transition_type == TransitionType.CIRCLE_CLOSE:
                return self.circle_max_radius * (1.0 - self.progress)
            else:  # CIRCLE_OPEN
                return self.circle_max_radius * self.progress
        return 0.0
    
    def _apply_easing(self, t: float) -> float:
        """Apply easing function to progress value."""
        # Basic easing functions - could be expanded with more complex easing
        if self.easing == "linear":
            return t
        elif self.easing == "ease_in":
            return t * t
        elif self.easing == "ease_out":
            return 1 - (1 - t) * (1 - t)
        elif self.easing == "ease_in_out":
            if t < 0.5:
                return 2 * t * t
            else:
                return 1 - 2 * (1 - t) * (1 - t)
        elif self.easing == "ease_in_cubic":
            return t * t * t
        elif self.easing == "ease_out_cubic":
            return 1 - (1 - t) * (1 - t) * (1 - t)
        elif self.easing == "ease_in_out_cubic":
            if t < 0.5:
                return 4 * t * t * t
            else:
                return 1 - 4 * (1 - t) * (1 - t) * (1 - t)
        else:
            return t  # Default to linear
    
    def get_transition_info(self) -> Dict[str, Any]:
        """Get current transition information."""
        return {
            'type': self.transition_type.value,
            'is_transitioning': self.is_transitioning,
            'direction': 'in' if self.transition_direction == 1 else 'out',
            'progress': self.progress,
            'duration': self.duration,
            'current_time': self.current_time,
            'easing': self.easing,
            'alpha': self.get_current_alpha(),
            'offset': self.get_current_offset(),
            'circle_radius': self.get_current_circle_radius()
        }
