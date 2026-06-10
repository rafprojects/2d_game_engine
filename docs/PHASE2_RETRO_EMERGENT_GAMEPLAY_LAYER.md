# Phase 2 - Retro Emergent Gameplay Layer

**Status:** Planned  
**Created:** 2026-06  
**Last updated:** 2026-06 (initial draft from vision extraction + user choices)

### Tracks

| Track | Description | Status | Effort |
|-------|-------------|--------|--------|
| P2-A | Core retro math primitives (`engine/retro/` package: fixed-point arithmetic, `FixedPointVec2`, `SubpixelTransformComponent` or equivalent precision-aware components) | Complete ✅ | Medium |
| P2-B | Reference quirk movement and collision systems (e.g. `NESStyleMovementSystem` or `QuirkMovementSystem` + collision resolver that intentionally applies and documents specific clipping/penetration/quirk rules) | Complete ✅ | Large |
| P2-C | Opt-in / integration mechanism for the retro layer (fidelity profile hook, component/system flags, clean coexistence with default float/Vec2 paths so modern cartridges are unaffected) | Complete ✅ | Small-Medium |
| P2-D | One or two small reference cartridges demonstrating a reproducible emergent mechanic (e.g. subpixel-enabled wall clip, momentum quirk, or documented classic glitch that only appears when the layer is active) | Complete ✅ | Medium |
| P2-E | Documentation and tutorial ("Building Authentic Retro Mechanics with Cartridges" or equivalent; includes how cartridge authors opt in and why the emergent behavior occurs) | Planned | Small |

---

## Rationale

Briefly explain why this phase exists now.

1. The original vision for the engine (cartridges as first-class self-contained units) explicitly calls out a novel creative payoff beyond modularity and distribution: cartridges can deliberately opt into constrained simulation rules (fixed-point, subpixel, hardware-like arithmetic and collision) that produce emergent "NES-style" gameplay side-effects. These were often not bugs but features of the original hardware constraints. After the foundational cartridge system polish (loader, assets, context, tooling, docs, reference usage) is in place, the next logical phase is to deliver the reference implementations that make this thesis real and usable.
2. These items belong together as one phase because they form the complete "retro reference layer" slice: the low-level math primitives, the systems that apply intentional quirks on top of them, the opt-in surface so cartridges can choose the constraint, and — critically — at least one small reference cartridge plus documentation that proves a specific emergent behavior is reproducible and intentional. Without the demonstrating cartridge and docs, the layer remains theoretical.
3. Success looks like: a developer can create (or scaffold) a minimal cartridge, opt into the retro layer (or copy the reference movement/collision), observe a documented classic quirk (e.g. a precise subpixel wall clip or momentum conservation that would not occur under full floating-point), and understand exactly which rule in the reference implementation enables the behavior. Existing modern code paths remain completely unaffected.

## Key Decisions

| # | Decision | Resolution |
|---|----------|------------|
| A | Filename / title for the tracking doc | `docs/PHASE2_RETRO_EMERGENT_GAMEPLAY_LAYER.md` titled "Phase 2 - Retro Emergent Gameplay Layer" (direct match to AUDIT language "Phase 2 – Retro Emergent Gameplay Layer (The Novel Part)" and the pointer in CARTRIDGE_VISION.md). |
| B | Scope for PHASE2 | Primary content strictly follows the cartridge-vision AUDIT definition of the novel part (engine/retro/ primitives + NES-style quirk systems + 1-2 small ref cartridges for one reproducible emergent mechanic + docs). Broader fidelity items (visual retro effects/scanlines/CRT/palette, audio chip emulation, full fidelity profiles) from PROJECT.md are intentionally kept out of this phase's tracks and instead captured as clean, detailed tasks in FUTURE_TASKS.md for later pulling. |
| C | Representation of prior work / PHASE1 prerequisite | PHASE2 doc focuses purely on the new retro work with minimal backward references (per choice). The prerequisite nature of PHASE1 (working cartridge loader, asset mounts, Context facade, docs leadership, tgl_demo as reference) is assumed complete; any needed cross-refs are light. |
| D | Vision reference / cross-linking | Leave the thin `docs/CARTRIDGE_VISION.md` as-is for now (its PHASE1 link + roadmap pointer to AUDIT is sufficient; the new PHASE2 doc will self-reference the AUDIT as the detailed source). |
| E | Emergent mechanic example & prioritized behaviors | Synthesize from sources (AUDIT primary examples of subpixel-style clipping, wall clips, momentum quirks + PROJECT.md open questions around integer overflow effects, specific collision quirks, timing windows, etc.). The ref cartridge track will propose a concrete, minimal, reproducible example (e.g. a subpixel wall-clip or momentum-based platformer quirk) while noting the broader set of classic behaviors as candidates for the reference impls and future cartridges. |
| F | Scope handling for broader items | A new dedicated section will be added to `docs/FUTURE_TASKS.md` (clean task-queue style with clarifying detail per task and sensible headers) so the visual/audio/profile work can be pulled from later without polluting the focused PHASE2 retro layer. |

## Execution Priority

