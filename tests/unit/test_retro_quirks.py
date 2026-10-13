"""
Tests for the rebuilt retro quirk layer (P2-B re-work + P2-C opt-in).

The simulation under test is the fixed-tick, axis-separated
QuirkMovementSystem with the "subpixel_wall_clip" quirk implemented as
*midline ejection* (see engine/retro/systems/collision.py for the rule and
the worked example these numbers come from).

Canonical geometry (8.8 fixed point, virtual pixels):
- player collider 12x16 (half 6x8), running at 4.0 px/tick
- clip wall centered at x=203, 6 px thick -> raw min/mid/max 51200/51968/52736
- alignment A: x0 = 153.5 (raw 39296)  -> CLIPS to x=212.0 on the 11th tick
- alignment B: x0 = 150.5 (raw 38528)  -> BLOCKED at x=194.0
- one-subpixel flip: raw 39168 blocks (edge lands exactly on the midline,
  strict compare), raw 39169 clips
- quirk OFF: every alignment is blocked at x=194.0 (motion-based ejection)

All assertions are exact (raw-integer arithmetic), mirroring the P2-B AC:
the emergent behavior occurs ONLY with the retro system + the rule enabled.
"""

from __future__ import annotations

from engine.core.system import World
from engine.retro import (
    FixedPoint,
    FixedPointVec2,
    QuirkMovementSystem,
    QuirkRegistry,
    RetroObstacle,
    RetroProfile,
    SubpixelColliderComponent,
    SubpixelMovementComponent,
    SubpixelTransformComponent,
    register_retro_systems,
)

FB = 8
CLIP_WALL = RetroObstacle(203, 68, 6, 104, name="clip_wall")
GROUND = RetroObstacle(128, 8, 256, 16, name="ground")

ALIGN_A_RAW = 39296  # 153.5  -> clips
ALIGN_B_RAW = 38528  # 150.5  -> blocked
MIDLINE_EXACT_RAW = 39168  # 153.0 -> edge lands ON the midline -> blocked
MIDLINE_PLUS_ONE_RAW = 39169  # one subpixel later -> clips

BLOCKED_X = 194.0  # wall min (200) - half width (6)
CLIPPED_X = 212.0  # wall max (206) + half width (6)


def _make_world(
    start_x_raw: int,
    vx: float = 4.0,
    *,
    quirk_on: bool,
    obstacles: list[RetroObstacle] | None = None,
    y: float = 24.0,
    collider: tuple[float, float] = (12, 16),
) -> tuple[World, QuirkMovementSystem, SubpixelTransformComponent, SubpixelMovementComponent]:
    """Standard rig: one retro player + level obstacles + the quirk system."""
    world = World()
    e = world.create_entity()

    st = SubpixelTransformComponent(
        x=FixedPoint.from_raw(start_x_raw, frac_bits=FB), y=y, frac_bits=FB
    )
    sm = SubpixelMovementComponent(frac_bits=FB)
    sm.current_velocity = FixedPointVec2(vx, 0.0, frac_bits=FB)
    world.add_component(e.id, st)
    world.add_component(e.id, sm)
    world.add_component(e.id, SubpixelColliderComponent(*collider, frac_bits=FB))

    profile = RetroProfile(
        "nes-test",
        frac_bits=FB,
        tick_hz=60,
        enable_quirks=["subpixel_wall_clip"] if quirk_on else [],
    )
    sys = QuirkMovementSystem(
        world, profile=profile, obstacles=obstacles if obstacles is not None else [CLIP_WALL]
    )
    world.add_system(sys)
    return world, sys, st, sm


# =============================================================================
# Surface + registry
# =============================================================================

def test_public_surface_imports():
    """The locked P2 public surface plus the rebuilt additions import cleanly."""
    from engine.retro import (  # noqa: F401
        FixedPoint,
        FixedPointVec2,
        QuirkMovementSystem,
        QuirkRegistry,
        RetroObstacle,
        RetroProfile,
        SubpixelColliderComponent,
        SubpixelMovementComponent,
        SubpixelTransformComponent,
        VirtualPlayfield,
        register_retro_systems,
    )
    from engine.retro.systems.collision import (  # noqa: F401
        AxisResolution,
        quantize_obstacles,
        resolve_axis,
    )


