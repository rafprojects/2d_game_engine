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
from engine.physics.typesg import CollisionLayer, mask_of

from tgl.components.player_component import PlayerComponent
from tgl.components.enemy_component import EnemyComponent

LAYER_ENEMY = int(CollisionLayer.ENEMY)
# Enemy mask using the standard helper (player + player bullets)
ENEMY_COLLISION_MASK = mask_of(CollisionLayer.PLAYER, CollisionLayer.PLAYER_BULLET)


def _asteroid_sprite_path() -> str:
    return os.path.join("assets", "sprites", "enemies", "asteroid", "asteroid.egg")


class WaveSpawnerSystem(System):
    """Timed enemy wave spawning with difficulty ramp."""

    def __init__(self, world, cfg: dict):
        super().__init__(world)
        sp = cfg["spawner"]
        self._base_interval = sp["interval"]
        self._base_max = sp["max_enemies"]
        self._ramp_interval = sp["difficulty_ramp_interval"]
        self._speed_delta = sp["difficulty_speed_delta"]
        self._spawn_delta = sp["difficulty_spawn_delta"]
        self._max_cap = sp["difficulty_max_enemies_cap"]
        self._despawn_y = sp["despawn_y"]
        self._spawn_y = sp["spawn_y"]
        self._x_range = sp["enemy_x_range"]
        self._patterns = cfg["enemies"]["patterns"]
        self._enemy_scale = cfg["enemies"].get("scale", 0.8)
        # collider_size may be a single float (square) or will have been pre-computed
        # in entrypoint via the sprite visual size helper + factor.
        self._collider_size = cfg["enemies"].get("collider_size", 0.18)
        self._spawn_timer: float = 0.0
        self._elapsed: float = 0.0
        self._game_over: bool = False

    def update(self, dt: float):
        # Check game-over state from player
        for entity in self.world.get_entities_with_components(PlayerComponent):
            pc = self.world.get_component(entity.id, PlayerComponent)
            if pc and pc.game_over:
                self._game_over = True
        if self._game_over:
            return

        self._elapsed += dt

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

            if transform.y < self._despawn_y:
                to_remove.append(entity.id)

        for eid in to_remove:
            self.world.remove_entity(eid)

        # Spawn new enemies with difficulty ramp
        self._spawn_timer -= dt
        step = int(self._elapsed / self._ramp_interval)
        current_interval = max(0.5, self._base_interval + step * self._spawn_delta)
        current_max = min(self._max_cap, self._base_max + step)

        current_count = len(self.world.get_entities_with_components(EnemyComponent))
        if self._spawn_timer <= 0 and current_count < current_max:
            self._spawn_enemy(step)
            self._spawn_timer = current_interval

    def _spawn_enemy(self, step: int = 0):
        x = random.uniform(-self._x_range, self._x_range)

        # Weighted pattern selection
        pattern_names = [p["name"] for p in self._patterns]
        weights = [p["weight"] for p in self._patterns]
        pattern_name = random.choices(pattern_names, weights=weights, k=1)[0]
        pattern = next(p for p in self._patterns if p["name"] == pattern_name)

        # Difficulty-scaled speed
        speed_base = random.uniform(0.3, 0.55)
        speed = speed_base * pattern["speed_multiplier"] * (1 + step * self._speed_delta)

        enemy = self.world.create_entity("enemy")
        self.world.add_component(enemy.id, TransformComponent(x=x, y=self._spawn_y, scale_x=self._enemy_scale, scale_y=self._enemy_scale))
        self.world.add_component(enemy.id, SpriteComponent(image_path=_asteroid_sprite_path(), layer=1))
        self.world.add_component(enemy.id, EnemyComponent(
            point_value=pattern["point_value"],
            speed=speed,
            pattern=pattern_name
        ))

        # Support either a scalar (legacy square) or [w, h] / (w, h) for a properly proportioned rect.
        csize = self._collider_size
        if isinstance(csize, (list, tuple)) and len(csize) >= 2:
            cvec = Vec2(float(csize[0]), float(csize[1]))
        else:
            s = float(csize)
            cvec = Vec2(s, s)

        self.world.add_component(enemy.id, ColliderComponent(
            collider_type=ColliderType.RECTANGLE,
            size=cvec,
            is_trigger=True,
            collision_layer=LAYER_ENEMY,
            collision_mask=ENEMY_COLLISION_MASK,
        ))
