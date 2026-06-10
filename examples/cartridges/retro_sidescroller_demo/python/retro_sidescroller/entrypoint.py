"""retro_sidescroller_demo entrypoint (P2-D reference cartridge).

2D sidescroller in Super Mario Bros spirit whose sole job is to make the
subpixel wall clip (the iconic NES-era emergent behavior) obvious, reproducible,
and directly attributable to the reference rule in engine/retro/.

This cartridge:
- Uses the P2-C opt-in surface in a few lines (register_retro_systems + RetroProfile).
- Creates entities with Subpixel* components (the per-entity "flag").
- Sets up a minimal platformer scene (floor + the exact clip wall from the unit tests).
- Exercises the clip at initialize time (and leaves state for host updates) so a
  human running `python main.py --cartridge ...` or a test sees the passage.
- Prints a clear "this only happens because..." message with pointer to
  engine/retro/systems/collision.py:subpixel_wall_clip_rule and the test.
- Documents the variant (modern/float path blocks the same start state).

Keep it tiny on purpose. The point is the quirk + the "copy this tree to experiment" template.
"""

from __future__ import annotations

from typing import Any

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


def _make_clip_wall(frac_bits: int = 8) -> dict[str, Any]:
    """Exact obstacle dict from tests/unit/test_retro_quirks.py clip test.

    Using this guarantees the cartridge reproduces the same deterministic emergent
    outcome that the unit test asserts "only with retro + rule".
    """
    return {
        "pos": FixedPointVec2(5.0, 0.0, frac_bits=frac_bits),
        "size": FixedPointVec2(1.0, 2.0, frac_bits=frac_bits),
        "solid": True,
        "player_size": FixedPointVec2(0.8, 0.8, frac_bits=frac_bits),
    }


class RetroSidescrollerDemo:
    """SMB-spirit 2D sidescroller reference cartridge for P2-D.

    Demonstrates the complete retro layer (P2-A math + P2-B quirk rules + P2-C opt-in)
    producing a classic, documented, reproducible emergent behavior (subpixel wall clip)
    that does not occur under default float modern paths.

    See:
    - docs/PHASE2_RETRO_EMERGENT_GAMEPLAY_LAYER.md (Track P2-D)
    - engine/retro/systems/collision.py (the exact rule + NES research comments)
    - tests/unit/test_retro_quirks.py (the passing "only with retro+rule" test this cart mirrors)
    - The cartridge README.md
    """

    def initialize(self, context: Any) -> None:
        """P2-C style initialize using CartridgeContext (preferred path).

        A cartridge author copies this pattern:
            profile = RetroProfile("nes-smb", frac_bits=8, enable_quirks=["subpixel_wall_clip"])
            register_retro_systems(context.world, profile=profile)
            ... add Subpixel* to gameplay entities ...
        """
        world = context.world
        self.context = context
        self.world = world

        fb = 8

        # --- P2-C opt-in (the "few lines" surface) ---
        profile = RetroProfile(
            name="nes-smb",
            frac_bits=fb,
            enable_quirks=["subpixel_wall_clip"],
            # options can carry cartridge-specific tuning later (P5 precursor)
        )
        register_retro_systems(world, profile=profile)
        self.profile = profile

        # --- Player: retro precision components (the per-entity opt-in) ---
        # Start state taken directly from the deterministic clip test so the cartridge
        # "best shows the wall clip" with the exact same numbers that prove the AC.
        start_x = FixedPoint(4.0, frac_bits=fb) + FixedPoint.from_raw(0x18, frac_bits=fb)
        st = SubpixelTransformComponent(x=float(start_x), y=0.0, frac_bits=fb)
        sm = SubpixelMovementComponent(frac_bits=fb)
        sm.current_velocity = FixedPointVec2(2.0, 0.0, frac_bits=fb)

        player = world.create_entity()
        world.add_component(player.id, st)
        world.add_component(player.id, sm)
        self.player_id = player.id
        self.player_st = st
        self.player_sm = sm

        # --- Level geometry ---
        # Critical clip wall uses the exact extra_obstacles form from the unit test
        # (guarantees identical low_bits / window behavior).
        wall = _make_clip_wall(fb)

        # Attach to the Quirk system that register_retro_systems just added.
        # (A production cartridge would typically manage Colliders + let the system snapshot them,
        # or pass extra_obstacles at QuirkMovementSystem construction time.)
        quirk_sys = None
        for sys in getattr(world, "_systems", []):
            if getattr(sys, "__class__", None) and sys.__class__.__name__ == "QuirkMovementSystem":
                quirk_sys = sys
                break
        if quirk_sys is not None:
            quirk_sys._extra_obstacles = [wall]  # type: ignore[attr-defined]
            self.quirk_sys = quirk_sys
        else:
            self.quirk_sys = None

        # (Optional floor via Collider omitted for minimal surface — the clip repro uses
        # the exact extra_obstacles wall from the unit test. A fuller sidescroller cart can
        # add Collider + Transform platforms here; the Quirk system snapshots them.)

        # --- Repro the clip at cartridge load time (observable "wow" moment) ---
        # This is the heart of "for the test one of the sample reference cartridges should be
        # a 2D sidescroller in Super Mario Bros spirit to best show the wall clip".
        dt = 0.6
        print("\n[P2-D] retro_sidescroller_demo (SMB-spirit wall clip reference)")
        print(f"  Profile: {profile}")
        print(f"  Player start x (fb=8): {float(start_x):.6f}")
        print("  Wall obstacle at x=5 (size 1). vx=2.0, dt=0.6.")
        print("  Performing controlled step to exercise QuirkMovementSystem + subpixel_wall_clip_rule...")

        world.update(dt)

        final_x, final_y = st.get_position()
        passed = final_x > 5.0
        print(f"  After step: x={final_x:.6f}, y={final_y:.6f}  (passed the wall? {passed})")

        if passed:
            print(
                "\n  *** EMERGENT BEHAVIOR REPRODUCED ***\n"
                "  The player passed through what should be a solid 1-unit wall.\n"
                "  This ONLY happens because the subpixel_wall_clip_rule (enabled via the profile)\n"
                "  saw the contact low_bits inside its window and intentionally skipped the full\n"
                "  push/clamp, returning the intended position (micro-penetration carry).\n\n"
                "  See exactly:\n"
                "    engine/retro/systems/collision.py:242 (low_bits = contact_raw & (scale-1))\n"
                "    engine/retro/systems/collision.py:246 (if clip_window_low <= low_bits <= high)\n"
                "    tests/unit/test_retro_quirks.py (the 'only with retro+rule' asserts + float control)\n"
                "    docs/PHASE2... (P2-B research notes on SMB 8.8 / 256 subpixels + 'partially inside' frames)\n"
                "\n  The identical start state + velocity with the rule disabled (or using default\n"
                "  float MovementSystem + CollisionSystem + Transform) produces a clean block.\n"
            )
        else:
            print("  (No clip observed this run — check that the quirk is enabled and start state matches.)")

        print("[P2-D] retro layer active. This cartridge is a template: copy the tree, change the")
        print("       enable_quirks list or the start numbers / wall, and observe a different (or the")
        print("       same modified) emergent behavior. Modern code paths are unaffected.\n")

    def teardown(self, context: Any | None = None) -> None:
        """Optional symmetric hook called by the loader on unload."""
        print("[P2-D] retro_sidescroller_demo teardown")