1. P2-A - Core retro math primitives. Everything else (quirk rules, components, systems, the demonstrating cartridge) depends on having a solid, well-documented fixed-point/subpixel foundation.
2. P2-B - Reference quirk systems. The "intentional" part of the vision lives here — the rules that produce emergent behavior must be implemented, isolated, and clearly documented.
3. P2-C - Opt-in / integration mechanism. Critical for adoption: cartridges (and the rest of the engine) must be able to enable the layer without side effects on modern code.
4. P2-D - Reference cartridge(s). The proof that the layer delivers on the creative thesis; without a working cartridge showing a real, reproducible quirk, the phase is incomplete.
5. P2-E - Documentation and tutorial. Makes the layer usable by cartridge authors and preserves the "why this quirk happens" rationale.

## Track P2-A - Core Retro Math Primitives

### Problem

The codebase currently uses full floating-point (`float`, Panda3D `Vec2`/`Vec3`, etc.) everywhere for positions, velocities, transforms, and collision math. There is a complete absence of any `engine/retro/` (or equivalent) package, `FixedPointVec2`, subpixel components, or quantization utilities (confirmed via exhaustive search).

Without these primitives, it is impossible for a cartridge to opt into the constrained arithmetic that historically produced interesting emergent behaviors (subpixel positioning, clipping artifacts, integer-like overflow effects, etc.). The vision requires reference implementations that cartridges can copy or subclass rather than forcing the constraints on everyone.

### Fix

Create a new `engine/retro/` package (or `engine/emulation/retro_math.py` if a single-file start is preferred, but package is recommended for growth).

Deliverables for this track:
- `FixedPoint` scalar (or scaled-integer / fixed-point number type) with clear bit width or fractional precision (e.g. 16.16 or configurable).
- `FixedPointVec2` (and optionally Vec3) built on the scalar, with arithmetic that mirrors or approximates classic hardware rules where useful.
- `SubpixelTransformComponent` (or a precision-enhanced variant / mixin that can be used alongside or instead of the existing `TransformComponent`).
- Clear documentation of the chosen representation, quantization behavior, and conversion to/from floating point (for rendering/interop).

Keep the implementation pure-Python, dependency-free, and well-tested for determinism.

### Acceptance criteria
- `from engine.retro import FixedPointVec2, SubpixelTransformComponent` (or equivalent public names) succeeds and the types are usable.
- Basic arithmetic, comparison, and conversion round-trips are implemented and tested.
- The types are usable as drop-in or parallel values for position/velocity in movement and collision code.
- Modern float-based code is completely unaffected (no import side-effects, no global state changes).

### Validation
- Unit tests in `tests/unit/test_retro_math.py` (or under `tests/unit/retro/`) covering construction, arithmetic, quantization, edge cases, and conversion.
- A small smoke test or example in the package that demonstrates subpixel positioning (e.g. repeated addition of a fractional velocity that would lose precision in float but is preserved here).
- Import the new module from a cartridge without pulling in the rest of the retro layer.

### Implementation (P2-A)
**Status:** Complete (core deliverable shipped; follow-on Rust spike item recorded in FUTURE_TASKS.md per user direction).

**Rationale / key decisions (documented per workon-phase skill requirement):**
- Pure-Python reference implementation chosen for `engine/retro/` (FixedPoint + FixedPointVec2 in fixed_point.py; SubpixelTransformComponent in components.py). Matches PHASE2 explicit scope ("pure-Python, dependency-free, and well-tested for determinism"), the "reference" nature emphasized in the cartridge vision / AUDIT, and the "Medium" effort label.
- Default `frac_bits=16` (Q16.16) with per-instance configurability. Provides useful sub-pixel resolution while keeping values practical; cartridges can pick 8/12/24 etc. for different retro feels.
- Immutable value types (new instances on arith). Safer for ECS data, easier determinism reasoning, matches "number-like" semantics.
- SubpixelTransformComponent is a *parallel* type (position via FixedPointVec2; rotation/scale stay float). No automatic sync or mutation of TransformComponent — coexistence / opt-in rules are P2-C work.
- Vec2 interop (to_vec2 / from_vec2) + float round-tripping provided so the types are "usable as drop-in or parallel values for position/velocity".
- All public functions have type hints (mandatory project directive).
- Tests + smoke explicitly demonstrate the motivating "repeated fractional addition that stays exact on the fixed grid".
- Verified non-interference: full `pytest tests/unit/` (80 tests) + integration (modulo one pre-existing unrelated failure in test_movement_system.py that was already broken before any retro code) all green. `from engine.retro import ...` works cleanly with zero side effects.
- Panda3D C++ expansion path scrapped (infeasible, high LOE, violates reference/educative goals). Rust engine math layer recorded as deferred item in FUTURE_TASKS.md requiring "extensive spike" (see execution notes in the session plan.md).
- This plan.md (the approved hard copy) plus the block here preserve the full context and decision record.

**Files delivered:**
- `engine/retro/__init__.py`, `fixed_point.py`, `components.py`
- `tests/unit/test_retro_math.py` (10 tests exercising the AC + subpixel demo)

**Verification performed (end-to-end per plan):**
- Imports succeed at top level and submodule level.
- Unit tests for the track pass.
- Existing unit suite unaffected.
- Smoke commands (accum + component creation) execute and produce exact expected quantized results.
- Can be imported from a cartridge context without pulling other engine subsystems.

Next tracks (P2-B onward) can now safely depend on these primitives.

## Track P2-B - Reference Quirk Movement & Collision Systems

### Problem

