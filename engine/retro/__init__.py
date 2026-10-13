"""
engine.retro - Reference retro / emergent gameplay primitives + systems
(P2-A math, P2-B fixed-tick quirk systems [rebuilt], P2-C opt-in surface).

Pure-Python, dependency-free implementations of fixed-point arithmetic,
precision-aware components, a virtual pixel playfield, and *reference*
fixed-tick movement/collision systems. Intended as reference code that
cartridges can import, copy, subclass, or study to deliberately reproduce
classic hardware-induced behaviors as intentional design features rather
than bugs.

The flagship emergent behavior is the **subpixel wall clip**: with the
"subpixel_wall_clip" quirk enabled, collision ejection uses the authentic
NES *midline rule* ("push out of whichever half of the obstacle you're in")
instead of motion-based ejection. When per-tick speed exceeds half a thin
wall's thickness and the subpixel alignment is right, the body is ejected
out the FAR side - a genuine clip that a single subpixel of starting
position can make or break. See engine/retro/systems/collision.py for the
exact rule and a worked example.

P2-C opt-in / integration (lightweight, per PHASE2):
- Per-entity opt-in: add Subpixel* components (transform + movement, plus
  SubpixelColliderComponent for entities that should collide).
- At cartridge initialize time: create a RetroProfile (precision + tick rate
  + quirks) and call register_retro_systems(world, profile=..., obstacles=...).
  The returned QuirkMovementSystem is the live handle (enable_quirk /
  disable_quirk / add_tick_callback / clip_events).
- Retro systems only ever act on entities with the Subpixel* components;
  default float/Vec2 cartridges and engine systems are unaffected.

Key properties:
- Deterministic: fixed simulation ticks, velocities per tick, raw-integer
  comparisons at one frac_bits scale. No float dt in the simulation.
- Opt-in and coexistence-friendly (no import side effects).
- Documented "why this quirk happens" rules so emergent behavior is
  reproducible and explainable.

Public surface (import what you need):
    from engine.retro import FixedPoint, FixedPointVec2
    from engine.retro import (
        SubpixelTransformComponent, SubpixelMovementComponent,
        SubpixelColliderComponent,
    )
    from engine.retro import (
        QuirkMovementSystem, QuirkRegistry, RetroObstacle, RetroProfile,
        VirtualPlayfield, register_retro_systems,
    )

See:
- docs/PHASE2_RETRO_EMERGENT_GAMEPLAY_LAYER.md (Tracks P2-A..D + re-work notes)
- examples/cartridges/retro_sidescroller_demo (the reference cartridge)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Sequence

from .components import (  # noqa: F401
    SubpixelColliderComponent,
    SubpixelMovementComponent,
    SubpixelTransformComponent,
)
from .fixed_point import FixedPoint, FixedPointVec2  # noqa: F401
from .playfield import VirtualPlayfield  # noqa: F401
from .profile import RetroProfile  # noqa: F401
from .systems import (  # noqa: F401
    QuirkMovementSystem,
    QuirkRegistry,
    RetroObstacle,
)

if TYPE_CHECKING:
    from engine.core.system import World


def register_retro_systems(
    world: "World",
    *,
    profile: RetroProfile | None = None,
    obstacles: Sequence[RetroObstacle] | None = None,
) -> QuirkMovementSystem:
    """One-liner opt-in helper for the retro layer (P2-C).

    Creates and registers the fixed-tick QuirkMovementSystem on the given
    World and returns it - the returned system is the cartridge's live
    handle for toggling quirks (enable_quirk / disable_quirk), registering
    per-tick controllers (add_tick_callback), replacing level geometry
    (set_obstacles), and reading clip_events.

    Intended for use in a cartridge's initialize hook (via CartridgeContext):

        from engine.retro import register_retro_systems, RetroProfile, RetroObstacle
        profile = RetroProfile("nes", frac_bits=8, tick_hz=60,
                               enable_quirks=["subpixel_wall_clip"])
        retro_sys = register_retro_systems(
            context.world, profile=profile, obstacles=LEVEL,
        )

    Entities opt in individually by receiving Subpixel* components. Default
    (non-retro) cartridges simply never call this.
    """
    if profile is None:
        profile = RetroProfile()

    system = QuirkMovementSystem(world, profile=profile, obstacles=obstacles)
    world.add_system(system)
    return system


__all__ = [
    "FixedPoint",
    "FixedPointVec2",
    "QuirkMovementSystem",
    "QuirkRegistry",
    "RetroObstacle",
    "RetroProfile",
    "SubpixelColliderComponent",
    "SubpixelMovementComponent",
    "SubpixelTransformComponent",
    "VirtualPlayfield",
    "register_retro_systems",
]
