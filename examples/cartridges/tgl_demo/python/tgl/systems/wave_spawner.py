from __future__ import annotations

import math
import os
import random

from panda3d.core import Vec2

from engine.core.system import System
from engine.graphics.components.transform_component import TransformComponent
from engine.graphics.components.sprite_component import SpriteComponent
from engine.physics.components.collider_component import ColliderComponent
from engine.physics.typesg import ColliderType

from tgl.components.player_component import PlayerComponent
from tgl.components.enemy_component import EnemyComponent

LAYER_ENEMY = 2
# Enemy collides with player (layer 1) and bullets (layer 4)
ENEMY_COLLISION_MASK = (1 << (1 - 1)) | (1 << (4 - 1))  # = 1 | 8 = 9

SPAWN_INTERVAL = 1.5      # seconds between spawns
MAX_ENEMIES = 4           # max enemies on screen at once
SPAWN_Y = 1.15            # spawn just above top of screen
DESPAWN_Y = -1.2          # remove when off-screen bottom
ENEMY_X_RANGE = 0.8       # ±X range for spawning

PATTERNS = ["straight", "sinusoidal", "diagonal_left", "diagonal_right"]


def _asteroid_sprite_path() -> str:
    return os.path.join("assets", "sprites", "enemies", "asteroid", "asteroid.egg")


class WaveSpawnerSystem(System):
    """Timed enemy wave spawning and movement."""

    def __init__(self, world):
        super().__init__(world)
        self._spawn_timer: float = 0.0
        self._game_over: bool = False

    def update(self, dt: float):
        # Check game-over state from player
        for entity in self.world.get_entities_with_components(PlayerComponent):
            pc = self.world.get_component(entity.id, PlayerComponent)
            if pc and pc.game_over:
                self._game_over = True
        if self._game_over:
            return

        # Move existing enemies
        enemies = list(self.world.get_entities_with_components(EnemyComponent, TransformComponent))
        to_remove = []
        for entity in enemies:
            enemy_comp = self.world.get_component(entity.id, EnemyComponent)
            transform = self.world.get_component(entity.id, TransformComponent)
            if not enemy_comp or not transform:
                continue

            enemy_comp.pattern_time += dt
            t = enemy_comp.pattern_time

            dy = -enemy_comp.speed * dt
            dx = 0.0

            if enemy_comp.pattern == "sinusoidal":
                dx = math.cos(t * 3.0) * enemy_comp.speed * 0.5 * dt
            elif enemy_comp.pattern == "diagonal_left":
                dx = -enemy_comp.speed * 0.4 * dt
            elif enemy_comp.pattern == "diagonal_right":
                dx = enemy_comp.speed * 0.4 * dt

            transform.x += dx
            transform.y += dy

            if transform.y < DESPAWN_Y:
                to_remove.append(entity.id)

        for eid in to_remove:
            self.world.remove_entity(eid)

        # Spawn new enemies
        self._spawn_timer -= dt
        current_count = len(self.world.get_entities_with_components(EnemyComponent))
        if self._spawn_timer <= 0 and current_count < MAX_ENEMIES:
            self._spawn_enemy()
            self._spawn_timer = SPAWN_INTERVAL

    def _spawn_enemy(self):
        x = random.uniform(-ENEMY_X_RANGE, ENEMY_X_RANGE)
        pattern = random.choice(PATTERNS)
        speed = random.uniform(0.3, 0.55)

        enemy = self.world.create_entity("enemy")
        self.world.add_component(enemy.id, TransformComponent(x=x, y=SPAWN_Y, scale_x=0.8, scale_y=0.8))
        self.world.add_component(enemy.id, SpriteComponent(image_path=_asteroid_sprite_path(), layer=1))
        self.world.add_component(enemy.id, EnemyComponent(point_value=100, speed=speed, pattern=pattern))
        self.world.add_component(enemy.id, ColliderComponent(
            collider_type=ColliderType.RECTANGLE,
            size=Vec2(0.18, 0.18),
            is_trigger=True,
            collision_layer=LAYER_ENEMY,
            collision_mask=ENEMY_COLLISION_MASK,
        ))