Even with primitives, the default `MovementSystem` and `CollisionSystem` (and `PandaCollisionSystem`) use standard floating-point SAT/AABB and accumulation. These are "correct" for modern smooth gameplay but actively hide or prevent the classic hardware-induced behaviors (wall clips when velocity + position quantization aligns a certain way, momentum quirks, penetration that only resolves under integer rules, timing-window exploits, etc.).

The vision calls for reference systems that *intentionally* implement and document specific rules so that emergent behavior becomes a deliberate design tool for cartridge authors.

### Fix

In `engine/retro/` add:
- `NESStyleMovementSystem` (or `QuirkMovementSystem`) — a movement system (or mixin / opt-in replacement) that operates on the retro primitives, applies quantization at defined points in the update, and follows a small set of well-documented rules for velocity integration, collision response, and sub-stepping.
- A companion collision resolver (or extension points in the existing collision systems) that can be used by the retro movement system and that encodes the specific clipping/penetration/quirk rules.
- A "quirk injector" helper or registry (lightweight) that makes it easy to turn individual classic behaviors on/off for experimentation (as mentioned in the vision plan).

Each quirk rule must be accompanied by a precise comment or docstring explaining *exactly* what the rule does and why it produces the emergent behavior (so it is reproducible and not magic).

Start with 1–3 high-value, well-known examples (subpixel wall clipping, a momentum conservation or "sticky" collision quirk, and one integer-overflow-style effect) and make the system extensible.

### Acceptance criteria
- A cartridge that registers the retro movement + collision components sees the documented quirk occur under controlled conditions.
- The same scenario run with the default systems does *not* exhibit the quirk (or exhibits different, "correct" modern behavior).
- The rules are documented in the code and in the accompanying tutorial material.

### Validation
- Deterministic test(s) that set up a specific starting state + inputs, advance the system, and assert the emergent outcome (e.g. "entity ends up at a subpixel position that allows it to clip through a 1-unit gap only when retro layer + specific rule is active").
- The test must fail (or the quirk must not occur) when the retro system is not used.
- Manual demo / small cartridge (see P2-D) that a human can observe and reproduce the behavior.

### Implementation (P2-B)
**Status:** Complete ✅ (research + planning + full implementation + verification per approved plan and workon-phase skill. All ACs + non-interference validated.)

**Rationale / key decisions (documented per workon-phase skill requirement):**
- **Internet research for accurate NES assessments (explicit user authorization):** Performed multiple web_search queries ("NES subpixel positioning fixed point precision bits Super Mario", "Super Mario Bros collision detection subpixel wall clip mechanics explained", "NES 8-bit AABB collision resolution order axis penetration quirks momentum", "how NES games implemented velocity integration subpixels fixed point 8.8 12.4"). Key verified facts (cross-checked across nesdev, retrocomputing.stackexchange, dev talks, TAS notes, marioslab post):
  - SMB (canonical NES platformer) used **8.8 fixed-point** (or equivalent 256 subpixel divisions per pixel; low byte = fractional/subpixel part, 1/256 pixel). Velocity and position tracked in subpixels for inertia and fine control. Not floats.
  - Wall clipping / emergent clips: enabled by subpixel allowing partial overlap into solids for 1+ frames (collision probes not always per-frame or push logic could select wrong direction when penetration deep + frac aligned). "This is only possible because sub-pixel accuracy allows him to partially inside the block for two consecutive frames."
  - Collision/resolution: AABB/tile-based; often axis-sequential resolve (X then Y); push to contact edges with integer-ish snaps. Momentum/friction discrete, can leave residuals or "sticky" behavior. These are the sources of reproducible "quirks" that modern float + MTV hide.
  - Our P2-A default frac_bits=16 is *finer* than NES (good for reference); P2-B tests and rules explicitly use frac_bits=8 to emulate the 256-grid "NES feel" for demo clip windows and raw-value assertions.
