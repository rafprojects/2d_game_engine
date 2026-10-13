"""Path-shape checks for the shmup pattern registry. No window."""

from __future__ import annotations

import math
from pathlib import Path

import pytest
import yaml

from engine.patterns.shmup import NAMES, create, scaled_params, step

ROOT = Path(__file__).resolve().parents[2]


def test_unknown_name_lists_known_patterns():
    with pytest.raises(KeyError) as exc:
        create("nope", 0.0, 0.0)
    message = str(exc.value)
    assert "nope" in message
    assert "sinusoidal" in message
    assert "wait_and_beeline" in message


def test_registry_has_fifteen_names():
    assert len(NAMES) == 15
    assert len(set(NAMES)) == 15


def test_straight_descends_and_holds_x():
    state = create("straight", 0.2, 1.0, descent=0.45)
    step(state, 1.0)
    assert state.x == pytest.approx(0.2)
    assert state.y == pytest.approx(1.0 - 0.45)


def test_linear_reaches_peak_then_returns():
    state = create("linear", 0.0, 1.0, peak_x=0.4, duration=1.0, descent=0.2)
    step(state, 1.0)
    assert state.x == pytest.approx(0.4)
    assert state.y == pytest.approx(0.8)
    step(state, 1.0)
    assert state.x == pytest.approx(0.0)
    assert state.y == pytest.approx(0.6)


def test_sinusoidal_stays_inside_amplitude_and_descends():
    state = create("sinusoidal", 1.5, 2.0, amplitude=0.25, frequency=0.8, descent=0.35)
    samples = []
    for _ in range(90):
        step(state, 1.0 / 30.0)
        samples.append(state.x)
    assert max(samples) - min(samples) > 0.05
    assert all(abs(x - 1.5) <= 0.25 + 1e-9 for x in samples)
    assert state.y < 2.0


def test_circular_orbits_a_descending_center():
    state = create("circular", 1.0, 1.0, radius=0.18, frequency=0.5, descent=0.25)
    step(state, 0.4)
    center_y = 1.0 - 0.25 * state.elapsed
    assert math.hypot(state.x - 1.0, state.y - center_y) == pytest.approx(0.18)


def test_figure_eight_stays_near_spawn_not_the_origin():
    state = create("figure_eight", 2.0, 3.0, amplitude=0.22, frequency=0.6, descent=0.0)
    for _ in range(120):
        step(state, 1.0 / 60.0)
        assert abs(state.x - 2.0) <= 0.22 + 1e-9
        assert abs(state.y - 3.0) <= 0.22 + 1e-9


def test_spiral_radius_grows_around_spawn():
    state = create(
        "spiral",
        0.5,
        -0.25,
        initial_radius=0.1,
        spiral_rate=0.2,
        rotation_speed=1.0,
        descent=0.0,
    )
    step(state, 1.0)
    assert math.hypot(state.x - 0.5, state.y - (-0.25)) == pytest.approx(0.3)


def test_pendulum_damping_shrinks_the_swing():
    open_swing = create("pendulum", 0.0, 0.0, amplitude=1.0, frequency=0.25, damping=0.0)
    damped = create("pendulum", 0.0, 0.0, amplitude=1.0, frequency=0.25, damping=2.0)
    step(open_swing, 1.0)
    step(damped, 1.0)
    assert open_swing.x == pytest.approx(1.0)
    assert abs(damped.x) < abs(open_swing.x)


def test_zigzag_oscillates_around_spawn():
    state = create("zigzag", -0.4, 0.8, amplitude=0.28, frequency=2.5, descent=0.4)
    samples = []
    for _ in range(40):
        step(state, 0.05)
        samples.append(state.x)
    assert max(samples) - min(samples) > 0.05
    assert all(abs(x - (-0.4)) <= 0.28 + 1e-9 for x in samples)
    assert state.y < 0.8


def test_random_walk_is_seeded():
    first = create("random_walk", 0.0, 0.0, step_size=1.0, speed=1.0, seed=7)
    second = create("random_walk", 0.0, 0.0, step_size=1.0, speed=1.0, seed=7)
    other = create("random_walk", 0.0, 0.0, step_size=1.0, speed=1.0, seed=8)
    for _ in range(10):
        step(first, 0.1)
        step(second, 0.1)
        step(other, 0.1)
    assert first.x == pytest.approx(second.x)
    assert first.y == pytest.approx(second.y)
    assert other.x != pytest.approx(first.x)


