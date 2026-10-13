"""Fifteen corridor-shooter movement patterns.

Positions use engine corridor space: X to the right, Y up. `descent` is a
positive speed subtracted from Y, and every path is relative to the spawn
point. Each state owns a `random.Random`, so a pattern never touches the
process-wide RNG.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Callable, Mapping

from engine.animation.tweening import EasingFunctions

NAMES: tuple[str, ...] = (
    "straight",
    "linear",
    "sinusoidal",
    "circular",
    "figure_eight",
    "spiral",
    "pendulum",
    "zigzag",
    "random_walk",
    "arc",
    "teleport",
    "random",
    "evading",
    "straight_evading",
    "wait_and_beeline",
)

_RATE_KEYS = frozenset({
    "descent",
    "frequency",
    "rotation_speed",
    "speed",
    "wander_speed",
    "evade_speed",
    "beeline_speed",
})

_EASES: dict[str, Callable[[float], float]] = {
    "linear": EasingFunctions.linear,
    "quad_in_out": EasingFunctions.ease_in_out_quad,
}


@dataclass
class PatternState:
    """Mutable kinematic state for one enemy."""

    name: str
    x: float
    y: float
    origin_x: float
    origin_y: float
    elapsed: float
    params: dict
    rng: random.Random
    extra: dict = field(default_factory=dict)


def create(
    name: str,
    x: float,
    y: float,
    *,
    seed: int | None = None,
    **params: object,
) -> PatternState:
    """Build a pattern at a spawn point.

    Raises:
        KeyError: `name` is not one of `NAMES`.
    """
    if name not in _STEPPERS:
        known = ", ".join(NAMES)
        raise KeyError(f"unknown shmup pattern {name!r}. known: {known}")
    return PatternState(
        name=name,
        x=float(x),
        y=float(y),
        origin_x=float(x),
        origin_y=float(y),
        elapsed=0.0,
        params=dict(params),
        rng=random.Random(seed),
        extra={},
    )


def step(
    state: PatternState,
    dt: float,
    player: tuple[float, float] | None = None,
) -> None:
    """Advance `state` by `dt` seconds.

    `player` is the ship position in the same space. Patterns that track the
    ship wander, or keep waiting, when it is missing.
    """
    state.elapsed += dt
    _STEPPERS[state.name](state, dt, player)


def scaled_params(params: Mapping[str, object], scale: float) -> dict[str, object]:
    """Multiply rate-like numbers by `scale`. Distances and names stay put."""
    scaled: dict[str, object] = {}
    for key, value in params.items():
        if key in _RATE_KEYS and isinstance(value, (int, float)):
            scaled[key] = float(value) * scale
        else:
            scaled[key] = value
    return scaled


def _num(state: PatternState, key: str, default: float) -> float:
    value = state.params.get(key, default)
    if isinstance(value, (int, float)):
        return float(value)
    raise TypeError(f"{state.name} param {key!r} must be a number")


def _wander(state: PatternState, dt: float, speed: float) -> None:
    angle = state.rng.random() * math.tau
    state.x += math.cos(angle) * speed * dt
    state.y += math.sin(angle) * speed * dt


def _apply_descent(state: PatternState) -> None:
    state.y = state.origin_y - _num(state, "descent", 0.0) * state.elapsed


def _straight(state: PatternState, dt: float, player: tuple[float, float] | None) -> None:
    del dt, player
    _apply_descent(state)


def _linear(state: PatternState, dt: float, player: tuple[float, float] | None) -> None:
    del player
    duration = max(_num(state, "duration", 1.0), 1e-6)
    peak = _num(state, "peak_x", 0.4)
    direction = int(state.extra.get("direction", 1))
    leg = float(state.extra.get("leg", 0.0)) + dt
    while leg >= duration:
        leg -= duration
        direction *= -1
    t = leg / duration
    sample = t if direction == 1 else 1.0 - t
    state.x = state.origin_x + EasingFunctions.ease_in_out_quad(sample) * peak
    _apply_descent(state)
    state.extra["direction"] = direction
    state.extra["leg"] = leg


def _sinusoidal(state: PatternState, dt: float, player: tuple[float, float] | None) -> None:
    del dt, player
    amplitude = _num(state, "amplitude", 0.25)
    frequency = _num(state, "frequency", 0.8)
    ease_name = str(state.params.get("ease", "quad_in_out"))
    try:
        ease = _EASES[ease_name]
    except KeyError as exc:
        known = ", ".join(_EASES)
        raise KeyError(f"unknown ease {ease_name!r}. known: {known}") from exc
    cycle = (state.elapsed * frequency) % 1.0
    state.x = state.origin_x + math.sin(ease(cycle) * math.tau) * amplitude
    _apply_descent(state)


def _circular(state: PatternState, dt: float, player: tuple[float, float] | None) -> None:
    del dt, player
    radius = _num(state, "radius", 0.18)
    frequency = _num(state, "frequency", 0.5)
    angle = state.elapsed * frequency * math.tau
    center_y = state.origin_y - _num(state, "descent", 0.0) * state.elapsed
    state.x = state.origin_x + radius * math.cos(angle)
    state.y = center_y + radius * math.sin(angle)


def _figure_eight(state: PatternState, dt: float, player: tuple[float, float] | None) -> None:
    del dt, player
    amplitude = _num(state, "amplitude", 0.22)
    frequency = _num(state, "frequency", 0.6)
    t = state.elapsed * frequency * math.tau
    state.x = state.origin_x + amplitude * math.sin(t)
    state.y = (
        state.origin_y
        + amplitude * math.sin(2.0 * t)
        - _num(state, "descent", 0.0) * state.elapsed
    )


def _spiral(state: PatternState, dt: float, player: tuple[float, float] | None) -> None:
    del dt, player
    radius = _num(state, "initial_radius", 0.05) + _num(state, "spiral_rate", 0.05) * state.elapsed
    angle = state.elapsed * _num(state, "rotation_speed", 2.0)
    state.x = state.origin_x + radius * math.cos(angle)
    state.y = (
        state.origin_y
        + radius * math.sin(angle)
        - _num(state, "descent", 0.0) * state.elapsed
    )


def _pendulum(state: PatternState, dt: float, player: tuple[float, float] | None) -> None:
    del dt, player
    amplitude = _num(state, "amplitude", 0.3) * math.exp(-_num(state, "damping", 0.0) * state.elapsed)
    t = state.elapsed * _num(state, "frequency", 0.5) * math.tau
    state.x = state.origin_x + amplitude * math.sin(t)
    _apply_descent(state)


def _zigzag(state: PatternState, dt: float, player: tuple[float, float] | None) -> None:
    del dt, player
    amplitude = _num(state, "amplitude", 0.28)
    t = state.elapsed * _num(state, "frequency", 2.5) * math.tau
    state.x = state.origin_x + amplitude * math.sin(t)
    _apply_descent(state)


def _random_walk(state: PatternState, dt: float, player: tuple[float, float] | None) -> None:
    del player
    step_size = _num(state, "step_size", 0.4)
    speed = _num(state, "speed", 1.0)
    state.x += (state.rng.random() - 0.5) * step_size * dt * speed
    state.y += (state.rng.random() - 0.5) * step_size * dt * speed
    state.y -= _num(state, "descent", 0.0) * dt


def _arc(state: PatternState, dt: float, player: tuple[float, float] | None) -> None:
    del dt, player
    radius = _num(state, "radius", 0.3)
    swept = ((state.elapsed * _num(state, "speed", 1.0)) % 1.0) * math.radians(
        _num(state, "angle_range", 180.0)
    )
    state.x = state.origin_x + radius * math.cos(swept)
    state.y = state.origin_y + radius * math.sin(swept) - _num(state, "descent", 0.0) * state.elapsed


def _teleport(state: PatternState, dt: float, player: tuple[float, float] | None) -> None:
    del player
    interval = max(_num(state, "teleport_interval", 2.0), 1e-6)
    timer = float(state.extra.get("timer", 0.0)) + dt
    if timer < interval:
        state.y -= _num(state, "descent", 0.0) * dt
        state.extra["timer"] = timer
        return
    bounds = state.params.get("area_bounds", ((-1.0, 1.0), (-1.0, 1.0)))
    if not isinstance(bounds, (list, tuple)) or len(bounds) != 2:
        raise TypeError(f"{state.name} param 'area_bounds' must be ((xmin, xmax), (ymin, ymax))")
    x_bounds, y_bounds = bounds
    state.x = state.rng.uniform(float(x_bounds[0]), float(x_bounds[1]))
    state.y = state.rng.uniform(float(y_bounds[0]), float(y_bounds[1]))
    state.extra["timer"] = 0.0


def _random(state: PatternState, dt: float, player: tuple[float, float] | None) -> None:
    del player
    interval = max(_num(state, "change_interval", 1.0), 1e-6)
    if "heading" not in state.extra:
        _pick_heading(state)
        state.extra["next"] = interval
    elif state.elapsed >= float(state.extra["next"]):
        _pick_heading(state)
        state.extra["next"] = float(state.extra["next"]) + interval
    speed = float(state.extra["move_speed"])
    state.x += math.cos(float(state.extra["heading"])) * speed * dt
    state.y += math.sin(float(state.extra["heading"])) * speed * dt
    state.y -= _num(state, "descent", 0.0) * dt


def _pick_heading(state: PatternState) -> None:
    state.extra["heading"] = state.rng.random() * math.tau
    lo = _num(state, "min_speed", 0.15)
    hi = _num(state, "max_speed", 0.45)
    state.extra["move_speed"] = state.rng.uniform(lo, hi)


def _evading(state: PatternState, dt: float, player: tuple[float, float] | None) -> None:
    evade_distance = _num(state, "evade_distance", 0.45)
    evade_speed = _num(state, "evade_speed", 0.9)
    wander_speed = _num(state, "wander_speed", 0.25)
    if player is None:
        _wander(state, dt, wander_speed)
        return
    dx = player[0] - state.x
    dy = player[1] - state.y
    dist = math.hypot(dx, dy)
    if dist < evade_distance:
        if dist == 0.0:
            dx, dy, dist = 1.0, 0.0, 1.0
        state.x -= (dx / dist) * evade_speed * dt
        state.y -= (dy / dist) * evade_speed * dt
        return
    _wander(state, dt, wander_speed)


def _straight_evading(state: PatternState, dt: float, player: tuple[float, float] | None) -> None:
    evade_distance = _num(state, "evade_distance", 0.45)
    evade_speed = _num(state, "evade_speed", 0.9)
    wander_speed = _num(state, "wander_speed", 0.2)
    evade_duration = _num(state, "evade_duration", 0.6)
    max_evade = _num(state, "max_evade_distance", 0.5)
    extra = state.extra
    if extra.get("evading"):
        extra["evade_timer"] = float(extra.get("evade_timer", 0.0)) + dt
        moved = math.hypot(state.x - float(extra["start_x"]), state.y - float(extra["start_y"]))
        if extra["evade_timer"] >= evade_duration or moved >= max_evade:
            extra["evading"] = False
            extra["evade_timer"] = 0.0
        else:
            state.x += float(extra["dir_x"]) * evade_speed * dt
            state.y += float(extra["dir_y"]) * evade_speed * dt
            return
    if player is None:
        _wander(state, dt, wander_speed)
        return
    dx = player[0] - state.x
    dy = player[1] - state.y
    dist = math.hypot(dx, dy)
    if dist == 0.0:
        dx, dy, dist = 1.0, 0.0, 1.0
    if dist < evade_distance:
        extra["evading"] = True
        extra["evade_timer"] = 0.0
        extra["start_x"] = state.x
        extra["start_y"] = state.y
        extra["dir_x"] = -dx / dist
        extra["dir_y"] = -dy / dist
        state.x += float(extra["dir_x"]) * evade_speed * dt
        state.y += float(extra["dir_y"]) * evade_speed * dt
        return
    _wander(state, dt, wander_speed)


def _wait_and_beeline(state: PatternState, dt: float, player: tuple[float, float] | None) -> None:
    wait_time = _num(state, "wait_time", 1.0)
    speed = _num(state, "beeline_speed", 0.6)
    follow = bool(state.params.get("follow_through", False))
    max_dist = state.params.get("max_beeline_distance")
    extra = state.extra
    if extra.get("waiting", True):
        extra["waiting"] = True
        extra["wait_timer"] = float(extra.get("wait_timer", 0.0)) + dt
        if extra["wait_timer"] < wait_time or player is None:
            return
        extra["waiting"] = False
        extra["beelining"] = True
        dx = player[0] - state.x
        dy = player[1] - state.y
        dist = math.hypot(dx, dy)
        if dist == 0.0:
            dx, dy, dist = 1.0, 0.0, 1.0
        extra["dir_x"] = dx / dist
        extra["dir_y"] = dy / dist
    if not extra.get("beelining"):
        return
    if follow:
        state.x += float(extra["dir_x"]) * speed * dt
        state.y += float(extra["dir_y"]) * speed * dt
        return
    if player is None:
        return
    dx = player[0] - state.x
    dy = player[1] - state.y
    dist = math.hypot(dx, dy)
    if dist == 0.0 or (max_dist is not None and dist <= float(max_dist)):
        extra["beelining"] = False
        return
    state.x += (dx / dist) * speed * dt
    state.y += (dy / dist) * speed * dt


_STEPPERS: dict[str, Callable[[PatternState, float, tuple[float, float] | None], None]] = {
    "straight": _straight,
    "linear": _linear,
    "sinusoidal": _sinusoidal,
    "circular": _circular,
    "figure_eight": _figure_eight,
    "spiral": _spiral,
    "pendulum": _pendulum,
    "zigzag": _zigzag,
    "random_walk": _random_walk,
    "arc": _arc,
    "teleport": _teleport,
    "random": _random,
    "evading": _evading,
    "straight_evading": _straight_evading,
    "wait_and_beeline": _wait_and_beeline,
}