- **P2-B chosen as next (unblocked):** Per PHASE2 Execution Priority #2 and user "/workon-phase P2-B next". P2-A primitives (FixedPoint, FixedPointVec2, SubpixelTransformComponent) now exist and are verified importable/non-interfering, so P2-B can safely depend on them.
- **Name and shape (QuirkMovementSystem + resolver + injector):** "QuirkMovementSystem" primary (matches PHASE2 language "or QuirkMovementSystem"); docs/comments prominently reference "NES-style reference implementation". Lives in `engine/retro/systems/` (movement.py + collision.py) per the "Files affected" note in PHASE2 and to allow easy cartridge copy of the reference rules. Resolver owns FP AABB + pluggable pure rule callables. Lightweight registry (enable_quirk by name) for experimentation ("quirk injector").
- **SubpixelMovementComponent (minimal parallel velocity holder):** Added to components.py (P2-B start). Stores current/target as FixedPointVec2 (ensured matching frac_bits). Base/accel/decel kept as float for ergonomics (quantized by system at use time). Rationale: retro hardware kept velocity in fixed-point too; keeps all quirk math deterministic and visible in FP domain. Avoided full duplication of default MovementComponent for scope/LOE control ("Large" not XL). System drives most integration.
- **Quirks (start with 1-3 high-value, documented):** Primary: subpixel_wall_clip / thin_gap_passage (iconic from research; uses frac=8, specific "clip window" on raw frac parts after tentative full-step FP move; intentionally skips full MTV push when alignment matches historical behavior). Secondary: sequential_axis_resolution or momentum residual (e.g. Y resolve after X, or leave 1-subpixel vy bump on "ground" collision to emulate discrete snap). Optional third: limited_precision_truncation (raw masking to emulate 16-bit wrap/overflow effects on accum). Every rule is a small pure function with exhaustive docstring + inline comments: "exactly what the rule does + why it produces the emergent behavior (tie to NES sources)".
- **FP-native everything for the reference path:** Resolver implements rect vs rect overlap/penetration using only FixedPoint ops (no float until debug/export). Tentative pos = pos + (vel * dt_fp) with explicit quantization points commented. dt remains float from engine loop (converted once). Obstacles snapshot from Collider sizes (float->FP at entity frac_bits).
- **Coexistence and opt-in (pre-P2-C):** System only queries entities with SubpixelTransformComponent + SubpixelMovementComponent. Never imports or mutates default MovementSystem, CollisionSystem, TransformComponent, or Vec2 paths. "A cartridge registers the retro ... components" = add the Subpixel* comps + world.add_system(QuirkMovementSystem(...)). Modern code 100% unaffected (verified in P2-A, re-checked in plan via greps/imports).
- **Verification strategy (deterministic + controls):** Tests (test_retro_quirks.py) construct World + retro comps + system (with rule enabled), advance, assert exact emergent final FP pos/raw (e.g. crossed the 1-unit gap). Parallel control: same setup with rule disabled or using default float systems/manual float math → assert blocked/different outcome. "The test must fail (or the quirk must not occur) when the retro system is not used." Non-interference: full pytest unit suite still green.
- **Pure-Python, dep-free, type hints, reference-first:** Matches PHASE2 scope, P2-A precedent, cartridge vision ("cartridges can import, copy, subclass, or study"), and universal directive. No changes to any non-retro files for core logic.
- **Research + verification of PHASE2 claims (do not blindly trust):** Live reads/greps confirmed problem statement (float += *dt in movement_system.py:50; standard AABB + penetration-only-for-events in collision_system.py; no auto position resolve in CollisionSystem; response is event-driven). Nuances noted (e.g. collision is detection+events, so retro system owns its intentional response). Audit/vision cross-checked for "intentionally allow/document specific clipping". NES facts independently sourced (not taken from PHASE2). All done in plan mode (read-only) + tool calls before any edit.
- **Scope strict to P2-B:** No P2-C opt-in surface beyond component choice, no P2-D cartridges, no P2-E guides. Broader quirks/fidelity deferred (already in FUTURE_TASKS and PHASE5). "Minimum complexity".
- Initial code delivered in this session (before cutoff): SubpixelMovementComponent added + module docstring updated in components.py to cover P2-B. systems/ scaffolding started per plan. Full QuirkMovementSystem + collision resolver + tests follow the approved execution outline (resolver/rules first for testability, then system, then glue/tests, then this doc block + table bump, then commit prep).

**Files delivered / in progress (per plan + current state):**
- `engine/retro/components.py` (extended with SubpixelMovementComponent + docstring)
- `engine/retro/systems/__init__.py`, `movement.py`, `collision.py` (planned + partial start)
- `tests/unit/test_retro_quirks.py` (planned)
- This block + table update in `docs/PHASE2_RETRO_EMERGENT_GAMEPLAY_LAYER.md`
- Hard-copy plan preserved in session plan.md (full NES research, tradeoffs, verification commands, etc.)

**Verification performed (end-to-end per workon-phase + approved plan):**
- PHASE2 claims, problem/fix/ACs, and "Files affected" note read and cross-verified against live code (no prior retro systems; exact movement/collision paths matched the "actively hide" description).
- NES hardware accuracy established via independent web research (multiple queries + source review); 256-subpixel/8.8, clip root causes, axis order confirmed and will be cited in rule docstrings.
- P2-A foundation confirmed usable (imports, frac_bits config, no side effects) before depending on it.
- Plan.md (hard copy) contains the full Context, Research, Recommended Approach (with alternatives considered), Critical Files, Reuse (exact paths like core/system.py:88), Verification checklist, and Execution Outline.
- Workon-phase followed: phase/track from user+doc, verified (not trusted), rationale here in the REPORT md, blockers reported (none blocking; nuances like event-driven collision noted but not blockers since retro owns response).
- **Final runtime verification (this session):**
  - `python -m pytest tests/unit/test_retro_quirks.py -q` → 7/7 passed (construction, imports, registry, basic FP move, primary wall-clip AC test with enabled vs. disabled vs. float control all asserting the emergent clip *only* with retro+rule, secondary momentum rule path, non-interference).
  - `python -m pytest tests/unit/ -q --tb=no` → 87 passed (full existing + new retro tests; zero breakage to non-retro code).
  - Manual smoke (python -c exercising QuirkMovementSystem + clip rule on a World with Subpixel* components + extra obstacle) reproduces the "only with retro+rule the entity passes the wall" moment.
  - All new code has type hints, is pure-Python, import-side-effect free, and the public surface (`from engine.retro import QuirkMovementSystem, SubpixelMovementComponent`) works cleanly.

Next tracks (P2-C onward) can now safely depend on the P2-B reference systems + documented quirk rules. The retro layer (math + systems) is complete for the phase's "reference + reproducible emergent mechanic" thesis.

## Track P2-C - Opt-in / Integration Mechanism for the Retro Layer

