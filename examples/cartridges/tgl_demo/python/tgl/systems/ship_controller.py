from __future__ import annotations

import os
import uuid

from panda3d.core import Vec2

from engine.core.system import System
from engine.graphics.components.transform_component import TransformComponent
from engine.graphics.components.sprite_component import SpriteComponent
from engine.input.components.input_component import InputComponent
from engine.physics.components.collider_component import ColliderComponent
from engine.physics.typesg import ColliderType

from tgl.components.player_component import PlayerComponent
from tgl.components.enemy_component import EnemyComponent

# Collision layer constants
LAYER_PLAYER = 1
LAYER_ENEMY = 2
LAYER_BULLET = 4

# Bullet collides with enemies; enemy layer bit = (1 << (LAYER_ENEMY - 1))
BULLET_COLLISION_MASK = 1 << (LAYER_ENEMY - 1)  # = 2


def _bullet_sprite_path() -> str:
    return os.path.join("assets", "sprites", "weapons", "bullet.egg")


class ShipControllerSystem(System):
    """Handles player ship input, animation state, and bullet firing."""

    def __init__(self, world, cfg_player: dict, cfg_bullet: dict):
        super().__init__(world)
        self._player_entity_id: uuid.UUID | None = None
        self._speed = cfg_player["speed"]
        self._x_limit = cfg_player["x_limit"]
        self._fire_rate = cfg_player["fire_rate"]
        self._max_shots = cfg_player["max_shots"]
        self._bullet_speed = cfg_bullet["speed"]
        self._bullet_lifetime = cfg_bullet["lifetime"]

    def _find_player(self) -> uuid.UUID | None:
        for entity in self.world.get_entities_with_components(PlayerComponent):
            return entity.id
        return None

    def update(self, dt: float):
        if self._player_entity_id is None:
            self._player_entity_id = self._find_player()
        if self._player_entity_id is None:
            return

        player_comp = self.world.get_component(self._player_entity_id, PlayerComponent)
        if player_comp is None or player_comp.game_over:
            return

        transform = self.world.get_component(self._player_entity_id, TransformComponent)
        sprite = self.world.get_component(self._player_entity_id, SpriteComponent)
        input_comp = self.world.get_component(self._player_entity_id, InputComponent)
        if not transform or not input_comp:
            return

        # Tick timers
        if player_comp.invulnerable_timer > 0:
            player_comp.invulnerable_timer = max(0.0, player_comp.invulnerable_timer - dt)
        if player_comp.fire_cooldown > 0:
            player_comp.fire_cooldown = max(0.0, player_comp.fire_cooldown - dt)

        # Horizontal movement
        moving_left = input_comp.action_active.get("move_left", False)
        moving_right = input_comp.action_active.get("move_right", False)
        dx = 0.0
        if moving_left:
            dx -= self._speed * dt
        if moving_right:
            dx += self._speed * dt
        transform.x = max(-self._x_limit, min(self._x_limit, transform.x + dx))

        # Animation state
        if sprite is not None:
            if moving_left and not moving_right:
                if sprite.current_animation != "left":
                    sprite.play_animation("left")
            elif moving_right and not moving_left:
                if sprite.current_animation != "right":
                    sprite.play_animation("right")
            else:
                if sprite.current_animation != "idle":
                    sprite.play_animation("idle")

        # Shooting
        if input_comp.action_active.get("shoot", False) and player_comp.fire_cooldown <= 0:
            self._spawn_bullet(transform.x, transform.y, self._player_entity_id)
            player_comp.fire_cooldown = self._fire_rate

    def _spawn_bullet(self, x: float, y: float, owner_id: uuid.UUID):
        from engine.physics.components.projectile_component import ProjectileComponent

        # Check shot limit
        active = list(self.world.get_entities_with_components(ProjectileComponent))
        if len(active) >= self._max_shots:
            return

        bullet = self.world.create_entity("bullet")
        self.world.add_component(bullet.id, TransformComponent(x=x, y=y + 0.08, scale_x=0.3, scale_y=0.3))
        self.world.add_component(bullet.id, SpriteComponent(image_path=_bullet_sprite_path(), layer=2))
        self.world.add_component(bullet.id, ProjectileComponent(
            velocity=Vec2(0, 1),
            speed=self._bullet_speed,
            lifetime=self._bullet_lifetime,
            damage=1.0,
            owner_entity_id=owner_id,
        ))
        self.world.add_component(bullet.id, ColliderComponent(
            collider_type=ColliderType.RECTANGLE,
            size=Vec2(0.06, 0.1),
            is_trigger=True,
            collision_layer=LAYER_BULLET,
            collision_mask=BULLET_COLLISION_MASK,
        ))
