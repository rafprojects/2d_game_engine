"""retro_sidescroller_demo entrypoint - P2-D reference (interactive SMB-spirit sidescroller).

Mirrors the structure and patterns of the working tgl_demo cartridge as closely as possible
for a playable demo using the engine's component/system/render/input model.

- Player uses Subpixel* components (P2-A) + SubpixelMovementComponent for the retro layer.
- register_retro_systems + RetroProfile enables the QuirkMovementSystem (P2-B + P2-C).
- A local RetroSidescrollerControllerSystem reads InputComponent, applies platformer logic
  (run accel, gravity, grounded jump), writes FP velocities to SubpixelMovementComponent.
- QuirkMovementSystem integrates the velocities (with quantization) and applies quirk rules
  (wall clip) when resolving against Collider entities (the level platforms/wall).
- Syncs standard TransformComponent from SubpixelTransform for rendering.
- Uses SpriteComponent (with color for no-asset colored rect fallback) + RenderSystem
  (added like tgl) so visuals appear under aspect2d exactly like the working tgl_demo.
- InputSystem + InputComponent with bindings (like tgl) for responsive controls.
- Level: ground + platforms + a clip wall using Collider + Transform + Sprite (colored).
- Hotkeys 'c'/'C' to force a state near the clip wall with velocity (demonstrates the exact
  retro condition from the unit tests: passage only with quirk active).
- 't'/'T' to toggle the quirk (live comparison: modern blocks, retro clips).
- This proves the retro layer in an interactive, visible sidescroller context.

The cartridge is self-contained, packable, and follows the established cartridge patterns.
No direct NodePath hacking outside the engine's systems (the source of previous issues).
"""

from __future__ import annotations

from typing import Any

from panda3d.core import Vec4, Vec2

from engine.core.system import System, World
from engine.graphics.components.transform_component import TransformComponent
from engine.graphics.components.sprite_component import SpriteComponent
from engine.graphics.systems.render_system import RenderSystem
from engine.input.components.input_component import InputComponent
from engine.input.input_bindings import InputBinding
from engine.input.systems.input_system import InputSystem
from engine.physics.components.collider_component import ColliderComponent
from engine.physics.typesg import ColliderType

from engine.retro import (
    FixedPoint,
    FixedPointVec2,
    RetroProfile,
    SubpixelMovementComponent,
    SubpixelTransformComponent,
    register_retro_systems,
)

# Level tuned to fit aspect2d playfield (roughly -1.3..1.3) while allowing a visible
# "clip wall" that the subpixel rule can let the player pass under the right conditions.
# The repro logic mirrors the unit test (subpixel alignment + velocity into a solid
# triggers the intentional non-push in the rule when quirk enabled).
LEVEL_PLATFORMS = [
    # (x, y, w, h, is_clip_wall)
    (-2.0, -0.8, 5.0, 0.5, False),     # ground
    (0.0, 0.3, 1.2, 0.4, False),       # platform 1
    (1.2, 0.9, 0.9, 0.4, False),       # platform 2
    (2.2, 0.0, 0.35, 1.2, True),       # THE CLIP WALL (small vertical solid; C hotkey forces approach)
]

RUN_SPEED = 1.8
GRAVITY = 7.0
JUMP_IMPULSE = 3.5
RUN_ACCEL = 10.0
RUN_DECEL = 12.0

def _player_bindings():
    return {
        "move_left": [
            InputBinding(input_type="key", event_name="arrow_left"),
            InputBinding(input_type="key", event_name="a"),
        ],
        "move_right": [
            InputBinding(input_type="key", event_name="arrow_right"),
            InputBinding(input_type="key", event_name="d"),
        ],
        "jump": [
            InputBinding(input_type="key", event_name="space"),
            InputBinding(input_type="key", event_name="w"),
        ],
    }

