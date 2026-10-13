"""retro_sidescroller_demo entrypoint - P2-D reference cartridge (rebuilt).

A small playable SMB-spirit sidescroller that demonstrates a *genuine*
emergent retro mechanic: the subpixel wall clip produced by midline ejection
(the "subpixel_wall_clip" quirk in engine/retro).

How it fits together:
- The whole game lives on a virtual 256x240 pixel playfield (VirtualPlayfield).
  Level geometry is integer pixels; positions/velocities are 8.8 fixed point
  (256 subpixels per pixel, the NES grid); velocities are pixels PER TICK at
  a fixed 60 Hz simulation tick.
- ``LEVEL`` (RetroObstacle boxes, below) is the single source of truth: the
  physics consumes it directly and the gray render rectangles are generated
  from it, so what you see is exactly what you collide with.
- The player opts into the retro layer with the P2-C few-liner:
  Subpixel* components + RetroProfile + register_retro_systems(...). The
  returned QuirkMovementSystem is kept as the live handle for toggling the
  quirk and hooking the per-tick controller.
- RetroSidescrollerController.control_tick (registered as a tick callback)
  applies the game feel each simulation tick: run acceleration, gravity,
  grounded jumps - using the resolver-owned ``on_ground`` flag rather than
  any ad-hoc geometry checks. The controller's per-frame update() only syncs
  the render Transform from the subpixel position and narrates clip events.

The emergent mechanic (see engine/retro/systems/collision.py for the rule
and the worked arithmetic): the clip wall is 6 px thick and the player runs
at 4.0 px/tick. 4.0 > 3 (half the wall), so on the first overlapping tick the
player's leading edge CAN land past the wall's midline - and midline ejection
then pushes the player out the FAR side. Whether that happens depends on the
subpixel alignment of the approach: roughly 1 in 4 full-speed run-ups clips,
and a single subpixel of starting position flips the outcome.

Hotkeys:
  C - teleport to the exact alignment that clips (x=153.5, full speed)
  X - teleport to an alignment 3 px away that is always blocked
  T - toggle the quirk (midline vs modern ejection) and respawn

Run with:
  python main.py --cartridge examples/cartridges/retro_sidescroller_demo

The cartridge relies on main.py's core systems (Render/Input) - it does not
add its own. It only registers its controller and the retro system.
"""

from __future__ import annotations

from typing import Any

from panda3d.core import Vec4, WindowProperties

from engine.core.system import System, World
from engine.graphics.components.sprite_component import SpriteComponent
from engine.graphics.components.transform_component import TransformComponent
from engine.input.components.input_component import InputComponent
from engine.input.input_bindings import InputBinding

from engine.retro import (
    FixedPointVec2,
    RetroObstacle,
    RetroProfile,
    SubpixelColliderComponent,
    SubpixelMovementComponent,
    SubpixelTransformComponent,
    VirtualPlayfield,
    register_retro_systems,
)

# ---------------------------------------------------------------------------
# Simulation constants (8.8 fixed point; velocities in px/tick at 60 Hz).
# All values are exact on the 1/256 grid.
# ---------------------------------------------------------------------------
FB = 8
TICK_HZ = 60
RUN_SPEED = 4.0        # px/tick  (> half the clip wall's 6 px -> clips possible)
RUN_ACCEL = 0.125      # px/tick^2
RUN_DECEL = 0.25
GRAVITY = 0.25
JUMP_IMPULSE = 4.5     # < platform half-thickness 5 -> ceilings un-clippable
TERMINAL_FALL = -4.0   # < ground half-thickness 8  -> floors un-clippable

PLAYER_W, PLAYER_H = 12, 16
SPAWN = (40.0, 24.0)   # bottom edge exactly on the ground top (16): stable rest

# The two reference alignments from the unit tests (run at RUN_SPEED toward
# the wall): 153.5 clips on the 11th tick; 150.5 - 3 px away - is blocked.
CLIP_ALIGN_X = 153.5
BLOCK_ALIGN_X = 150.5

