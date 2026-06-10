"""
engine.retro.systems - Reference retro / emergent gameplay systems (P2-B).

Pure-Python, dependency-free implementations of quirk-aware movement and
collision resolution. Intended as *reference* code that cartridges can
import, copy, subclass, or study to deliberately reproduce classic hardware-
induced behaviors (subpixel wall clips, momentum quirks, etc.) as intentional
design features.

Key properties:
- Operates exclusively on P2-A retro primitives (SubpixelTransformComponent,
  SubpixelMovementComponent, FixedPointVec2).
- Opt-in and coexistence-friendly: modern float/Vec2/MovementSystem/CollisionSystem
  code paths are completely unaffected.
- Quirk rules are pluggable, documented with exact "why this happens" explanations
  tied to historical NES/8-bit mechanics (e.g. 8.8 fixed-point / 256 subpixels,
  axis-sequential resolve, penetration alignment).
- Deterministic within the chosen frac_bits.

Public surface (import what you need):
    from engine.retro.systems import QuirkMovementSystem
    from engine.retro import QuirkMovementSystem

    # For advanced use (standalone resolver / rules):
    from engine.retro.systems.collision import resolve_quirky, subpixel_wall_clip_rule

See:
- docs/PHASE2_RETRO_EMERGENT_GAMEPLAY_LAYER.md (Track P2-B)
- The individual modules for API details, rule implementations, and examples.

No import side effects. Safe to pull into a cartridge.
"""

from .movement import QuirkMovementSystem  # noqa: F401

# collision module provides the resolver and rules; re-exported here for convenience
# (populated after collision.py is implemented; direct submodule import always works)
try:
    from .collision import QuirkRegistry, resolve_quirky, subpixel_wall_clip_rule  # noqa: F401
except ImportError:
    # During incremental implementation / tests that only need movement
    pass

__all__ = [
    "QuirkMovementSystem",
    "QuirkRegistry",
    "resolve_quirky",
    "subpixel_wall_clip_rule",
]
