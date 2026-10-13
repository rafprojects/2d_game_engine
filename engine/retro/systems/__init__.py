"""
engine.retro.systems - Reference retro / emergent gameplay systems (P2-B, rebuilt).

Pure-Python, dependency-free implementations of fixed-tick, axis-separated
retro movement and collision resolution. Intended as *reference* code that
cartridges can import, copy, subclass, or study to deliberately reproduce
classic hardware-induced behaviors (the subpixel wall clip) as intentional
design features.

Key properties:
- Fixed simulation tick (RetroProfile.tick_hz, default 60) with velocities in
  units **per tick** - deterministic regardless of frame rate.
- Axis-separated integrate-and-resolve (X then Y) against RetroObstacle level
  geometry; bodies snap to faces and zero the collided axis's velocity, so
  floors/walls/ceilings just work.
- The "subpixel_wall_clip" quirk swaps motion-based ejection for *midline
  ejection* - the authentic NES rule that makes genuine, subpixel-sensitive
  wall clips emerge (see collision.resolve_axis for the rule and the worked
  example).
- Operates exclusively on retro primitives (SubpixelTransformComponent,
  SubpixelMovementComponent, SubpixelColliderComponent, FixedPoint*).
- Opt-in and coexistence-friendly: modern float/Vec2/MovementSystem/
  CollisionSystem code paths are completely unaffected.

Public surface (import what you need):
    from engine.retro.systems import QuirkMovementSystem, RetroObstacle
    from engine.retro.systems.collision import resolve_axis, quantize_obstacles

See:
- docs/PHASE2_RETRO_EMERGENT_GAMEPLAY_LAYER.md (Track P2-B + re-work notes)
- The individual modules for API details, the ejection rules, and examples.

No import side effects. Safe to pull into a cartridge.
"""

from .collision import (  # noqa: F401
    AxisResolution,
    FPSpan,
    KNOWN_QUIRKS,
    QUIRK_SUBPIXEL_WALL_CLIP,
    QuirkRegistry,
    RetroObstacle,
    quantize_obstacles,
    resolve_axis,
)
from .movement import QuirkMovementSystem  # noqa: F401

__all__ = [
    "AxisResolution",
    "FPSpan",
    "KNOWN_QUIRKS",
    "QUIRK_SUBPIXEL_WALL_CLIP",
    "QuirkMovementSystem",
    "QuirkRegistry",
    "RetroObstacle",
    "quantize_obstacles",
    "resolve_axis",
]