# ---------------------------------------------------------------------------
# Level - single source of truth for physics AND visuals (virtual pixels,
# Y-up, origin bottom-left of the 256x240 playfield).
# ---------------------------------------------------------------------------
LEVEL = [
    RetroObstacle(128, 8, 256, 16, name="ground"),
    RetroObstacle(88, 40, 48, 10, name="platform_1"),
    RetroObstacle(160, 64, 40, 10, name="platform_2"),
    # 6 px thick, too tall to jump over (even from platform_2): the ONLY way
    # past it is the subpixel clip.
    RetroObstacle(203, 68, 6, 104, name="clip_wall"),
    # Decorative reward marker on the far side (not solid).
    RetroObstacle(236, 20, 32, 8, solid=False, name="goal_pad"),
    # Playfield border walls (16 px thick -> categorically un-clippable at
    # 4 px/tick), so the player cannot run off the world edges.
    RetroObstacle(-8, 120, 16, 240, name="border_left"),
    RetroObstacle(264, 120, 16, 240, name="border_right"),
]

_COLORS = {
    "ground": Vec4(0.45, 0.45, 0.50, 1.0),
    "platform_1": Vec4(0.55, 0.55, 0.62, 1.0),
    "platform_2": Vec4(0.55, 0.55, 0.62, 1.0),
    "clip_wall": Vec4(0.75, 0.70, 0.35, 1.0),   # stands out: this is THE wall
    "goal_pad": Vec4(0.25, 0.65, 0.30, 1.0),
}


def _player_bindings() -> dict[str, list[InputBinding]]:
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
    """Cartridge-side game feel + render sync for the retro player.

    Split of responsibilities:
    - ``control_tick`` runs once per SIMULATION TICK (registered with the
      QuirkMovementSystem): reads input, applies run accel/decel, gravity and
      grounded jumps, and writes the per-tick FP velocity. The retro system
      then integrates and resolves it (with the quirk, when enabled).
    - ``update`` runs once per RENDER FRAME (ordinary System): syncs the
      float TransformComponent from the subpixel position through the
      playfield mapping, and narrates clip / goal events.
    """

    def __init__(
        self,
        world: World,
        player_id: Any,
        retro_system: Any,
        playfield: VirtualPlayfield,
        base: Any = None,
    ) -> None:
        super().__init__(world)
        self.player_id = player_id
        self.retro_system = retro_system
        self.playfield = playfield
        self.base = base
        self._jump_held = False
        self._auto_run_ticks = 0  # C/X hotkeys force a clean full-speed run-up
        self._goal_announced = False

    # ------------------------------------------------------------------
    # Per simulation tick (called by QuirkMovementSystem before integration)
    # ------------------------------------------------------------------
    def control_tick(self, tick: int) -> None:
        sm = self.world.get_component(self.player_id, SubpixelMovementComponent)
        if not sm or not sm.can_move:
            return

        vx, vy = sm.current_velocity.get_xy_float()

        left = right = jump = False
        inp = self.world.get_component(self.player_id, InputComponent)
        if inp is not None:
            left = bool(inp.action_active.get("move_left") or inp.action_just_pressed.get("move_left"))
            right = bool(inp.action_active.get("move_right") or inp.action_just_pressed.get("move_right"))
            jump = bool(inp.action_active.get("jump") or inp.action_just_pressed.get("jump"))
        # Raw polling fallback keeps the reference demo responsive even if
        # action states lag a frame. Guarded so headless tests (DummyBase)
        # simply skip it.
        if self.base is not None and hasattr(self.base, "mouseWatcherNode"):
            mw = self.base.mouseWatcherNode
            left = left or mw.is_button_down("arrow_left") or mw.is_button_down("a")
            right = right or mw.is_button_down("arrow_right") or mw.is_button_down("d")
            jump = jump or mw.is_button_down("space") or mw.is_button_down("w")

        if self._auto_run_ticks > 0:
            self._auto_run_ticks -= 1
            right, left = True, False

        # Horizontal: accelerate toward the target speed, decelerate to rest.
        # All steps are multiples of 1/256 so the FP round-trip is exact.
        target = RUN_SPEED if (right and not left) else (-RUN_SPEED if (left and not right) else 0.0)
        if target != 0.0:
            if vx < target:
                vx = min(vx + RUN_ACCEL, target)
            elif vx > target:
                vx = max(vx - RUN_ACCEL, target)
        else:
            if vx > 0.0:
                vx = max(vx - RUN_DECEL, 0.0)
            elif vx < 0.0:
                vx = min(vx + RUN_DECEL, 0.0)

        # Vertical: gravity every tick (keeps on_ground fresh) + grounded,
        # edge-latched jumps (holding the key does not bounce).
        vy = max(vy - GRAVITY, TERMINAL_FALL)
        if jump and not self._jump_held and sm.on_ground:
            vy = JUMP_IMPULSE
        self._jump_held = jump

        sm.current_velocity = FixedPointVec2(vx, vy, frac_bits=FB)

    # ------------------------------------------------------------------
    # Per render frame
    # ------------------------------------------------------------------
    def update(self, dt: float) -> None:
        st = self.world.get_component(self.player_id, SubpixelTransformComponent)
        tr = self.world.get_component(self.player_id, TransformComponent)
        if not st or not tr:
            return

        px, py = st.get_position()
        tr.x, tr.y = self.playfield.to_render(px, py)

        # Safety net: respawn if somehow off the world (should not happen with
        # the border walls, but cheap insurance for experimentation).
        if py < -40.0:
            st.set_position(*SPAWN)
            sm = self.world.get_component(self.player_id, SubpixelMovementComponent)
            if sm:
                sm.current_velocity = FixedPointVec2(0.0, 0.0, frac_bits=FB)
            print("[P2-D] Player fell out of the world - respawned.")

        # Narrate this frame's emergent clips (the retro system clears its
        # event list at the start of its own update, which ran just before us).
        for ev in self.retro_system.clip_events:
            if ev.get("entity_id") != self.player_id:
                continue
            ex, _ey = ev["pos"]
            print("\n*** SUBPIXEL WALL CLIP (emergent) ***")
            print(f"  tick {ev['tick']}: ejected out the FAR side of '{ev['obstacle']}' to x={ex:.4f} px.")
            print("  Why: with the quirk on, ejection asks which HALF of the wall the leading")
            print("  edge is in - and this approach's subpixel alignment landed it past the")
            print("  midline on the contact tick. 3 px earlier (press X) it gets blocked.")
            print("  Rule + worked example: engine/retro/systems/collision.py (resolve_axis).")
            print("  Press T for modern ejection - the same approach is always blocked.\n")

        if not self._goal_announced and px > 220.0:
            self._goal_announced = True
            print("[P2-D] Goal pad reached - you are on the far side of the clip wall.")


