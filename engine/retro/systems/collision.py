"""
FP-native axis-separated collision resolution with an authentic NES-style
ejection quirk (P2-B, rebuilt).

This module is the "intentional" part of the retro reference layer. It
implements the collision model that classic 8-bit platformers actually used -
move one axis at a time, then push the body out of any solid it overlaps -
together with the *ejection-direction rule* that made genuine wall clips
possible on real hardware.

The two ejection policies
=========================

Modern (quirk OFF - motion-based ejection):
    "Push the body back out the face it moved into." If you were moving
    right and overlap a wall, you are snapped to the wall's left face;
    moving left, to its right face. You can NEVER end up on the far side of
    a solid, no matter how fast you move. This mirrors what a correct
    modern resolver (or the engine's float MTV systems) guarantees.

Retro (quirk ON - "subpixel_wall_clip", mechanism: midline ejection):
    "Push the body out of whichever half of the obstacle it is in." The
    resolver does not ask which way you were moving - it asks where your
    penetrating edge sits relative to the obstacle's midline, exactly like
    NES tile engines that ejected based on which half of the tile a probe
    point landed in. The consequence is genuinely emergent:

    * If your per-tick movement exceeds HALF the obstacle's thickness, the
      first tick that overlaps the obstacle can land your leading edge
      *past* its midline. The resolver then "helpfully" ejects you out the
      FAR side: a wall clip.
    * Whether that happens on a given approach depends on your exact
      subpixel position modulo the per-tick stride - a one-subpixel change
      in starting position flips the outcome (see the worked example below).
    * Obstacles thicker than 2x your speed can never be clipped (the
      leading edge cannot reach the midline on the contact tick), which is
      why floors/platforms in the reference cartridge are safe while the
      thin wall is clippable.

Worked example (8.8 fixed point, the reference cartridge's numbers)
===================================================================
Player half-width 6 px (raw 1536), wall spanning x 200..206 px
(raw min/mid/max = 51200/51968/52736), running right at 4.0 px/tick
(raw 1024) from center x0 = 153.5 px (raw 39296):

    tick 10: x = 193.5, right edge raw = 51072 <= 51200 -> no overlap yet
    tick 11: x = 197.5, right edge raw = 52096 >  51200 -> overlap!
             probe = 52096 > midline 51968 -> ejected out the FAR side
             -> x = (52736 + 1536) / 256 = 212.0  *** through the wall ***

Same speed from x0 = 150.5 (raw 38528): tick-11 right edge raw = 51328,
which is <= 51968, so the player is pushed back to x = 194.0 - blocked.
From raw 39168 (x0 = 153.0) the tick-11 edge lands EXACTLY on the midline
(51968); the strict `>` comparison fails and the player is blocked - but
one subpixel later (raw 39169) it clips. That single-subpixel sensitivity
is the point of the whole layer.

All comparisons are raw-integer compares at one shared frac_bits scale, so
every outcome is exact and reproducible. Overlap is STRICT (`>` / `<`):
touching edges do not collide, which keeps bodies resting exactly on
surfaces stable.

Usage (typically via QuirkMovementSystem; direct use shown for clarity):

    from engine.retro.systems.collision import (
        QuirkRegistry, RetroObstacle, quantize_obstacles, resolve_axis,
    )

    spans = quantize_obstacles([RetroObstacle(203, 68, 6, 104, name="wall")], frac_bits=8)
    res = resolve_axis(pos_x, pos_y, half_w, half_h,
                       delta=vel_x, axis="x", obstacles=spans,
                       midline_ejection=True)
    # res.value is the final X; res.clipped tells you the emergent moment.

Pure Python, no side effects, safe to copy into cartridges.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, NamedTuple, Sequence

from ..fixed_point import FixedPoint


QUIRK_SUBPIXEL_WALL_CLIP = "subpixel_wall_clip"
KNOWN_QUIRKS = frozenset({QUIRK_SUBPIXEL_WALL_CLIP})


class QuirkRegistry:
    """
    Lightweight registry for enabling/disabling individual quirk rules by name.

    Makes it easy for cartridges (and tests) to turn specific classic behaviors
    on or off for experimentation, exactly as described in the cartridge vision
    and PHASE2.

    Example:
        reg = QuirkRegistry()
        reg.enable("subpixel_wall_clip")
        if reg.is_active("subpixel_wall_clip"):
            ...
    """

    def __init__(self) -> None:
        self._active: set[str] = set()

    def enable(self, name: str) -> None:
        """Enable a named quirk rule (idempotent)."""
        if not isinstance(name, str) or not name:
            raise ValueError("quirk name must be a non-empty string")
        self._active.add(name)

    def disable(self, name: str) -> None:
        """Disable a named quirk rule (idempotent)."""
        self._active.discard(name)

    def is_active(self, name: str) -> bool:
        """Return whether the named quirk is currently enabled."""
        return name in self._active

    @property
    def active(self) -> set[str]:
        """Return a copy of the currently active quirk names."""
        return self._active.copy()

    def __repr__(self) -> str:
        return f"QuirkRegistry(active={sorted(self._active)})"


@dataclass(frozen=True)
class RetroObstacle:
    """A static solid (or decorative) axis-aligned box in retro-space units.

    cx/cy is the CENTER of the box; w/h its full extents - all in the same
    units as the Subpixel* components that collide with it (virtual pixels
    for a VirtualPlayfield cartridge). ``solid=False`` boxes are ignored by
    the resolver (handy for decorative markers that still want a render
    entity generated from the same level list).

    Level geometry is assumed non-overlapping between solids; the resolver
    does a single pass per axis.
    """

    cx: float
    cy: float
    w: float
    h: float
    solid: bool = True
    name: str = ""


class FPSpan(NamedTuple):
    """A RetroObstacle pre-quantized to raw fixed-point integer spans.

    mid_* is the obstacle midline used by the retro ejection rule
    (floor of the exact midpoint - deterministic for odd raw extents).
    """

    min_x: int
    max_x: int
    mid_x: int
    min_y: int
    max_y: int
    mid_y: int
    solid: bool
    name: str


def quantize_obstacles(
    obstacles: Sequence[RetroObstacle], frac_bits: int
) -> list[FPSpan]:
    """Quantize obstacle boxes once into raw-int spans at the given precision.

    Done once (not per tick) so the per-tick resolver works purely on ints.
    """
    spans: list[FPSpan] = []
    two = FixedPoint(2, frac_bits=frac_bits)
    for obs in obstacles:
        cx = FixedPoint(obs.cx, frac_bits=frac_bits)
        cy = FixedPoint(obs.cy, frac_bits=frac_bits)
        half_w = FixedPoint(obs.w, frac_bits=frac_bits) / two
        half_h = FixedPoint(obs.h, frac_bits=frac_bits) / two
        min_x = cx.raw - half_w.raw
        max_x = cx.raw + half_w.raw
        min_y = cy.raw - half_h.raw
        max_y = cy.raw + half_h.raw
        spans.append(
            FPSpan(
                min_x=min_x,
                max_x=max_x,
                mid_x=(min_x + max_x) // 2,
                min_y=min_y,
                max_y=max_y,
                mid_y=(min_y + max_y) // 2,
                solid=obs.solid,
                name=obs.name,
            )
        )
    return spans


@dataclass
class AxisResolution:
    """Result of resolving one axis of movement against the level solids.

    value:     final axis coordinate (body center) as FixedPoint.
    collided:  the body overlapped at least one solid on this axis this tick.
    eject_dir: -1 pushed toward the obstacle's min side, +1 toward its max
               side, 0 if no collision.
    clipped:   midline ejection pushed the body out the side it was MOVING
               toward - i.e. the emergent wall clip happened.
    obstacle:  name of the obstacle involved (the clipping one if clipped,
               else the last one resolved against).
    """

    value: FixedPoint
    collided: bool = False
    eject_dir: int = 0
    clipped: bool = False
    obstacle: str = ""


def resolve_axis(
    pos_x: FixedPoint,
    pos_y: FixedPoint,
    half_w: FixedPoint,
    half_h: FixedPoint,
    delta: FixedPoint,
    axis: Literal["x", "y"],
    obstacles: Sequence[FPSpan],
    midline_ejection: bool,
) -> AxisResolution:
    """Integrate `delta` on one axis and resolve overlaps against solids.

    This is the rebuilt core of P2-B. All inputs must share one frac_bits
    scale (QuirkMovementSystem guarantees this); every comparison below is a
    raw-integer compare, so results are exact and deterministic.

    Policy selection:
    - ``midline_ejection=False`` -> modern motion-based ejection: snap back
      out the face you moved into. Never clips.
    - ``midline_ejection=True``  -> the "subpixel_wall_clip" quirk: ejection
      side is chosen by comparing the penetrating probe edge against the
      obstacle's midline ("which half of the obstacle am I in?"). When the
      per-tick delta exceeds half the obstacle's thickness AND the subpixel
      alignment lands the leading edge strictly past the midline on the
      contact tick, the body is ejected out the FAR side - the emergent
      clip. See the module docstring for the worked 8.8 example.

    The probe is the player edge that lies strictly inside the obstacle's
    span (leading edge in the common case); if both or neither edge is
    inside (body engulfed / spanning), the body center is used.

    A stationary overlap (delta == 0, e.g. a spawn inside a solid) is pushed
    to the nearest side under BOTH policies - you cannot clip without motion.

    Returns an AxisResolution; callers zero the axis velocity when
    ``collided`` is True (classic hardware behavior).
    """
    fb = pos_x.frac_bits

    if axis == "x":
        moved = pos_x.raw + delta.raw
        half_axis = half_w.raw
        other_min = pos_y.raw - half_h.raw
        other_max = pos_y.raw + half_h.raw
    else:
        moved = pos_y.raw + delta.raw
        half_axis = half_h.raw
        other_min = pos_x.raw - half_w.raw
        other_max = pos_x.raw + half_w.raw

    d = delta.raw
    collided = False
    eject_dir = 0
    clipped = False
    obstacle_name = ""

    for obs in obstacles:
        if not obs.solid:
            continue
        if axis == "x":
            o_min, o_max, o_mid = obs.min_x, obs.max_x, obs.mid_x
            oo_min, oo_max = obs.min_y, obs.max_y
        else:
            o_min, o_max, o_mid = obs.min_y, obs.max_y, obs.mid_y
            oo_min, oo_max = obs.min_x, obs.max_x

        # Strict overlap check on the OTHER axis (touching is not overlap).
        if not (other_max > oo_min and other_min < oo_max):
            continue

        lo = moved - half_axis
        hi = moved + half_axis
        # Strict overlap on the moving axis.
        if not (hi > o_min and lo < o_max):
            continue

        collided = True

        if d == 0:
            # Stationary overlap safety: nearest-side push, never a clip.
            if moved <= o_mid:
                moved = o_min - half_axis
                this_eject = -1
            else:
                moved = o_max + half_axis
                this_eject = +1
        elif midline_ejection:
            # THE QUIRK. Which half of the obstacle is the probe in?
            hi_inside = o_min < hi < o_max
            lo_inside = o_min < lo < o_max
            if hi_inside and not lo_inside:
                probe = hi
            elif lo_inside and not hi_inside:
                probe = lo
            else:
                probe = moved
            if probe > o_mid:  # STRICT: landing exactly on the midline blocks
                moved = o_max + half_axis
                this_eject = +1
            else:
                moved = o_min - half_axis
                this_eject = -1
            if (d > 0 and this_eject > 0) or (d < 0 and this_eject < 0):
                # Ejected out the side we were moving toward: the clip.
                clipped = True
                obstacle_name = obs.name
        else:
            # Modern: snap back out the face we moved into.
            if d > 0:
                moved = o_min - half_axis
                this_eject = -1
            else:
                moved = o_max + half_axis
                this_eject = +1

        eject_dir = this_eject
        if not clipped:
            obstacle_name = obs.name
        # Single pass continues with the corrected position (level solids
        # are assumed non-overlapping, so later obstacles see a clean state).

    return AxisResolution(
        value=FixedPoint.from_raw(moved, frac_bits=fb),
        collided=collided,
        eject_dir=eject_dir,
        clipped=clipped,
        obstacle=obstacle_name,
    )
