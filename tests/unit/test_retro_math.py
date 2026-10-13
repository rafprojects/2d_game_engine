"""
Unit tests for the P2-A retro math primitives (FixedPoint, FixedPointVec2,
SubpixelTransformComponent).

These tests also serve as executable documentation for the quantization
behavior that enables reproducible emergent mechanics.
"""

import math

import pytest
from panda3d.core import Vec2

# ------------------------------------------------------------------
# FixedPoint scalar
# ------------------------------------------------------------------

def test_fixedpoint_basic_construction_and_roundtrip():
    from engine.retro.fixed_point import FixedPoint

    # Default 16 frac bits
    a = FixedPoint(3)
    assert float(a) == 3.0
    assert int(a) == 3
    assert a.frac_bits == 16

    b = FixedPoint(1.5)
    assert abs(float(b) - 1.5) < 1e-9

    # from_float explicit
    c = FixedPoint.from_float(1.0 / 3.0, frac_bits=8)
    # 1/3 at 8 bits is 0.00390625 * 85 = 0.33203125 (representable)
    assert c.frac_bits == 8
    assert abs(float(c) - (85 / 256)) < 1e-9

    # from_raw
    d = FixedPoint.from_raw(0x10000, 16)  # exactly 1.0
    assert float(d) == 1.0


def test_fixedpoint_quantization_demonstrates_subpixel_preservation():
    """Core motivating example for P2-A.

    Repeated addition of a small fraction. With fixed-point we stay on the
    exact grid defined by the scale; pure float can drift.
    """
    from engine.retro.fixed_point import FixedPoint

    step = FixedPoint(1, frac_bits=8) / 3   # ~0.00390625 * 85/256 wait, better 1/256 style
    # Use a clean 1/256 step (common sub-pixel unit)
    step = FixedPoint.from_float(1.0 / 256.0, frac_bits=8)

    acc = FixedPoint(0, frac_bits=8)
    for _ in range(100):
        acc = acc + step

    # Must be *exactly* 100/256 in the fixed representation
    expected = 100 / 256.0
    assert math.isclose(float(acc), expected, abs_tol=1e-12)

    # The raw value must be an exact multiple of the scale unit
    assert acc.raw == 100 * (1 << (8 - 8)) * (1 << 0)  # adjust: for 8 bits, unit = 1/256 = 2^-8
    # Simpler: scale for 8 bits is 256, 100 steps of 1 -> 100
    # Our step is 1 raw unit (because 1/256 at 8 bits = raw 1)
    assert acc.raw == 100


def test_fixedpoint_arithmetic_and_mixed_scale():
    from engine.retro.fixed_point import FixedPoint

    a = FixedPoint(2, frac_bits=4)
    b = FixedPoint(0.5, frac_bits=4)
    assert float(a + b) == 2.5

    # Different scales -> resampled to left
    c = FixedPoint(1, frac_bits=8)
    d = a + c   # a (4 bits) + c (resampled)
    assert d.frac_bits == 4

    # Mul / div
    e = FixedPoint(10, frac_bits=4) * 2
    assert float(e) == 20.0

    f = FixedPoint(10, frac_bits=4) / 2
    assert abs(float(f) - 5.0) < 1e-9


def test_fixedpoint_comparisons_and_hash():
    from engine.retro.fixed_point import FixedPoint

    a = FixedPoint(1.25, frac_bits=8)
    b = FixedPoint(1.25, frac_bits=8)
    assert a == b
    assert a < FixedPoint(2, frac_bits=8)
    assert hash(a) == hash(b)


# ------------------------------------------------------------------
# FixedPointVec2
# ------------------------------------------------------------------

