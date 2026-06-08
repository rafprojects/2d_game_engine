"""TGL Demo cartridge entrypoint — scrolling-shooter corridor mode."""
from __future__ import annotations

import os
import pathlib

import yaml
from panda3d.core import CardMaker, NodePath, TransparencyAttrib, Vec2, Vec4, WindowProperties

from engine.core.system import World
from engine.graphics.components.transform_component import TransformComponent
from engine.graphics.components.sprite_component import SpriteComponent
from engine.graphics.systems.render_system import RenderSystem
from engine.input.components.input_component import InputComponent
from engine.input.input_bindings import InputBinding
from engine.input.systems.input_system import InputSystem
from engine.physics.components.collider_component import ColliderComponent
from engine.physics.systems.collision_system import CollisionSystem, TriggerEnterEvent
from engine.physics.systems.projectile_system import ProjectileSystem
from engine.physics.typesg import ColliderType

from tgl.components.enemy_component import EnemyComponent
from tgl.components.player_component import PlayerComponent
from tgl.systems.hud_system import HUDSystem
from tgl.systems.ship_controller import ShipControllerSystem
from tgl.systems.starfield_system import StarfieldSystem
from tgl.systems.wave_spawner import WaveSpawnerSystem

# Collision layers
LAYER_PLAYER = 1
LAYER_ENEMY = 2
LAYER_BULLET = 4

# Player collides with enemies only
PLAYER_COLLISION_MASK = 1 << (LAYER_ENEMY - 1)  # = 2

PLAYER_START_Y = -0.7


def _load_config() -> dict:
    root = pathlib.Path(__file__).parent.parent.parent  # tgl_demo/
    with open(root / "config" / "game_settings.yaml") as f:
        return yaml.safe_load(f)


def _ship_sprite_path() -> str:
    return os.path.join("assets", "sprites", "ship", "ship.egg")


