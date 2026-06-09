"""
engine.retro - Reference retro / emergent gameplay math primitives.

Pure-Python, dependency-free implementations of fixed-point arithmetic and
precision-aware components. Intended as *reference* code that cartridges can
import, copy, subclass, or study to deliberately reproduce classic hardware-
induced behaviors (subpixel positioning, quantization effects, etc.) as
intentional design features rather than bugs.

Key properties (for cartridge authors and the emergent layer):
- Deterministic (Python int under the hood; no floating-point associativity surprises
  within the chosen precision).
- Opt-in and coexistence-friendly: modern float/Vec2 code paths are completely
  unaffected by the presence or use of this package.
- Documented quantization and conversion rules so the "why this quirk happens"
  is reproducible and explainable.

Public surface (import what you need):
    from engine.retro import FixedPoint, FixedPointVec2
    from engine.retro import SubpixelTransformComponent

    # Or
    from engine.retro.fixed_point import FixedPoint, FixedPointVec2
    from engine.retro.components import SubpixelTransformComponent

See:
- docs/PHASE2_RETRO_EMERGENT_GAMEPLAY_LAYER.md (Track P2-A and later tracks)
- The individual modules for API details and examples.

No import side effects. Safe to pull into a cartridge without pulling in
movement systems, render, or other engine subsystems.
"""

# Concrete re-exports. The package is now complete for P2-A.
# Direct submodule imports (engine.retro.fixed_point etc.) also continue to work
# and are useful when a cartridge wants to avoid pulling the whole surface.

from .fixed_point import FixedPoint, FixedPointVec2  # noqa: F401
from .components import SubpixelTransformComponent  # noqa: F401

__all__ = [
    "FixedPoint",
    "FixedPointVec2",
    "SubpixelTransformComponent",
]

