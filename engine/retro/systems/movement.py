"""
QuirkMovementSystem - Reference retro movement system with intentional quirk rules (P2-B).

This is the main deliverable for Track P2-B. It is a drop-in style System that
operates *only* on entities carrying the P2-A retro precision components
(SubpixelTransformComponent + SubpixelMovementComponent).

It performs:
- Velocity integration using FixedPoint arithmetic (with explicit quantization
  points documented in comments).
- Collision response via the FP resolver in collision.py.
- Application of any enabled quirk rules (via QuirkRegistry), which can
  intentionally produce classic emergent behaviors.

The system never touches float Transforms, Vec2 velocities, the default
MovementSystem, or the default CollisionSystem. Modern code paths remain
completely unaffected.

A cartridge "registers the retro movement + collision components" by:
    world.add_component(e.id, SubpixelTransformComponent(...))
    world.add_component(e.id, SubpixelMovementComponent(...))
    # (existing ColliderComponent on walls work via FP snapshot)
    sys = QuirkMovementSystem(world)
    sys.enable_quirk("subpixel_wall_clip")
    world.add_system(sys)

See docs/PHASE2_RETRO_EMERGENT_GAMEPLAY_LAYER.md and the approved plan
for the full design rationale, NES research basis, and deterministic test
examples that prove a quirk only occurs when the retro path + rule is active.

Pure Python, no external dependencies beyond the engine's own retro primitives
and core World.
"""

from __future__ import annotations

from engine.core.system import System
from engine.graphics.components.transform_component import TransformComponent
from engine.physics.components.collider_component import ColliderComponent

from ..components import SubpixelTransformComponent, SubpixelMovementComponent
from .collision import QuirkRegistry, resolve_quirky
from ..fixed_point import FixedPoint, FixedPointVec2


class QuirkMovementSystem(System):
    """
    Reference implementation of NES-style / quirk movement (P2-B).

    Applies velocity in the fixed-point domain, performs a full tentative step,
    then resolves against obstacles (snapped from any ColliderComponents in the
    world, plus any extra obstacles supplied at construction) using pluggable
    documented quirk rules.

    Quantization is applied at well-defined points so that the "why this quirk
    happens" is always reproducible and explainable.

    Usage:
        reg = QuirkRegistry()
        reg.enable("subpixel_wall_clip")
        sys = QuirkMovementSystem(world, quirk_registry=reg)
        # or
        sys = QuirkMovementSystem(world)
        sys.enable_quirk("subpixel_wall_clip")
    """

    def __init__(
        self,
        world,
        extra_obstacles: list[dict] | None = None,
        quirk_registry: QuirkRegistry | None = None,
    ) -> None:
        super().__init__(world)
        self._extra_obstacles: list[dict] = extra_obstacles or []
        self.quirk_registry: QuirkRegistry = quirk_registry or QuirkRegistry()

    def enable_quirk(self, name: str) -> None:
        """Enable a named quirk for this system instance."""
        self.quirk_registry.enable(name)

    def disable_quirk(self, name: str) -> None:
        """Disable a named quirk for this system instance."""
        self.quirk_registry.disable(name)

    def update(self, dt: float) -> None:
        """Advance all entities using Subpixel* components with quirk-aware rules."""
        entities = self.world.get_entities_with_components(
            SubpixelTransformComponent, SubpixelMovementComponent
        )

        for entity in entities:
            st: SubpixelTransformComponent | None = self.world.get_component(
                entity.id, SubpixelTransformComponent
            )
            sm: SubpixelMovementComponent | None = self.world.get_component(
                entity.id, SubpixelMovementComponent
            )

            if not st or not sm or not sm.can_move:
                continue

            fb = st.frac_bits

            # ------------------------------------------------------------------
            # Velocity integration (reference implementation)
            # ------------------------------------------------------------------
            # In a fuller cartridge you would also handle input -> target_velocity,
            # acceleration toward target, etc. Here we keep the reference minimal
            # and focused on the precision + quirk story: we take whatever
            # current_velocity is set on the component (tests and cartridges can
            # set it directly or implement their own higher-level controller that
            # writes FP velocities).

            vel: FixedPointVec2 = sm.current_velocity

            # Quantization point 1: convert dt to FixedPoint at *this entity's* precision.
            # This emulates a per-frame fixed-point time step.
            dt_fp = FixedPoint.from_float(dt, frac_bits=fb)

            # Quantization point 2: multiply velocity by dt (the FixedPointVec2 *
            # operator performs the scale-aware multiplication + rounding back
            # to the vector's frac_bits).
            delta: FixedPointVec2 = vel * dt_fp

            current_pos: FixedPointVec2 = st.position
            intended_pos: FixedPointVec2 = current_pos + delta

            # ------------------------------------------------------------------
            # Build obstacle list (FP snapshot)
            # ------------------------------------------------------------------
            obstacles: list[dict] = list(self._extra_obstacles)

            # Snapshot any entities that have a (float) Transform + Collider.
            # We convert their data to the mover's frac_bits so all math stays FP.
            collider_entities = self.world.get_entities_with_components(
                TransformComponent, ColliderComponent
            )
            for other in collider_entities:
                if other.id == entity.id:
                    continue
                t = self.world.get_component(other.id, TransformComponent)
                c = self.world.get_component(other.id, ColliderComponent)
                if not t or not c:
                    continue

                obs_pos = FixedPointVec2(float(t.x), float(t.y), frac_bits=fb)

                # Approximate size from collider (rect or circle->square for this reference)
                if getattr(c, "collider_type", None) is not None and "RECT" in str(c.collider_type).upper():
                    sx = float(getattr(c.size, "x", c.size[0]) if hasattr(c.size, "x") else c.size[0])
                    sy = float(getattr(c.size, "y", c.size[1]) if hasattr(c.size, "y") else c.size[1])
                else:
                    r = float(getattr(c, "radius", 0.5)) * 2.0
                    sx = sy = r

                obs_size = FixedPointVec2(sx, sy, frac_bits=fb)

                obstacles.append({
                    "pos": obs_pos,
                    "size": obs_size,
                    "solid": not getattr(c, "is_trigger", False),
                    "player_size": FixedPointVec2(0.8, 0.8, frac_bits=fb),
                })

            # ------------------------------------------------------------------
            # Resolve using the quirk-aware FP resolver
            # ------------------------------------------------------------------
            final_pos, final_vel, _info = resolve_quirky(
                current_pos,
                intended_pos,
                vel,
                obstacles,
                self.quirk_registry,
                fb,
            )

            # Write the (possibly quirk-modified) results back
            st.position = final_pos
            sm.current_velocity = final_vel

            # Very light "is_moving" maintenance for ergonomics
            if sm.current_velocity.length() > 0.001:
                sm.is_moving = True
            else:
                sm.is_moving = False
