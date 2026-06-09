# Future Tasks

Tasks deferred from the TGL demo MVP. Listed roughly by priority / dependency order.

---

## TGL Cartridge

### 1. Top-down labyrinth mode
The NES game alternates between scrolling-shooter corridors and top-down overhead
exploration rooms. The labyrinth mode requires:
- 8-directional player movement (free X/Y on the ground plane)
- Orthographic camera looking down the Z axis (swap from current side view)
- Tile-based room layout loader
- Enemy pathfinding behaviour in the labyrinth context

**Assets available:** `assets/sprites/walking/` — 24 raw PNG frames covering
8 directions × 3 phases (down, up, left, right, diagonals).

### 2. Walking sprite integration
The 24 PNG frames in `assets/sprites/walking/` need to be assembled into an
animation source before the labyrinth mode can render character movement.

**Options:**
- **Sprite sheet (recommended):** Pack frames into a single spritesheet PNG,
  define `SpriteSheet.create_animation_from_frames()` entries for each direction.
- **egg-texture-cards:** Run `egg-texture-cards` on each directional set to
  produce per-direction `.egg` files, consistent with the ship/asteroid assets.

### 3. Mode transition animation
19 frames `assets/sprites/transform/TGA_17.png` – `TGA_35.png` represent
Alyssa's transformation between labyrinth-walker and fighter-ship forms.

This sequence plays when entering/exiting a corridor. Requires:
- A `TransformAnimationSystem` (or a one-shot `play_animation` on a non-looping
  sequence) triggered by a mode-switch event
- Camera and control handoff logic between the two modes

### 4. Scrolling starfield background
Replace the current solid-colour background with a tile-scrolling NES-style
starfield. Approach: one or two `SpriteComponent` planes on a background layer
that repeat/wrap as they scroll.

### 5. Boss battles
The reference `game_settings.yaml` defines a multi-phase boss system with
configurable AI patterns. Port or redesign into the current ECS:
- `BossComponent` with phase list and HP thresholds
- Per-phase movement pattern overrides (already partially available via
  `EnemyAISystem`)
- Unique boss sprite (not yet extracted/available)

### 6. Power-up system
Reference config lists four power-up types: `health`, `shield`, `weapon_upgrade`,
`speed_boost`. Implement as:
- `PowerUpComponent` dropped by enemies at a configurable drop rate
- `PowerUpSystem` that detects player collisions and applies effects to
  `PlayerComponent`

### 7. Additional enemy types
Only asteroids exist as assets. At minimum, extract and integrate enemies from
the original spritesheet. The reference movement system supports 15+ patterns
(`sinusoidal`, `circular`, `figure_eight`, `spiral`, `pendulum`, `arc`,
`evading`, etc.) that are ready to plug in once sprite assets exist.

### 8. Audio
The reference `config/game_settings.yaml` defines BGM tracks and SFX volumes.
The current engine has `AudioSystem` and `MusicSystem`. Integration tasks:
- Wire cartridge-level music cues (corridor entry, labyrinth, boss, game-over)
- SFX for shooting, explosion, player hit, power-up collection

### 9. TGL save state
Persist player progress (score, lives, current corridor index) across sessions
using `WorldSaveProvider`. Requires registering `PlayerComponent` with
`SaveStateManager.register_component()` in the entrypoint.

### 10. ZIP packaging / release build
A build script (`tools/pack_cartridge.py` or similar) that:
1. Copies sprites from `assets/sprites/` into `examples/cartridges/tgl_demo/assets/`
2. ZIPs the cartridge directory into `dist/tgl_demo-<version>.zip`
3. Verifies the archive loads correctly via `CartridgeLoader.load_archive()`

---

## Engine

### A. egg-texture-cards workflow documentation
Document how to generate `.egg` animation files from PNG frame sequences using
Panda3D's `egg-texture-cards` CLI. Include a helper script in `tools/` that
wraps the common invocation patterns (grid layout, per-frame custom coords).

### B. Sprite-sheet packing tool
A small utility (`tools/pack_spritesheet.py`) that assembles individual frame
PNGs into a single spritesheet image and outputs the `SpriteSheet` configuration
(row/col counts or frame-coordinate list) as a Python snippet or JSON. Useful
for the walking sprites and any future hand-drawn animation.

### C. Trigger-layer collision documentation
The `ColliderComponent` layer/mask system uses a bitfield convention that is
not currently documented. Add an explanation (and constants file) so cartridge
authors can set up collision matrices without guessing bit offsets.

### D. Rust engine math / core layer (extensive spike required)
Consideration surfaced during P2-A (core retro math primitives). Evaluate
re-implementing performance-sensitive or determinism-critical primitives
(fixed-point arithmetic, possibly later systems) as a Rust layer (PyO3 etc.)
for optional acceleration or as a future engine foundation.

**Status:** Deferred. Requires an *extensive spike* (build system changes,
cross-platform wheel/CI, contributor ergonomics, packaging impact on pure-Py
cartridges, comparison vs the pure-Python reference, synergy with PHASE3
native plugin boundary) before any commitment or partial implementation.
The P2-A reference implementation (pure Python) remains the supported path
for the retro emergent layer.

See the approved P2-A session plan for the full pros/cons/LOE analysis of
native paths (C++ Panda expansion was scrapped; Rust via added layer is the
only path worth future investigation).

---



*(Broader Fidelity Profiles / Retro Authenticity items and remaining Native Plugin Boundary & FFI Readiness items (packaging, richer FFI, security sketch) were formalized into PHASE5_FIDELITY_RETRO_PRODUCTION.md tracks during Phase 5 planning and removed here to keep the FUTURE queue clean. See PHASE5 for the authoritative tracking.)*
