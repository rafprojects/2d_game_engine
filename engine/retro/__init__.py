"""
engine.retro - Reference retro / emergent gameplay math primitives + systems (P2-A + P2-B + P2-C).

Pure-Python, dependency-free implementations of fixed-point arithmetic,
precision-aware components, and *reference* quirk movement/collision systems.
Intended as *reference* code that cartridges can import, copy, subclass, or
study to deliberately reproduce classic hardware-induced behaviors (subpixel
positioning, wall clips, momentum quirks, etc.) as intentional design
features rather than bugs.

P2-C opt-in / integration (lightweight, per PHASE2):
- Per-entity opt-in: Use Subpixel* components (the "flag" / enhanced precision
  transform) on entities that should participate in retro math/quirks.
- At cartridge initialize time (via CartridgeContext): Create a RetroProfile
  (simple fidelity profile concept / enum-like) and register retro systems,
  or use the one-liner register_retro_systems(context.world, profile=...).
- Retro systems only ever act on entities with the Subpixel* components.
- Clean coexistence with default float/Vec2 paths and systems (default
  cartridges and other engine systems are unaffected).
- Documented coexistence rules (see RetroProfile and QuirkMovementSystem docs).

Key properties (for cartridge authors and the emergent layer):
- Deterministic (Python int under the hood; no floating-point associativity surprises
  within the chosen precision).
- Opt-in and coexistence-friendly: modern float/Vec2 code paths are completely
  unaffected by the presence or use of this package.
- Documented quantization and "why this quirk happens" rules so emergent
  behavior is reproducible and explainable (see the rule docstrings in
  systems/collision.py).

Public surface (import what you need):
    from engine.retro import FixedPoint, FixedPointVec2
    from engine.retro import SubpixelTransformComponent, SubpixelMovementComponent
    from engine.retro import QuirkMovementSystem, RetroProfile, register_retro_systems

    # Or direct submodule imports (useful when you want to avoid pulling the
    # whole surface):
    from engine.retro.fixed_point import FixedPoint, FixedPointVec2
    from engine.retro.components import (
        SubpixelTransformComponent, SubpixelMovementComponent
    )
    from engine.retro.systems import QuirkMovementSystem
    from engine.retro.systems.collision import (
        QuirkRegistry, resolve_quirky, subpixel_wall_clip_rule
    )
    from engine.retro.profile import RetroProfile

See:
- docs/PHASE2_RETRO_EMERGENT_GAMEPLAY_LAYER.md (Tracks P2-A, P2-B, P2-C)
- The individual modules for API details, examples, and the exact rules that
  produce each emergent behavior.

No import side effects. Safe to pull into a cartridge without pulling in
render, input, or other engine subsystems.
"""

# Concrete re-exports. The package now includes P2-A math, P2-B reference systems,
# and P2-C opt-in surface (RetroProfile + registration helper).
# Direct submodule imports continue to work and are recommended when a cartridge
# wants to cherry-pick.

from .fixed_point import FixedPoint, FixedPointVec2  # noqa: F401
from .components import (  # noqa: F401
    SubpixelTransformComponent,
    SubpixelMovementComponent,
)
from .systems import QuirkMovementSystem  # noqa: F401
from .profile import RetroProfile  # noqa: F401


def register_retro_systems(world, *, profile: "RetroProfile" | None = None) -> "RetroProfile":
    """One-liner opt-in helper for the retro layer (P2-C).

    Registers the reference retro systems (QuirkMovementSystem etc.) on the
    given World. Entities opt-in individually by receiving Subpixel* components.

    Intended for use in a cartridge's initialize hook (via CartridgeContext):

        from engine.retro import register_retro_systems, RetroProfile
        profile = RetroProfile("nes", frac_bits=8, enable_quirks=["subpixel_wall_clip"])
        register_retro_systems(context.world, profile=profile)

    This is the "system-level registration pattern" + "fidelity profile concept
    (even if just a dict or enum at cartridge initialize time)" suggested in
    PHASE2 for clean, declarative opt-in. Default (non-retro) cartridges simply
    never call this.

    Returns the (possibly default-constructed) profile for further use.
    """
    from .systems.movement import QuirkMovementSystem

    if profile is None:
        profile = RetroProfile()

    world.add_system(QuirkMovementSystem(world, profile=profile))
    # Future retro systems (e.g. dedicated collision resolver) can be added here
    # when they exist; they will also accept the profile.
    return profile


__all__ = [
    "FixedPoint",
    "FixedPointVec2",
    "SubpixelTransformComponent",
    "SubpixelMovementComponent",
    "QuirkMovementSystem",
    "RetroProfile",
    "register_retro_systems",
]

