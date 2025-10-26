"""
Projectile Component

Component for managing projectile entities in the game.
"""
from typing import Optional
from panda3d.core import Vec2

from engine.core.component import Component


class ProjectileComponent(Component):
    """
    Component for projectile entities.

    Handles projectile movement, lifetime, and collision behavior.
    """

    def __init__(self,
                 velocity: Vec2 = Vec2(0, 0),
                 speed: float = 5.0,
                 lifetime: float = 3.0,
                 damage: float = 1.0,
                 owner_entity_id: Optional[str] = None,
                 projectile_type: str = "bullet"):
        """
        Initialize a projectile component.

        Args:
            velocity: Initial velocity vector
            speed: Movement speed
            lifetime: How long the projectile lives (seconds)
            damage: Damage dealt on collision
            owner_entity_id: ID of the entity that fired this projectile
            projectile_type: Type of projectile ("bullet", "laser", etc.)
        """
        self.velocity = velocity
        self.speed = speed
        self.lifetime = lifetime
        self.damage = damage
        self.owner_entity_id = owner_entity_id
        self.projectile_type = projectile_type

        # Runtime state
        self.time_alive = 0.0
        self.is_alive = True
