"""
Enemy AI System

System for managing enemy AI behavior, movement, and combat.
"""
import random
import math
from typing import Optional
from panda3d.core import Vec2

from engine.core.system import System
from engine.graphics.components.transform_component import TransformComponent
from engine.physics.components.enemy_ai_component import EnemyAIComponent
from engine.physics.systems.projectile_system import ProjectileSystem


class EnemyAISystem(System):
    """
    System for managing enemy AI behavior.

    Handles enemy movement patterns, shooting, and decision making.
    """

    def __init__(self, world, projectile_system: ProjectileSystem):
        super().__init__(world)
        self.projectile_system = projectile_system

    def update(self, dt: float):
        """Update all enemy AI entities."""
        # Find player position for targeting
        player_position = self._find_player_position()

        for entity in self.world.get_entities_with_components(
            EnemyAIComponent, TransformComponent
        ):
            ai_comp = self.world.get_component(entity.id, EnemyAIComponent)
            transform_comp = self.world.get_component(entity.id, TransformComponent)

            if not ai_comp or not transform_comp:
                continue

            # Initialize spawn position if not set
            if ai_comp.spawn_position == Vec2(0, 0):
                ai_comp.spawn_position = Vec2(transform_comp.x, transform_comp.y)

            # Update AI behavior
            self._update_enemy_behavior(entity.id, ai_comp, transform_comp, player_position, dt)

    def _find_player_position(self) -> Optional[Vec2]:
        """Find the player's current position."""
        for entity in self.world.get_entities_with_components(TransformComponent):
            # Simple heuristic: look for entity named "player"
            if hasattr(entity, 'name') and entity.name == "player":
                transform_comp = self.world.get_component(entity.id, TransformComponent)
                if transform_comp:
                    return Vec2(transform_comp.x, transform_comp.y)
        return None

    def _update_enemy_behavior(self, entity_id: str, ai_comp: EnemyAIComponent,
                              transform_comp: TransformComponent, player_position: Optional[Vec2], dt: float):
        """Update individual enemy behavior."""
        current_pos = Vec2(transform_comp.x, transform_comp.y)

        # Update timers
        ai_comp.time_since_last_shot += dt
        ai_comp.patrol_timer += dt

        # Check if player is in range
        if player_position:
            distance_to_player = ((current_pos.x - player_position.x) ** 2 +
                                (current_pos.y - player_position.y) ** 2) ** 0.5

            if distance_to_player <= ai_comp.aggression_range:
                # Player is in range - become aggressive
                self._handle_aggressive_behavior(entity_id, ai_comp, transform_comp, player_position, dt)
            else:
                # Player is out of range - patrol
                self._handle_patrol_behavior(ai_comp, transform_comp, dt)
        else:
            # No player found - patrol
            self._handle_patrol_behavior(ai_comp, transform_comp, dt)

        # Keep enemy on screen bounds
        transform_comp.x = max(-4, min(4, transform_comp.x))
        transform_comp.y = max(-3, min(3, transform_comp.y))

    def _handle_aggressive_behavior(self, entity_id: str, ai_comp: EnemyAIComponent,
                                   transform_comp: TransformComponent, player_position: Vec2, dt: float):
        """Handle enemy behavior when player is in range."""
        current_pos = Vec2(transform_comp.x, transform_comp.y)

        # Move towards player (but not too close)
        direction_to_player = player_position - current_pos
        distance = math.sqrt(direction_to_player.x ** 2 + direction_to_player.y ** 2)

        if distance > 1.0:  # Keep some distance
            # Normalize direction
            if distance > 0:
                direction_to_player.x /= distance
                direction_to_player.y /= distance

            # Move towards player
            transform_comp.x += direction_to_player.x * ai_comp.movement_speed * dt
            transform_comp.y += direction_to_player.y * ai_comp.movement_speed * dt

        # Try to shoot at player
        if ai_comp.time_since_last_shot >= ai_comp.shoot_cooldown:
            self._shoot_at_target(entity_id, current_pos, player_position)
            ai_comp.time_since_last_shot = 0.0

    def _handle_patrol_behavior(self, ai_comp: EnemyAIComponent, transform_comp: TransformComponent, dt: float):
        """Handle enemy patrol behavior when player is out of range."""
        # Change direction periodically
        if ai_comp.patrol_timer >= ai_comp.patrol_change_time:
            # Pick a new random direction
            angle = random.uniform(0, 2 * math.pi)
            ai_comp.movement_direction = Vec2(math.cos(angle), math.sin(angle))
            ai_comp.patrol_timer = 0.0

        # Move in current direction
        transform_comp.x += ai_comp.movement_direction.x * ai_comp.movement_speed * dt
        transform_comp.y += ai_comp.movement_direction.y * ai_comp.movement_speed * dt

        # Check if we've moved too far from spawn point
        current_pos = Vec2(transform_comp.x, transform_comp.y)
        distance_from_spawn = ((current_pos.x - ai_comp.spawn_position.x) ** 2 +
                             (current_pos.y - ai_comp.spawn_position.y) ** 2) ** 0.5

        if distance_from_spawn > ai_comp.patrol_radius:
            # Move back towards spawn point
            direction_to_spawn = ai_comp.spawn_position - current_pos
            distance = math.sqrt(direction_to_spawn.x ** 2 + direction_to_spawn.y ** 2)
            if distance > 0:
                direction_to_spawn.x /= distance
                direction_to_spawn.y /= distance

            transform_comp.x += direction_to_spawn.x * ai_comp.movement_speed * dt
            transform_comp.y += direction_to_spawn.y * ai_comp.movement_speed * dt

    def _shoot_at_target(self, entity_id: str, shooter_pos: Vec2, target_pos: Vec2):
        """Make enemy shoot a projectile at the target."""
        direction = target_pos - shooter_pos
        self.projectile_system.create_projectile(
            position=shooter_pos,
            direction=direction,
            speed=4.0,
            lifetime=2.0,
            damage=1.0,
            owner_entity_id=entity_id,
            projectile_type="enemy_bullet"
        )