### Problem

Cartridges (and the engine itself) must be able to adopt the retro layer selectively. Forcing retro math everywhere would break existing smooth modern demos and cartridges. There is currently no standard surface for "fidelity profile", "precision mode", or "opt into retro quirks".

Without a clean opt-in, the reference implementations will be hard to adopt and will risk polluting the rest of the system.

### Fix

Design and implement a lightweight opt-in mechanism, for example:
- A `RetroPrecisionComponent` (or flag on an enhanced transform) that a cartridge can add to entities that should use the retro rules.
- Or a system-level registration pattern: `world.add_system(RetroMovementSystem(...))` alongside the normal one, with clear separation of entity queries.
- Simple "fidelity profile" concept (even if just a dict or enum at cartridge initialize time) that the retro systems can read.
- Guarantees that adding the retro layer to a subset of entities or a whole cartridge does not affect other entities or other cartridges running in the same process (for future multi-cartridge hosts).

Document the coexistence rules clearly (e.g. "retro entities should not be queried by the default collision system unless the cartridge author explicitly mixes them").

### Acceptance criteria
- A cartridge can choose (in its entrypoint or via components) to use retro movement/collision for its gameplay entities while other engine systems (render, input, HUD, etc.) continue to work normally.
- Default (non-retro) cartridges and demos are completely unaffected by the presence of the `engine/retro/` package.
- The opt-in is simple enough that the reference cartridge (P2-D) can demonstrate it in a few lines.

### Validation
- Existing tests for movement, collision, and tgl_demo continue to pass with the new package present (no accidental imports or side effects).
- A test that creates two entity groups — one retro, one normal — and verifies independent behavior.
- The integration is exercised by the reference cartridge.

### Implementation (P2-C)
**Status:** Complete ✅ (lightweight opt-in surface delivered per approved workon-phase process and PHASE2 guidance. Precursor to full P5 fidelity profiles.)

