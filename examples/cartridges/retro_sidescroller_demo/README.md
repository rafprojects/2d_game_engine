# retro_sidescroller_demo — P2-D Reference Cartridge (SMB-Spirit Wall Clip)

**Phase 2 Track P2-D deliverable.**  
One small, self-contained, packable, runnable reference cartridge whose primary purpose is to make the subpixel wall clip (the most iconic NES-era emergent behavior) *obvious, reproducible, and directly attributable to a specific rule* in the engine's retro layer.

This is the sidescroller requested by the user: "one of the sample reference cartridges should be a 2D sidescroller in Super Mario Bros spirit to best show the wall clip". A single cartridge suffices (everything important is showed off here).

## What it demonstrates

- **P2-C opt-in (a few lines)**: `register_retro_systems(context.world, profile=RetroProfile(...))` + `Subpixel*` components on the player entity.
- **P2-B reference quirk system + rule**: `QuirkMovementSystem` with `subpixel_wall_clip` enabled via the profile. The exact repro numbers and obstacle from `tests/unit/test_retro_quirks.py` are used so the emergent passage is deterministic and matches the unit test that proves "only with retro + rule".
- **"This only happens because..."**: At load time (and on the repro step) the cartridge prints a clear attribution block pointing straight at:
  - `engine/retro/systems/collision.py` (the `subpixel_wall_clip_rule`, the low_bits window check, the intentional early return of `intended_pos`).
  - The P2-B research (SMB 8.8 fixed-point / 256 subpixels, "partially inside the block for two consecutive frames").
  - The control case (rule disabled or pure float modern path) that blocks cleanly.
- **Coexistence**: Modern float code paths (default MovementSystem, TransformComponent, CollisionSystem) are never touched. The cartridge only adds retro components and the retro system.
- **Template**: Copy this whole tree, change the `enable_quirks` list, the start position/velocity, or the wall rect, and you immediately have a new (or modified) emergent behavior to study.

## Run it

From the engine checkout root:

```bash
python main.py --cartridge examples/cartridges/retro_sidescroller_demo
```

You should see (among engine startup logs):

```
[P2-D] retro_sidescroller_demo (SMB-spirit wall clip reference)
  Profile: RetroProfile(...)
  Player start x (fb=8): 4.09375...
  ...
  After step: x=... (passed the wall? True)

  *** EMERGENT BEHAVIOR REPRODUCED ***
  ...
  See exactly:
    engine/retro/systems/collision.py:...
```

The player entity starts at the precise subpixel offset that makes the low-bits condition true for the wall at x=5. The Quirk system + enabled rule lets it carry through. The same numbers with the rule off (or default systems) stop at the wall edge.

## Pack / load (AC validation)

```bash
# Pack (produces a .car archive)
python -m tools.cli.cartridge_pack examples/cartridges/retro_sidescroller_demo -o /tmp/retro_ss.car --force

# Then load the archive the same way
python main.py --cartridge /tmp/retro_ss.car
```

The loader (dir or archive) + manifest + entry hook all work exactly as for `tgl_demo`.

## How the clip repro works (exact match to the unit test)

See `python/retro_sidescroller/entrypoint.py` and the numbers pulled from `test_retro_quirks.py:test_subpixel_wall_clip_rule_produces_emergent_passage`:

- frac_bits=8 (emulates the canonical NES 256-subpixel grid)
- start_x = 4.0 + (0x18 / 256) ≈ 4.09375
- vx = 2.0
- dt = 0.6  (displacement 1.2, enough to cross the wall at 5.0)
- wall rect at (5.0, 0) size (1, 2), player size (0.8, 0.8) as extra_obstacle

The rule (after tentative FP step) computes penetration, extracts `low_bits = contact_raw & (scale-1)`, and when the bits fall in the reference window it returns the *intended* position instead of clamping. That is the entire "quirk".

Modern float + simple MTV push (the control in the unit test and what default systems effectively do) clamps the player to the left edge of the wall.

## Variant / modern contrast (AC)

The primary cartridge always runs with the quirk enabled (that's the feature being shown).

To see the block:

- Edit the profile in `entrypoint.py` to `enable_quirks=[]` (or omit the clip name) and re-run.
- Or don't call `register_retro_systems` at all and add a normal `TransformComponent` + `MovementComponent` + default systems (the cartridge comments show the pattern).
- The unit test that loads this cartridge (or directly mirrors the numbers) also runs the explicit float control and asserts the difference.

## Extending / experimenting (the real point of a reference cartridge)

1. Copy the whole `retro_sidescroller_demo/` tree to `my_weird_quirk_cart/`.
2. Change the name/entrypoint in `config/cartridge.json`.
3. In `entrypoint.py`:
   - Swap or add quirks: `enable_quirks=["subpixel_wall_clip", "momentum_residual"]`
   - Change start/vel/wall to hit different alignments.
   - Add more platforms or a jump arc (still using Subpixel* + the Quirk system).
4. Run it. Observe (and log) the new or modified emergent behavior.
5. Read the rule you toggled — it is 20-30 lines of pure Python with exhaustive comments.

Everything a cartridge author needs to *understand and reproduce* the classic effect lives in the retro package + this tiny demo.

## Files (intentionally small)

- `config/cartridge.json` — standard manifest (entrypoint, assets mount, engine req)
- `python/retro_sidescroller/entrypoint.py` — the whole demo (opt-in, player, level, repro step + attribution print, teardown)
- `python/retro_sidescroller/__init__.py` — package marker
- `assets/` — minimal placeholder (manifest requires a mount point)
- `README.md` — this file

No custom components or large asset trees. The "sidescroller" is the context that makes the wall clip meaningful; the code is the minimum that satisfies the ACs and user request.

## Relation to the rest of Phase 2

- P2-A gave us `FixedPoint*` + `Subpixel*`.
- P2-B gave us `QuirkMovementSystem` + the documented rules (wall clip is primary).
- P2-C gave us `RetroProfile` + `register_retro_systems` (the clean opt-in this cart uses).
- P2-D (this) proves it with a real, loadable, packable, studyable cartridge.
- P2-E (next) will be the prose tutorial that walks an author from this cartridge through a rule change.

## Non-interference

Loading and running this cartridge has zero effect on any default float/Vec2/Transform/Movement/Collision paths in the engine or in other cartridges. All retro work is gated behind the Subpixel components and the explicitly registered system.

## Credits / sources (for the "why")

- Unit test + rule implementation: this repo (P2-B).
- NES/SMB subpixel + wall clip mechanics: nesdev, retrocomputing.stackexchange, TAS notes, "Game Development in Eight Bits" talks, etc. (research performed with explicit user permission during P2-B and P2-D planning).
- Sidescroller level design spirit: classic Mario (gaps, precise alignments, momentum as feature, "show off" sections).

Enjoy the clip — and then go make your own.