def test_quirk_registry_enable_disable():
    reg = QuirkRegistry()
    assert not reg.is_active("subpixel_wall_clip")
    reg.enable("subpixel_wall_clip")
    assert reg.is_active("subpixel_wall_clip")
    reg.enable("subpixel_wall_clip")  # idempotent
    assert reg.active == {"subpixel_wall_clip"}
    reg.disable("subpixel_wall_clip")
    assert not reg.is_active("subpixel_wall_clip")
    reg.disable("subpixel_wall_clip")  # idempotent


def test_retro_profile_construction_and_defaults():
    p = RetroProfile("nes", frac_bits=8, tick_hz=60, enable_quirks=["subpixel_wall_clip"])
    assert p.name == "nes"
    assert p.frac_bits == 8
    assert p.tick_hz == 60
    assert "subpixel_wall_clip" in p.enable_quirks

    p2 = RetroProfile()  # modern defaults
    assert p2.name == "modern"
    assert p2.frac_bits == 16
    assert p2.tick_hz == 60
    assert p2.enable_quirks == []


# =============================================================================
# Fixed tick + per-tick velocity semantics
# =============================================================================

def test_fixed_tick_accumulator():
    """update() converts float frame dt into whole simulation ticks."""
    world, sys, _, _ = _make_world(ALIGN_B_RAW, vx=0.0, quirk_on=False, obstacles=[])

    sys.update(1.0 / 60.0)
    assert sys.tick_count == 1

    # Two half-frames make exactly one tick (no drift, nothing lost).
    world2, sys2, _, _ = _make_world(ALIGN_B_RAW, vx=0.0, quirk_on=False, obstacles=[])
    sys2.update(0.5 / 60.0)
    assert sys2.tick_count == 0
    sys2.update(0.5 / 60.0)
    assert sys2.tick_count == 1

    # Spiral-of-death guard: a huge frame runs at most max_ticks_per_frame.
    world3, sys3, _, _ = _make_world(ALIGN_B_RAW, vx=0.0, quirk_on=False, obstacles=[])
    sys3.update(10.0)
    assert sys3.tick_count == sys3._max_ticks_per_frame


def test_velocity_is_per_tick_and_exact():
    """vx=1.0 advances exactly 1.0 px per tick - no float dt in the sim."""
    _, sys, st, _ = _make_world(ALIGN_B_RAW, vx=1.0, quirk_on=False, obstacles=[])
    start_raw = st.position.x.raw
    sys.step_ticks(3)
    assert st.position.x.raw == start_raw + 3 * (1 << FB)


def test_entities_without_collider_integrate_only():
    """No SubpixelColliderComponent -> velocity integrates, no resolution."""
    world = World()
    e = world.create_entity()
    st = SubpixelTransformComponent(x=199.0, y=24.0, frac_bits=FB)
    sm = SubpixelMovementComponent(frac_bits=FB)
    sm.current_velocity = FixedPointVec2(4.0, 0.0, frac_bits=FB)
    world.add_component(e.id, st)
    world.add_component(e.id, sm)

    sys = QuirkMovementSystem(
        world, profile=RetroProfile("t", frac_bits=FB), obstacles=[CLIP_WALL]
    )
    sys.step_ticks(4)
    # Sailed straight through the wall region: never resolved.
    assert st.get_position()[0] == 215.0


# =============================================================================
# Platformer fundamentals: floors and ceilings work (this is what the old
# resolver could not do at all)
# =============================================================================

def test_lands_on_ground_and_stays(capsys):
    """Falling body lands exactly on the ground top and rests stably -
    with the quirk ON: floors are categorically un-clippable because no
    vertical speed reaches half the ground's 16px thickness."""
    world, sys, st, sm = _make_world(
        FixedPoint(40.0, frac_bits=FB).raw, vx=0.0, quirk_on=True,
        obstacles=[GROUND], y=60.0,
    )

    def gravity(_tick: int) -> None:
        vy = max(sm.current_velocity.get_xy_float()[1] - 0.25, -4.0)
        sm.current_velocity = FixedPointVec2(0.0, vy, frac_bits=FB)

    sys.add_tick_callback(gravity)
    sys.step_ticks(60)

    x, y_final = st.get_position()
    assert y_final == 24.0  # bottom edge (24 - 8) sits exactly on ground top 16
    assert sm.on_ground is True
    assert sm.current_velocity.get_xy_float()[1] == 0.0  # zeroed by the resolver
    assert sys.clip_events == []  # the quirk never fired on the floor


