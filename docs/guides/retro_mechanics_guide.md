# Building Authentic Retro Mechanics with Cartridges

*The P2-E guide for the retro emergent gameplay layer. It explains why the
layer exists, how the classics actually produced their famous glitches, how
the engine's `engine/retro/` reference implementation recreates one of those
mechanisms honestly, how the
[retro_sidescroller_demo](../../examples/cartridges/retro_sidescroller_demo/README.md)
reference cartridge was designed around it, and how to opt in, then bend
the rules, from your own cartridge.*

**Audience:** cartridge authors. You should be able to load a cartridge
(`python main.py --cartridge <path>`) and have skimmed the
[cartridge loader guide](cartridge_loader_guide.md).

---

## 1. The thesis: constraints make gameplay

The cartridge vision's creative claim is that cartridges can *deliberately opt
into constrained simulation rules* (fixed-point math, fixed ticks,
hardware-style collision) and get something modern engines can't give them:
**emergent mechanics**. Not scripted behaviors, but consequences that fall out
of simple rules interacting, the way the best-loved glitches of the 8-bit era
did.

The key word is *emergent*. A wall you pass through because the code says
`if lucky: pass_through()` is a parlor trick. A wall you pass through because
the era-authentic ejection rule, fed an era-authentic fixed-point position,
*computes* an exit on the far side: that is a mechanic. Players can learn it,
practice it, route speedruns around it, and explain it to each other. That
difference is the entire reason `engine/retro/` exists.

## 2. How the classics actually worked

