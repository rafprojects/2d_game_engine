"""
QuirkMovementSystem - fixed-tick retro movement + collision system (P2-B, rebuilt).

This is the reference implementation of NES-style platformer simulation for
the retro layer. It owns:

- A **fixed simulation tick** (default 60 Hz from RetroProfile.tick_hz). The
  system accumulates the engine's float frame dt and steps the simulation in
  whole ticks; positions and velocities are only ever touched inside a tick,
  and velocities are **units per tick** (pixels/tick for a VirtualPlayfield
  cartridge). The float dt is never converted into the fixed-point domain,
  which keeps the simulation deterministic - the same inputs always produce
  the same subpixel positions regardless of frame rate. (This matches how the
  original hardware worked and the project's deterministic keystone.)

- **Axis-separated integrate-and-resolve** per entity per tick: move X,
  resolve X against the level solids, then move Y, resolve Y (the classic
  axis-sequential order). Resolution snaps the body to the obstacle face and
  zeroes that axis's velocity. Standing on floors, hitting walls, and bonking
  ceilings all fall out of this naturally.

- **The quirk**: when "subpixel_wall_clip" is enabled (via the profile or
  enable_quirk), axis resolution uses *midline ejection* instead of
  motion-based ejection - see collision.resolve_axis for the rule and the
  worked example. Clips are recorded in ``clip_events`` so cartridges can
  surface the emergent moment to the player.

- **Contact flags** on SubpixelMovementComponent (on_ground / hit_ceiling /
  hit_wall), updated every tick. Cartridge controllers should read these
  instead of doing their own float geometry checks. Note: on_ground means
  "pushed up out of a solid while moving down this tick" - keep applying
  gravity every tick (as real games did) so the flag stays fresh.

Opt-in (P2-C):
    from engine.retro import (
        RetroProfile, RetroObstacle, register_retro_systems,
        SubpixelTransformComponent, SubpixelMovementComponent,
        SubpixelColliderComponent,
    )
    profile = RetroProfile("nes", frac_bits=8, tick_hz=60,
                           enable_quirks=["subpixel_wall_clip"])
    retro_sys = register_retro_systems(world, profile=profile, obstacles=LEVEL)
    # add Subpixel* components to gameplay entities; retro_sys is the handle
    # for enable_quirk/disable_quirk/add_tick_callback.

Cartridge game-feel code (acceleration, gravity, jumping) belongs in a
cartridge-side controller registered with ``add_tick_callback`` so it runs
once per simulation tick, not per render frame.

Entities with SubpixelTransform + SubpixelMovement but no SubpixelCollider
integrate velocity without collision. Entities whose components use a
different frac_bits than the profile are skipped (warned once) so that all
raw-integer comparisons stay exact at a single scale.

The system never touches float Transforms, the default MovementSystem, or the
default CollisionSystem. Modern code paths remain completely unaffected.

Pure Python, no external dependencies beyond the engine's own retro
primitives and core World.
"""

from __future__ import annotations

from typing import Any, Callable, Sequence

from engine.core.system import System

from ..components import (
    SubpixelColliderComponent,
    SubpixelMovementComponent,
    SubpixelTransformComponent,
)
from ..fixed_point import FixedPoint, FixedPointVec2
from ..profile import RetroProfile
from .collision import (
    FPSpan,
    QUIRK_SUBPIXEL_WALL_CLIP,
    QuirkRegistry,
    RetroObstacle,
    quantize_obstacles,
    resolve_axis,
)


