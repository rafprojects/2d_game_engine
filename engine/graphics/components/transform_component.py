"""
Transform Component for 2D positioning, rotation, and scale.
"""

from dataclasses import dataclass
from engine.core.component import Component


@dataclass
class TransformComponent(Component):
    """Component for 2D transform properties."""
    x: float = 0.0
    y: float = 0.0
    rotation: float = 0.0
    scale_x: float = 1.0
    scale_y: float = 1.0
    
    def get_position(self) -> tuple[float, float]:
        """Get the position as a tuple."""
        return (self.x, self.y)
    
    def set_position(self, x: float, y: float):
        """Set the position."""
        self.x = x
        self.y = y
    
    def get_scale(self) -> tuple[float, float]:
        """Get the scale as a tuple."""
        return (self.scale_x, self.scale_y)
    
    def set_scale(self, scale_x: float, scale_y: float):
        """Set the scale."""
        self.scale_x = scale_x
        self.scale_y = scale_y