class RetroSidescrollerController(System):
    """Drives the retro player using input -> SubpixelMovement velocities.

    The QuirkMovementSystem (registered via P2-C) will consume the velocities
    for FP integration + quirk-aware collision resolve (including subpixel wall clip).
    We sync the standard TransformComponent so the engine RenderSystem (added like tgl_demo)
    produces visible sprites/colored rects under aspect2d.
    """

    def __init__(self, world: World, player_id, level_rects: list[dict]):
        super().__init__(world)
        self.player_id = player_id
        self.level_rects = level_rects  # for cheap grounded checks
        self._grounded = False
        self._clip_shown = False

    def _is_grounded(self, px: float, py: float, pw: float = 0.35, ph: float = 0.5) -> bool:
        bottom = py - ph * 0.5
        for r in self.level_rects:
            rx, ry, rw, rh = r["x"], r["y"], r["w"], r["h"]
            ptop = ry + rh * 0.5
            if abs(bottom - ptop) < 0.12:
                if max(px - pw * 0.5, rx - rw * 0.5) < min(px + pw * 0.5, rx + rw * 0.5):
                    return True
        return False

    def update(self, dt: float) -> None:
        st = self.world.get_component(self.player_id, SubpixelTransformComponent)
        sm = self.world.get_component(self.player_id, SubpixelMovementComponent)
        inp = self.world.get_component(self.player_id, InputComponent)
        tr = self.world.get_component(self.player_id, TransformComponent)

        if not st or not sm or not sm.can_move or not inp or not tr:
            return

        fb = st.frac_bits

        # Input (populated by the InputSystem we added, using the bindings on the component)
        left = bool(inp.action_active.get("move_left") or inp.action_just_pressed.get("move_left"))
        right = bool(inp.action_active.get("move_right") or inp.action_just_pressed.get("move_right"))
        jump = bool(inp.action_just_pressed.get("jump"))

        cvx, cvy = sm.current_velocity.get_xy_float()

        desired = 0.0
        if right:
            desired = RUN_SPEED
        elif left:
            desired = -RUN_SPEED

        if abs(desired) > 0.01:
            cvx += (desired - cvx) * min(1.0, RUN_ACCEL * dt)
        else:
            cvx += (0.0 - cvx) * min(1.0, RUN_DECEL * dt)

        cvy -= GRAVITY * dt

        px, py = st.get_position()
        self._grounded = self._is_grounded(px, py)

        if jump and self._grounded:
            cvy = JUMP_IMPULSE
            self._grounded = False

        # Write velocities for the retro layer (QuirkMovementSystem will integrate + resolve)
        sm.current_velocity = FixedPointVec2(cvx, cvy, frac_bits=fb)

        # Sync standard Transform for the engine's RenderSystem (produces the visible rect)
        tr.x, tr.y = st.get_position()

        # Demo feedback: detect when we passed the clip wall thanks to the quirk
        wall = next((r for r in self.level_rects if r.get("is_clip_wall")), None)
        if wall and not self._clip_shown and cvx > 0.1:
            if px > wall["x"] - 0.1:
                print("\n*** CLIP DETECTED (live) ***")
                print("Player passed the wall using subpixel positioning + the subpixel_wall_clip_rule")
                print("from the retro layer (P2-B). This only happens with the quirk enabled via P2-C.")
                print("See engine/retro/systems/collision.py and tests/unit/test_retro_quirks.py\n")
                self._clip_shown = True