class RetroSidescrollerDemo:
    """Cartridge entrypoint (new-style hook: initialize(context))."""

    def initialize(self, context: Any) -> None:
        world: World = context.world
        base = getattr(context, "base", None)
        self.world = world
        self.base = base

        playfield = VirtualPlayfield(256, 240)
        self.playfield = playfield

        # Window setup (like tgl_demo): 1024x960 is 16:15 - the playfield's
        # exact aspect, so the 256x240 world fills the window. Requesting
        # properties also raises/focuses the window under WSLg-style window
        # managers; without it the window can open without keyboard focus
        # and "keys do nothing".
        if base is not None and hasattr(base, "win") and base.win is not None:
            try:
                props = WindowProperties()
                props.setTitle("Retro Sidescroller Demo - subpixel wall clip (P2-D)")
                props.setSize(1024, 960)
                props.setForeground(True)
                base.win.requestProperties(props)
            except Exception:
                pass

        # Level: physics consumes LEVEL directly; render entities are
        # generated from the same list (visual size == collision size).
        for obs in LEVEL:
            e = world.create_entity()
            rx, ry = playfield.to_render(obs.cx, obs.cy)
            sx, sy = playfield.size_to_render_scale(obs.w, obs.h)
            world.add_component(e.id, TransformComponent(x=rx, y=ry, scale_x=sx, scale_y=sy))
            color = _COLORS.get(obs.name, Vec4(0.5, 0.5, 0.5, 1.0))
            world.add_component(e.id, SpriteComponent(image_path=None, color=color, layer=0))

        # Player: retro components (P2-A/P2-C) + render/input components.
        player = world.create_entity()
        st = SubpixelTransformComponent(x=SPAWN[0], y=SPAWN[1], frac_bits=FB)
        sm = SubpixelMovementComponent(frac_bits=FB)
        rx, ry = playfield.to_render(*SPAWN)
        sx, sy = playfield.size_to_render_scale(PLAYER_W, PLAYER_H)
        world.add_component(player.id, st)
        world.add_component(player.id, sm)
        world.add_component(player.id, SubpixelColliderComponent(PLAYER_W, PLAYER_H, frac_bits=FB))
        world.add_component(player.id, TransformComponent(x=rx, y=ry, scale_x=sx, scale_y=sy))
        world.add_component(player.id, SpriteComponent(image_path=None, color=Vec4(0.9, 0.2, 0.1, 1.0), layer=2))
        world.add_component(player.id, InputComponent(action_bindings=_player_bindings()))

        self.player_id = player.id
        self.player_st = st
        self.player_sm = sm

        # P2-C opt-in, few lines: profile + register. The returned system is
        # the live handle (toggle quirks, tick callbacks, clip events).
        profile = RetroProfile(
            name="nes-smb",
            frac_bits=FB,
            tick_hz=TICK_HZ,
            enable_quirks=["subpixel_wall_clip"],
        )
        self.profile = profile
        self.retro_system = register_retro_systems(world, profile=profile, obstacles=LEVEL)

        # Controller AFTER the retro system so its per-frame update sees this
        # frame's ticks (transform sync + clip narration).
        self._controller = RetroSidescrollerController(
            world, player.id, self.retro_system, playfield, base=base
        )
        world.add_system(self._controller)
        self.retro_system.add_tick_callback(self._controller.control_tick)

        self._quirk_enabled = True

        if base is not None and hasattr(base, "accept"):
            for key, fn in (
                ("c", self.force_clip_alignment),
                ("x", self.force_block_alignment),
                ("t", self.toggle_quirk),
            ):
                base.accept(key, fn)
                base.accept(key.upper(), fn)
        if base is not None and hasattr(base, "setBackgroundColor"):
            try:
                base.setBackgroundColor(0.10, 0.10, 0.16)
            except Exception:
                pass

        print("\n[P2-D] retro_sidescroller_demo loaded (rebuilt: genuine emergent clip).")
        print("  256x240 virtual-pixel playfield | 8.8 fixed point | 60 Hz fixed ticks.")
        print("  Controls: arrows/A,D run - Space/W jump (red rect = you, 12x16 px).")
        print("  The yellow wall is 6 px thick; you run 4 px/tick. Run at it at full")
        print("  speed: ~1 in 4 subpixel alignments ejects you out the FAR side (the clip).")
        print("  C = teleport to the exact clipping alignment (x=153.5, full speed)")
        print("  X = the blocked alignment 3 px away   T = toggle quirk (modern vs retro)")
        print("  Why it happens: engine/retro/systems/collision.py (midline ejection).\n")

    # ------------------------------------------------------------------
    # Hotkey / test surface (public so headless tests can drive them)
    # ------------------------------------------------------------------
    def force_clip_alignment(self) -> None:
        """C: the exact alignment from the unit tests - clips on the 11th tick."""
        self._reset_run(CLIP_ALIGN_X)
        print(f"[P2-D] Player set to x={CLIP_ALIGN_X} at full speed -> this alignment CLIPS (quirk on).")

    def force_block_alignment(self) -> None:
        """X: 3 px from the clip alignment - always blocked, same speed."""
        self._reset_run(BLOCK_ALIGN_X)
        print(f"[P2-D] Player set to x={BLOCK_ALIGN_X} at full speed -> this alignment is BLOCKED.")

    def toggle_quirk(self) -> None:
        """T: swap midline (retro) vs motion-based (modern) ejection, respawn."""
        self._quirk_enabled = not self._quirk_enabled
        if self._quirk_enabled:
            self.retro_system.enable_quirk("subpixel_wall_clip")
            print("[P2-D] subpixel_wall_clip ENABLED (midline ejection - clips possible).")
        else:
            self.retro_system.disable_quirk("subpixel_wall_clip")
            print("[P2-D] subpixel_wall_clip DISABLED (modern ejection - the wall always blocks).")
        self.player_st.set_position(*SPAWN)
        self.player_sm.current_velocity = FixedPointVec2(0.0, 0.0, frac_bits=FB)
        self._controller._goal_announced = False

    def reset(self) -> None:
        """Hot-restart hook (main.py R/F5): respawn the player."""
        self.player_st.set_position(*SPAWN)
        self.player_sm.current_velocity = FixedPointVec2(0.0, 0.0, frac_bits=FB)
        self._controller._goal_announced = False
        print("[P2-D] Player respawned.")

    def _reset_run(self, x: float) -> None:
        self.player_st.set_position(x, SPAWN[1])
        self.player_sm.current_velocity = FixedPointVec2(RUN_SPEED, 0.0, frac_bits=FB)
        self._controller._auto_run_ticks = 30
        self._controller._goal_announced = False

    def teardown(self, context: Any | None = None) -> None:
        print("[P2-D] retro_sidescroller_demo teardown")
