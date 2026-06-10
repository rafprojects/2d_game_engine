# Retro Sidescroller Demo (SMB spirit — the subpixel wall clip)

The P2-D reference cartridge: a small playable sidescroller that demonstrates
one **genuinely emergent** retro mechanic — the subpixel wall clip — produced
by the documented ejection rule in the engine's retro layer, not by a scripted
pass-through.

## Run it

```bash
python main.py --cartridge examples/cartridges/retro_sidescroller_demo
```

> The `--cartridge` flag is required. (`--cartridge-extract` is only the
> extraction cache directory — on its own it loads the engine's default demo
> and none of this cartridge's content.)

You should see a dark window with a gray level (ground + two platforms), a
**yellow wall** on the right, a green goal pad behind it, and a **red 12×16
rectangle**: you.

## Controls

| Key | Action |
|-----|--------|
| Arrows / A, D | Run left/right |
| Space / W | Jump (when grounded) |
| **C** | Teleport to the exact alignment that **clips** (x=153.5, full speed) |
| **X** | Teleport to an alignment 3 px away that is always **blocked** |
| **T** | Toggle the quirk: midline (retro) vs motion-based (modern) ejection |
| R / F5 | Respawn · ESC quits |

## What you're looking at

Everything runs on a virtual **256×240 pixel playfield** (NES-like), mapped
once to the window. Positions and velocities are **8.8 fixed point** — 256
subpixels per pixel — and the simulation advances in fixed **60 Hz ticks**
with velocities in pixels *per tick*, exactly like the original hardware.
The level geometry is one list of pixel-space boxes (`LEVEL` in
`entrypoint.py`); both the physics and the gray rectangles are generated from
it, so what you see is exactly what you collide with.

## The emergent mechanic

The yellow wall is **6 px thick**. You run at **4.0 px/tick**. The retro
ejection rule ("subpixel_wall_clip", enabled by default here) resolves a
collision by asking *which half of the obstacle the penetrating edge is in*
— the authentic NES tile-ejection question — instead of "which way was I
moving?".

Because 4.0 > 3 (half the wall), the first tick that overlaps the wall can
land your leading edge **past its midline**, and the rule then "helpfully"
ejects you out the **far side**. Whether that happens depends purely on your
subpixel alignment at approach — about 1 in 4 full-speed run-ups clip.

The worked arithmetic (also in `engine/retro/systems/collision.py` and pinned
by unit tests):

| | raw (×256) | result |
|---|---|---|
| wall min / mid / max | 51200 / 51968 / 52736 | x = 200…206, midline 203 |
| start x = **153.5**, 4 px/tick | tick-11 edge = **52096** > 51968 | **clips** → x = 212.0 |
| start x = **150.5** (3 px earlier) | tick-11 edge = 51328 ≤ 51968 | blocked → x = 194.0 |
| start raw 39168 (x = 153.0) | edge lands exactly **on** the midline | blocked (strict compare) |
| start raw **39169** (+1 subpixel) | edge = midline + 1 | **clips** |

One subpixel flips the outcome. That determinism is the whole point of the
retro layer.

Press **T** and the same approaches are *always* blocked: modern ejection
pushes you back out the face you moved into, no matter the alignment.

Floors and ceilings can never clip — no vertical speed (jump 4.5, terminal
fall 4.0) reaches half the thickness of the ground (8) or platforms (5).
That asymmetry is by design: the wall is the only clippable solid, and the
only way to the goal pad (it's too tall to jump over, even from the upper
platform — climb ground → platform 1 → platform 2 and try).

## How a cartridge opts in (the P2-C few-liner)

```python
profile = RetroProfile("nes-smb", frac_bits=8, tick_hz=60,
                       enable_quirks=["subpixel_wall_clip"])
retro_sys = register_retro_systems(world, profile=profile, obstacles=LEVEL)
retro_sys.add_tick_callback(my_controller.control_tick)   # game feel, per tick
# + Subpixel{Transform,Movement,Collider}Component on the player entity
```

The returned system is the live handle: `enable_quirk` / `disable_quirk`
(the T hotkey), `clip_events` (the narration), `step_ticks` (headless tests).
Game feel (run accel, gravity, grounded jumps via the resolver's `on_ground`
flag) lives in this cartridge's `RetroSidescrollerController` — copy it as a
starting point for your own retro cartridge.

## Notes

- The cartridge relies on `main.py`'s core systems (Render/Input); it only
  adds its own controller and the retro system.
- Headless end-to-end coverage lives in
  `tests/unit/test_cartridge.py::test_retro_sidescroller_demo_loads_and_reproduces_wall_clip`
  (drives the loaded cartridge frame-by-frame, no window needed) and
  `tests/unit/test_retro_quirks.py` (the rule itself).
- The cartridge requests a 1024×960 window (16:15 — the playfield's exact
  aspect) with foreground focus. If keys ever do nothing, click the game
  window once: some window managers (e.g. WSLg) open windows without
  keyboard focus.
- Border walls (16 px, un-clippable) enclose the playfield, and a fall
  respawn is in place as insurance for experimentation.
