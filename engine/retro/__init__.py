"""
engine.retro - Reference retro / emergent gameplay math primitives + systems (P2-A + P2-B).

Pure-Python, dependency-free implementations of fixed-point arithmetic,
precision-aware components, and *reference* quirk movement/collision systems.
Intended as *reference* code that cartridges can import, copy, subclass, or
study to deliberately reproduce classic hardware-induced behaviors (subpixel
positioning, wall clips, momentum quirks, etc.) as intentional design
features rather than bugs.

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
    from engine.retro import QuirkMovementSystem

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

See:
- docs/PHASE2_RETRO_EMERGENT_GAMEPLAY_LAYER.md (Tracks P2-A and P2-B)
- The individual modules for API details, examples, and the exact rules that
  produce each emergent behavior.

No import side effects. Safe to pull into a cartridge without pulling in
render, input, or other engine subsystems.
"""

# Concrete re-exports. The package now includes both P2-A math primitives and
# P2-B reference systems. Direct submodule imports continue to work and are
# recommended when a cartridge wants to cherry-pick.

from .fixed_point import FixedPoint, FixedPointVec2  # noqa: F401
from .components import (  # noqa: F401
    SubpixelTransformComponent,
    SubpixelMovementComponent,
)
from .systems import QuirkMovementSystem  # noqa: F401

__all__ = [
    "FixedPoint",
    "FixedPointVec2",
    "SubpixelTransformComponent",
    "SubpixelMovementComponent",
    "QuirkMovementSystem",
]

