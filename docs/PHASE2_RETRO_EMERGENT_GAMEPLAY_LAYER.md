# Phase 2 - Retro Emergent Gameplay Layer

**Status:** Planned  
**Created:** 2026-06  
**Last updated:** 2026-06 (initial draft from vision extraction + user choices)

### Tracks

| Track | Description | Status | Effort |
|-------|-------------|--------|--------|
| P2-A | Core retro math primitives (`engine/retro/` package: fixed-point arithmetic, `FixedPointVec2`, `SubpixelTransformComponent` or equivalent precision-aware components) | Planned | Medium |
| P2-B | Reference quirk movement and collision systems (e.g. `NESStyleMovementSystem` or `QuirkMovementSystem` + collision resolver that intentionally applies and documents specific clipping/penetration/quirk rules) | Planned | Large |
| P2-C | Opt-in / integration mechanism for the retro layer (fidelity profile hook, component/system flags, clean coexistence with default float/Vec2 paths so modern cartridges are unaffected) | Planned | Small-Medium |
| P2-D | One or two small reference cartridges demonstrating a reproducible emergent mechanic (e.g. subpixel-enabled wall clip, momentum quirk, or documented classic glitch that only appears when the layer is active) | Planned | Medium |
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
