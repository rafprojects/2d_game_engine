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
from engine.physics.systems.panda_collision_system import PandaCollisionSystem
from engine.physics.typesg import ColliderType
from engine.physics.typesg import CollisionLayer, mask_of   # standard layers (preferred)

from tgl.components.enemy_component import EnemyComponent
from tgl.components.player_component import PlayerComponent
from tgl.systems.hud_system import HUDSystem
from tgl.systems.ship_controller import ShipControllerSystem
from tgl.systems.starfield_system import StarfieldSystem
from tgl.systems.wave_spawner import WaveSpawnerSystem
from tgl.utils.sprite_visual_size import get_visual_size, compute_hitbox_size

# ------------------------------------------------------------------
# Collision layers — now using the engine standard definitions.
# We still keep tiny local aliases for the handful of places that
# historically used raw ints, but all *masks* are built with mask_of.
# ------------------------------------------------------------------
LAYER_PLAYER = int(CollisionLayer.PLAYER)
LAYER_ENEMY = int(CollisionLayer.ENEMY)
LAYER_BULLET = int(CollisionLayer.PLAYER_BULLET)

# Recommended masks (replaces the old bit-shift expressions)
PLAYER_COLLISION_MASK = mask_of(CollisionLayer.ENEMY)
ENEMY_COLLISION_MASK = mask_of(CollisionLayer.PLAYER, CollisionLayer.PLAYER_BULLET)
BULLET_COLLISION_MASK = mask_of(CollisionLayer.ENEMY)

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

        # ------------------------------------------------------------------
        # Compute authoritative visual sizes + hitboxes from the actual sprites.
        # This is the key step that makes hitboxes "bound to the visible sprites".
        #
        # IMPORTANT: get_visual_size + compute_hitbox_size return sizes for
        # transform.scale == 1.0.  ColliderComponent.size must be in *final world
        # units* (same space as Transform.x/y). Therefore we multiply the derived
        # hitbox by the chosen archetype scale before storing the value that the
        # spawners will put directly into ColliderComponent.
        # ------------------------------------------------------------------
        ship_path = _ship_sprite_path()
        bullet_path = os.path.join("assets", "sprites", "weapons", "bullet.egg")
        asteroid_path = os.path.join("assets", "sprites", "enemies", "asteroid", "asteroid.egg")

        # Pass resource_manager (available on the Game/base after cartridge load mounts assets)
        # so the visual-size probe for hitbox derivation also respects cartridge-private assets.
        rm = getattr(base, "resource_manager", None)
        ship_vis = get_visual_size(ship_path, base.loader, rm)
        bullet_vis = get_visual_size(bullet_path, base.loader, rm)
        enemy_vis = get_visual_size(asteroid_path, base.loader, rm)

        p_scale = float(cfg["player"].get("scale", 1.0))
        b_scale = float(cfg["bullet"].get("scale", 0.25))
        e_scale = float(cfg["enemies"].get("scale", 0.22))

        p_factor = float(cfg["player"].get("collider_scale_factor", 0.70))
        b_factor = float(cfg["bullet"].get("collider_scale_factor", 0.60))
        e_factor = float(cfg["enemies"].get("collider_scale_factor", 0.80))

        p_hit_at1 = compute_hitbox_size(ship_vis, p_factor)
        b_hit_at1 = compute_hitbox_size(bullet_vis, b_factor)
        e_hit_at1 = compute_hitbox_size(enemy_vis, e_factor)

        # Final world-unit sizes (base_hitbox * transform_scale we will use for the sprite)
        p_cw = p_hit_at1[0] * p_scale
        p_ch = p_hit_at1[1] * p_scale
        b_cw = b_hit_at1[0] * b_scale
        b_ch = b_hit_at1[1] * b_scale
        e_cw = e_hit_at1[0] * e_scale
        e_ch = e_hit_at1[1] * e_scale

        cfg["player"]["collider_size"] = [p_cw, p_ch]
        cfg["bullet"]["collider_size"] = [b_cw, b_ch]
        # Store as list so wave_spawner can use a proper (non-square) rect if it wants.
        # (wave_spawner currently falls back to square using the average for compatibility.)
        cfg["enemies"]["collider_size"] = [e_cw, e_ch]

        # Make sure the scales are present for the systems (they read them for the Transform)
        cfg["player"]["scale"] = p_scale
        cfg["bullet"]["scale"] = b_scale
        cfg["enemies"]["scale"] = e_scale

        # Also expose the raw visual sizes (useful for debugging / future non-square enemy colliders)
        cfg["player"]["_visual_size"] = ship_vis
        cfg["bullet"]["_visual_size"] = bullet_vis
        cfg["enemies"]["_visual_size"] = enemy_vis

        # Keep a reference for reset() / _spawn_player which need the patched sizes etc.
        self.cfg = cfg

        # --- Systems ---
        self._ship_ctrl = ShipControllerSystem(world, cfg["player"], cfg["bullet"])
        self._wave_spawner = WaveSpawnerSystem(world, cfg)
        self._starfield = StarfieldSystem(world, base, cfg["starfield"], self._aspect)
        self._collision = CollisionSystem(world)
        self._projectile = ProjectileSystem(world)
        self._render = RenderSystem(world, base)
        self._input = InputSystem(world, base)
        self._hud = HUDSystem(world, base)

        # Panda3D collision (for playfield bounds + excellent hitbox visualization during tuning).
        # It publishes the same TriggerEnterEvent that our handler already subscribes to,
        # so the gameplay collision logic continues to work. The plain CollisionSystem is
        # kept for now; you can later drop it if you only need the Panda one.
        self._panda_collision = PandaCollisionSystem(world, base=base)
        # Use the same rough playfield the movement code already respects
        self._panda_collision.set_playfield_bounds(
            min_x=-self._aspect + 0.05, min_y=-0.90,
            max_x=self._aspect - 0.05, max_y=0.78
        )

        # Dev mode support: when --dev-mode is passed to the engine, the base
        # object gets .dev_mode = True.  We auto-enable colored collision outlines
        # (player=blue, enemies=red, bullets=yellow) so you can immediately see whether
        # the hitboxes match the art.
        dev_mode = getattr(base, "dev_mode", False)
        if dev_mode:
            # Set nice per-type colors for the debug hitboxes (player=blue, enemies=red, bullets=yellow)
            self._panda_collision.set_debug_color_for_layer(LAYER_PLAYER, (0.15, 0.55, 1.0, 0.8))
            self._panda_collision.set_debug_color_for_layer(LAYER_ENEMY, (1.0, 0.2, 0.2, 0.8))
            self._panda_collision.set_debug_color_for_layer(LAYER_BULLET, (1.0, 0.9, 0.15, 0.8))

            self._panda_collision.show_collision_nodes(True)
            # Allow easy toggle during a troubleshooting session
            base.accept("v", self._toggle_collision_viz)
            base.accept("V", self._toggle_collision_viz)
            print("🛠️  --dev-mode: collision visualization ON (press V to toggle).")
            print("    Colors: blue=player, red=enemies, yellow=bullets")

        # One-time wiring (systems + events). Safe to call initialize again; guards + EventManager dedup prevent dups.
        self._ensure_systems_and_events(world, base)

        # Create (or re-create on reset) the visual scene + player.
        self._spawn_initial_scene()

        print("🧩 TGL demo ready. Derived hitboxes (scaled to sprite visuals) are active.")
        if not getattr(base, "dev_mode", False):
            print("   Tip: run with --dev-mode to auto-show colored collision hitbox outlines (blue/red/yellow; toggle with V). Press R or F5 to restart, ESC to quit.")

        # Reference SaveStateProvider registration (P1-G canonical exercise of full surface:
        # context/legacy, SSM attachment, provider capture for save/load scenarios).
        # This makes tgl_demo demonstrate the complete modern cartridge features alongside
        # its hot-restart guard, visual hitboxes, CollisionLayer, and dev tooling.
        ssm = getattr(self, "save_state_manager", None)
        if ssm is not None and not getattr(self, "_tgl_provider_registered", False):
            class _TGLDemoSaveProvider:
                """Minimal SaveStateProvider for the reference tgl_demo cartridge."""
                def __init__(self, world):
                    self.world = world

                def capture(self):
                    data = {"cartridge": "tgl_demo", "version": "0.1.0"}
                    # Capture live player state if present (score / lives from PlayerComponent)
                    for eid in list(self.world.entities):
                        pc = self.world.get_component(eid, PlayerComponent)
                        if pc:
                            data["score"] = getattr(pc, "score", 0)
                            data["lives"] = getattr(pc, "lives", 3)
                            break
                    return data

                def restore(self, data):
                    # Demo only — real cartridges would apply to player component / world state.
                    pass

            ssm.register_provider("tgl_demo", _TGLDemoSaveProvider(self.world))
            self._tgl_provider_registered = True

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
        # Clean any prior background(s) so restart() does not accumulate dark rects.
        for child in list(base.aspect2d.getChildren()):
            if "tgl_background" in child.getName():
                try:
                    child.removeNode()
                except Exception:
                    pass

        cm = CardMaker("tgl_background")
        cm.setFrame(-aspect, aspect, -1.0, 1.0)
        bg = NodePath(cm.generate())
        bg.setColor(Vec4(0.02, 0.02, 0.06, 1.0))
        bg.reparentTo(base.aspect2d)
        bg.setBin("background", 0)
        self._bg_np = bg

    def _toggle_collision_viz(self):
        """Toggle colored debug collision outlines (only useful when PandaCollisionSystem is active)."""
        if not hasattr(self, "_panda_collision") or self._panda_collision is None:
            print("No PandaCollisionSystem registered for viz toggle.")
            return
        try:
            currently_visible = self._panda_collision.is_collision_nodes_visible()
        except Exception:
            currently_visible = False
        new_state = not currently_visible
        self._panda_collision.show_collision_nodes(new_state)
        print(f"🔍 Collision viz: {'ON' if new_state else 'OFF'}")

    # ------------------------------------------------------------------
    # Restart / reset support (for dev iteration without full process restart)
    # ------------------------------------------------------------------

    def _ensure_systems_and_events(self, world: World, base):
        """Add cartridge systems and wire events only once (supports repeated resets)."""
        if getattr(self, "_systems_wired", False):
            return
        world.add_system(self._input)
        world.add_system(self._ship_ctrl)
        world.add_system(self._wave_spawner)
        world.add_system(self._starfield)
        world.add_system(self._projectile)
        world.add_system(self._collision)
        world.add_system(self._panda_collision)   # viz + bounds
        world.add_system(self._render)
        world.add_system(self._hud)

        world.event_manager.subscribe(TriggerEnterEvent, self._on_trigger_enter)
        self._systems_wired = True

    def _spawn_initial_scene(self):
        """(Re)create background + player. Used by both first initialize and restart()."""
        self._create_background(self.base, self._aspect)
        self._spawn_player()

    def _spawn_player(self):
        """Create the player entity using pre-derived collider sizes from config."""
        player = self.world.create_entity("player")

        if not hasattr(self, "cfg") or not self.cfg:
            self.cfg = _load_config()
        p_scale = self.cfg["player"].get("scale", 1.0)

        self.world.add_component(player.id, TransformComponent(
            x=0.0, y=PLAYER_START_Y, scale_x=p_scale, scale_y=p_scale
        ))
        self.world.add_component(player.id, SpriteComponent(
            image_path=_ship_sprite_path(),
            layer=3,
            egg_animation_ranges={"idle": (0, 1), "left": (2, 3), "right": (4, 5)},
        ))
        self.world.add_component(player.id, PlayerComponent(
            health=self.cfg["player"]["health"],
            lives=self.cfg["player"]["lives"],
            score=0
        ))

        p_cw, p_ch = self.cfg["player"]["collider_size"]
        self.world.add_component(player.id, ColliderComponent(
            collider_type=ColliderType.RECTANGLE,
            size=Vec2(p_cw, p_ch),
            is_trigger=True,
            collision_layer=LAYER_PLAYER,
            collision_mask=PLAYER_COLLISION_MASK,
        ))
        self.world.add_component(player.id, InputComponent(action_bindings=_player_bindings()))

        self._player_id = player.id

    def reset(self):
        """Hot-restart the gameplay (called by engine on R/F5 when a cartridge provides .reset)."""
        print("🔄 Resetting TGL game...")
        # Destroy all entities — this triggers PandaCollisionSystem cleanup (nodes + colored overlays)
        for eid in list(self.world.entities.keys()):
            self._safe_destroy(eid)

        # Remove previous manual background node (if tracked)
        if getattr(self, "_bg_np", None):
            try:
                self._bg_np.removeNode()
            except Exception:
                pass
            self._bg_np = None

        # Reset key system state so waves, timers, etc. start fresh
        if self._wave_spawner:
            self._wave_spawner._spawn_timer = 0.0
            self._wave_spawner._elapsed = 0.0
            self._wave_spawner._game_over = False
        if self._ship_ctrl:
            self._ship_ctrl._player_entity_id = None

        # Respawn scene content
        self._spawn_initial_scene()

        print("✅ Reset complete — new run started (press R/F5 again anytime).")

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
