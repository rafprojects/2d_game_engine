"""
Precision-aware components for the retro layer.

SubpixelTransformComponent (P2-A) stores position using FixedPointVec2 while
keeping rotation and scale as float (consistent with historical emphasis on
sub-pixel position/velocity for emergent collision and movement quirks).

SubpixelMovementComponent (P2-B) is a minimal velocity holder using
FixedPointVec2 for current/target velocity. It lets QuirkMovementSystem (and
cartridge authors) keep all integration and quirk rule math in the fixed-point
domain. Under the fixed-tick QuirkMovementSystem, velocities are expressed in
**pixels (or units) per tick**, like real 8-bit hardware - not per second.
It also carries the resolver-owned contact flags (on_ground / hit_ceiling /
hit_wall) that the system updates every tick.

SubpixelColliderComponent (P2-B re-work) gives an entity its own collision
extents in the retro layer (per-entity size; nothing is hardcoded). Entities
without it still integrate velocity but skip collision resolution.

All are deliberately *parallel* types to the float equivalents
(TransformComponent, MovementComponent, ColliderComponent). Cartridges opt
into them (or copy their rules) rather than the engine forcing retro
constraints on everyone.

See docs/PHASE2_RETRO_EMERGENT_GAMEPLAY_LAYER.md (tracks P2-A and P2-B) and
the individual classes for usage examples with QuirkMovementSystem.
"""

from __future__ import annotations

from engine.core.component import Component
from .fixed_point import FixedPoint, FixedPointVec2


class SubpixelTransformComponent(Component):
    """
    2D transform using fixed-point subpixel precision for position.

    Position is the primary retro-precise field (stored as FixedPointVec2).
    Rotation and uniform/non-uniform scale remain float because classic
    hardware constraints produced the most interesting emergent behavior
    in the position + velocity + collision domain.

    The component accepts ordinary floats on construction (they are quantized
    immediately) so cartridge code can look similar to modern code:

        SubpixelTransformComponent(x=10.25, y=3.0625, frac_bits=12)

    Use get_position_fp() / set_position() when you want to stay in the
    fixed domain, or the _float variants for interop with rendering / debug.
    """

    def __init__(
        self,
        x: float | int | FixedPoint = 0.0,
        y: float | int | FixedPoint = 0.0,
        rotation: float = 0.0,
        scale_x: float = 1.0,
        scale_y: float = 1.0,
        *,
        frac_bits: int = 16,
        position: FixedPointVec2 | None = None,
    ) -> None:
        if position is not None:
            if not isinstance(position, FixedPointVec2):
                raise TypeError("position must be a FixedPointVec2 when provided")
            self.position: FixedPointVec2 = position
            self._frac_bits: int = position.frac_bits
        else:
            self.position = FixedPointVec2(x, y, frac_bits=frac_bits)
            self._frac_bits = frac_bits

        self.rotation: float = float(rotation)
        self.scale_x: float = float(scale_x)
        self.scale_y: float = float(scale_y)

    @property
    def frac_bits(self) -> int:
        return self._frac_bits

    # ------------------------------------------------------------------
    # Position (primary retro-precise data)
    # ------------------------------------------------------------------
    def get_position_fp(self) -> FixedPointVec2:
        """Return the fixed-point position vector (no conversion)."""
        return self.position

    def get_position(self) -> tuple[float, float]:
        """Return position as (float, float) for compatibility with older code."""
        return self.position.get_xy_float()

    def set_position(self, x: float | int | FixedPoint, y: float | int | FixedPoint) -> None:
        """Set position, quantizing to the component's frac_bits."""
        self.position = FixedPointVec2(x, y, frac_bits=self._frac_bits)

    # ------------------------------------------------------------------
    # Scale (float, mirrors TransformComponent)
    # ------------------------------------------------------------------
    def get_scale(self) -> tuple[float, float]:
        return (self.scale_x, self.scale_y)

    def set_scale(self, scale_x: float, scale_y: float) -> None:
        self.scale_x = float(scale_x)
        self.scale_y = float(scale_y)

    # ------------------------------------------------------------------
    # Convenience / interop
    # ------------------------------------------------------------------
    def to_float_transform(self) -> "TransformComponent":  # type: ignore[name-defined]
        """
        Return a plain TransformComponent snapshot (float values).

        Useful for one-off hand-off to rendering or other float-based systems.
        The returned object is independent; further mutations to self will
        not affect it.
        """
        from engine.graphics.components.transform_component import TransformComponent

        fx, fy = self.get_position()
        return TransformComponent(
            x=fx,
            y=fy,
            rotation=self.rotation,
            scale_x=self.scale_x,
            scale_y=self.scale_y,
        )

    def __repr__(self) -> str:
        px, py = self.position.get_xy_float()
        return (
            f"SubpixelTransformComponent(x={px:.6f}, y={py:.6f}, "
            f"rotation={self.rotation}, scale=({self.scale_x}, {self.scale_y}), "
            f"frac_bits={self._frac_bits})"
        )


