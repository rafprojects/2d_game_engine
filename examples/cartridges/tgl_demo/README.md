# TGL Demo Cartridge

Scrolling-shooter "corridor" proof-of-concept inspired by *The Guardian Legend* (NES).

This cartridge demonstrates the engine's cartridge loading, sprite/animation, input, simple collision triggers, and player/enemy systems.

## Running

From the repo root:

```bash
python main.py --cartridge examples/cartridges/tgl_demo
```

- Default window: 1024×960 (2× the classic 512×480 "NES doubled" target used in the comments).
- Controls: Arrow keys / WASD to move, Space to shoot.
- The demo is intentionally minimal — a vertical lane with a player ship, basic enemy waves, score/lives, and invulnerability on hit.

### Developer mode (hitbox visualization)

```bash
python main.py --cartridge examples/cartridges/tgl_demo --dev-mode
# or
python main.py --cartridge examples/cartridges/tgl_demo --dev
```

When `--dev-mode` is active the cartridge automatically turns on colored debug collision outlines from `PandaCollisionSystem`:
- **Blue** = Player
- **Red** = Enemies
- **Yellow** = Bullets

Press **V** (or **v**) to toggle the hitbox overlays on/off while the game is running. This is the primary tool for diagnosing collider size/position problems.

The debug outlines are drawn as always-on-top wireframes so they remain visible even over sprites. They are sized exactly to the final `ColliderComponent` (after applying the transform scale), so what you see is what actually collides.

**Other dev hotkeys (engine-level):**
- **R** or **F5**: Hot-restart the cartridge (clears entities, resets spawners/controllers, respawns player — no need to fully exit/relaunch the process).
- **ESC**: Request clean quit (also reacts to the window close button). The engine now handles shutdown more promptly and tries to clean Panda collision resources before exit. (Previously Ctrl-C could appear to hang for a while.)

## Recent Fixes (Hitboxes, Scaling, Damage Feel)

The changes in this session directly addressed the reported issues:

- **Hitboxes are now bound to the visible sprites**
  - Added `python/tgl/utils/sprite_visual_size.py` (and package `__init__`).
  - `get_visual_size(path, loader)` replicates the `.egg` normalization + `base_scale=0.5` math from `RenderSystem` and returns the on-screen footprint (width, height) for a sprite at `Transform(scale=1)`.
  - `compute_hitbox_size(visual, factor=0.7)` turns that into a suggested collider size.
  - Entry point pre-computes the three assets (ship / bullet / asteroid) once it has the loader, then injects the final collider sizes (and raw visual sizes for debugging) into the config dicts passed to the controller and spawner.

- **Playfield vs. sprite scaling fixed; player no longer feels huge**
  - `game_settings.yaml` now declares explicit `scale` + `collider_scale_factor` under `player`, `enemies`, and `bullet`.
  - Player spawn reads `cfg["player"]["scale"]` (example starting value 0.40).
  - Enemy and bullet scales similarly reduced and documented.
  - The example numbers are *starting points derived from the actual .egg vertex extents*. They must be (and were) tuned by running the game and comparing rendered size vs. the collider rects produced by the helper.

- **Player damage animation / visual feedback**
  - While `PlayerComponent.invulnerable_timer > 0` the `ShipControllerSystem` now modulates the player's `SpriteComponent`:
    - Rapid opacity blink (~10 Hz) — classic retro "i-frames" look.
    - Mild red tint (`Vec4(1, 0.6, 0.6, 1)`) for the whole invuln window so a hit is immediately obvious.
  - Appearance is restored exactly when the timer hits zero.
  - No new assets or component fields were required.

- **Layer/mask hygiene**
  - All three modules (`entrypoint`, `ship_controller`, `wave_spawner`) now import and use `engine.physics.typesg.CollisionLayer` + `mask_of` instead of hand-rolled bit math. Local `LAYER_*` ints are kept only where `ColliderComponent` still wants a raw layer number.