class TGLDemo:
    """Cartridge entrypoint for the TGL scrolling-shooter demo."""

    def initialize(self, world: World, base, manifest):
        self.world = world
        self.base = base

        # Load configuration
        cfg = _load_config()
        self._invulnerable_duration = cfg["player"]["invulnerable_duration"]

        # Apply window size and compute viewport aspect ratio
        win_cfg = cfg["window"]
        props = WindowProperties()
        props.setSize(win_cfg["width"], win_cfg["height"])
        base.win.requestProperties(props)
        self._aspect = win_cfg["width"] / win_cfg["height"]  # X spans ±aspect, Y spans ±1.0

        # --- Systems ---
        self._ship_ctrl = ShipControllerSystem(world, cfg["player"], cfg["bullet"])
        self._wave_spawner = WaveSpawnerSystem(world, cfg)
        self._starfield = StarfieldSystem(world, base, cfg["starfield"], self._aspect)
        self._collision = CollisionSystem(world)
        self._projectile = ProjectileSystem(world)
        self._render = RenderSystem(world, base)
        self._input = InputSystem(world, base)
        self._hud = HUDSystem(world, base)

        world.add_system(self._input)
        world.add_system(self._ship_ctrl)
        world.add_system(self._wave_spawner)
        world.add_system(self._starfield)
        world.add_system(self._projectile)
        world.add_system(self._collision)
        world.add_system(self._render)
        world.add_system(self._hud)

        # --- Background (solid dark rectangle, fills full viewport) ---
        self._create_background(base, self._aspect)

        # --- Player entity ---
        player = world.create_entity("player")
        world.add_component(player.id, TransformComponent(
            x=0.0, y=PLAYER_START_Y, scale_x=1.0, scale_y=1.0
        ))
        world.add_component(player.id, SpriteComponent(
            image_path=_ship_sprite_path(),
            layer=3,
            egg_animation_ranges={"idle": (0, 1), "left": (2, 3), "right": (4, 5)},
        ))
        world.add_component(player.id, PlayerComponent(
            health=cfg["player"]["health"],
            lives=cfg["player"]["lives"],
            score=0
        ))
        world.add_component(player.id, ColliderComponent(
            collider_type=ColliderType.RECTANGLE,
            size=Vec2(0.12, 0.14),
            is_trigger=True,
            collision_layer=LAYER_PLAYER,
            collision_mask=PLAYER_COLLISION_MASK,
        ))
        world.add_component(player.id, InputComponent(action_bindings=_player_bindings()))

        self._player_id = player.id

        # Subscribe to trigger collisions
        world.event_manager.subscribe(TriggerEnterEvent, self._on_trigger_enter)

    # ------------------------------------------------------------------
    # Collision handling
    # ------------------------------------------------------------------

    def _on_trigger_enter(self, event: TriggerEnterEvent):
        trigger_id = event.trigger_entity_id
        other_id = event.other_entity_id

        trigger_enemy = self.world.get_component(trigger_id, EnemyComponent)
        other_enemy = self.world.get_component(other_id, EnemyComponent)
        trigger_player = self.world.get_component(trigger_id, PlayerComponent)
        other_player = self.world.get_component(other_id, PlayerComponent)

        from engine.physics.components.projectile_component import ProjectileComponent
        trigger_bullet = self.world.get_component(trigger_id, ProjectileComponent)
        other_bullet = self.world.get_component(other_id, ProjectileComponent)

        # Bullet hits enemy
        if trigger_bullet and other_enemy:
            self._bullet_hit_enemy(trigger_id, other_id)
        elif other_bullet and trigger_enemy:
            self._bullet_hit_enemy(other_id, trigger_id)

        # Player hits enemy
        elif trigger_player and other_enemy:
            self._player_hit_enemy(trigger_id, other_id)
        elif other_player and trigger_enemy:
            self._player_hit_enemy(other_id, trigger_id)

    def _bullet_hit_enemy(self, bullet_id, enemy_id):
        from engine.physics.components.projectile_component import ProjectileComponent

        bullet_comp = self.world.get_component(bullet_id, ProjectileComponent)
        enemy_comp = self.world.get_component(enemy_id, EnemyComponent)
        if bullet_comp is None or enemy_comp is None:
            return
        # Award score
        player_comp = self.world.get_component(self._player_id, PlayerComponent)
        if player_comp:
            player_comp.score += enemy_comp.point_value
        # Despawn both
        bullet_comp.is_alive = False
        self._safe_destroy(enemy_id)

    def _player_hit_enemy(self, player_id, enemy_id):
        player_comp = self.world.get_component(player_id, PlayerComponent)
        if player_comp is None or player_comp.invulnerable_timer > 0 or player_comp.game_over:
            return
        player_comp.lives -= 1
        player_comp.invulnerable_timer = self._invulnerable_duration
        self._safe_destroy(enemy_id)
        if player_comp.lives <= 0:
            player_comp.game_over = True

    def _safe_destroy(self, entity_id):
        if entity_id in self.world.entities:
            self.world.remove_entity(entity_id)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _create_background(self, base, aspect: float):
        cm = CardMaker("tgl_background")
        cm.setFrame(-aspect, aspect, -1.0, 1.0)
        bg = NodePath(cm.generate())
        bg.setColor(Vec4(0.02, 0.02, 0.06, 1.0))
        bg.reparentTo(base.aspect2d)
        bg.setBin("background", 0)


def _player_bindings() -> dict:
    return {
        "move_left": [
            InputBinding(input_type="key", event_name="arrow_left"),
            InputBinding(input_type="key", event_name="a"),
        ],
        "move_right": [
            InputBinding(input_type="key", event_name="arrow_right"),
            InputBinding(input_type="key", event_name="d"),
        ],
        "move_up": [
            InputBinding(input_type="key", event_name="arrow_up"),
            InputBinding(input_type="key", event_name="w"),
        ],
        "move_down": [
            InputBinding(input_type="key", event_name="arrow_down"),
            InputBinding(input_type="key", event_name="s"),
        ],
        "shoot": [
            InputBinding(input_type="key", event_name="space"),
        ],
    }