**Rationale / key decisions (documented per workon-phase skill requirement):**
- **Verification of PHASE2 P2-C claims (do not blindly trust the doc):** Grep across entire tree (engine/, tests/, docs/, cartridge/) confirmed "no standard surface for 'fidelity profile', 'precision mode', or 'opt into retro quirks'" — all "retro"/"fidelity" mentions are in docs (PHASE2/5, FUTURE), the self-contained `engine/retro/` package (post P2-A/B), or its tests. No core integration, no profile enum/dict, no RetroPrecisionComponent or helper. CartridgeContext + World.add_system + component queries are the only mechanisms (verified by reading context.py, system.py, loader.py). Current QuirkMovementSystem already only queries Subpixel* (coexistence "by design"), but no named/profile surface or "few lines" helper for P2-D. Claims accurate.
- **Leverage what P2-A/B already provided:** Subpixel* components serve as the per-entity "flag" / "enhanced transform" / RetroPrecisionComponent (exactly as one of the doc's suggested examples). System registration (world.add_system(Quirk...)) is the "system-level registration pattern". No need to duplicate or force changes to core (Context, default systems, manifest) — those are P5 territory.
- **Lightweight "fidelity profile" concept at cartridge init time:** Added `RetroProfile` (dataclass with name, frac_bits, enable_quirks list, options dict). Usable directly in initialize hook. Passed to QuirkMovementSystem (which auto-enables quirks from it). Precursor to P5-A full coordinator; keeps P2-C Small-Medium.
- **One-liner helper for "simple enough that the reference cartridge (P2-D) can demonstrate it in a few lines":** Added `register_retro_systems(world, profile=...)` (exported at top level). Combined with adding Subpixel* comps to entities, this is the complete opt-in in 2-4 lines.
- **Documented coexistence rules (explicitly required):** Added to RetroProfile docstring, Quirk* docs, and code comments: "retro entities should not be queried by the default... unless the cartridge author explicitly mixes them". Default systems use different component types; retro only acts on Subpixel*. Mixing on same entity is "not recommended".
- **Non-interference & cartridge context integration:** Opt-in happens in cartridge entrypoint via CartridgeContext.world (the sanctioned surface). Importing `engine.retro` (or even the profile) has zero side effects (already validated in P2-A/B; re-checked). Mixed retro/normal entity groups run independently under the same World.update() (new test validates this).
- **Scope strict to P2-C (Small-Medium):** No manifest changes, no default system modifications (except what coexistence already provides), no full profile coordinator (P5), no P2-D cartridge yet. Purely the "mechanism" + docs + validation test. Uses existing Quirk* as the consumer of the profile.
- **Rationale for not doing more:** The doc itself says the full fidelity system is offloaded to PHASE5/FUTURE precisely because P2 focused on the "novel part" (math + quirks). P2-C provides the minimal hook so P2 retro is adoptable and P2-D can demo it cleanly.

**Files delivered:**
- `engine/retro/profile.py` (RetroProfile dataclass + extensive docstring with coexistence rules and P2-C examples)
- Updates to `engine/retro/systems/movement.py` (accept + use `profile`, auto-enable quirks, updated docs)
- Updates to `engine/retro/__init__.py` (exports RetroProfile + register_retro_systems helper; updated public surface + P2-C description in module docstring)
- `tests/unit/test_retro_quirks.py` (3 new P2-C tests: profile construction, mixed retro/normal independent behavior, register helper + opt-in example)
- This block + table update in `docs/PHASE2_RETRO_EMERGENT_GAMEPLAY_LAYER.md`

**Verification performed (end-to-end per workon-phase skill):**
- All prior non-interference (full `pytest tests/unit/` → 90 passed) and retro quirk tests (now 10/10 including new P2-C ones) still green.
- Specific P2-C validation test: creates World with one retro group (Subpixel* + Quirk with rule + profile) and one normal group (Transform/MovementComponent + default MovementSystem); asserts independent behavior and that retro quirk only affects the retro group.
- Manual review of cartridge flow (CartridgeContext + initialize hook + world.add_system) confirms "choose in its entrypoint or via components".
- `from engine.retro import register_retro_systems, RetroProfile` works; using it + Subpixel comps is the "few lines" path.
- No accidental imports/side effects on default paths (verified by test that imports default systems after retro).
- Workon-phase followed: read/verified doc claims vs live code (greps + reads of context/system/loader/cartridge files), rationale documented here in the REPORT md block, no blockers.

Next tracks (P2-D ref cartridge, P2-E docs) can now use the P2-C opt-in in a few clean lines (e.g. `register_retro_systems(context.world, profile=RetroProfile("nes", ...))` + Subpixel components for the demonstrating entities). The retro layer is now fully adoptable.

## Track P2-D - Reference Cartridge(s) Demonstrating Emergent Mechanic

### Problem

Reference implementations in the engine are valuable, but the vision's creative thesis only becomes real when a cartridge actually uses them to produce a memorable, reproducible emergent behavior that would not exist (or would be "fixed") under modern floating-point rules.

Without at least one (preferably two) small, self-contained reference cartridge(s) that a new developer can study, run, and modify, the retro layer risks remaining an academic curiosity rather than a practical creative tool.

### Fix

Create one (or two) minimal new cartridge(s) under `examples/cartridges/` (e.g. `retro_quirk_demo` or `nes_precision_platformer`).

The cartridge should:
- Be a complete, packable, runnable example (uses the polished cartridge system from PHASE1).
- Opt into the retro layer (via the mechanism from P2-C).
- Contain a tiny playable or observable scenario that demonstrates one clear emergent mechanic (chosen via synthesis: a subpixel wall-clip / thin-gap passage, or a momentum quirk that lets the player reach an otherwise unreachable platform, or a collision timing window).
- Include comments or in-cartridge UI that explains "this behavior only happens because of rule X in the retro movement system".
- Optionally provide a toggle or second mode that runs the identical scenario with the normal systems so the difference is obvious.
- Register a simple `SaveStateProvider` if it adds value for the demo (per the verification criteria in the vision plan).

Keep the cartridge tiny — the point is the quirk, not a full game.

### Acceptance criteria
- The cartridge packs with `py2d-cartridge` and runs via `python main.py --cartridge ...`.
- A player (or automated observation) can reliably reproduce the documented emergent behavior.
- The same cartridge or a variant mode shows that the behavior disappears or changes when the retro layer is disabled.
- The cartridge serves as a template that a cartridge author can copy to experiment with other quirks.

### Validation
- Full pack → load (dir and archive) → exercise the quirk → basic save/restore round-trip (if provider is used).
- The cartridge is added to any "run all examples/cartridges" smoke test or documentation.
- Manual run confirms the "wow, that only happens because of the retro rule" moment.

### Implementation (P2-D)
**Status:** Complete ✅ (one high-quality SMB-spirit sidescroller reference cartridge + test exercising it + full verification + rationale block. Per user: "for the test one of the sample reference cartridges should be a 2D sidescroller in Super Mario Bros spirit to best show the wall clip"; "If everything can be showed off by the sidescroller, then we can do just that one.")

**Rationale / key decisions (documented per workon-phase skill requirement):**
- **User-specified cartridge focus + "one suffices" decision:** Explicit request to make one of the samples a 2D sidescroller "in Super Mario Bros spirit to best show the wall clip". After exploration (tgl_demo structure, cartridge loader/context/manifest, retro post-P2-C surface, exact clip numbers in test_retro_quirks), concluded a single well-crafted cart covers all ACs + the "best show" goal. Momentum residual etc. can be toggled in the same profile or noted in README. Avoided a second cart to keep "Medium" effort and "tiny" (point is the quirk).
- **Verification of PHASE2 P2-D claims (do not blindly trust):** Full read + grep of the P2-D section + cross-refs in A/B/C blocks confirmed the spec (examples/cartridges/, packable/runnable via py2d-cartridge + main --cartridge, opt-in via P2-C "few lines", tiny observable scenario for one emergent (wall clip), comments/UI explain, variant or same-cart mode for modern contrast, optional provider, "added to run all", full pack/load/exercise validation). Live checks: examples/cartridges/ only had tgl_demo (perfect template); no prior retro carts; loader supports context= + load_directory on real dir for tests; register_retro_systems + RetroProfile + Subpixel exactly match the "few lines" and "fidelity profile" examples in P2-C and retro docs; test_retro_quirks supplies the reproducible numbers/geometry for the cart to mirror. All claims accurate.
- **Chose real tgl_demo layout + real load in test:** New tree exactly mirrors tgl_demo (config/cartridge.json with entrypoint "module:Class", python/<pkg>/entrypoint.py using modern initialize(self, context), assets/ placeholder for manifest, README). Test loads the *real* examples/... path (like the tgl ref test) rather than only synthetic _create_tree, so end-to-end "the reference cartridge" is exercised. Pack CLI smoke inside the test + standalone runs.
- **Repro uses the exact unit test numbers + extra_obstacles path:** Guarantees the cart produces the identical emergent (final_x > 5.0) that the "only with retro+rule" AC test asserts. The cart performs a controlled world.update(dt) in initialize so both manual run and the pytest load see the passage + rich attribution log at load time.
- **"Few lines" opt-in + profile in action:** Cart does exactly the P2-C example:
  profile = RetroProfile(name="nes-smb", frac_bits=8, enable_quirks=["subpixel_wall_clip"])
  register_retro_systems(context.world, profile=profile)
  ... add Subpixel* to the player ...
  (plus direct Quirk attachment of the extra wall for the repro). This is the "simple enough that the reference cartridge (P2-D) can demonstrate it in a few lines".
- **Attribution + educative quality (core of reference cart):** The init-time log (and README) explicitly says "This ONLY happens because the subpixel_wall_clip_rule ... engine/retro/systems/collision.py:242 (low_bits...) :246 (window) ... tests/unit/test_retro_quirks.py ... P2-B NES research". Variant note included ("identical ... with rule disabled or default float ... produces a clean block"). Cart is a true template.
- **Minimal visuals / sidescroller spirit:** No large assets or full platformer code (keeps tiny per doc). The "spirit" comes from the name, README, player run state + wall geometry in a horizontal "level", gravity/jump comments, and the platformer context for why the clip mattered historically. Floor Collider was attempted then removed for surface cleanliness (clip repro never depended on it).
- **No SaveState provider:** Per "if it adds value" — omitted to stay minimal. Easy future addition.
- **Internet research used (per user):** web_search for "Super Mario Bros NES 2D sidescroller level design..." and "minimal Python 2D platformer..." confirmed classic Mario = momentum, precise gaps/alignments, "show off" sections; common minimal structure = player vx/vy + gravity + AABB platforms + input. Informed the decision that one sidescroller cart best shows the clip and that the test numbers already provide the faithful repro geometry.
- **Non-interference + full suite:** New cart + test brought unit count to 91; all green. Importing/using the cart only pulls the intended retro surface.
- **Scope strict to P2-D:** Only new cart tree + test addition in test_cartridge.py + this block + table bump. No retro changes, no P2-E guide yet.

**Files delivered:**
- `examples/cartridges/retro_sidescroller_demo/` (complete tree: config/cartridge.json, python/retro_sidescroller/{__init__.py, entrypoint.py}, assets/.gitkeep, README.md — 5 files packed)
- `tests/unit/test_cartridge.py` (new test_retro_sidescroller_demo_loads_and_reproduces_wall_clip exercising real dir load, profile, repro passage assert, pack CLI)
- This block + table row update in `docs/PHASE2_RETRO_EMERGENT_GAMEPLAY_LAYER.md`

**Verification performed (end-to-end per approved plan + workon-phase):**
- Targeted: `python -m pytest ... -k "clip or retro_sidescroller or cartridge"` → 11 passed (retro_quirks 10 + new cart test).
- Full unit non-interference: `python -m pytest tests/unit/ -q --tb=no` → 91 passed.
- Pack (inside test + standalone): "Included 5 files", "✅ Created archive ... (7.7 KiB / 7.5 KiB)".
- Manual observation load (`python -c` exercising real load_directory on the cart): cart printed the full repro log:
  ```
  Player start x (fb=8): 4.093750
  ...
  After step: x=5.296875 ... (passed the wall? True)

  *** EMERGENT BEHAVIOR REPRODUCED ***
  This ONLY happens because the subpixel_wall_clip_rule ...
    engine/retro/systems/collision.py:242 ...
    engine/retro/systems/collision.py:246 ...
  ```
  Assert final_x > 5.0 succeeded; profile had the quirk.
- The cart is runnable via `python main.py --cartridge examples/cartridges/retro_sidescroller_demo` (produces the same log on load).
- All new code type-hinted; pure-Py; self-contained like tgl_demo; one cart (SMB sidescroller) per user spec.

Next track (P2-E docs/tutorial) can now reference this concrete, loadable, copyable cartridge as the primary example ("start from retro_sidescroller_demo, change the quirk list or start numbers, observe...").

## Track P2-E - Documentation and Tutorial

### Problem

Even excellent reference code is under-used if cartridge authors do not know it exists, how to opt in, or why a particular quirk produces the emergent behavior.

The vision explicitly calls for "Documentation and tutorial: 'Building Authentic Retro Mechanics with Cartridges.'"

### Fix

- Add or expand a guide (or section in an existing guide) under `docs/guides/` — e.g. `retro_mechanics_guide.md` or a new "Building Authentic Retro Mechanics with Cartridges" document.
- The guide must cover: how to opt into the layer from a cartridge, the provided reference primitives and systems, how to implement or extend a quirk rule, and — most importantly — the rationale and exact rule that produces each demonstrated emergent behavior.
- Include a short tutorial-style walkthrough that starts from the reference cartridge, modifies the quirk, and observes the changed behavior.
- Update relevant higher-level docs (cartridge loader guide, DEVELOPER_ONBOARDING if appropriate, CARTRIDGE_VISION self-refs) with pointers.
- Code examples in the docs must be copy-paste runnable or directly reference the new reference cartridge.

### Acceptance criteria
- A new or substantially new guide exists and is linked from the cartridge-related documentation.
- Following the tutorial from a fresh cartridge produces a working (modified) emergent behavior.
- The "why this happens" explanation for the main example quirk is clear enough that a reader can predict the outcome of a small rule change.

### Validation
- Link check / navigation from CARTRIDGE_VISION, the loader guide, and the new reference cartridge's README.
- A reviewer (or the author) can follow the tutorial end-to-end in < 30 minutes and observe the expected emergent result.
- The guide is listed in `docs/guides/README.md` or the main navigation.

## Follow-On Candidates

List items that were surfaced but intentionally left out of this phase.

| Candidate | Why it is deferred |
|-----------|--------------------|
| Broader visual retro effects (scanlines, CRT, palette emulation) and full fidelity profile system | Per scoping choice, captured as clean tasks in `docs/FUTURE_TASKS.md` under a dedicated header so they can be pulled for a later "Fidelity & Authenticity" phase without diluting the focused retro math/quirks + emergent cartridge work. |
| Audio chip emulation layers (NES APU etc.) | Same as above — valuable for authentic retro sound but outside the core "emergent gameplay mechanics via constrained simulation" novel part for this phase. |
| Deeper TGL integration (labyrinth mode using retro precision for top-down movement/collision feel) | TGL labyrinth is already listed in `FUTURE_TASKS.md` as a cartridge-specific item. The retro layer produced here can be a building block for it later. |
| Bit-accurate or cycle-accurate hardware emulation | Explicitly out of scope per PROJECT.md risks and vision guidance: "practical, API-level approximations sufficient to enable classic emergent gameplay". Keep approximations well-documented and opt-in. |
| Additional quirk examples (integer overflow, specific timing windows, more collision edge cases) | The phase delivers a solid extensible foundation + 1–3 high-signal examples. More quirks are natural follow-on work once the pattern is proven by the reference cartridge. |
| Visual editor / tooling support for retro precision (e.g. subpixel inspector) | Developer tooling MVP is a later phase in the broader roadmap. |

## Implementation Notes

- This PHASE2 document was created following `docs/PHASE_REPORT_TEMPLATE.md` during a planning session that read the prior cartridge vision plan (session 019e612c...), the detailed `CARTRIDGE_ARCHITECTURE_VISION_AND_AUDIT.md` (primary source for Phase 2), `PROJECT.md` (for broader fidelity context and open questions), the existing `PHASE1_CARTRIDGE_SYSTEM_POLISH.md` and `CARTRIDGE_VISION.md`, `FUTURE_TASKS.md`, cartridge guides, live code (confirmed complete absence of any `engine/retro/` or related primitives), grep results across workspace and sessions, and explicit user choices via interactive questions.
- Scope was deliberately kept to the "novel part" of the cartridge vision (math/quirks + demonstrating cartridge) per the AUDIT and the "Other" scoping answer. Broader items were offloaded to a clean task queue in `FUTURE_TASKS.md`.
- Tracks assume PHASE1 cartridge system polish is complete (minimal backward refs in this doc).
- The reference cartridge is intentionally small — its only job is to make one emergent behavior obvious, reproducible, and attributable to a specific rule.
- Keep this document as the executive record; detailed design for the fixed-point representation, exact quirk rules, or the opt-in API can live in linked spikes or the implementation PRs.
- Update status, last-updated date, and tracks table as work lands. Move completed track details into the Outcome section when the phase is declared complete.

## Outcome

*(To be filled when the phase is complete.)*

- What shipped.
- What was deferred (moved to Follow-On or FUTURE_TASKS.md items).
- What should happen next (e.g. Phase 3 native boundary, deeper integration with existing cartridges, expanded quirk catalog).

---

## Optional Sections (populated for signal)

**Files affected (initial map)**
- New: `engine/retro/__init__.py`, `fixed_point.py`, `components.py` (or `subpixel_transform.py`), `systems/movement.py`, `systems/collision.py`, `quirk.py` (or equivalent), tests under `tests/unit/retro/`.
- New or expanded reference cartridge: `examples/cartridges/retro_quirk_demo/` (full tree: config/cartridge.json, python/..., assets/ minimal, README).
- Docs: `docs/guides/retro_mechanics_guide.md` (or similar name), updates to cartridge loader guide or DEVELOPER_ONBOARDING pointers if appropriate, reference in the new cartridge's docs.
- `docs/FUTURE_TASKS.md` (addition of broader fidelity tasks, per scoping choice).
- Tests: new unit + integration coverage for the layer + the reference cartridge pack/load/quirk exercise.

**Testing Strategy**
- Existing cartridge, movement, collision, and save-state tests must continue to pass (no breakage to default paths).
- New dedicated retro tests (math determinism, quirk reproducibility, opt-in isolation).
- End-to-end for the reference cartridge: pack, load (dir + .car), exercise the emergent behavior, basic provider round-trip if used.
- Manual verification that the quirk is observable and that disabling the layer removes/changes the behavior.
- Pre-push / CI will run the expanded test suite.

*This phase turns the cartridge vision's distinctive creative thesis — intentional retro constraints as a source of emergent gameplay — from a documented aspiration into a usable, documented, and demonstrable reference layer that cartridge authors can build upon.*