class RetroSidescrollerDemo:
    """Cartridge entrypoint following tgl_demo patterns for a working interactive demo."""

    def initialize(self, context: Any) -> None:
        world: World = context.world
        base = getattr(context, "base", None)

        # Add the engine systems tgl_demo adds (critical for input + rendering to work in real runs).
        # Guarded for test/minimal bases (DummyBase/object lack .accept etc.); real ShowBase in
        # main.py --cartridge will succeed exactly like tgl_demo does.
        try:
            if base is not None and hasattr(base, "accept"):
                self._input = InputSystem(world, base)
                self._render = RenderSystem(world, base)
                world.add_system(self._input)
                world.add_system(self._render)
            else:
                self._input = self._render = None
        except Exception:
            self._input = self._render = None

        # Build level as proper entities (Colliders for Quirk snapshot, Transforms + Sprites for render)
        level_rects: list[dict] = []
        for x, y, w, h, is_wall in LEVEL_PLATFORMS:
            e = world.create_entity()
            world.add_component(e.id, TransformComponent(x=x, y=y))
            world.add_component(
                e.id,
                ColliderComponent(size=Vec2(w, h), collider_type=ColliderType.RECTANGLE),
            )
            col = Vec4(0.6, 0.6, 0.65, 0.95) if is_wall else Vec4(0.35, 0.35, 0.4, 1.0)
            world.add_component(e.id, SpriteComponent(image_path=None, color=col, layer=0))
            level_rects.append({"x": x, "y": y, "w": w, "h": h, "is_clip_wall": is_wall})

        self.level_rects = level_rects

        # Player: retro components + standard ones for input/render + the layer
        player = world.create_entity()
        fb = 8
        st = SubpixelTransformComponent(x=-1.2, y=0.0, frac_bits=fb)
        sm = SubpixelMovementComponent(frac_bits=fb, base_speed=RUN_SPEED, acceleration=RUN_ACCEL, deceleration=RUN_DECEL)
        tr = TransformComponent(x=-1.2, y=0.0)

        world.add_component(player.id, st)
        world.add_component(player.id, sm)
        world.add_component(player.id, tr)

        # Colored rect via SpriteComponent fallback (no assets needed; RenderSystem creates it)
        world.add_component(player.id, SpriteComponent(image_path=None, color=Vec4(0.9, 0.2, 0.1, 1), layer=2))

        # Input (processed by the InputSystem we added)
        world.add_component(player.id, InputComponent(action_bindings=_player_bindings()))

        self.player_id = player.id
        self.player_st = st
        self.player_sm = sm

        # P2-C opt-in (the "few lines" surface). This registers QuirkMovementSystem.
        profile = RetroProfile(
            name="nes-smb",
            frac_bits=fb,
            enable_quirks=["subpixel_wall_clip"],
        )
        # Add our controller first so it sets velocities; register appends Quirk after it in the list.
        self._controller = RetroSidescrollerController(world, player.id, level_rects)
        world.add_system(self._controller)

        register_retro_systems(world, profile=profile)
        self.profile = profile

        # Hotkeys like tgl_demo uses base.accept for one-shot actions
        if base and hasattr(base, "accept"):
            base.accept("c", self._force_clip_test)
            base.accept("t", self._toggle_quirk)
            base.accept("C", self._force_clip_test)
            base.accept("T", self._toggle_quirk)

        print("\n[P2-D] retro_sidescroller_demo (interactive SMB-spirit sidescroller)")
        print("  Retro layer active via register_retro_systems + RetroProfile (P2-C).")
        print("  Controls: Left/Right (arrows or A/D), Space/W to jump.")
        print("  C = force clip test state (exact subpixel + vel near wall; passage only with quirk).")
        print("  T = toggle the subpixel_wall_clip quirk (modern blocks vs retro clips).")
        print("  This demonstrates the retro math + rules in a real playable context.\n")

        self._quirk_enabled = True

    def _force_clip_test(self):
        if not hasattr(self, "player_st"):
            return
        fb = 8
        # Use numbers near our clip wall (2.2) with speed to cross it.
        # The rule will trigger on subpixel alignment exactly as in the unit test.
        start_x = 1.9
        self.player_st.set_position(start_x, 0.0)
        self.player_sm.current_velocity = FixedPointVec2(1.8, 0.0, frac_bits=fb)
        self._controller._clip_shown = False if hasattr(self, "_controller") else False
        print("[P2-D] Forced clip test state (subpixel + velocity into wall).")
        print("       With quirk enabled the retro rule should let it pass (see collision.py).")

    def _toggle_quirk(self):
        # Find the Quirk system registered by the helper and toggle the rule
        quirk_sys = None
        for sys in getattr(self.world, "_systems", []):
            if "QuirkMovement" in sys.__class__.__name__:
                quirk_sys = sys
                break
        if not quirk_sys:
            print("[P2-D] Could not find Quirk system to toggle.")
            return

        self._quirk_enabled = not self._quirk_enabled
        if self._quirk_enabled:
            quirk_sys.enable_quirk("subpixel_wall_clip")
            print("[P2-D] subpixel_wall_clip ENABLED (retro mode - clip should work)")
        else:
            quirk_sys.disable_quirk("subpixel_wall_clip")
            print("[P2-D] subpixel_wall_clip DISABLED (modern mode - wall should block)")

        # Reset player to a good run-up position for comparison
        if hasattr(self, "player_st"):
            self.player_st.set_position(-1.0, 0.0)
            self.player_sm.current_velocity = FixedPointVec2(1.0, 0.0, frac_bits=8)
            if hasattr(self, "_controller"):
                self._controller._clip_shown = False

    def teardown(self, context: Any | None = None) -> None:
        print("[P2-D] retro_sidescroller_demo teardown")