def test_fixedpointvec2_construction_and_vec2_roundtrip():
    from engine.retro.fixed_point import FixedPointVec2

    v = FixedPointVec2(1.5, 2.25, frac_bits=8)
    assert v.frac_bits == 8
    p = v.to_vec2()
    assert isinstance(p, Vec2)
    assert abs(p.x - 1.5) < 1e-4 and abs(p.y - 2.25) < 1e-4

    v2 = FixedPointVec2.from_vec2(Vec2(3.0, -1.0), frac_bits=12)
    assert v2.frac_bits == 12
    assert abs(float(v2.x) - 3.0) < 1e-4


def test_fixedpointvec2_vector_ops():
    from engine.retro.fixed_point import FixedPointVec2, FixedPoint

    a = FixedPointVec2(1, 2, frac_bits=8)
    b = FixedPointVec2(3, 4, frac_bits=8)

    c = a + b
    assert float(c.x) == 4.0 and float(c.y) == 6.0

    d = b - a
    assert float(d.x) == 2.0

    e = a * 2
    assert float(e.y) == 4.0

    dot = a.dot(b)
    assert isinstance(dot, FixedPoint)
    assert float(dot) == 1*3 + 2*4   # 11

    lsq = a.length_sq()
    assert float(lsq) == 1 + 4

    length = a.length()
    assert math.isclose(length, math.sqrt(5), abs_tol=1e-9)


def test_fixedpointvec2_subpixel_accumulation_demo():
    """Demonstrate the exact subpixel preservation story using the vector type."""
    from engine.retro.fixed_point import FixedPointVec2

    pos = FixedPointVec2(0, 0, frac_bits=8)
    vel = FixedPointVec2(0, 1.0 / 256.0, frac_bits=8)

    for _ in range(100):
        pos = pos + vel

    x, y = pos.get_xy_float()
    assert x == 0.0
    assert math.isclose(y, 100 / 256.0, abs_tol=1e-12)


# ------------------------------------------------------------------
# SubpixelTransformComponent
# ------------------------------------------------------------------

def test_subpixel_transform_initialization_and_position():
    from engine.retro.components import SubpixelTransformComponent
    from engine.retro.fixed_point import FixedPointVec2

    t = SubpixelTransformComponent()
    assert t.frac_bits == 16
    assert float(t.position.x) == 0.0

    t2 = SubpixelTransformComponent(x=10.25, y=3.0625, frac_bits=12, rotation=45.0)
    assert t2.frac_bits == 12
    assert abs(t2.get_position()[0] - 10.25) < 1e-3
    assert t2.rotation == 45.0

    # Set via float (quantizes)
    t2.set_position(0.1, 0.2)
    fx, fy = t2.get_position()
    # After quantize at 12 bits the value is a multiple of 2^-12
    unit = 1.0 / (1 << 12)
    assert abs(fx % unit) < 1e-12 or abs((fx % unit) - unit) < 1e-12

    # Direct FP position
    fpv = FixedPointVec2(5, 7, frac_bits=10)
    t3 = SubpixelTransformComponent(position=fpv)
    assert t3.frac_bits == 10
    assert float(t3.position.y) == 7.0


def test_subpixel_transform_to_float_transform():
    from engine.retro.components import SubpixelTransformComponent
    from engine.graphics.components.transform_component import TransformComponent

    t = SubpixelTransformComponent(x=1.5, y=2.25, frac_bits=8, scale_x=2.0)
    tf = t.to_float_transform()
    assert isinstance(tf, TransformComponent)
    assert abs(tf.x - 1.5) < 1e-3
    assert tf.scale_x == 2.0


def test_subpixel_transform_import_from_engine_retro():
    """AC: from engine.retro import ... succeeds."""
    from engine.retro import FixedPoint, FixedPointVec2, SubpixelTransformComponent

    v = FixedPointVec2(0.5, 0.25)
    t = SubpixelTransformComponent(x=0, y=0)
    assert isinstance(v, FixedPointVec2)
    assert isinstance(t, SubpixelTransformComponent)
    # Also scalar
    f = FixedPoint(3.0)
    assert float(f) == 3.0