class SubpixelMovementComponent(Component):
    """
    Minimal movement state holder using fixed-point for velocity.

    Intended for use with QuirkMovementSystem (P2-B). Stores current and
    target velocity as FixedPointVec2 so that velocity integration, tentative
    position deltas, and quirk rules all execute with deterministic
    quantization in the reference retro layer.

    Velocity semantics under the fixed-tick QuirkMovementSystem: values are
    **per tick** (e.g. pixels/tick at 60 ticks per second), exactly like
    classic hardware. The system never multiplies by a float dt.

    Contact flags (owned by the resolver, read by cartridge controllers):
    - on_ground: entity was pushed up out of a solid while moving down this tick.
    - hit_ceiling: pushed down out of a solid while moving up.
    - hit_wall: collided on the X axis this tick.
    These replace ad-hoc float "grounded checks" in cartridges - the resolver's
    geometry is the single source of truth.

    Acceleration/deceleration and base speed remain float for cartridge
    ergonomics (they are quantized to the component's frac_bits by the system
    when producing FP deltas). This keeps the component small while ensuring
    the "why this emergent behavior" math stays visible in FP.

    It is deliberately parallel to MovementComponent. Cartridges opt in by
    adding Subpixel* components and registering the retro system.

    Example (cartridge or test):
        move = SubpixelMovementComponent(base_speed=2.0, frac_bits=8)
        move.current_velocity = FixedPointVec2(1.25, 0, frac_bits=8)
    """

    def __init__(
        self,
        base_speed: float = 1.0,
        acceleration: float = 10.0,
        deceleration: float = 10.0,
        *,
        frac_bits: int = 16,
        current_velocity: FixedPointVec2 | None = None,
        target_velocity: FixedPointVec2 | None = None,
    ) -> None:
        self.base_speed: float = float(base_speed)
        self.acceleration: float = float(acceleration)
        self.deceleration: float = float(deceleration)
        self._frac_bits: int = frac_bits

        if current_velocity is not None:
            self.current_velocity: FixedPointVec2 = FixedPointVec2(
                current_velocity, frac_bits=frac_bits
            )
        else:
            self.current_velocity = FixedPointVec2(0, 0, frac_bits=frac_bits)

        if target_velocity is not None:
            self.target_velocity: FixedPointVec2 = FixedPointVec2(
                target_velocity, frac_bits=frac_bits
            )
        else:
            self.target_velocity = FixedPointVec2(0, 0, frac_bits=frac_bits)

        self.can_move: bool = True
        self.is_moving: bool = False

        # Contact flags - written by QuirkMovementSystem each tick.
        self.on_ground: bool = False
        self.hit_ceiling: bool = False
        self.hit_wall: bool = False

    @property
    def frac_bits(self) -> int:
        return self._frac_bits

    # ------------------------------------------------------------------
    # Velocity (primary retro-precise data)
    # ------------------------------------------------------------------
    def get_velocity_fp(self) -> FixedPointVec2:
        """Return current velocity as FixedPointVec2 (no conversion)."""
        return self.current_velocity

    def get_velocity(self) -> tuple[float, float]:
        """Return current velocity as (float, float) for interop/debug."""
        return self.current_velocity.get_xy_float()

    def set_velocity(self, x: float | int | FixedPoint, y: float | int | FixedPoint) -> None:
        """Set current velocity, quantizing to the component's frac_bits."""
        self.current_velocity = FixedPointVec2(x, y, frac_bits=self._frac_bits)

    def set_target_velocity(self, x: float | int | FixedPoint, y: float | int | FixedPoint) -> None:
        """Set target velocity (for smoothed movement), quantizing."""
        self.target_velocity = FixedPointVec2(x, y, frac_bits=self._frac_bits)

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------
    def __repr__(self) -> str:
        vx, vy = self.current_velocity.get_xy_float()
        return (
            f"SubpixelMovementComponent(vel=({vx:.6f}, {vy:.6f}), "
            f"base_speed={self.base_speed}, frac_bits={self._frac_bits})"
        )


class SubpixelColliderComponent(Component):
    """
    Per-entity collision extents for the retro layer (axis-aligned box).

    Width/height are in the same units as the entity's SubpixelTransform
    position (virtual pixels for a VirtualPlayfield cartridge). They are
    quantized to frac_bits on construction and stored as half-extents, which
    is what the axis resolver actually consumes.

    Entities with SubpixelTransform + SubpixelMovement but WITHOUT this
    component integrate velocity normally but skip collision resolution
    entirely (useful for particles/decorations).

    Example (12x16 px player on an 8.8 grid):
        SubpixelColliderComponent(12, 16, frac_bits=8)
    """

    def __init__(
        self,
        width: float | int | FixedPoint,
        height: float | int | FixedPoint,
        *,
        frac_bits: int = 16,
    ) -> None:
        w = FixedPoint(width, frac_bits=frac_bits)
        h = FixedPoint(height, frac_bits=frac_bits)
        if w.raw <= 0 or h.raw <= 0:
            raise ValueError("SubpixelColliderComponent width/height must be positive")
        self._frac_bits: int = frac_bits
        two = FixedPoint(2, frac_bits=frac_bits)
        self.half_w: FixedPoint = w / two
        self.half_h: FixedPoint = h / two

    @property
    def frac_bits(self) -> int:
        return self._frac_bits

    @property
    def width(self) -> float:
        return float(self.half_w) * 2.0

    @property
    def height(self) -> float:
        return float(self.half_h) * 2.0

    def __repr__(self) -> str:
        return (
            f"SubpixelColliderComponent({self.width}x{self.height}, "
            f"frac_bits={self._frac_bits})"
        )
