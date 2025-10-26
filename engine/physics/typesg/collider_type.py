from enum import Enum

class ColliderType(Enum):
    """Types of colliders supported by the physics system."""
    RECTANGLE = "rectangle"
    CIRCLE = "circle"
    SPHERE = "sphere"      # 3D sphere collision
    BOX = "box"           # 3D box collision
    CAPSULE = "capsule"   # Capsule for character controllers
    POLYGON = "polygon"   # Custom polygon shapes
