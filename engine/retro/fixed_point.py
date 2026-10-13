"""
Fixed-point scalar and 2D vector types for deterministic retro math.

All values are stored as integers (arbitrary precision via Python int) scaled
by 2**frac_bits. This gives exact representation for multiples of the unit
and fully deterministic results for the supported operations, independent of
IEEE-754 rounding or associativity within the chosen precision.

Default precision (16 fractional bits) is a practical compromise used by many
classic and modern 2D engines for sub-pixel positioning (resolution ~1/65536).
Cartridges can choose other widths (8, 12, 24, ...) per component or vector.
"""

from __future__ import annotations

from typing import Union, overload
import math

Number = Union[int, float, "FixedPoint"]


class FixedPoint:
    """
    Immutable fixed-point scalar.

    Construction:
        FixedPoint(3)                    # exact integer
        FixedPoint(1.5)                  # quantized to default 16 frac bits
        FixedPoint.from_float(1/3, 8)    # explicit precision
        FixedPoint.from_raw(0x10000, 16) # raw scaled integer

    Arithmetic always produces a result quantized to the *left* operand's
    scale (or the explicit scale on construction). Mixed-scale operands are
    resampled by rounding to the target scale.

    The type is intentionally minimal and dependency-free so it can be
    copied verbatim into cartridges or used as the authoritative reference
    for "why this emergent behavior occurs".
    """

    __slots__ = ("_raw", "_frac_bits", "_scale")

    def __init__(
        self,
        value: Number = 0,
        *,
        frac_bits: int = 16,
        _raw: int | None = None,
    ) -> None:
        if not isinstance(frac_bits, int) or frac_bits < 0:
            raise ValueError("frac_bits must be a non-negative integer")
        self._frac_bits: int = frac_bits
        self._scale: int = 1 << frac_bits

        if _raw is not None:
            self._raw: int = int(_raw)
            return

        if isinstance(value, FixedPoint):
            if value._frac_bits == frac_bits:
                self._raw = value._raw
            else:
                # Resample by converting through float (lossy only at the target precision)
                self._raw = int(round(float(value) * self._scale))
            return

        if isinstance(value, (int, float)):
            self._raw = int(round(float(value) * self._scale))
            return

        raise TypeError(
            f"FixedPoint value must be int, float or FixedPoint, got {type(value)}"
        )

    # ------------------------------------------------------------------
    # Alternate constructors
    # ------------------------------------------------------------------
    @classmethod
    def from_float(cls, value: float, frac_bits: int = 16) -> FixedPoint:
        """Create from float, quantizing to the given fractional precision."""
        return cls(value, frac_bits=frac_bits)

    @classmethod
    def from_raw(cls, raw: int, frac_bits: int = 16) -> FixedPoint:
        """Create directly from a scaled raw integer (no quantization)."""
        return cls(0, frac_bits=frac_bits, _raw=raw)

    # ------------------------------------------------------------------
    # Conversion
    # ------------------------------------------------------------------
    def to_float(self) -> float:
        """Return the closest float representation."""
        return self._raw / self._scale

    def __float__(self) -> float:
        return self.to_float()

    def __int__(self) -> int:
        """Truncate toward zero (classic integer cast of fixed-point)."""
        return self._raw // self._scale

    @property
    def raw(self) -> int:
        """The underlying scaled integer (for advanced use / serialization)."""
        return self._raw

    @property
    def frac_bits(self) -> int:
        return self._frac_bits

    # ------------------------------------------------------------------
    # Arithmetic (produce new instances, quantized to self's scale)
    # ------------------------------------------------------------------
    def __add__(self, other: Number) -> FixedPoint:
        if isinstance(other, FixedPoint):
            if other._frac_bits == self._frac_bits:
                return FixedPoint(0, frac_bits=self._frac_bits, _raw=self._raw + other._raw)
            other_raw = int(round(float(other) * self._scale))
            return FixedPoint(0, frac_bits=self._frac_bits, _raw=self._raw + other_raw)
        return self + FixedPoint(other, frac_bits=self._frac_bits)

    def __radd__(self, other: Number) -> FixedPoint:
        return self + other

    def __sub__(self, other: Number) -> FixedPoint:
        if isinstance(other, FixedPoint):
            if other._frac_bits == self._frac_bits:
                return FixedPoint(0, frac_bits=self._frac_bits, _raw=self._raw - other._raw)
            other_raw = int(round(float(other) * self._scale))
            return FixedPoint(0, frac_bits=self._frac_bits, _raw=self._raw - other_raw)
        return self - FixedPoint(other, frac_bits=self._frac_bits)

    def __rsub__(self, other: Number) -> FixedPoint:
        return FixedPoint(other, frac_bits=self._frac_bits) - self

    def __mul__(self, other: Number) -> FixedPoint:
        if isinstance(other, FixedPoint):
            # Multiply then divide by the *other* scale to keep result at self scale
            # (a * b) / 2^f  when a and b are already scaled by their own 2^f
            if other._frac_bits == self._frac_bits:
                # (raw_a * raw_b) / scale   (integer division with rounding)
                product = self._raw * other._raw
                # Round to nearest: add half scale before trunc
                rounded = (product + (self._scale // 2)) // self._scale if self._scale > 0 else product // self._scale
                return FixedPoint(0, frac_bits=self._frac_bits, _raw=rounded)
            # Different scales: fall back to float round-trip at self precision
            return FixedPoint(float(self) * float(other), frac_bits=self._frac_bits)
        # scalar (int/float)
        other_fp = FixedPoint(other, frac_bits=self._frac_bits)
        return self * other_fp

    def __rmul__(self, other: Number) -> FixedPoint:
        return self * other

    def __truediv__(self, other: Number) -> FixedPoint:
        if isinstance(other, FixedPoint):
            if other._raw == 0:
                raise ZeroDivisionError("division by zero")
            if other._frac_bits == self._frac_bits:
                # (a / b)  =>  (raw_a * scale) / raw_b
                num = self._raw * self._scale
                # Round to nearest
                if num >= 0:
                    rounded = (num + (other._raw // 2)) // other._raw
                else:
                    rounded = (num - (other._raw // 2)) // other._raw
                return FixedPoint(0, frac_bits=self._frac_bits, _raw=rounded)
            return FixedPoint(float(self) / float(other), frac_bits=self._frac_bits)
        other_fp = FixedPoint(other, frac_bits=self._frac_bits)
        return self / other_fp

    def __rtruediv__(self, other: Number) -> FixedPoint:
        return FixedPoint(other, frac_bits=self._frac_bits) / self

    def __neg__(self) -> FixedPoint:
        return FixedPoint(0, frac_bits=self._frac_bits, _raw=-self._raw)

    def __abs__(self) -> FixedPoint:
        return FixedPoint(0, frac_bits=self._frac_bits, _raw=abs(self._raw))

    # ------------------------------------------------------------------
    # Comparisons (normalize via float for mixed-scale; exact for same scale)
    # ------------------------------------------------------------------
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, (int, float, FixedPoint)):
            return NotImplemented
        return math.isclose(float(self), float(other), rel_tol=0, abs_tol=1e-12)

    def __lt__(self, other: Number) -> bool:
        return float(self) < float(other)

    def __le__(self, other: Number) -> bool:
        return float(self) <= float(other)

    def __gt__(self, other: Number) -> bool:
        return float(self) > float(other)

    def __ge__(self, other: Number) -> bool:
        return float(self) >= float(other)

    # ------------------------------------------------------------------
    # Utility / representation
    # ------------------------------------------------------------------
    def __repr__(self) -> str:
        return f"FixedPoint({self.to_float()}, frac_bits={self._frac_bits})"

    def __str__(self) -> str:
        return f"{self.to_float()}Q{self._frac_bits}"

    def __hash__(self) -> int:
        # Hash on the quantized float value + precision so equal values compare equal
        return hash((round(self.to_float(), self._frac_bits + 4), self._frac_bits))

    def copy(self, *, frac_bits: int | None = None) -> FixedPoint:
        """Return a (possibly resampled) copy."""
        if frac_bits is None:
            return FixedPoint(0, frac_bits=self._frac_bits, _raw=self._raw)
        return FixedPoint(self, frac_bits=frac_bits)


# Convenience alias used by some older notes
Q = FixedPoint


# =============================================================================
# FixedPointVec2
# =============================================================================

class FixedPointVec2:
    """
    Immutable 2D vector of FixedPoint values (same fractional precision for x and y).

    Designed to be a drop-in *parallel* type for position/velocity storage in
    retro movement and collision code. Interoperates with panda3d.core.Vec2
    via to_vec2() / from_vec2().

    Most operations return a new FixedPointVec2 quantized to the vector's
    frac_bits. Length is returned as float (sqrt is not fixed-point friendly).
    """

    __slots__ = ("x", "y", "_frac_bits")

    def __init__(
        self,
        x: Number = 0,
        y: Number = 0,
        *,
        frac_bits: int = 16,
    ) -> None:
        self._frac_bits: int = frac_bits
        if isinstance(x, FixedPoint) and isinstance(y, FixedPoint):
            # If they have different prec, we resample y to x's (or use explicit frac_bits)
            fb = frac_bits if frac_bits != 16 or x._frac_bits == y._frac_bits else x._frac_bits
            self.x: FixedPoint = FixedPoint(x, frac_bits=fb) if x._frac_bits != fb else x
            self.y: FixedPoint = FixedPoint(y, frac_bits=fb) if y._frac_bits != fb else y
            self._frac_bits = fb
        else:
            self.x = FixedPoint(x, frac_bits=frac_bits)
            self.y = FixedPoint(y, frac_bits=frac_bits)

    @property
    def frac_bits(self) -> int:
        return self._frac_bits

    # ------------------------------------------------------------------
    # Construction helpers
    # ------------------------------------------------------------------
    @classmethod
    def from_vec2(cls, v: "Vec2", frac_bits: int = 16) -> FixedPointVec2:  # type: ignore[name-defined]
        """Create from a panda3d Vec2 (or any .x/.y float container)."""
        return cls(float(v.x), float(v.y), frac_bits=frac_bits)

    def to_vec2(self) -> "Vec2":  # type: ignore[name-defined]
        """Convert to a fresh panda3d.core.Vec2 (float values)."""
        from panda3d.core import Vec2  # local import to avoid hard dep at module load for pure tests

        return Vec2(float(self.x), float(self.y))

    # ------------------------------------------------------------------
    # Vector arithmetic
    # ------------------------------------------------------------------
    def __add__(self, other: "FixedPointVec2") -> FixedPointVec2:
        if not isinstance(other, FixedPointVec2):
            return NotImplemented
        fb = self._frac_bits
        return FixedPointVec2(
            self.x + other.x,
            self.y + other.y,
            frac_bits=fb,
        )

    def __sub__(self, other: "FixedPointVec2") -> FixedPointVec2:
        if not isinstance(other, FixedPointVec2):
            return NotImplemented
        fb = self._frac_bits
        return FixedPointVec2(
            self.x - other.x,
            self.y - other.y,
            frac_bits=fb,
        )

    def __mul__(self, scalar: Number) -> FixedPointVec2:
        fb = self._frac_bits
        return FixedPointVec2(
            self.x * scalar,
            self.y * scalar,
            frac_bits=fb,
        )

    def __rmul__(self, scalar: Number) -> FixedPointVec2:
        return self * scalar

    def __truediv__(self, scalar: Number) -> FixedPointVec2:
        fb = self._frac_bits
        return FixedPointVec2(
            self.x / scalar,
            self.y / scalar,
            frac_bits=fb,
        )

    def __neg__(self) -> FixedPointVec2:
        return FixedPointVec2(-self.x, -self.y, frac_bits=self._frac_bits)

    # ------------------------------------------------------------------
    # Vector products & metrics (deterministic where possible)
    # ------------------------------------------------------------------
    def dot(self, other: "FixedPointVec2") -> FixedPoint:
        """Dot product, result has this vector's fractional precision."""
        if not isinstance(other, FixedPointVec2):
            raise TypeError("dot requires another FixedPointVec2")
        # (x1*x2 + y1*y2) quantized
        return self.x * other.x + self.y * other.y

    def length_sq(self) -> FixedPoint:
        """Squared length (exact within precision, no sqrt)."""
        return self.x * self.x + self.y * self.y

    def length(self) -> float:
        """Euclidean length as float (sqrt of length_sq)."""
        return math.sqrt(float(self.length_sq()))

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------
    def get_xy_float(self) -> tuple[float, float]:
        return (float(self.x), float(self.y))

    def __repr__(self) -> str:
        return f"FixedPointVec2({float(self.x):.6f}, {float(self.y):.6f}, frac_bits={self._frac_bits})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FixedPointVec2):
            return NotImplemented
        return self.x == other.x and self.y == other.y
