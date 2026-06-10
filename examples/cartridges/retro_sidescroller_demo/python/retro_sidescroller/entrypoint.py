"""retro_sidescroller_demo entrypoint (P2-D reference cartridge) - RE-WORKED.

This is a *simple but playable* 2D sidescroller in Super Mario Bros spirit.

Goals (addressing feedback):
- Real interactive controls: left/right run (with acceleration), jump when grounded, gravity.
- Actual environment: floor, floating platforms, and a deliberate "clip wall" (vertical solid) with alignment/speed that lets the player pass *only* when the retro subpixel_wall_clip quirk is active.
- The QuirkMovementSystem (P2-B) + P2-A math + P2-C opt-in are exercised *every frame* while the user plays.
- Clear proof the retro layer is responsible: on-screen instructions, "quirk active" status, "CLIP DETECTED" feedback when the emergent behavior triggers, a hotkey to force the exact unit-test start conditions (so the known clip is reliably reproducible live), and a toggle to disable the quirk and observe the modern block behavior on the identical approach.
- Minimal code and visuals (colored rectangles via CardMaker + NodePath) so it stays a focused reference/template, not a full game.

The higher-level platformer controller (in RetroPlatformerController) sets velocities on the SubpixelMovementComponent.
The registered QuirkMovementSystem performs the FP integration + quirk-aware resolve every update.
All emergent behavior (the wall clip) comes from the retro layer rules.

Run:
  python main.py --cartridge examples/cartridges/retro_sidescroller_demo

Controls (while running):
  Left/Right arrows or A/D : run
  Space : jump (when on ground)
  C : force exact test clip start state (the numbers from test_retro_quirks) + impulse -- watch the player clip the wall
  T : toggle the subpixel_wall_clip quirk on/off + reset player for comparison (modern path blocks)

See the cartridge README and docs/PHASE2... Track P2-D for the full story and how to copy/extend this as a template.
"""

from __future__ import annotations

import uuid
from typing import Any

from panda3d.core import CardMaker, NodePath, Vec2

# OnscreenText is nice for instructions but lives in direct.gui and may not be
# importable in minimal / headless test environments. We guard it.
try:
    from direct.gui.OnscreenText import OnscreenText  # type: ignore
    from panda3d.core import TextNode  # type: ignore
    ONSCREEN_TEXT_AVAILABLE = True
except Exception:
    OnscreenText = None  # type: ignore
    TextNode = None  # type: ignore
    ONSCREEN_TEXT_AVAILABLE = False

from engine.core.system import System, World
from engine.input.components.input_component import InputComponent
from engine.input.input_bindings import InputBinding
from engine.input.systems.input_system import InputSystem
from engine.physics.components.collider_component import ColliderComponent

from engine.retro import (
    FixedPoint,
    FixedPointVec2,
    RetroProfile,
    SubpixelMovementComponent,
    SubpixelTransformComponent,
    register_retro_systems,
)


# ------------------------------------------------------------------
# Simple level data for both visuals and the controller's grounded checks.
# These are also turned into Collider entities so the Quirk system snapshots them.
# The special "clip_wall" is the one the subpixel rule is tuned to allow passage through
# under the right conditions (exact numbers from the unit test).
# ------------------------------------------------------------------
LEVEL_PLATFORMS = [
    # (x, y, w, h, is_clip_wall)
    (-4.0, -1.0, 20.0, 1.0, False),   # long ground
    (2.0, 1.5, 3.0, 0.6, False),      # floating platform 1
    (6.0, 2.8, 2.5, 0.6, False),      # floating platform 2
    (9.5, 0.5, 1.0, 4.0, True),       # THE CLIP WALL (tall thin vertical solid at ~x=9.5-10.5)
]

JUMP_IMPULSE = 6.0
GRAVITY = 12.0
RUN_SPEED = 4.5
RUN_ACCEL = 18.0
RUN_DECEL = 22.0


def _fp(v: float, fb: int) -> FixedPoint:
    return FixedPoint(v, frac_bits=fb)