def test_ceiling_bonk_sets_flag_no_clip():
    """Rising into a 10px platform ejects the body down and flags hit_ceiling
    (platform half-thickness 5 > max vertical speed 4.5 -> never clippable)."""
    platform = RetroObstacle(88, 40, 48, 10, name="platform_1")
    world, sys, st, sm = _make_world(
        FixedPoint(88.0, frac_bits=FB).raw, vx=0.0, quirk_on=True,
        obstacles=[platform], y=20.0,
    )
    sm.current_velocity = FixedPointVec2(0.0, 4.0, frac_bits=FB)

    bonked_y = None
    for _ in range(6):
        sys.step_ticks(1)
        if sm.hit_ceiling:
            bonked_y = st.get_position()[1]
            break

    assert bonked_y == 27.0  # platform bottom (35) - half height (8)
    assert sm.current_velocity.get_xy_float()[1] == 0.0
    assert sys.clip_events == []


# =============================================================================
# The emergent clip (P2-B acceptance criteria)
# =============================================================================

def test_clip_alignment_A_quirk_on():
    """AC: the documented clip occurs with retro + rule at alignment A."""
    _, sys, st, sm = _make_world(ALIGN_A_RAW, quirk_on=True)
    sys.step_ticks(14)

    assert st.get_position()[0] == CLIPPED_X  # through the wall
    assert len(sys.clip_events) == 1
    ev = sys.clip_events[0]
    assert ev["obstacle"] == "clip_wall"
    assert ev["quirk"] == "subpixel_wall_clip"
    assert ev["axis"] == "x"


def test_block_alignment_B_quirk_on():
    """Same speed, same wall, 3px different start: blocked. The quirk is
    alignment-dependent, not a dice roll."""
    _, sys, st, _ = _make_world(ALIGN_B_RAW, quirk_on=True)
    sys.step_ticks(14)

    assert st.get_position()[0] == BLOCKED_X
    assert sys.clip_events == []


def test_one_subpixel_flips_the_outcome():
    """The determinism showpiece: landing exactly ON the midline blocks
    (strict compare); one subpixel later it clips."""
    _, sys_a, st_a, _ = _make_world(MIDLINE_EXACT_RAW, quirk_on=True)
    sys_a.step_ticks(14)
    assert st_a.get_position()[0] == BLOCKED_X

    _, sys_b, st_b, _ = _make_world(MIDLINE_PLUS_ONE_RAW, quirk_on=True)
    sys_b.step_ticks(14)
    assert st_b.get_position()[0] == CLIPPED_X
    assert len(sys_b.clip_events) == 1


def test_quirk_off_always_blocks():
    """Modern control: with motion-based ejection the SAME setups all block."""
    for start_raw in (ALIGN_A_RAW, ALIGN_B_RAW, MIDLINE_EXACT_RAW, MIDLINE_PLUS_ONE_RAW):
        _, sys, st, sm = _make_world(start_raw, quirk_on=False)
        sys.step_ticks(14)
        assert st.get_position()[0] == BLOCKED_X, f"start_raw={start_raw}"
        assert sys.clip_events == []
        assert sm.hit_wall is False  # already at rest, last tick had no contact

    # Live-toggle path (what the demo's T hotkey does): disable on the handle.
    _, sys, st, _ = _make_world(ALIGN_A_RAW, quirk_on=True)
    sys.disable_quirk("subpixel_wall_clip")
    sys.step_ticks(14)
    assert st.get_position()[0] == BLOCKED_X


def test_per_entity_collider_sizes():
    """Collision extents come from SubpixelColliderComponent, not hardcodes."""
    _, sys_a, st_a, _ = _make_world(ALIGN_A_RAW, quirk_on=False, collider=(12, 16))
    sys_a.step_ticks(14)
    assert st_a.get_position()[0] == 194.0  # 200 - 6

    _, sys_b, st_b, _ = _make_world(ALIGN_A_RAW, quirk_on=False, collider=(20, 16))
    sys_b.step_ticks(14)
    assert st_b.get_position()[0] == 190.0  # 200 - 10


