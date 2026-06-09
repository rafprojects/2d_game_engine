"""
Precision-aware components for the retro layer.

SubpixelTransformComponent is the primary deliverable for P2-A. It stores
position using FixedPointVec2 while keeping rotation and scale as float
(consistent with historical emphasis on sub-pixel position/velocity for
emergent collision and movement quirks).

It is deliberately a *parallel* type to TransformComponent. Cartridges opt
into it (or copy its rules) rather than the engine forcing it on everyone.
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