## Tuning Hitboxes After Asset Changes

1. Run the cartridge.
2. (Optional but excellent) Temporarily register `PandaCollisionSystem` (see comment in `entrypoint.py`) and press the viz toggle (example in the demo uses `V` in other code).
3. Look at the relationship between the rendered ship/asteroid/bullet and the collision rects.
4. Adjust the three `*collider_scale_factor` values in `game_settings.yaml` (0.65–0.85 range is typical).
5. Re-run. The helper + cfg injection means you usually only edit YAML.

If you change the source art (new .egg frames with different native extents), just re-run — the visual size computation is dynamic.

## "Making It Feel Like The Guardian Legend" — Ideas & Roadmap

The current demo is still a tech skeleton (asteroids + a generic ship). Real TGL fidelity requires several more layers. These are captured from `docs/FUTURE_TASKS.md` plus direct observation of the NES game.

### Immediate / High-Impact Polish (small code, big feel)
- Register `PandaCollisionSystem` + playfield bounds + `V` key viz toggle (already stubbed in comments).
- Simple death "pop" / impact particles on enemy kill (cheap expanding CardMaker or a short non-looping sprite).
- Wire the included `Guardian_Legend.nsf` on initialize (engine has full NSF support). One or two basic shoot/hit sounds.
- Slight movement squish or a one-line acceleration curve so the ship doesn't feel like a teleporting rectangle.
- A few distinct enemy "looks" even while still using the asteroid model (tint + slight scale variance per pattern).

### Core TGL Identity (bigger lifts)
- **Real corridor enemies** from `assets/spritesheets/enemies.png` (corridor half of the sheet). Either:
  - Cut frames and `egg-texture-cards` them (consistent with current ship/asteroid), or
  - Load the sheet texture and drive `SpriteSheet` + UV animation on `SpriteComponent`.
- **The labyrinth / top-down mode** (the other half of TGL). 8-directional free movement, overhead view, tile rooms, pathfinding enemies, the walking sprites in `assets/sprites/walking/`.
- **Transformation sequence** — the 19-frame `assets/sprites/transform/` set that plays when you switch between fighter-ship and ground-walker forms.
- Proper weapon progression, sub-weapons, and the four power-up types the old reference config already enumerated.
- Multi-phase bosses (art in `bosses.png`).
- Enemy bullets, destructible obstacles, the classic "busy but fair" screen density, score multipliers, etc.

### Audio & Presentation
- Full NSF track switching (corridor vs. labyrinth vs. boss vs. game over).
- Chiptune SFX for all the important actions.
- Optional CRT/scanline overlay or NES-accurate palette limiting.

### Engine-Level Things That Would Help TGL-Style Games
- Easy "graze box" (larger visual collider vs. a smaller damage collider on the same entity).
- Optional fixed-point / subpixel simulation layer (the engine vision document talks about deliberate retro quirks producing emergent behavior).
- A small "impact" / screen-shake utility.

See `docs/FUTURE_TASKS.md` (TGL Cartridge section) for the original prioritized list and asset notes.

## Packaging Note

When you eventually run `py2d-cartridge` (or equivalent), the sprites currently live in the engine root `assets/`. For a self-contained `.car` you will need to copy the used sprite subtrees into `examples/cartridges/tgl_demo/assets/sprites/` (the FUTURE_TASKS build step describes this). Directory-loaded cartridges during development resolve through the ResourceManager mount + fallback search order.

## Quick Dev Tips

- The cartridge's Python code lives under `python/tgl/` (this becomes the import root when the cartridge is loaded).
- `ShipControllerSystem` and `WaveSpawnerSystem` already receive the relevant slices of `game_settings.yaml`.
- `PlayerComponent.invulnerable_timer` is the single source of truth for i-frames.
- Use the dev tools (`component_inspector`, hot reload) while iterating on scales and factors.

Enjoy the corridor — and the eventual labyrinth!
