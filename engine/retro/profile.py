"""Lightweight retro fidelity profile for P2-C opt-in.

This provides a simple "fidelity profile" concept (dict/enum-like at cartridge
initialize time) that retro systems can read. It is a minimal precursor to the
full FidelityProfile coordinator planned for PHASE5.

Cartridges opt into the retro layer by:
- Using Subpixel* components (SubpixelTransformComponent, SubpixelMovementComponent)
  on entities that should use retro math/quirks. These act as the per-entity
  "flag" / enhanced transform for precision (as suggested in PHASE2).
- Registering retro systems (e.g. QuirkMovementSystem) in the cartridge
  entrypoint (via CartridgeContext.world.add_system), optionally passing a
  RetroProfile.

Example (in cartridge initialize hook, a few lines for P2-D ref cartridge):
    from engine.retro import (
        RetroProfile,
        SubpixelTransformComponent,
        SubpixelMovementComponent,
        QuirkMovementSystem,
    )

    profile = RetroProfile(
        name="nes",
        frac_bits=8,
        enable_quirks=["subpixel_wall_clip"],
    )
    context.world.add_system(QuirkMovementSystem(context.world, profile=profile))

    # For a gameplay entity:
    e = context.world.create_entity()
    context.world.add_component(e.id, SubpixelTransformComponent(x=0, y=0, frac_bits=profile.frac_bits))
    context.world.add_component(e.id, SubpixelMovementComponent(frac_bits=profile.frac_bits))
    # ... set velocity etc.

Coexistence rules (documented per PHASE2):
- Retro systems ONLY query entities that have the Subpixel* components.
- Default systems (MovementSystem, CollisionSystem) use TransformComponent /
  MovementComponent / ColliderComponent and will not pick up pure-retro entities.
- Do not mix Subpixel* and regular float components on the SAME entity unless
  you explicitly want both systems to act (not recommended; can cause double
  updates or conflicts). Retro entities should use Subpixel* exclusively for
  their precision-sensitive parts.
- The presence of `engine/retro/` (import) has no side effects on modern
  cartridges or the default engine path (verified in P2-A/P2-B).
- Future multi-cartridge hosts (PHASE4+) will benefit because each cartridge
  controls its own systems/components via its context/world.

See:
- docs/PHASE2_RETRO_EMERGENT_GAMEPLAY_LAYER.md (Track P2-C)
- engine/retro/ for the systems and components.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class RetroProfile:
    """Simple fidelity/precision profile for the retro layer (P2-C).

    name: Human-readable profile name (e.g. "nes", "modern", "arcade").
    frac_bits: Default fractional precision for Subpixel* components created
               under this profile (cartridges can override per-component).
    enable_quirks: List of quirk names to auto-enable on QuirkMovementSystem
                   (e.g. ["subpixel_wall_clip", "momentum_residual"]).
    options: Extensible dict for future profile dimensions (visuals, audio,
             other simulation rules). Ignored by P2 retro systems but available
             for P5+ full fidelity coordinator and cartridges.

    This is intentionally lightweight (dataclass + simple fields) so it can be
    used directly at cartridge initialize time without pulling in heavier
    machinery. It satisfies the PHASE2 suggestion of a "simple 'fidelity profile'
    concept (even if just a dict or enum at cartridge initialize time)".

    The retro systems (QuirkMovementSystem etc.) accept an optional profile and
    will use its settings (e.g. auto-enabling quirks, default frac).
    """

    name: str = "modern"
    frac_bits: int = 16
    enable_quirks: List[str] = field(default_factory=list)
    options: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name:
            raise ValueError("RetroProfile.name must be a non-empty string")
        if not isinstance(self.frac_bits, int) or self.frac_bits < 0:
            raise ValueError("RetroProfile.frac_bits must be a non-negative int")
        if not isinstance(self.enable_quirks, (list, tuple)):
            raise TypeError("RetroProfile.enable_quirks must be a list of str")
        if not isinstance(self.options, dict):
            raise TypeError("RetroProfile.options must be a dict")

    def __repr__(self) -> str:
        return (
            f"RetroProfile(name={self.name!r}, frac_bits={self.frac_bits}, "
            f"enable_quirks={self.enable_quirks}, options={self.options})"
        )
