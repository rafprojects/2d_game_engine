from panda3d.core import Vec2, Vec3
from engine.core.component import Component

class TransformComponent(Component):
    def __init__(self, position: Vec2 = Vec2(0, 0), rotation: float = 0.0, scale: Vec2 = Vec2(1, 1)):
        self.position = position  # For 2D, z can be used for depth sorting if needed, or use a dedicated layer property
        self.rotation = rotation  # In degrees
        self.scale = scale
