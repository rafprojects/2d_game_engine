"""
Enemy AI Component

Component for managing enemy AI behavior.
"""
from panda3d.core import Vec2

from engine.core.component import Component


class EnemyAIComponent(Component):
    """
    Component for enemy AI behavior.

    Handles enemy movement patterns, shooting, and decision making.
    """

    def __init__(self,
                 movement_speed: float = 1.5,
                 shoot_cooldown: float = 2.0,
                 patrol_radius: float = 3.0,
                 aggression_range: float = 4.0):
        """
        Initialize enemy AI component.

        Args:
            movement_speed: How fast the enemy moves
            shoot_cooldown: Time between shots (seconds)
            patrol_radius: How far enemy patrols from spawn point
            aggression_range: Distance at which enemy becomes aggressive
        """
        self.movement_speed = movement_speed
        self.shoot_cooldown = shoot_cooldown
        self.patrol_radius = patrol_radius
        self.aggression_range = aggression_range

        # Runtime state
        self.spawn_position = Vec2(0, 0)
        self.current_target = Vec2(0, 0)
        self.time_since_last_shot = 0.0
        self.movement_direction = Vec2(1, 0)  # Default movement direction
        self.patrol_timer = 0.0
        self.patrol_change_time = 3.0  # Change direction every 3 seconds