None of the famous retro glitches were random. Each one is a small, honest
rule colliding with a constraint of the hardware. This section is the field
guide; sources are collected [at the end](#sources--further-reading).

### 2.1 No FPU: fixed point and the subpixel

The NES CPU (a 6502 derivative at ~1.8 MHz) had no floating-point unit, so
fractional positions were stored as **fixed-point integers**: some bits for
whole pixels, some for the fraction. In *Super Mario Bros.*, 16 subpixels make
one pixel. Mario's position carries 4 fractional bits, and the renderer
simply shifts them away ([TASVideos SMB notes](https://tasvideos.org/GameResources/NES/SuperMarioBros),
[nesdev: sub pixel movement](https://forums.nesdev.org/viewtopic.php?t=12125)).
Other games and platforms used 8 fractional bits, 256 subpixels per pixel,
the "8.8" format this engine's demo uses. Speeds were stored the same way, in
*subpixels per frame*: acceleration of a fraction of a pixel per frame is what
gives NES movement its distinctive ramp-up feel
([Jitterbugs: subpixel movement](https://marioslab.io/posts/jitterbugs/)).

Two properties matter for everything below:

1. **The fraction is invisible.** Two Marios can stand on what looks like the
   same pixel and behave differently, because their subpixel values differ.
2. **The math is exact.** Integer adds always produce the same result. The
   same inputs replay to the same outcome, every time, on every machine.

That second property is why speedrunners talk about **subpixel optimization**:
in tool-assisted runs, entire strategies hinge on entering a room with the
right subpixel value ([ALttP speedrun wiki: Subpixels](https://alttp-wiki.net/index.php/Subpixels)).
The fraction you cannot see is real, persistent state.

### 2.2 Collision on a budget: probe points and ejection

A full overlap test of every sprite against every tile was unaffordable, so
8-bit collision worked with a handful of **probe points** checked against the
tile grid, usually one axis at a time. When a probe ended up inside a solid
tile, the engine *ejected* the body, snapping it to a tile face. The
interesting design question was always: **which face?**

A "modern" answer is motion-based: push the body back out the face it moved
into. The era answer was usually cheaper: decide from **where the probe is
now**, which side, or which half, of the tile it landed in. Position-based
ejection is one comparison. It is also, as the next section shows, the door
the famous clips walked through.

### 2.3 The Super Mario Bros. wall clip

SMB's wall ejection decides from position, not travel direction: while
standing, the game checks where Mario's body sits relative to the wall's edge
and pushes him toward "the side he's mostly on"; while jumping, held input
steers the decision ([TASVideos](https://tasvideos.org/GameResources/NES/SuperMarioBros)).
Two more facts sit next to that rule. Solid-object collision is only evaluated
every other frame, and a fast Mario can sink about 3 pixels into a block before the
check runs. The rule then inverts: penetrate *deep enough* and the ejection
that was supposed to push you out starts "helpfully" pulling you through
([SDA knowledge base](https://kb.speeddemosarchive.com/Super_Mario_Bros.),
[subpixels and wall clipping explained](http://hcfyk.blogspot.com/2019/09/what-is-subpixel-in-super-mario-bros.html),
[speedrun.com SMB1 glitch guide](https://www.speedrun.com/smb1/guides/09v5d)).

Whether a given approach clips depends on the subpixel alignment of the
approach, which is why runners practice setups that control it. No randomness
anywhere: a deterministic rule, plus deterministic state you can't see on
screen, equals a mechanic that *feels* like magic and *replays* like
clockwork.

### 2.4 When a clip rewrites the map: the Minus World

The most famous consequence of the SMB wall clip is the **Minus World**. Clip
through the brick wall at the end of World 1-2 and you can reach the Warp Zone
*before the game has finished setting it up*. The warp pipes still hold stale
destination data. One of them sends you to "World 36-1"; tile 36 renders as a
blank, so the HUD shows ` -1`. It's an underwater copy of 7-2 whose exit pipe
loops back to itself: unwinnable, unforgettable
([Wikipedia: Minus World](https://en.wikipedia.org/wiki/Minus_World),
[Super Mario Wiki](https://www.mariowiki.com/Minus_World)).

Note the anatomy: a *collision quirk* (the clip) exposed an *initialization
quirk* (stale warp data). Emergent mechanics compound. That is what makes
them generative rather than just broken.

### 2.5 Integer overflow: the kill screens

Fixed-width integers wrap, and two arcade legends end exactly there:

- **Pac-Man, level 256.** The level counter is one byte. The routine that
  draws the fruit row takes `level + 1`; at level 256 that's `255 + 1`, which
  wraps to 0 and sends the fruit-drawing loop off drawing **256 entries**
  straight out of memory, shredding the right half of the maze into garbage
  tiles. Only 9 of the required 244 dots survive in the debris, so the level
  is mathematically uncompletable
  ([Pac-Man Map 256 glitch](https://pacman.fandom.com/wiki/Map_256_Glitch)).
- **Donkey Kong, level 22.** The bonus-timer seed is computed as
  `10 * (level + 4)` in an 8-bit register. At level 22: `260`, which wraps to
  `4`, about seven seconds to finish a screen that needs far more. The run
  simply ends there
  ([DK kill screen](https://errors.fandom.com/wiki/DK_kill_screen),
  [annotated fix of the overflow](https://gist.github.com/guebe/e074b165ab6fd291b1fa3f424c18a893)).

Neither is a collision bug. Both are the same lesson: **the representation
is the rule.** When numbers have edges, gameplay happens at the edges.

### 2.6 Reading the wrong memory: MissingNo.

In *Pokémon Red/Blue*, the scripted old-man tutorial temporarily stores your
player name in the buffer used for wild-encounter data. The east coast of
Cinnabar Island defines no encounter table of its own, so surfing there rolls
encounters against whatever the buffer last held, the bytes of your name.
Species IDs beyond the 151 real Pokémon land in undefined slots of the
256-entry space, producing the scrambled sprite the world knows as
**MissingNo.** A beloved side effect sets a high bit that adds 128
copies of your sixth inventory item
([Wikipedia: MissingNo.](https://en.wikipedia.org/wiki/MissingNo.),
[Bulbapedia: old man glitch](https://bulbapedia.bulbagarden.net/wiki/Old_man_glitch)).
Players didn't avoid it; they farmed it. An out-of-bounds read became one of
the most cherished "features" in the series' history.

### 2.7 The far end: arbitrary code execution

Follow the ladder far enough and you reach runs that **program the game from
inside it**. In *Super Mario World*, manipulating sprite slots and then eating
a Chargin' Chuck makes the game jump into open RAM and execute it; runners
arrange sprites, and even the *held buttons on extra controllers*, so that
memory reads as instructions that set the game mode to "credits". A human
being, on a stock console, beats the game in about 40 seconds by writing
machine code with koopa shells
([TheGamer: SMW credits warp](https://www.thegamer.com/how-super-mario-world-speedrunners-beat-the-game-in-40-seconds-by-writing-code-with-koopa-shells/),
[Kotaku](https://kotaku.com/people-can-now-beat-super-mario-world-in-less-than-a-mi-1822666925)).
TASBot showcases have used the same family of exploits to inject entirely new
programs into a running SNES. This guide's layer stops well short of ACE.
It sits on the same continuum: deterministic rules, fully understood, turned
into expression.

### 2.8 Why people love this (and why it's worth engineering for)

Speedrunning communities treat a finished game as a system to be understood
past its intended surface, and glitches are where the system shows its true
shape ([Kotaku: why speedrunners use glitches](https://kotaku.com/why-speedruners-use-glitches-1582919382)).
Categories form around which rules you exploit (any% vs glitchless); knowledge
is produced collaboratively, often beyond what the developers knew; and
developers increasingly *protect* beloved glitches rather than patch them.
None of that culture can form around `if random() < 0.25: clip()`. It forms
around mechanisms: rules you can learn, state you can control, outcomes you
can reproduce. That's the bar this engine's retro layer sets for itself.

## 3. Determinism: what makes a quirk a feature

Everything above shares one requirement so basic it's easy to miss: **the
same inputs must always produce the same outcome.** A glitch you cannot
reproduce is a crash; a glitch you can set up by controlling visible and
invisible state is a technique. The engine's retro layer enforces this with
three rules, and they are non-negotiable for any quirk you add:

1. **Fixed-point integers only.** All retro positions/velocities are
   `FixedPoint` raw integers at one shared `frac_bits` scale. No floats enter
   the simulation.
2. **Fixed ticks.** `QuirkMovementSystem` accumulates the renderer's float
   `dt` and steps the simulation in whole ticks at `tick_hz` (default 60).
   Velocities are **per tick**, not per second; frame rate cannot change
   physics.
3. **No randomness.** Variation comes from state the player influences
   (position, speed, subpixel alignment), never from dice.

This is also the project's broader deterministic keystone: retro cartridges
replay exactly, which is what makes the worked examples in this guide, and
the unit tests that pin them, possible at all.

## 4. The retro layer in one tour

Everything lives under [engine/retro/](../../engine/retro/) and is pure
Python, opt-in, and inert for cartridges that don't use it.

| Piece | What it is |
|---|---|
| `FixedPoint`, `FixedPointVec2` ([fixed_point.py](../../engine/retro/fixed_point.py)) | Scaled-integer scalar/vector; `frac_bits=8` gives 256 subpixels per unit |
| `SubpixelTransformComponent`, `SubpixelMovementComponent`, `SubpixelColliderComponent` ([components.py](../../engine/retro/components.py)) | Per-entity opt-in: FP position, per-tick FP velocity + resolver-owned contact flags (`on_ground`/`hit_wall`/`hit_ceiling`), FP half-extents |
| `RetroProfile` ([profile.py](../../engine/retro/profile.py)) | The opt-in bundle: `frac_bits`, `tick_hz`, `enable_quirks` |
| `RetroObstacle`, `resolve_axis` ([systems/collision.py](../../engine/retro/systems/collision.py)) | Level geometry as center+extent boxes, quantized once to raw-int spans; the axis resolver with both ejection policies |
| `QuirkMovementSystem` ([systems/movement.py](../../engine/retro/systems/movement.py)) | Fixed-tick driver: per tick, run cartridge callbacks, integrate X and resolve, integrate Y and resolve, set contact flags, record `clip_events` |
| `QuirkRegistry` | Named on/off switches for quirk rules (open set: your own names welcome) |
| `VirtualPlayfield` ([playfield.py](../../engine/retro/playfield.py)) | Maps a virtual pixel space (256x240 by default) to render coordinates so visual size == collision size |

The opt-in is deliberately a few lines (this is P2-C's contract, quoted from
the code's own docs):

```python
from engine.retro import (
    RetroProfile, RetroObstacle, register_retro_systems,
    SubpixelTransformComponent, SubpixelMovementComponent,
    SubpixelColliderComponent,
)

profile = RetroProfile("nes", frac_bits=8, tick_hz=60,
                       enable_quirks=["subpixel_wall_clip"])
retro_sys = register_retro_systems(world, profile=profile, obstacles=LEVEL)
retro_sys.add_tick_callback(my_controller.control_tick)   # game feel, per tick
```

`register_retro_systems` **returns the live system**. Keep it. It is your
handle for `enable_quirk`/`disable_quirk`, `add_tick_callback`,
`clip_events`, and `step_ticks` (headless tests). Entities participate by
carrying the `Subpixel*` components; everything else in the engine ignores
them, and the retro system ignores everything else.

## 5. The ejection rule, exactly

The resolver ([systems/collision.py](../../engine/retro/systems/collision.py))
moves one axis at a time and, on overlap with a solid, chooses an exit face.
Two policies:

**Modern (quirk off): motion-based.** Push the body back out the face it
moved into. Moving right into a wall always snaps you to the wall's left
face. You can never end up on the far side. This is what a correct modern
resolver guarantees.

**Retro (quirk `"subpixel_wall_clip"`): midline ejection.** The resolver
never asks which way you were moving. It asks **which half of the obstacle
the penetrating edge is in**, the same family of position-based decision SMB
used:

```python
hi_inside = o_min < hi < o_max          # leading edge strictly inside?
lo_inside = o_min < lo < o_max
probe = hi if (hi_inside and not lo_inside) else \
        lo if (lo_inside and not hi_inside) else moved
if probe > o_mid:                       # STRICT: exactly-on-midline blocks
    moved = o_max + half_axis           # ejected out the MAX side
else:
    moved = o_min - half_axis           # ejected out the MIN side
```

The emergent consequence, stated as a theorem you can design levels with:

> **A solid can be clipped iff your per-tick speed exceeds half its
> thickness.** Only then can the contact tick land your leading edge past
> the midline, **and whether a given approach actually clips is decided by
> subpixel alignment.**

The reference numbers (8.8 fixed point; also pinned in the module docstring
and the unit tests). Wall spans x 200..206 px, raw min/mid/max
51200/51968/52736; player half-width 6 px (raw 1536); run speed 4.0 px/tick
(raw 1024):

| Start (center x) | Contact-tick leading edge (raw) | vs midline 51968 | Outcome |
|---|---|---|---|
| 153.5 (raw 39296) | 52096 | past it | **clips** to x = 212.0 |
| 150.5 (raw 38528) | 51328 | short of it | blocked at x = 194.0 |
| 153.0 (raw 39168) | 51968 | exactly on it | blocked (strict `>`) |
| 153.0 + 1 subpixel (raw 39169) | 51969 | one past | **clips** |

One subpixel (1/256 of a pixel) flips the outcome. That sensitivity isn't a
defect to paper over; it is the mechanic.

**Clip probability is computable.** On a constant-speed approach the leading
edge lands uniformly in a stride-wide window past the wall's near face; the
clip happens in the slice past the midline:

```
P(clip) = (stride - half_thickness) / stride        when stride > half_thickness
        = (1024 - 768) / 1024 = 25%                 for the demo's 4 px/tick vs 6 px wall
```

And the inverse design rule: anything you must *never* clip just needs
`half_thickness >= max per-tick speed`. The demo's floors (half 8), platforms
(half 5) and borders (half 8) all dominate the maximum vertical/horizontal
speeds (4.5/4.0). They are un-clippable *by construction*, with no special case.

## 6. Case study: how retro_sidescroller_demo was designed

The reference cartridge
([examples/cartridges/retro_sidescroller_demo/](../../examples/cartridges/retro_sidescroller_demo/README.md))
exists to make one emergent mechanic **observable, reproducible, and
attributable**. Every design decision serves one of those three words.

### 6.1 What it had to prove, and the rebuild lesson

The first implementation of this demo faked it: the "clip" was a hardcoded
gate that let the player through any solid whenever position low-bits fell in
a window covering half of all values. It *looked* like a quirk and was
actually a dice roll: no mechanism, no preconditions, nothing to learn. The
P2 audit re-opened the track and the layer was rebuilt around the real rule
described above. The lesson is worth engraving:

> **If the quirk is an `if`, it isn't emergent.** Implement the *mechanism*
> (the era's ejection decision), not the *outcome* (the pass-through), and
> let the outcome fall out where the preconditions truly hold.

### 6.2 Choosing the numbers

The whole level is tuned so the theorem in section 5 partitions the world cleanly:
exactly one solid is clippable, and only at genuine full speed:

| Constant | Value | Why this value |
|---|---|---|
| Playfield | 256x240 px, `frac_bits=8` | NES-resolution space; subpixel = 1/256 px, the authentic grain |
| Tick rate | 60 Hz, velocities px/tick | Hardware-style timing; frame rate cannot perturb physics |
| Player | 12x16 px | Small-sprite proportions; collider == visual (via `VirtualPlayfield.size_to_render_scale`) |
| `RUN_SPEED` | 4.0 px/tick | **> 3** (the wall's half-thickness): the wall is clippable, ~25% of natural alignments |
| `clip_wall` | 6 px thick, 104 px tall | Thin enough to clip; too tall to jump over (max jump from the upper platform leaves your feet ~8 px below its top). The clip is the *only* way past |
| `JUMP_IMPULSE` / `TERMINAL_FALL` | +4.5 / -4.0 px/tick | Both **< 5** (platform half) and **< 8** (ground half): floors and ceilings categorically un-clippable |
| Borders | 16 px thick | Half 8 > 4.0: the playfield edge cannot be clipped, ever |
| `SPAWN` | (40, 24) | Bottom edge exactly on the ground top. Strict-overlap resting contact is stable from tick 0 |
| `goal_pad` | non-solid, behind the wall | A visible reason to want through; placed clear of the post-clip ejection point (x = 212) |

The level itself is one list of `RetroObstacle` boxes (`LEVEL` in
[entrypoint.py](../../examples/cartridges/retro_sidescroller_demo/python/retro_sidescroller/entrypoint.py)),
and both the physics spans and the gray render rectangles are generated from
it. **What you see is exactly what you collide with.** There is no second,
subtly different copy of the geometry to drift out of sync.

### 6.3 Instruments, not magic

A demo that clips "sometimes" teaches nothing. The cartridge ships
instruments that make the invisible state controllable:

- **C** teleports to x=153.5 at full speed, the exact worked-example
  alignment. It clips, every time, on the 11th move. (Teleport+velocity-set
  is deliberate: it removes the acceleration ramp so the alignment is an
  experimental control, not an accident of your run-up.)
- **X** teleports to x=150.5, three whole pixels away, same speed, same
  wall: blocked, every time. The pair proves alignment, not luck, decides.
- **T** toggles the quirk live: the same C alignment under modern ejection is
  always blocked. The rule, not the level, is the variable.
- Every clip prints an attribution line (from the system's `clip_events`):
  which obstacle, which tick, which axis, where you ended up. The emergent
  moment narrates itself.

This is the design pattern to copy into your own quirk cartridges: **give the
player (and yourself) handles on the hidden state**, and announce the
emergence when it fires.

### 6.4 Why a sidescroller at all

Axis-separated move-and-resolve is the simplest world in which floors, walls
and ceilings all exist and behave differently under one rule. Landing and
standing exercises Y-resolution every tick (gravity keeps applying, as on
real hardware, so `on_ground` stays honest); running exercises X; and the one
deliberately thin wall turns the resolver's midline question into gameplay.

## 7. Tutorial: opt your cartridge in (about 10 minutes)

The steps below are the integration shape. They use the same calls the demo
makes. The demo's `initialize` is the full copy: real level, controller, and
hotkeys. These snippets are shortened so each step is visible on its own.

**1. Declare the profile and level, register the system:**

```python
from engine.retro import (
    RetroProfile, RetroObstacle, register_retro_systems,
    SubpixelTransformComponent, SubpixelMovementComponent,
    SubpixelColliderComponent, VirtualPlayfield,
)

LEVEL = [
    RetroObstacle(128, 8, 256, 16, name="ground"),
    RetroObstacle(200, 40, 6, 64, name="thin_wall"),   # half 3 < your speed?
]

def initialize(self, context):
    world = context.world
    profile = RetroProfile("nes", frac_bits=8, tick_hz=60,
                           enable_quirks=["subpixel_wall_clip"])
    self.retro_system = register_retro_systems(world, profile=profile,
                                               obstacles=LEVEL)
```

**2. Give gameplay entities the Subpixel components** (positions in pixels,
velocities per tick, every `frac_bits` matching the profile):

```python
player = world.create_entity("player")
world.add_component(player.id, SubpixelTransformComponent(x=40, y=24, frac_bits=8))
world.add_component(player.id, SubpixelMovementComponent(frac_bits=8))
world.add_component(player.id, SubpixelColliderComponent(12, 16, frac_bits=8))
```

Entities without a `SubpixelColliderComponent` integrate velocity but skip
collision. That is fine for particles and effects.

**3. Put game feel in a tick callback,** not in a per-frame `update`. The
callback runs exactly once per simulation tick, before integration; read the
resolver-owned contact flags rather than doing your own geometry:

```python
def control_tick(self, tick: int) -> None:
    sm = self.world.get_component(self.player_id, SubpixelMovementComponent)
    vx, vy = sm.current_velocity.get_xy_float()
    vy = max(vy - GRAVITY, TERMINAL_FALL)          # gravity EVERY tick
    if jump_pressed and sm.on_ground:
        vy = JUMP_IMPULSE
    sm.current_velocity = FixedPointVec2(vx, vy, frac_bits=8)

self.retro_system.add_tick_callback(controller.control_tick)
```

**4. Sync visuals per frame.** The retro state is the truth; your ordinary
per-frame System copies it into the float `TransformComponent` through the
playfield mapping (and `size_to_render_scale` makes sprites exactly collider
sized):

```python
playfield = VirtualPlayfield()                      # 256x240 mapped to aspect2d
px, py = st.position.get_xy_float()
tr.x, tr.y = playfield.to_render(px, py)
```

**5. Surface the emergence.** `self.retro_system.clip_events` holds this
frame's clips (entity, tick, axis, obstacle, position). Print them, ping a
sound, unlock a door. Make the moment legible.

Run headlessly in tests with `retro_system.step_ticks(n)`. No window, no
Panda, same exact integers.

## 8. Tutorial: bend the rule (and predict the result first)

The point of a documented mechanism is that you can *predict* it. Each
experiment below states the prediction the theory makes; make it, then run
`python main.py --cartridge examples/cartridges/retro_sidescroller_demo` and
check. All edits are in the demo's
[entrypoint.py](../../examples/cartridges/retro_sidescroller_demo/python/retro_sidescroller/entrypoint.py)
unless noted. (The full unit suite, `pytest tests/unit -q`, will tell you
loudly which pinned behaviors your edit changed. That's it working.)

### Experiment 1: thicken the wall, and the clip vanishes

In `LEVEL`, change `clip_wall` from `w=6` to `w=8`:

```python
RetroObstacle(203, 68, 8, 104, name="clip_wall"),
```

**Predict before running:** half-thickness becomes 4.0 = `RUN_SPEED`, so the
strict `stride > half` condition fails. `P(clip) = (1024-1024)/1024 = 0`.
**C must now block**, and no natural run-up will ever clip. The quirk is still
on; the *preconditions* are gone. (Verify, then change it back.)

### Experiment 2: speed up, more clips, but C blocks

Set `RUN_SPEED = 6.0`.

**Predict:** natural full-speed approaches now clip
`(1536-768)/1536 = 50%` of the time, twice as often. But the **C alignment
now blocks**: from x=153.5 at 6 px/tick the contact tick lands the leading
edge at raw 51584, *short* of midline 51968. Alignment is relative to the
stride; changing the stride re-deals every alignment. (This is exactly why
speedrunners practice setups per-strategy rather than "going fast".)

### Experiment 3: one subpixel

Set `CLIP_ALIGN_X = 153.0` and press C: blocked. The edge lands exactly on
the midline and the strict `>` refuses. Now set it to `153.00390625`
(+1/256 px, raw 39169): clips. You have just reproduced the
one-subpixel-flip row of the table in section 5 interactively.

### Experiment 4: write your own quirk, the momentum-preserving clip

Real hardware zeroed your velocity on ejection; let's invent a variant where
a *clip* (and only a clip) keeps your speed, so you burst through the wall
still running. This shows the full extension pattern: a new named rule,
gated by the registry, layered on the existing mechanism.

In [movement.py](../../engine/retro/systems/movement.py), the per-tick resolve
currently zeroes a collided axis:

```python
zero = FixedPoint(0, frac_bits=fb)
new_vx = zero if res_x.collided else vel.x
```

Change to:

```python
zero = FixedPoint(0, frac_bits=fb)
keep = res_x.clipped and self.quirk_registry.is_active("momentum_preserving_clip")
new_vx = vel.x if (not res_x.collided or keep) else zero
```

Then enable it in the demo's `initialize`, right after registration:

```python
self.retro_system.enable_quirk("momentum_preserving_clip")
```

(`QuirkRegistry` accepts any non-empty name. `KNOWN_QUIRKS` documents the
engine-recognized set, but the registry is an open switchboard precisely so
cartridges can add rules.)

**Predict:** C still clips at tick 11 and ejects to x=212, but instead of
stopping there, you keep doing 4 px/tick across the goal pad until the border
wall (half 8 > 4: un-clippable) stops you at x=250. The clip becomes a
*launch*. Quirk off (T), nothing changes at all. Your new rule is opt-in,
exactly like the layer itself.

The same pattern scales to honest new mechanisms: an integer-overflow
position wrap, sticky walls, narrow jump timing windows. Implement the rule
in the resolver/system, name it, gate it through the registry, and document
the preconditions under which it fires. (The resolver is also explicitly
"safe to copy into cartridges". For cartridge-private physics, vendor
`collision.py` into your package instead of editing the engine.)

## 9. Pin your quirk with tests

A quirk without tests will not survive its first refactor, and the strict
comparisons are load-bearing (Experiment 3 is one `>=` away from not
existing). The layer's test conventions, all visible in
[tests/unit/test_retro_quirks.py](../../tests/unit/test_retro_quirks.py):

- **Pin the worked arithmetic.** `test_clip_alignment_A_quirk_on`,
  `test_block_alignment_B_quirk_on` and `test_one_subpixel_flips_the_outcome`
  assert the exact raw integers from the section 5 table. If a "small cleanup"
  changes an outcome, the diff names the subpixel.
- **Pin the negative space.** `test_quirk_off_always_blocks` (modern mode
  never clips) and `test_lands_on_ground_and_stays` (resting contact is
  stable) keep the quirk from leaking where it mustn't.
- **Drive headless.** Build a `World`, `register_retro_systems(...)`,
  `step_ticks(n)`, assert positions. No window required, and exact by
  construction. The cartridge-level test
  (`test_cartridge.py::test_retro_sidescroller_demo_loads_and_reproduces_wall_clip`)
  then proves the same behaviors end-to-end through real frames.

A pinning test for Experiment 4, as a template:

```python
def test_momentum_preserving_clip_keeps_velocity():
    world = World()
    profile = RetroProfile("nes", frac_bits=8, tick_hz=60,
                           enable_quirks=["subpixel_wall_clip",
                                          "momentum_preserving_clip"])
    system = register_retro_systems(world, profile=profile, obstacles=WALL_LEVEL)
    eid = _make_player(world, x=153.5, vx=4.0)          # the clip alignment
    system.step_ticks(11)                                # clips on tick 11
    sm = world.get_component(eid, SubpixelMovementComponent)
    assert sm.current_velocity.get_xy_float()[0] == 4.0  # momentum survived
```

## 10. Design guidelines for new quirks

Distilled from the rebuild, the research above, and the demo:

1. **Mechanism, not outcome.** Recreate the *decision* old hardware made
   (which half? which face? what wraps?), never the visible result.
2. **Stay integer, stay ticked.** Float math or frame-time anywhere in a
   quirk silently breaks determinism, the property the whole layer sells.
3. **Make preconditions level data.** The demo's clip exists because of a
   *6 px wall* against a *4 px/tick runner*: numbers a designer tunes, not
   flags a programmer sets. Design rules like "clippable iff
   `speed > half_thickness`" give level designers a dial.
4. **No dice.** If variation doesn't come from controllable state, players
   can't practice it and testers can't pin it.
5. **Ship instruments.** A teleport-to-alignment key, a quirk toggle, an
   attribution printout. Make hidden state manipulable and emergence
   legible (C/X/T in the demo).
6. **Pin everything.** Worked arithmetic in the docstring; the same numbers
   asserted in tests; strict-vs-inclusive comparisons treated as API.
7. **Opt-in, always.** Quirks activate through `RetroProfile.enable_quirks`
   or `enable_quirk()` on the system handle; modern cartridges and the
   default engine path must be untouched by your additions.

## Sources & further reading

**Mechanics of the era**
- [TASVideos: SMB game resources](https://tasvideos.org/GameResources/NES/SuperMarioBros) (subpixels, wall ejection, frame rules)
- [SDA Knowledge Base: Super Mario Bros.](https://kb.speeddemosarchive.com/Super_Mario_Bros.) (wall clipping practice)
- [What is a subpixel in SMB, and how does it relate to wall clipping?](http://hcfyk.blogspot.com/2019/09/what-is-subpixel-in-super-mario-bros.html)
- [speedrun.com: SMB1 useful glitches guide](https://www.speedrun.com/smb1/guides/09v5d)
- [nesdev forums: sub pixel movement](https://forums.nesdev.org/viewtopic.php?t=12125)
- [Jitterbugs: why subpixel movement is hard](https://marioslab.io/posts/jitterbugs/)
- [ALttP wiki: Subpixels](https://alttp-wiki.net/index.php/Subpixels)

**Famous emergent results**
- [Wikipedia: Minus World](https://en.wikipedia.org/wiki/Minus_World), [Super Mario Wiki](https://www.mariowiki.com/Minus_World)
- [Pac-Man: Map 256 glitch](https://pacman.fandom.com/wiki/Map_256_Glitch)
- [Donkey Kong kill screen](https://errors.fandom.com/wiki/DK_kill_screen), [the overflow, annotated and fixed](https://gist.github.com/guebe/e074b165ab6fd291b1fa3f424c18a893)
- [Wikipedia: MissingNo.](https://en.wikipedia.org/wiki/MissingNo.), [Bulbapedia: old man glitch](https://bulbapedia.bulbagarden.net/wiki/Old_man_glitch)
- [SMW credits warp / human ACE](https://www.thegamer.com/how-super-mario-world-speedrunners-beat-the-game-in-40-seconds-by-writing-code-with-koopa-shells/), [Kotaku](https://kotaku.com/people-can-now-beat-super-mario-world-in-less-than-a-mi-1822666925)

**Culture**
- [Kotaku: why speedrunners use glitches](https://kotaku.com/why-speedruners-use-glitches-1582919382)

**In this repository**
- [retro_sidescroller_demo README](../../examples/cartridges/retro_sidescroller_demo/README.md): the playable companion to this guide
- [engine/retro/systems/collision.py](../../engine/retro/systems/collision.py): the rule, with the worked example in the docstring
- [PHASE2 tracking doc](../PHASE2_RETRO_EMERGENT_GAMEPLAY_LAYER.md): why the layer exists and how it got here
- [Cartridge loader guide](cartridge_loader_guide.md): packaging and loading the cartridge that carries your mechanic