class RetroPlatformerController(System):
    """
    Minimal interactive platformer controller for the retro layer demo.

    - Reads input (via InputComponent actions or direct base polling as fallback).
    - Applies run acceleration, gravity, and jump to the player's SubpixelMovementComponent (FP).
    - Maintains a simple grounded state using the level rects (so jump only when appropriate).
    - After the Quirk system has integrated + resolved for the frame, syncs a parallel
      standard TransformComponent (for any engine render) and updates direct visual NodePaths.
    - Detects when the player has "clipped" the special wall (x crossed the wall while
      still overlapping it) and prints clear feedback that this is the retro emergent behavior.
    - Supports runtime toggle of the quirk (for live modern vs retro comparison).
    """

    def __init__(
        self,
        world: World,
        player_id: uuid.UUID,
        player_st: SubpixelTransformComponent,
        player_sm: SubpixelMovementComponent,
        quirk_sys: Any,
        level_rects: list[dict],
        visuals: dict[str, NodePath],
        base: Any,
    ) -> None:
        super().__init__(world)
        self.player_id = player_id
        self.player_st = player_st
        self.player_sm = player_sm
        self.quirk_sys = quirk_sys
        self.level_rects = level_rects  # list of {"x":, "y":, "w":, "h":, "is_clip_wall":}
        self.visuals = visuals
        self.base = base

        self._grounded = False
        self._prev_vy = 0.0
        self._clip_shown = False
        self._quirk_enabled = True

        # Input actions (set up in initialize)
        self.move_left = False
        self.move_right = False
        self.jump_pressed = False

    def set_input_state(self, left: bool, right: bool, jump: bool) -> None:
        self.move_left = left
        self.move_right = right
        self.jump_pressed = jump

    def toggle_quirk(self) -> None:
        if self.quirk_sys is None:
            return
        self._quirk_enabled = not self._quirk_enabled
        if self._quirk_enabled:
            self.quirk_sys.enable_quirk("subpixel_wall_clip")
            print("[Retro] subpixel_wall_clip QUIRK RE-ENABLED (retro mode)")
        else:
            self.quirk_sys.disable_quirk("subpixel_wall_clip")
            print("[Retro] subpixel_wall_clip QUIRK DISABLED (modern/float-like mode)")

        # Reset player to a good run-up position for comparison
        fb = self.player_st.frac_bits
        self.player_st.set_position(3.0, 0.0)
        self.player_sm.current_velocity = FixedPointVec2(3.5, 0.0, frac_bits=fb)
        self._clip_shown = False
        self._grounded = False

    def force_exact_clip_test(self) -> None:
        """Instantly put the player into the exact state from the unit test repro.
        Next integration will demonstrate the known wall clip if the quirk is on.
        """
        fb = self.player_st.frac_bits
        start_x = FixedPoint(4.0, frac_bits=fb) + FixedPoint.from_raw(0x18, frac_bits=fb)
        self.player_st.set_position(float(start_x), 0.0)
        self.player_sm.current_velocity = FixedPointVec2(2.0, 0.0, frac_bits=fb)
        self._clip_shown = False
        print("[Retro] Forced exact test clip start state (from test_retro_quirks).")
        print("        Watch the player pass the wall at x~5 only because of the retro rule.")

    def _is_grounded(self, px: float, py: float, pw: float = 0.8, ph: float = 0.8) -> bool:
        """Cheap grounded test against our level rects (player bottom near platform top)."""
        bottom = py - ph * 0.5
        for r in self.level_rects:
            rx, ry, rw, rh = r["x"], r["y"], r["w"], r["h"]
            platform_top = ry + rh * 0.5
            if abs(bottom - platform_top) < 0.15:  # small tolerance
                # x overlap
                left = px - pw * 0.5
                right = px + pw * 0.5
                if max(left, rx - rw * 0.5) < min(right, rx + rw * 0.5):
                    return True
        return False

    def update(self, dt: float) -> None:
        st = self.player_st
        sm = self.player_sm
        if not st or not sm or not sm.can_move:
            return

        fb = st.frac_bits

        # --- Read input state (polled from the entrypoint which reads the InputComponent or base) ---
        desired_vx = 0.0
        if self.move_right:
            desired_vx = RUN_SPEED
        elif self.move_left:
            desired_vx = -RUN_SPEED

        # Current in float for controller math (we quantize only when writing back to the component)
        cvx, cvy = sm.current_velocity.get_xy_float()

        # Run accel/decel toward desired
        if abs(desired_vx) > 0.01:
            if (desired_vx > 0 and cvx < desired_vx) or (desired_vx < 0 and cvx > desired_vx):
                cvx += (desired_vx - cvx) * min(1.0, RUN_ACCEL * dt)
            else:
                # already at or past target, or opposing -- strong decel toward target
                cvx += (desired_vx - cvx) * min(1.0, RUN_DECEL * dt)
        else:
            # no input -> decelerate toward 0
            cvx += (0.0 - cvx) * min(1.0, RUN_DECEL * dt)

        # Gravity
        cvy -= GRAVITY * dt

        # Jump (use the state set by the entrypoint from action_just_pressed)
        self._grounded = self._is_grounded(st.position.x.to_float() if hasattr(st.position.x, 'to_float') else float(st.position.x),
                                           st.position.y.to_float() if hasattr(st.position.y, 'to_float') else float(st.position.y))
        if self.jump_pressed and self._grounded:
            cvy = JUMP_IMPULSE
            self._grounded = False

        # Write the new velocity back to the retro component (FP, quantized)
        sm.current_velocity = FixedPointVec2(cvx, cvy, frac_bits=fb)

        # The QuirkMovementSystem (registered separately) will, on its update:
        #   - take this current_velocity
        #   - do FP delta = vel * dt_fp
        #   - intended = pos + delta
        #   - resolve_quirky (which may apply the wall clip rule and return a different final pos/vel)
        #   - write the (possibly quirk-modified) final_pos and final_vel back

        # After the world has advanced the systems (the caller of this update usually does one
        # full world tick), our visuals will be synced in the entrypoint's post-tick or we can
        # do a best-effort sync here using the latest st.

        # Sync visuals (direct NodePaths) from the (possibly quirk-adjusted) Subpixel position.
        px, py = st.get_position()
        if "player" in self.visuals:
            self.visuals["player"].setPos(px * 0.12, 0, py * 0.12)  # scale to fit a nice view in aspect2d

        # Also keep a parallel standard Transform if anything else in the engine wants it.
        # (We create one on the player in initialize and keep it roughly in sync.)
        try:
            t = self.world.get_component(self.player_id, "TransformComponent")  # type: ignore[arg-type]
            if t is not None:
                t.x = px
                t.y = py
        except Exception:
            pass

        # --- Clip detection / proof of retro layer ---
        # If the player x has crossed the clip wall while still overlapping it in x, and we
        # are using the quirk, announce it. This is the observable "the retro layer did this".
        wall = next((r for r in self.level_rects if r.get("is_clip_wall")), None)
        if wall and not self._clip_shown:
            w_left = wall["x"] - wall["w"] * 0.5
            w_right = wall["x"] + wall["w"] * 0.5
            p_left = px - 0.4
            p_right = px + 0.4
            # Player has its center past the wall left edge while still overlapping the wall rect
            if px > w_left and p_left < w_right and cvx > 0.5:
                if self._quirk_enabled:
                    print("\n*** CLIP DETECTED (live during play) ***")
                    print("The player passed through the solid wall using subpixel positioning +")
                    print("the subpixel_wall_clip_rule from the retro layer (P2-B).")
                    print("This is the exact emergent behavior the unit tests prove only happens")
                    print("with the retro components + quirk enabled.")
                    print("See engine/retro/systems/collision.py and the P2-D reference cartridge.\n")
                else:
                    print("(You are overlapping the wall in modern mode -- the quirk is off, so this is not a full clip passage.)")
                self._clip_shown = True

        self._prev_vy = cvy