def test_arc_stays_on_its_radius():
    state = create("arc", 0.0, 0.0, radius=0.5, angle_range=180.0, speed=1.0, descent=0.0)
    step(state, 0.0)
    assert math.hypot(state.x, state.y) == pytest.approx(0.5)
    step(state, 0.5)
    assert math.hypot(state.x, state.y) == pytest.approx(0.5)


def test_teleport_holds_then_jumps_inside_bounds():
    bounds = ((0.0, 1.0), (2.0, 3.0))
    state = create("teleport", 5.0, 5.0, teleport_interval=1.0, area_bounds=bounds, seed=1)
    step(state, 0.5)
    assert state.x == pytest.approx(5.0)
    assert state.y == pytest.approx(5.0)
    step(state, 0.5)
    assert 0.0 <= state.x <= 1.0
    assert 2.0 <= state.y <= 3.0


def test_random_changes_heading_on_its_interval_and_stays_quiet(capsys):
    state = create("random", 0.0, 0.0, change_interval=1.0, seed=3)
    step(state, 0.1)
    first = state.extra["heading"]
    step(state, 1.0)
    assert state.extra["heading"] != first
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


def test_evading_moves_away_from_a_close_player():
    state = create(
        "evading",
        0.0,
        0.0,
        evade_distance=1.0,
        evade_speed=1.0,
        wander_speed=0.0,
        seed=1,
    )
    step(state, 1.0, player=(0.5, 0.0))
    assert state.x == pytest.approx(-1.0)
    assert state.y == pytest.approx(0.0)


def test_evading_wanders_in_place_when_the_player_is_missing():
    state = create(
        "evading",
        1.0,
        1.0,
        evade_distance=1.0,
        evade_speed=2.0,
        wander_speed=0.0,
        seed=1,
    )
    step(state, 0.5, player=None)
    assert state.x == pytest.approx(1.0)
    assert state.y == pytest.approx(1.0)


def test_straight_evading_keeps_its_locked_direction():
    state = create(
        "straight_evading",
        0.0,
        0.0,
        evade_distance=1.0,
        evade_speed=1.0,
        wander_speed=0.0,
        evade_duration=2.0,
        max_evade_distance=10.0,
        seed=1,
    )
    step(state, 0.5, player=(0.4, 0.0))
    assert state.extra["evading"] is True
    assert state.x == pytest.approx(-0.5)
    step(state, 0.5, player=(5.0, 5.0))
    assert state.extra["evading"] is True
    assert state.x == pytest.approx(-1.0)
    assert state.y == pytest.approx(0.0)


def test_wait_and_beeline_holds_then_locks_onto_the_player():
    state = create(
        "wait_and_beeline",
        0.0,
        0.0,
        wait_time=1.0,
        beeline_speed=1.0,
        follow_through=True,
        seed=1,
    )
    step(state, 0.5, player=(1.0, 0.0))
    assert state.x == pytest.approx(0.0)
    assert state.extra["waiting"] is True
    step(state, 0.5, player=(1.0, 0.0))
    assert state.x == pytest.approx(0.5)


def test_wait_and_beeline_keeps_waiting_without_a_player():
    state = create(
        "wait_and_beeline",
        0.0,
        0.0,
        wait_time=1.0,
        beeline_speed=1.0,
        seed=1,
    )
    step(state, 2.0, player=None)
    assert state.x == pytest.approx(0.0)
    assert state.y == pytest.approx(0.0)
    assert state.extra["waiting"] is True


def test_scaled_params_touch_rates_only():
    scaled = scaled_params(
        {"descent": 0.45, "amplitude": 0.25, "frequency": 0.8, "name": "sinusoidal"},
        2.0,
    )
    assert scaled["descent"] == pytest.approx(0.9)
    assert scaled["frequency"] == pytest.approx(1.6)
    assert scaled["amplitude"] == pytest.approx(0.25)
    assert scaled["name"] == "sinusoidal"


def test_tgl_yaml_patterns_are_registered():
    path = ROOT / "examples" / "cartridges" / "tgl_demo" / "config" / "game_settings.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    names = [entry["name"] for entry in data["enemies"]["patterns"]]
    assert names == ["straight", "sinusoidal", "circular", "figure_eight", "zigzag"]
    assert set(names) <= set(NAMES)