class QuirkMovementSystem(System):
    """Fixed-tick retro movement/collision with opt-in quirk rules.

    Args:
        world: the ECS World.
        profile: RetroProfile (frac_bits = simulation precision, tick_hz =
            simulation rate, enable_quirks auto-enabled). Defaults to the
            "modern" profile (frac_bits=16, 60 Hz, no quirks).
        obstacles: static level geometry as RetroObstacle boxes (quantized
            once at the profile's frac_bits). Can be replaced later with
            set_obstacles().
        quirk_registry: optionally share/inject a registry; by default the
            system owns one.
        max_ticks_per_frame: spiral-of-death guard - at most this many
            simulation ticks run per update() call; excess backlog is dropped.
    """

    def __init__(
        self,
        world: Any,
        profile: RetroProfile | None = None,
        obstacles: Sequence[RetroObstacle] | None = None,
        quirk_registry: QuirkRegistry | None = None,
        max_ticks_per_frame: int = 5,
    ) -> None:
        super().__init__(world)
        self.profile: RetroProfile = profile or RetroProfile(name="modern")
        self.quirk_registry: QuirkRegistry = quirk_registry or QuirkRegistry()
        for name in self.profile.enable_quirks:
            self.enable_quirk(name)

        self._frac_bits: int = self.profile.frac_bits
        self.obstacles: list[RetroObstacle] = []
        self._spans: list[FPSpan] = []
        if obstacles:
            self.set_obstacles(obstacles)

        self._tick_dt: float = 1.0 / float(self.profile.tick_hz)
        self._max_ticks_per_frame: int = max(1, int(max_ticks_per_frame))
        self._accum: float = 0.0
        self._tick_count: int = 0
        self._tick_callbacks: list[Callable[[int], None]] = []
        self._warned_mismatch: set[Any] = set()

        # Emergent-clip log: cleared at the start of every update() call, so
        # systems running after this one in the same frame see this frame's
        # events. (step_ticks does not clear - tests read accumulated events.)
        self.clip_events: list[dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Configuration surface
    # ------------------------------------------------------------------
    def set_obstacles(self, obstacles: Sequence[RetroObstacle]) -> None:
        """Replace the static level geometry (quantized once, not per tick)."""
        self.obstacles = list(obstacles)
        self._spans = quantize_obstacles(self.obstacles, self._frac_bits)

    def add_tick_callback(self, fn: Callable[[int], None]) -> None:
        """Register a per-tick callback fn(tick_index), run before integration.

        This is where cartridge controllers apply game feel (input ->
        acceleration, gravity, jumps) so their math runs exactly once per
        simulation tick.
        """
        self._tick_callbacks.append(fn)

    def enable_quirk(self, name: str) -> None:
        """Enable a named quirk for this system instance."""
        self.quirk_registry.enable(name)

    def disable_quirk(self, name: str) -> None:
        """Disable a named quirk for this system instance."""
        self.quirk_registry.disable(name)

    @property
    def tick_count(self) -> int:
        """Total simulation ticks run since construction."""
        return self._tick_count

    @property
    def tick_dt(self) -> float:
        """Duration of one simulation tick in seconds (1 / tick_hz)."""
        return self._tick_dt

    # ------------------------------------------------------------------
    # Frame entry point (fixed-tick accumulator)
    # ------------------------------------------------------------------
    def update(self, dt: float) -> None:
        """Accumulate frame time and run whole simulation ticks."""
        self.clip_events.clear()
        self._accum += dt
        ticks_run = 0
        while self._accum >= self._tick_dt and ticks_run < self._max_ticks_per_frame:
            self._run_tick()
            self._accum -= self._tick_dt
            ticks_run += 1
        if self._accum > self._tick_dt:
            # Too far behind: drop the backlog rather than spiral.
            self._accum = self._tick_dt

    def step_ticks(self, n: int) -> None:
        """Run n simulation ticks immediately (deterministic test/tool hook)."""
        for _ in range(n):
            self._run_tick()

    # ------------------------------------------------------------------
    # One simulation tick
    # ------------------------------------------------------------------
    def _run_tick(self) -> None:
        tick = self._tick_count
        for fn in list(self._tick_callbacks):
            fn(tick)

        midline = self.quirk_registry.is_active(QUIRK_SUBPIXEL_WALL_CLIP)
        fb = self._frac_bits

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

            if st.frac_bits != fb or sm.frac_bits != fb:
                if entity.id not in self._warned_mismatch:
                    print(
                        f"[retro] skipping entity {entity.id}: component frac_bits "
                        f"({st.frac_bits}/{sm.frac_bits}) != profile frac_bits ({fb})"
                    )
                    self._warned_mismatch.add(entity.id)
                continue

            vel: FixedPointVec2 = sm.current_velocity
            pos: FixedPointVec2 = st.position
            col: SubpixelColliderComponent | None = self.world.get_component(
                entity.id, SubpixelColliderComponent
            )

            if col is None:
                # No collider: pure integration (velocity is per tick).
                st.position = pos + vel
                sm.is_moving = vel.x.raw != 0 or vel.y.raw != 0
                continue

            # Axis-separated integrate + resolve: X first, then Y (with the
            # already-resolved X), the classic axis-sequential order.
            res_x = resolve_axis(
                pos.x, pos.y, col.half_w, col.half_h, vel.x, "x", self._spans, midline
            )
            res_y = resolve_axis(
                res_x.value, pos.y, col.half_w, col.half_h, vel.y, "y", self._spans, midline
            )

            st.position = FixedPointVec2(res_x.value, res_y.value, frac_bits=fb)

            zero = FixedPoint(0, frac_bits=fb)
            new_vx = zero if res_x.collided else vel.x
            new_vy = zero if res_y.collided else vel.y
            sm.current_velocity = FixedPointVec2(new_vx, new_vy, frac_bits=fb)
            sm.is_moving = new_vx.raw != 0 or new_vy.raw != 0

            # Contact flags (resolver-owned truth for cartridge controllers).
            sm.hit_wall = res_x.collided
            sm.on_ground = res_y.collided and res_y.eject_dir > 0 and vel.y.raw < 0
            sm.hit_ceiling = res_y.collided and res_y.eject_dir < 0 and vel.y.raw > 0

            if res_x.clipped or res_y.clipped:
                self.clip_events.append(
                    {
                        "entity_id": entity.id,
                        "tick": tick,
                        "axis": "x" if res_x.clipped else "y",
                        "obstacle": res_x.obstacle if res_x.clipped else res_y.obstacle,
                        "pos": st.position.get_xy_float(),
                        "quirk": QUIRK_SUBPIXEL_WALL_CLIP,
                    }
                )

        self._tick_count += 1