# =============================================================================
# Opt-in / coexistence (P2-C)
# =============================================================================

def test_register_retro_systems_returns_system_handle():
    """The helper returns the live QuirkMovementSystem (toggle/tick handle)."""
    world = World()
    profile = RetroProfile("nes", frac_bits=FB, enable_quirks=["subpixel_wall_clip"])
    sys = register_retro_systems(world, profile=profile, obstacles=[CLIP_WALL, GROUND])

    assert isinstance(sys, QuirkMovementSystem)
    assert sys in world.systems
    assert sys.profile is profile
    assert sys.obstacles == [CLIP_WALL, GROUND]
    assert sys.quirk_registry.is_active("subpixel_wall_clip")


def test_frac_bits_mismatch_is_skipped_with_one_warning(capsys):
    """Entities at a different precision than the profile are left untouched
    (all raw compares must share one scale) and warned about exactly once."""
    world = World()
    e = world.create_entity()
    st = SubpixelTransformComponent(x=10.0, y=10.0, frac_bits=12)
    sm = SubpixelMovementComponent(frac_bits=12)
    sm.current_velocity = FixedPointVec2(1.0, 0.0, frac_bits=12)
    world.add_component(e.id, st)
    world.add_component(e.id, sm)

    sys = QuirkMovementSystem(world, profile=RetroProfile("t", frac_bits=FB))
    world.add_system(sys)
    sys.step_ticks(3)

    assert st.get_position() == (10.0, 10.0)  # untouched
    out = capsys.readouterr().out
    assert out.count("[retro] skipping") == 1  # warned once, not per tick


def test_ignores_non_retro_entities():
    """Entities with only float components are invisible to the retro system."""
    from engine.graphics.components.transform_component import TransformComponent

    world = World()
    e = world.create_entity()
    t = TransformComponent(x=1.0, y=2.0)
    world.add_component(e.id, t)

    sys = QuirkMovementSystem(world, profile=RetroProfile("t", frac_bits=FB))
    world.add_system(sys)
    sys.step_ticks(5)

    assert (t.x, t.y) == (1.0, 2.0)


def test_mixed_retro_and_normal_entities_independent_behavior():
    """P2-C AC: a retro entity (fixed ticks, quirk clip) and a normal float
    entity (default MovementSystem) coexist in one World without cross-talk."""
    from panda3d.core import Vec2
    from engine.core.components.movement_component import MovementComponent
    from engine.core.systems.movement_system import MovementSystem
    from engine.graphics.components.transform_component import TransformComponent

    world = World()

    # Retro entity at the clip alignment.
    e_retro = world.create_entity("retro")
    st = SubpixelTransformComponent(
        x=FixedPoint.from_raw(ALIGN_A_RAW, frac_bits=FB), y=24.0, frac_bits=FB
    )
    sm = SubpixelMovementComponent(frac_bits=FB)
    sm.current_velocity = FixedPointVec2(4.0, 0.0, frac_bits=FB)
    world.add_component(e_retro.id, st)
    world.add_component(e_retro.id, sm)
    world.add_component(e_retro.id, SubpixelColliderComponent(12, 16, frac_bits=FB))

    profile = RetroProfile("nes", frac_bits=FB, enable_quirks=["subpixel_wall_clip"])
    register_retro_systems(world, profile=profile, obstacles=[CLIP_WALL])

    # Normal float entity driven by the default MovementSystem.
    e_normal = world.create_entity("normal")
    t = TransformComponent(x=0.0, y=0.0)
    m = MovementComponent()
    m.current_velocity = Vec2(2.0, 0.0)
    world.add_component(e_normal.id, t)
    world.add_component(e_normal.id, m)
    world.add_system(MovementSystem(world))

    for _ in range(15):
        world.update(1.0 / 60.0)  # 1 retro tick per frame

    assert st.get_position()[0] == CLIPPED_X  # retro clipped through the wall
    assert t.x > 0.0  # float entity moved under float rules
    assert world.get_component(e_normal.id, SubpixelTransformComponent) is None
    assert world.get_component(e_retro.id, TransformComponent) is None