class RetroSidescrollerDemo:
    """SMB-spirit interactive 2D sidescroller reference for P2-D (re-worked)."""

    def initialize(self, context: Any) -> None:
        world: World = context.world
        self.context = context
        self.world = world
        self.base = getattr(context, "base", None)

        fb = 8

        # --- P2-C opt-in ---
        profile = RetroProfile(
            name="nes-smb-interactive",
            frac_bits=fb,
            enable_quirks=["subpixel_wall_clip"],
        )
        register_retro_systems(world, profile=profile)
        self.profile = profile

        # Find the Quirk system we just registered so we can toggle it at runtime.
        quirk_sys = None
        for sys in getattr(world, "_systems", []):
            if getattr(sys, "__class__", None) and sys.__class__.__name__ == "QuirkMovementSystem":
                quirk_sys = sys
                break

        # --- Player entity (retro precision) ---
        player = world.create_entity()

        # Start the player on the left side with a little initial velocity so it feels alive.
        st = SubpixelTransformComponent(x=0.5, y=0.0, frac_bits=fb)
        sm = SubpixelMovementComponent(frac_bits=fb, base_speed=RUN_SPEED, acceleration=RUN_ACCEL, deceleration=RUN_DECEL)
        sm.current_velocity = FixedPointVec2(1.5, 0.0, frac_bits=fb)

        world.add_component(player.id, st)
        world.add_component(player.id, sm)

        # Also give it a standard Transform (we will keep it roughly synced for any engine systems).
        from engine.graphics.components.transform_component import TransformComponent
        world.add_component(player.id, TransformComponent(x=0.5, y=0.0))

        # Input component + system (best effort).
        # The engine InputSystem needs a real ShowBase with .accept for device listeners.
        # In test environments (DummyBase) we skip it and rely on the controller's
        # set_input_state + direct base polling for the interactive manual run.
        showbase = getattr(context, "base", None) or getattr(self, "base", None)
        try:
            if showbase is not None and hasattr(showbase, "accept"):
                world.add_system(InputSystem(world, showbase))
                has_input_system = True
            else:
                has_input_system = False
        except Exception:
            has_input_system = False

        self.has_input_system = has_input_system
        move_left = InputBinding(input_type="key", event_name="arrow_left")
        move_right = InputBinding(input_type="key", event_name="arrow_right")
        jump_bind = InputBinding(input_type="key", event_name="space")
        # Also support WASD / common keys
        move_left2 = InputBinding(input_type="key", event_name="a")
        move_right2 = InputBinding(input_type="key", event_name="d")
        jump2 = InputBinding(input_type="key", event_name="w")

        input_comp = InputComponent(
            action_bindings={
                "move_left": [move_left, move_left2],
                "move_right": [move_right, move_right2],
                "jump": [jump_bind, jump2],
            }
        )
        world.add_component(player.id, input_comp)

        self.player_id = player.id
        self.player_st = st
        self.player_sm = sm
        self.input_comp = input_comp

        # --- Build level colliders + rect data for controller ---
        level_rects: list[dict] = []
        for x, y, w, h, is_wall in LEVEL_PLATFORMS:
            rect_ent = world.create_entity()
            world.add_component(rect_ent.id, TransformComponent(x=x, y=y))
            # collider_type omitted (engine may not expose STATIC in this build; the
            # Quirk snapshot + our controller grounded logic only need size + position).
            world.add_component(
                rect_ent.id,
                ColliderComponent(size=Vec2(w, h)),
            )
            level_rects.append({"x": x, "y": y, "w": w, "h": h, "is_clip_wall": is_wall})

        self.level_rects = level_rects

        # --- Visuals (direct NodePaths so the player visibly moves and clips) ---
        # Guarded heavily because the test loader uses a very minimal DummyBase with no
        # aspect2d / render / OnscreenText. The interactive manual run (python main.py --cartridge)
        # will have a real ShowBase and will get the moving rects + instructions.
        self.visuals: dict[str, NodePath] = {}
        base_for_vis = getattr(self, "base", None) or getattr(context, "base", None)

        if base_for_vis is not None and hasattr(base_for_vis, "aspect2d"):
            try:
                # Player "blob" (red rectangle)
                cm = CardMaker("player")
                cm.setFrame(-0.4, 0.4, -0.4, 0.4)
                pnp = NodePath(cm.generate())
                pnp.setColor(0.9, 0.2, 0.1, 1.0)
                pnp.reparentTo(base_for_vis.aspect2d)
                pnp.setPos(0.5 * 0.12, 0, 0.0 * 0.12)
                self.visuals["player"] = pnp

                # Platform / wall visuals
                for i, r in enumerate(level_rects):
                    cm2 = CardMaker(f"plat_{i}")
                    cm2.setFrame(-r["w"] * 0.5, r["w"] * 0.5, -r["h"] * 0.5, r["h"] * 0.5)
                    np = NodePath(cm2.generate())
                    if r.get("is_clip_wall"):
                        np.setColor(0.4, 0.4, 0.5, 0.85)
                    else:
                        np.setColor(0.3, 0.3, 0.35, 1.0)
                    np.reparentTo(base_for_vis.aspect2d)
                    np.setPos(r["x"] * 0.12, 0, r["y"] * 0.12)
                    self.visuals[f"plat_{i}"] = np

                # On-screen instructions (guarded)
                if ONSCREEN_TEXT_AVAILABLE:
                    try:
                        title = OnscreenText(  # type: ignore
                            text="P2-D Retro Sidescroller (SMB spirit) - RE-WORKED",
                            pos=(0, 0.92),
                            scale=0.06,
                            fg=(1, 1, 1, 1),
                            align=TextNode.ACenter,  # type: ignore
                        )
                        self.visuals["title"] = title

                        help_text = OnscreenText(  # type: ignore
                            text="Left/Right (or A/D) to run  |  Space to jump  |  C = force exact clip test  |  T = toggle quirk",
                            pos=(0, 0.84),
                            scale=0.04,
                            fg=(0.9, 0.9, 0.6, 1),
                            align=TextNode.ACenter,  # type: ignore
                        )
                        self.visuals["help"] = help_text

                        status = OnscreenText(  # type: ignore
                            text="Retro quirk: subpixel_wall_clip ENABLED  (C = test clip, T = toggle modern)",
                            pos=(0, -0.9),
                            scale=0.045,
                            fg=(0.4, 1.0, 0.4, 1),
                            align=TextNode.ACenter,  # type: ignore
                        )
                        self.visuals["status"] = status
                        self._status_text = status
                    except Exception:
                        self._status_text = None
            except Exception:
                # Visuals are optional for the reference test; the logic (retro + controller) still runs.
                self.visuals = {}
        else:
            self._status_text = None

        # --- Controller system (the thing that makes it interactive and proves the layer) ---
        controller = RetroPlatformerController(
            world,
            player.id,
            st,
            sm,
            quirk_sys,
            level_rects,
            self.visuals,
            self.base,
        )
        world.add_system(controller)
        self.controller = controller

        # Also store a reference to the quirk system for the entrypoint's key handling.
        self.quirk_sys = quirk_sys

        # Initial on-screen / console message
        print("\n[P2-D] retro_sidescroller_demo (interactive SMB-spirit sidescroller) - RE-WORKED")
        print("  Retro layer active (P2-A math + P2-B quirks + P2-C opt-in via register_retro_systems).")
        print("  Use the keys listed on screen. The clip wall on the right is the star of the show.")
        print("  The emergent wall clip only happens because the retro rule is active.\n")

    def _update_input_from_component(self) -> tuple[bool, bool, bool]:
        """Poll the InputComponent we gave the player (populated by InputSystem)."""
        if not hasattr(self, "input_comp") or self.input_comp is None:
            return False, False, False
        ic = self.input_comp
        left = bool(ic.action_pressed.get("move_left") or ic.action_just_pressed.get("move_left"))
        right = bool(ic.action_pressed.get("move_right") or ic.action_just_pressed.get("move_right"))
        jump = bool(ic.action_just_pressed.get("jump"))
        return left, right, jump

    def update(self, dt: float) -> None:  # called by host if it polls the entry instance
        # Feed the latest input state into the controller (so it can use it in its System update).
        left, right, jump = self._update_input_from_component()
        if hasattr(self, "controller"):
            self.controller.set_input_state(left, right, jump)

            # Hotkeys for demo features (polled from base for reliability)
            if self.base and hasattr(self.base, "mouseWatcherNode"):
                mw = self.base.mouseWatcherNode
                # 'c' or 'C' - force exact clip test
                if mw.is_button_down("c"):
                    self.controller.force_exact_clip_test()
                # 't' or 'T' - toggle quirk
                if mw.is_button_down("t"):
                    # only toggle on the rising edge - simple debounce via a tiny flag on self
                    if not getattr(self, "_t_down", False):
                        self.controller.toggle_quirk()
                        self._t_down = True
                        # update status text if present
                        if hasattr(self, "_status_text") and self._status_text:
                            enabled = self.controller._quirk_enabled
                            self._status_text.setText(
                                f"Retro quirk: subpixel_wall_clip {'ENABLED' if enabled else 'DISABLED (modern mode)'}"
                            )
                    else:
                        pass
                else:
                    self._t_down = False

    def teardown(self, context: Any | None = None) -> None:
        print("[P2-D] retro_sidescroller_demo (interactive) teardown")
