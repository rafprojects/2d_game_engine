# Phase 5 - Fidelity Profiles, Retro Authenticity & Production Ecosystem Readiness

**Status:** Planned  
**Created:** 2026-06  
**Last updated:** 2026-06 (initial draft from vision extraction + user choices)

### Tracks

| Track | Description | Status | Effort |
|-------|-------------|--------|--------|
| P5-A | Core "Fidelity Profile" coordinator system (selectable profiles as first-class objects/enums/dicts; cartridge-scoped at minimum with per-entity/system overrides; manifest + entrypoint declaration + runtime switch support; coordinates retro math (P2), visual effects, audio emulation, and simulation rules to target baselines like "NES/8-bit", "Modern Smooth", "Arcade"; opt-in everywhere; "every new engine feature must be cartridge-usable" principle surface) | Planned | Medium-Large |
| P5-B | Visual retro effects implementation (initial shader-based or post-process scanlines, CRT curvature/distortion, palette emulation / limited color quantization; delivered as optional render passes or compositing layer; intensity/scanline count/curvature/palette controls; strictly optional — default RenderSystem / modern smooth path must be 100% unaffected) | Planned | Medium |
| P5-C | Audio chip emulation layers (starting with NES APU-style square/pulse waves, noise, triangle; later SNES SPC etc.; integrate with existing AudioSystem / MusicSystem / NSF player; cartridges that opt in get emulated voices while others continue with samples/MIDI/NSF; small practical API (frequency, duty, volume, envelope); API-level not cycle-accurate) | Planned | Medium |
| P5-D | Retro layer expansion + profile integration (add well-documented practical approximations for integer overflow effects, specific collision quirks, timing-window behaviors, and other classic console "features"; each with reproducible test/demo scenario + exact rule description in code/docs; opt-in path exclusively via fidelity profile or explicit component/system flag; does not affect non-retro entities/cartridges) | Planned | Small-Medium |
| P5-E | Native packaging, distribution, richer FFI surfaces & initial security sketch (extend `py2d-cartridge` / cartridge_pack + build story for first-class native artifacts: discover/validate/include .so/.dylib/.dll (and platform subdirs) in .car; optional build hooks + conventional `native/` layout; manifest `native`/`build` section growth; ABI compatibility matrix + engine version enforcement for native plugins; post-v1 richer FFI surfaces (native events on bus, native SaveStateProvider, controlled core component access via handles, native system update callbacks); initial security/provenance/sandboxing model sketch (signing, hash verification, capability restrictions, process isolation notes)) | Planned | Medium-Large |
| P5-F | Documentation, "cartridge-usable" principle, production packaging example & validation (update cartridge_loader_guide + new/expanded guides for profiles + native packaging; explicit "every new engine feature must be usable from a cartridge without engine modification" checklist + examples; minimal production packaging example (or note in host context) demonstrating native bundle + profile-declaring cartridge; validation track exercising full profiles + packaging on tgl_demo (or dedicated ref cartridge) including the TGL ZIP packaging item as a concrete consumer; initial security notes in docs) | Planned | Small |

---

## Rationale

Briefly explain why this phase exists now.

1. After Phase 4 (Isolation & Multi-Cartridge Host Readiness) the architecture has a clean load/unload seam and a proven secondary "host" mental model. The two largest bodies of work that were deliberately offloaded from earlier focused phases (P2 retro math layer and P3 narrow native boundary) are now the highest-leverage remaining surfaces for the original vision: deliberate creative constraints (fidelity profiles + retro authenticity) and production/ecosystem readiness (native packaging + richer FFI + initial security thinking). The AUDIT explicitly calls out the "Ongoing Principles" bucket ("Every new engine feature ... must be usable from a cartridge without engine modification") as the perpetual north star; formalizing the coordinator (profiles) + effects + packaging makes that principle concrete and enforceable rather than aspirational.

2. These items belong together as one phase because they form the "authenticity + production ecosystem" slice: the Fidelity Profile system is the unifying coordinator that makes P2's retro layer, visual effects, and audio emulation first-class and cartridge-declarable; the packaging + richer FFI + security sketch complete the native story that began with P3's narrow v1 boundary; the docs + validation + "cartridge-usable" enforcement close the loop so the principle is not just stated but demonstrated (including a concrete TGL packaging consumer and a ref cartridge exercising profiles end-to-end). Bundling them prevents the offloaded FUTURE items from languishing as an ever-growing queue.

3. Success looks like: a cartridge (or manifest) can declare a default fidelity profile ("NES/8-bit"); the profile activates coordinated retro math (P2 layer), optional scanline/CRT/palette post-effects, and emulated APU voices with a single switch; a second cartridge can stay on "Modern Smooth" with zero impact on its rendering/audio/math; native artifacts declared in a cartridge are automatically discovered, bundled by `py2d-cartridge`, validated at pack time, and loaded with ABI/engine-version checks at runtime; an initial security model sketch (signing, capabilities) exists as a documented starting point; a minimal production packaging example (or host-context smoke) succeeds; tgl_demo (or a dedicated ref cartridge) can be packaged with its assets + any native bits and run under a profile with observable retro effects; the "every new feature cartridge-usable" principle has a living checklist and at least one enforcement example in the tree; all prior single-cartridge and host flows remain unaffected.

## Key Decisions

| # | Decision | Resolution |
|---|----------|------------|
| A | Filename / title for the tracking doc | `PHASE5_FIDELITY_RETRO_PRODUCTION.md` / "Phase 5 - Fidelity Profiles, Retro Authenticity & Production Ecosystem Readiness" (user-specified exact string; synthesizes the two main FUTURE offload sections + AUDIT Ongoing into the post-P4 phase). |
| B | Scope for PHASE5 | "Broader: Include TGL-specific packaging + some ecosystem examples (e.g. a ref cartridge exercising full profiles) as a validation track, plus initial security model sketch." Primary content synthesizes directly from the two FUTURE subsections (Fidelity Profiles & Retro Authenticity from P2 planning + Native Plugin Boundary & FFI Readiness richer/packaging items from P3 planning) + AUDIT Ongoing principle. A clean validation track (P5-F) pulls the TGL ZIP packaging item (#10) as a concrete consumer and exercises a profile-declaring ref cartridge (or tgl_demo) + minimal production packaging example in host context. Initial security sketch is included (in P5-E or P5-F). Deeper items (full security/sandbox implementation, bit/cycle-accurate emulation, full concurrent multi-cartridge composition, advanced host UX) are offloaded or left in FUTURE. The two FUTURE subsections are deleted after formalization to keep the queue clean. |
| C | Representation of prior phases | "Assume complete + minimal backward refs (like PHASE4 and PHASE2 precedent)". Short rationale names P1–P4 at high level only for direct dependencies (P2 retro layer becomes one dimension of profiles; P3 narrow boundary + P4 unload/isolation are prerequisites for richer FFI + safe native packaging). The doc stays focused on new fidelity + ecosystem work. |
| D | Vision reference / cross-linking | "Leave CARTRIDGE_VISION as-is for now (its 'Phase 4+' language + AUDIT link is sufficient; PHASE5 doc self-references AUDIT)". Consistent with P1–P4 choices. Pointer update (to mention Phase 5 or Phase 5+) can be a cheap follow-on or part of later Outcome work. |
| E | Track synthesis, bundling, validation artifact & TGL handling | "Synthesize directly from the two FUTURE subsections + AUDIT Ongoing into 5-6 tracks (core Fidelity Profile coordinator as P5-A or central; separate or combined visual effects + audio emulation tracks; expand retro quirks track; native packaging + richer FFI tracks; docs + 'cartridge-usable' enforcement/validation). Include a minimal 'production packaging example' or note in host context. Keep TGL items in FUTURE unless they fit a clean validation track." Exact 6-track structure chosen: P5-A (coordinator central), P5-B (visual), P5-C (audio), P5-D (retro expansion + integration), P5-E (native pack + richer FFI + initial security sketch), P5-F (docs + cartridge-usable + production packaging example + validation with TGL packaging + ecosystem ref cartridge profile exercise). TGL items stay in FUTURE except the packaging item lightly surfaced in the P5-F validation track. |

## Execution Priority

1. P5-A - Core Fidelity Profile coordinator. Everything else (visual effects, audio, retro expansion, integration points, manifest/entrypoint support, "cartridge-usable" surface) depends on having a working, selectable, cartridge-scoped profile mechanism first.

2. P5-B - Visual retro effects. High user-visible authenticity payoff; can be developed against the coordinator once P5-A exists.

3. P5-C - Audio chip emulation. Pairs naturally with visual effects for "NES/8-bit" profile demonstrations; integrates with existing audio systems.

4. P5-D - Retro layer expansion + profile integration. Completes the creative constraint story started in P2; each added quirk must ship with test/demo + documentation + profile opt-in.

5. P5-E - Native packaging + distribution + richer FFI + initial security sketch. Completes the production side of the native story (P3 v1 + P4 isolation); packaging must work before richer FFI surfaces see heavy use; security sketch provides the starting point for ecosystem concerns.

6. P5-F - Documentation, cartridge-usable principle, production packaging example & validation. Makes the phase usable and the ongoing principle real (checklist + examples + concrete tgl/ref cartridge packaging + profile exercise smoke). Closes the phase.

## Track P5-A - Core Fidelity Profile Coordinator System

### Problem

The cartridge vision's novel creative thesis ("deliberately opt into constrained simulation rules ... that produce emergent 'NES-style' gameplay side-effects") and the AUDIT's Ongoing principle both require a unifying, cartridge-author-friendly mechanism to select and activate coordinated behaviors across math precision, rendering style, audio, and simulation rules.

After P2 delivered the core retro math/quirk reference layer (`engine/retro/`), there is still no standard "fidelity profile", "precision mode", or "opt-in" surface. Cartridges have no declarative way (manifest or entrypoint) to say "run me under NES/8-bit rules + visuals + sound." Visual effects, audio emulation, and additional glitches were explicitly scoped out of P2 (and captured in FUTURE) precisely because the coordinator did not exist yet.

Without the profile system, retro math remains an isolated curiosity, effects and audio emulation have no consistent activation story, and the "every new engine feature must be cartridge-usable" principle has no hook to hang on.

### Fix

Design and implement a small, first-class `FidelityProfile` (or `engine/fidelity/` package) concept:

- Profiles are selectable configuration objects / enums / simple dicts (or a small dataclass with well-known keys + extension points).
- Core dimensions at minimum: math precision (reference to P2 retro layer), visual style (effects pass/compositing), audio (chip emulation voices), simulation rules (quirk injector flags).
- Cartridge-scoped at minimum; possible per-entity or per-system overrides where it makes sense.
- Declarative surface: cartridge manifest can declare a default profile; entrypoint / `initialize` (via CartridgeContext) can set or switch it; runtime switch API for cartridges that want dynamic mode changes (e.g. TGL corridor vs. labyrinth).
- Opt-in contract: all participating systems/components read the active profile (or a derived "precision mode" / "effects enabled" flag) and degrade gracefully when absent (default = modern smooth / full float / no effects).
- The retro math layer from P2 participates as one explicit dimension.
- New engine features (systems, components, render passes, audio voices) are required to be profile-aware or at minimum profile-neutral from day one (enforcement via the P5-F checklist and review).

Update `CartridgeManifest` + schema lightly if needed for the declarative default. Wire the active profile into World / a small FidelityManager or via the existing event bus so interested systems can react.

### Acceptance criteria

- `from engine.fidelity import FidelityProfile` (or equivalent) succeeds; at least the canonical baselines ("NES/8-bit", "Modern Smooth", "Arcade") are defined or constructible.
- A cartridge can declare a default profile in its manifest or set it in `initialize`; the profile is observable by participating systems (retro math, a visual effect pass, an audio voice).
- Switching profiles at runtime (or per-cartridge) changes behavior for new entities/effects without affecting unrelated cartridges or the default engine path.
- The P2 retro layer is documented as participating in profiles; new quirks added in P5-D are only active under appropriate profiles.
- Pure modern cartridges (no profile declaration) continue to behave exactly as before.

### Validation

- Unit tests for profile selection, scoping, override, and default-neutral behavior.
- A minimal integration smoke: load a cartridge declaring "NES/8-bit", assert profile active, exercise one retro math path + one effect + one audio voice (or stubs), then load/switch to a second cartridge with no profile or "Modern Smooth" and confirm isolation.
- Manual: run tgl_demo (or ref cartridge) under a profile; observe coordinated changes (or documented stubs); confirm no visual/audio/math side-effects when profile is absent.
- Existing tests (cartridge, retro if any, audio, render) continue to pass with zero behavior change for non-profile users.
- The profile object (or a narrow view) is usable as a target for future native FFI (P5-E).

## Track P5-B - Visual Retro Effects Implementation

### Problem

The FUTURE "Visual Retro Effects & Fidelity Profiles" item (offloaded from P2) and the broader authenticity vision call for optional scanlines, CRT curvature/distortion, palette emulation / limited color quantization, etc.

Currently the engine has none of this. Adding effects directly into the main RenderSystem would violate the "strictly optional — modern smooth rendering ... must be completely unaffected" requirement repeated in the FUTURE text.

Without a delivery mechanism (render passes or compositing layer) + controls + profile integration, the visual half of "NES/8-bit" profiles cannot exist.

### Fix

Implement the effects as an optional, self-contained layer:

- New module(s) under `engine/graphics/` or `engine/fidelity/effects/` (post-process or CardMaker-based overlay quads for initial simplicity; shader path when Panda3D pipeline allows).
- Effects are off by default; enabled only when the active FidelityProfile requests them (or explicit opt-in).
- Public controls: intensity, scanline count, curvature amount, palette reduction levels (simple API or config object).
- Compositing happens after (or around) the main 2D scene so aspect2d sprites, HUD, etc. are affected consistently; or per-layer if needed.
- Zero changes to default RenderSystem path or any cartridge that does not opt in.
- Wire activation from the P5-A profile coordinator.

Provide a small debug key or console toggle during dev (guarded by dev_mode) to force effects on for inspection.

### Acceptance criteria

- A cartridge (or host) can enable "scanlines + mild CRT + NES-ish palette" via profile or direct API and see the effect on rendered output.
- Toggling the effects off (or using a non-retro profile) restores pixel-perfect modern rendering with no overhead or visual difference from before the phase.
- Controls are live (changing intensity mid-run updates the effect).
- Default (no profile / modern profile) path is completely untouched (measurable by diffing a before/after capture or by code inspection + test).

### Validation

- Manual visual QA on dev machine: enable profile with effects, observe scanlines/curvature/palette shift on tgl_demo or a simple sprite scene; disable and confirm identical output to baseline.
- Automated: a headless or offscreen render test that asserts "effects off" produces the same (or bitwise-close) frame as a profile-less run.
- Performance: enabling effects has bounded, documented cost; disabling has zero extra cost.
- The effects module is referenced from the profile coordinator and from the new guide material (P5-F).

## Track P5-C - Audio Chip Emulation Layers

### Problem

Authentic retro sound is part of the "Fidelity Profiles & Retro Authenticity" FUTURE item and the original TGL vision (NSF + chiptune SFX).

The engine already has `AudioSystem`, `MusicSystem`, and NSF player support. There is no optional layer that can drive NES APU-style square/pulse, noise, triangle voices (or later chips) from a simple frequency/duty/volume/envelope API so that cartridge authors can get "chip" timbre without shipping samples or relying solely on NSF.

Without this, "NES/8-bit" profiles are visually retro but sonically modern or NSF-only.

### Fix

Add an optional emulation layer (new `engine/audio/chip_emulation.py` or submodule):

- Small set of emulated voices (start with NES APU square/pulse + noise + triangle).
- Clean integration: the voices can be driven from cartridge code or from the MusicSystem/NSF path when a profile requests chip mode; normal cartridges continue to use existing sample/MIDI/NSF paths with zero change.
- Practical API surface: `set_frequency(voice, hz)`, `set_duty(voice, 0.0-1.0)`, `set_volume`, `set_envelope` (or ADSR-lite), `trigger` etc. Not cycle-accurate; API-level approximation sufficient for creative use.
- Profile-driven: when the active FidelityProfile includes an audio chip dimension, the emulation voices become the active backend for opted-in cartridges; otherwise the prior audio systems are used.
- Wire with existing audio manager so volume, mixing, and device output are shared.

Keep the implementation small and self-contained so it can be extended later (SNES SPC etc.) without touching the core audio contract.

### Acceptance criteria

- A cartridge running under a profile with chip audio can drive a square wave at a given frequency/duty and hear a recognizable chiptune timbre (distinct from a plain sine or sample).
- The same cartridge without the profile (or under "Modern Smooth") continues to use whatever audio backend it used before; no new voices or timbre change.
- NSF + sample paths continue to work for all cartridges.
- The emulation voices respect global volume/mute from the existing AudioSystem.

### Validation

- Manual: run a small test cartridge or instrumented tgl_demo under "NES/8-bit" profile; trigger chip voices for shoot/hit; confirm timbre; switch profile or cartridge and confirm prior audio behavior.
- Unit or integration test for the voice API (parameter setting + observable state or a thin mock backend).
- No regression in existing audio tests or NSF playback.
- Documented in the audio guide or a new fidelity audio note (P5-F).

## Track P5-D - Retro Layer Expansion + Profile Integration

### Problem

The P2 phase delivered the core novel part (FixedPointVec2, SubpixelTransform, NESStyleMovementSystem / quirk resolver with intentional clipping/penetration rules, opt-in via fidelity profile or flags, ref cartridges demonstrating one reproducible emergent mechanic).

The FUTURE "Additional Legacy Math & Glitch Priorities" item (offloaded from P2) calls for expanding that layer with more well-documented practical approximations (integer overflow effects, specific collision quirks, timing-window behaviors, other classic console "features").

Without the expansion + explicit tying to the P5-A profile coordinator, the retro math story is incomplete and the "powerful creative constraints" promise of the vision is only partially delivered.

### Fix

In `engine/retro/` (or a `quirks/` subpackage):

- Add 2–4 additional well-chosen, high-memorable quirks (examples from FUTURE: integer overflow wrap on position/velocity accumulators, specific wall-clip or momentum quirks, narrow timing windows for jumps/attacks, subpixel penetration rules beyond the P2 baseline).
- For each: a reproducible test or demo scenario (unit test + a tiny cartridge or example script that triggers the exact condition).
- Clear rationale + exact rule description in code comments and docs (so authors understand the preconditions under which the emergent behavior fires).
- Opt-in exclusively through the fidelity profile (or an explicit component/system flag that profiles set); non-profile / modern paths are completely unaffected.
- Integrate with P5-A: the profile object (or a derived "retro_quirks_enabled" / "math_mode" value) is the documented activation mechanism.

Prioritize behaviors that enabled memorable gameplay, speedruns, or creative mechanics in historical titles.

All additions remain "practical, API-level approximations (not bit/cycle-accurate full hardware emulation)" per the original scoping.

### Acceptance criteria

- At least two new documented quirks exist with tests/demos that reliably reproduce the emergent behavior only when the appropriate profile (or flag) is active.
- A cartridge author can read the rule description and the demo, understand the exact conditions, and choose to opt in (or not) via profile.
- Modern / no-profile cartridges and entities never exhibit the new quirks (even if they share the same movement/collision code paths).
- The P2 reference cartridge(s) can be updated (or a new one added) to demonstrate one of the new quirks under a profile.

### Validation

- The new tests/demos pass when profile is active and fail (or do not trigger the quirk) when profile is inactive.
- Manual run of the demo scenario under "NES/8-bit" vs "Modern Smooth" shows the difference.
- Docs (in the retro guide or P5-F material) contain the exact rule text + preconditions.
- No behavior change for any existing non-retro code.

## Track P5-E - Native Packaging, Distribution, Richer FFI Surfaces & Initial Security Sketch

### Problem

P3 delivered the narrow v1 native boundary (CartridgeContext as target, minimal ABI, manifest plugins section, thin PluginHost, bidirectional toy "hello" skeleton (C + Rust), guide).

P4 delivered unload/isolation so native handles can be released cleanly.

The FUTURE "Packaging, Distribution, Tooling & Production Concerns for Native Plugins" and "Richer Native FFI Surfaces (post-v1)" items (offloaded from P3) plus the security/provenance bullet remain unaddressed.

Without packaging support, a cartridge that declares a native plugin cannot be turned into a self-contained .car that includes the .so/.dylib/.dll. Without richer surfaces, native code is limited to the toy registration path. Without even an initial security sketch, the ecosystem story for untrusted third-party cartridges and native plugins is missing its starting point.

### Fix

**Packaging & distribution (core of this track):**

- Extend `tools/cli/cartridge_pack.py` (and the `py2d-cartridge` surface) to treat native artifacts as first-class:
  - During pack: discover declared native artifacts (from manifest `plugins` / new `native` section), validate their presence, include them (and platform-specific subdirs) inside the resulting .car.
  - Support optional build hooks or a conventional `native/` layout inside the cartridge tree so `cargo build` / `make` can be driven as part of the pack step (or documented pre-pack).
  - Manifest may grow a `native` / `build` section describing how to produce the artifacts for supported platforms.
- Loader (or the P3 PluginHost) consumes the packaged natives on extract.
- ABI compatibility matrix + engine version enforcement: the already-parsed `cartridge.requires.engine` (plus a new or extended `abi_version` on the plugin entry) should gate loading with clear errors: "native plugin built against engine 0.4 ABI v2 will not load under engine 0.3...".
- Keep all of this strictly additive: pure-Python cartridges and the default engine paths are never impacted.

**Richer FFI surfaces (post-v1, controlled & versioned):**

- Expand the narrow v1 surface with additional opt-in operations once the basic contract is stable (per FUTURE list):
  - Native code publishing events onto the world event bus (safe payload types only).
  - Native-implemented `SaveStateProvider` registration.
  - Controlled component data access/mutation for a pre-declared set of core component types (Transform, Collider, Sprite, ...) via opaque handles or generated accessors.
  - Native system update callbacks that the engine can drive each frame (instead of only one-time registration).
- Every addition must be versioned (ABI bump rules), documented in the header + Rust bindings + native guide, exercised from a "hello"-style example, and noted as additive.
- Full cross-language component & system type registration is acknowledged as significantly larger; design only after real usage of the narrower surfaces; consider bindgen + stubs or capability-passing.

**Initial security / provenance / sandboxing model sketch:**

- Document a starting point (not a full implementation): plugin signing, hash verification at load time, capability restrictions on what a native plugin may do via the handle, longer-term process isolation notes.
- Note that these are ecosystem-level concerns that become relevant only after the core boundary (P3), isolation (P4), and at least one real non-toy native plugin exist.
- Place the sketch in the native plugins guide (P5-F) and reference it from the PHASE5 doc.

All native work beyond the v1 narrow boundary defined in P3 must remain strictly additive.

### Acceptance criteria

- A cartridge tree with a declared native plugin + the compiled artifact can be packed with `py2d-cartridge .` and the resulting .car contains the native bits in the expected location.
- Loading the packaged .car causes the native plugin to be discovered, loaded, and registered (ABI/engine version checks pass on a matching build).
- A richer surface addition (e.g. native event publish or a controlled Transform handle write) can be exercised from an updated "hello" style example and observed from the Python side.
- The initial security sketch exists in docs and is referenced from the guide and this PHASE5 doc.
- Pure-Python cartridges and default paths are completely unaffected (no new cost or behavior).

### Validation

- End-to-end smoke: minimal cartridge declaring a (stub or real) native plugin → `py2d-cartridge` pack → inspect .car contents → load via main or host → native registers and exercises one richer surface (if implemented) or the v1 path.
- Packer and loader tests cover the new native artifact discovery/validation/bundling paths (and error cases: missing artifact, wrong ABI).
- Manual on dev platform: follow the (updated) guide, build a native artifact, pack, run, observe.
- Security sketch is a readable section in the guide; no claim of full implementation.
- Existing cartridge/pack tests continue to pass for non-native cases.

## Track P5-F - Documentation, "Cartridge-Usable" Principle, Production Packaging Example & Validation

### Problem

Even with a working Fidelity Profile coordinator (P5-A), effects (P5-B), audio (P5-C), expanded retro (P5-D), and packaging/richer FFI (P5-E), cartridge authors will not adopt the new surfaces if they do not know they exist, how to declare a profile in manifest/entrypoint, how to opt into effects or chip audio, how to package native bits, what the "cartridge-usable" principle means in practice for new engine work, or how to exercise the full stack in a production-like flow.

The public guides (cartridge_loader_guide.md etc.) and CARTRIDGE_VISION/AUDIT are silent on fidelity profiles and the post-P3/P4 native production story. The TGL ZIP packaging item (#10 in top-level FUTURE) and the vision verification criteria (pack → load → observe) have no home in the current phase tracking.

The "Ongoing" principle from the AUDIT ("Every new engine feature ... must be usable from a cartridge without engine modification") is still only a sentence, not an enforceable checklist with examples.

### Fix

- Update `docs/guides/cartridge_loader_guide.md` (Known Limitations if any remain, plus new sections on "Fidelity Profiles", "Retro Visual & Audio Authenticity", "Native Packaging & Distribution").
- Create or expand a focused guide (e.g. `docs/guides/fidelity_profiles.md` or augment the native plugins guide) that:
  - Explains the mental model (profiles as the unifying creative + authenticity control surface).
  - Walks through "declare a profile, opt into effects + chip audio, switch at runtime".
  - Documents the packaging story for natives (layout, pack step, manifest, loader consumption).
  - Includes the initial security sketch.
  - Contains or points to a minimal end-to-end production packaging example (or host-context smoke) and the validation cartridge/ref.
- Add a living "Cartridge-Usable Principle" section (or short doc) with a checklist: new systems/components/render/audio features must expose their cartridge surface (Context, profile hook, or explicit opt-in) without requiring engine changes; examples of recent features that followed the rule; how to test from a cartridge.
- Validation track (inside this doc or as a sibling artifact):
  - Use tgl_demo (or a small dedicated ref cartridge) to exercise a full "NES/8-bit" profile (retro math + visual effects + audio if wired) + the TGL packaging item (#10: copy sprites, produce .car, verify load).
  - Demonstrate the minimal production packaging example (native bits + profile-declaring cartridge) in a host context or standalone pack/load smoke.
  - Confirm that the packaged cartridge runs cleanly under the profile with observable coordinated behavior (or documented stubs for partial implementation).
- Light cross-references from the thin CARTRIDGE_VISION (left as-is per choice) and from DEVELOPER_ONBOARDING / README as needed.

### Acceptance criteria

- The loader guide and new/updated fidelity/native guides exist, are linked from the cartridge guides README or main navigation, and cover profile declaration, effects/audio opt-in, native packaging, and the cartridge-usable checklist.
- A reader following the guide + example can declare a profile, pack a cartridge (with or without native bits), load it, and see the profile-driven behavior (or the packaging succeed).
- The TGL packaging flow (#10) is exercised or explicitly validated as part of P5-F (even if the full TGL content remains in FUTURE).
- The "cartridge-usable" principle has a concrete, citable checklist + at least one enforcement example in the tree.
- The production packaging example (or host-context smoke) is referenced from the PHASE5 doc and the guides.

### Validation

- Link / navigation check from existing cartridge docs.
- A reviewer (or the author) can follow the guide + packaging example end-to-end and observe either the profile effects or a successful native-inclusive .car roundtrip.
- The validation cartridge / tgl pack smoke is runnable and documented in the PHASE5 "Files affected" / Testing Strategy.
- New or expanded tests (manifest profile fields, pack native artifacts, profile activation) are part of the regular suite.
- Pre-push / CI passes the expanded coverage.

## Follow-On Candidates

List items that were surfaced but intentionally left out of this phase.

| Candidate | Why it is deferred |
|-----------|--------------------|
| Full security / sandbox / provenance implementation for untrusted cartridges and native plugins in hosts | The phase includes only the initial sketch (per FUTURE text and broader scope choice). Full signing, capability enforcement, process isolation, etc. become relevant after real multi-cartridge host usage and at least one non-toy native plugin. |
| Bit-accurate or cycle-accurate hardware emulation (math, video, audio) | Explicitly out of scope per PROJECT.md risks, P2 scoping, and FUTURE language: "practical, API-level approximations sufficient". Keep approximations well-documented and opt-in. |
| Advanced / production "Cartridge Host" polish with live profile switching, concurrent composition of multiple active cartridges, or save-state handoff across switches | P4 delivered the minimal skeleton. Richer UX and live multi-cartridge behaviors are natural follow-on once the basic fidelity + packaging surfaces are stable. |
| Subprocess + IPC isolation model as an alternative (or complement) to in-process fidelity / native loading | One of the higher-safety options noted in prior vision/FUTURE; the in-process profile + packaging path is the pragmatic first step for this phase. |
| Richer lifecycle / profile events on the World event bus (CartridgeProfileChangedEvent, etc.) | Nice-to-have for host and cartridge authors once the core profile coordinator exists; can be added on top. |
| Remaining top-level TGL cartridge items (labyrinth mode, walking sprite integration, transform animation, bosses, power-ups, full audio wiring, TGL save state, etc.) | Stay in FUTURE_TASKS per the synthesis choice ("Keep TGL items in FUTURE unless they fit a clean validation track"). The packaging item is lightly surfaced in P5-F validation only. |
| Full cross-language component & system type registration from native | Acknowledged in P5-E as significantly larger than post-v1 controlled expansions; design only after real usage of the narrower surfaces. |

## Implementation Notes

- This PHASE5 document was created following `docs/PHASE_REPORT_TEMPLATE.md` and the exact structure/tone of the prior PHASE1–PHASE4 tracking docs during a planning session that re-entered plan mode.
- Extraction sources: the current session plan.md (with all prior Phase Tracking Documents additions), the referenced vision plan (019e612c.../plan.md — its "Ongoing" and packaging/tooling mentions), the detailed `CARTRIDGE_ARCHITECTURE_VISION_AND_AUDIT.md` (primary source for Phase 4+ language, the gap table retro/authenticity items, and the explicit "Ongoing Principles" bucket), the thin `CARTRIDGE_VISION.md` (still points to Phase 4+; left as-is per choice), `docs/FUTURE_TASKS.md` (the two full subsections "Fidelity Profiles & Retro Authenticity (broader items captured during Phase 2 planning)" and "Native Plugin Boundary & FFI Readiness (broader items captured during Phase 3 planning)" that were pre-populated in prior turns and are now being promoted), `docs/PHASE1_CARTRIDGE_SYSTEM_POLISH.md` through `PHASE4_ISOLATION_MULTI_CARTRIDGE.md` (to mirror structure, "assume complete + minimal refs" representation, FUTURE hygiene pattern, broader validation inclusion, and track granularity), `docs/guides/cartridge_loader_guide.md` (Known Limitations + packaging sections), `docs/PROJECT_ROADMAP.md` and other top-level docs for historical color, `list_dir docs/`, multiple greps (phase numbers, fidelity/scanline/CRT/APU/profile/packaging/native/FFI/security terms across docs + the original vision session plan), targeted reads of core cartridge sources (loader, manifest, packer, resource_manager, render, audio) confirming complete absence of any profile, fidelity, effects, chip emulation, or native packaging logic in the engine tree, and the explicit user choices via the ask_user_question (5 questions) for this turn.
- Scope is the "Broader" choice: the two FUTURE subsections are synthesized into the 6 formal tracks; the TGL packaging item (#10) is included as part of the clean P5-F validation track (ecosystem example + ref cartridge exercising full profiles + minimal production packaging example in host context); an initial security model sketch is included (P5-E/P5-F). Deeper security implementation, bit-accurate emulation, full concurrent composition, and remaining TGL content stay out or in FUTURE.
- Representation is "Assume complete + minimal backward refs" per the user's choice (PHASE4/PHASE2 precedent). Only light mentions of P2 retro layer (as a dimension of profiles), P3 narrow boundary (as the v1 foundation for richer FFI), and P4 isolation (as prerequisite for safe native packaging/unload of native handles) appear where they are direct dependencies.
- Vision cross-linking: CARTRIDGE_VISION.md is left exactly as-is per the chosen answer.
- FUTURE_TASKS hygiene: the two entire subsections (Fidelity... and Native... including all their sub-bullets and the "End of native..." marker) are removed via search_replace in the same turn so the task queue stays clean and non-duplicative. The PHASE5 doc becomes the authoritative tracking surface for this work. Top-level TGL and Engine A/B/C items remain.
- The 6-track structure + central P5-A coordinator + separate visual (P5-B) + audio (P5-C) + retro expansion (P5-D) + bundled native pack/richer FFI/security (P5-E) + docs + cartridge-usable + validation (P5-F) exactly follows the user's synthesis preference. The validation track (P5-F) is the concrete proof point that includes the TGL packaging consumer and a profile-exercising ecosystem example, plus the minimal production packaging example (or host-context note).
- ResourceManager, World event hooks, the existing audio systems, RenderSystem base path, and the P3/P4 cartridge/native loader surface are all leveraged as the foundation (no broad rewrites).
- Keep this document as the executive record. Detailed profile object layout, exact post-process vs. overlay implementation choices, voice API signatures, packer manifest delta, or the precise security capability model can live in the implementation PRs, the new guide(s), or short design notes alongside the code.
- Update status, last-updated date, and the tracks table as work lands. Move completed track details into the Outcome section when the phase is declared complete. After this phase lands, the "Phase 4+" language in CARTRIDGE_VISION can be updated in a follow-up pass if desired.
- This phase turns the cartridge vision's creative constraint thesis (profiles + retro authenticity) and its production extensibility thesis (native packaging + controlled richer FFI on top of a clean isolation seam) from offloaded FUTURE items into a single, coordinated, documented, and demonstrable body of work, while giving the "every new engine feature must be cartridge-usable" Ongoing principle a living home and enforcement mechanism.

## Outcome

*(To be filled when the phase is complete.)*

- What shipped.
- What was deferred (moved to Follow-On or remaining FUTURE items).
- What should happen next (e.g. full security model implementation, bit-accurate emulation spike, advanced concurrent host polish, integration of profiles into tgl_demo labyrinth or main TGL flow, richer native surfaces beyond the P5-E set, ongoing "cartridge-usable" enforcement as a standing review item for every new engine PR).

---

## Optional Sections (populated for signal)

**Files affected (initial map)**

- New or primary engine: `engine/fidelity/` (or `engine/fidelity/profile.py` + manager), `engine/graphics/effects/` or post-process layer for visual retro, `engine/audio/chip_emulation.py` (or submodule), expansion inside `engine/retro/`
- Modified: `engine/cartridge/manifest.py` + `schema.json` (light profile / native build section support if not already sufficient), `tools/cli/cartridge_pack.py` (native artifact discovery + bundling), loader / PluginHost (profile wiring + native pack consumption + ABI gating)
- Modified (light): RenderSystem or a thin compositing hook (for effects opt-in only), existing AudioSystem/MusicSystem/NSF integration points (additive)
- New docs: `docs/guides/fidelity_profiles.md` (or combined with native guide updates); updates to `docs/guides/cartridge_loader_guide.md`, `docs/guides/native_plugins_guide.md` (if exists), audio guide, retro-related docs
- Validation / examples: updates or a packaging smoke under `examples/hosts/` or a new `tools/packaging_example/`; optional profile-exercising additions or config to `examples/cartridges/tgl_demo/` (or a small dedicated ref cartridge under `examples/cartridges/`); the TGL packaging step exercised as part of P5-F validation
- Tests: new or expanded coverage for profile selection/activation, effects on/off, audio voices, native pack roundtrips, ABI gating, cartridge-usable checklist enforcement
- This PHASE5 tracking doc + the session plan.md record + `docs/FUTURE_TASKS.md` trim (the two subsections)

**Testing Strategy**

- All existing cartridge, save-state, loader, retro (P2), native (P3), audio, and render unit tests continue to pass with zero behavior change for non-profile / pure-Python / non-native cases (fidelity + packaging support is strictly additive and opt-in).
- Dedicated coverage: profile coordinator (select, scope, override, default-neutral, manifest/entrypoint roundtrip); visual effects (on/off isolation, control live update, no default path impact); audio chip voices (API + integration with existing systems, profile-driven activation); retro quirk expansion (reproducible demo + test that only fires under profile); native packaging (pack with declared artifact → .car contains it → load succeeds with ABI check; error cases for missing/wrong ABI).
- Validation smoke (P5-F): runnable end-to-end that (a) exercises a profile-declaring cartridge (tgl_demo or ref) under "NES/8-bit" (or equivalent) with observable coordinated behavior (or documented stubs), (b) performs the TGL packaging item (#10) or equivalent production pack step, (c) demonstrates the minimal production packaging example (native bits + profile cartridge) in host or standalone context, (d) confirms clean unload/reload after P4 work.
- Manual/visual QA on the development platform for effects (scanlines/CRT/palette visible when enabled, pixel-identical when disabled) and chip audio timbre.
- Pre-push / CI runs the expanded suite; native-related and effects tests may be conditional on toolchains or graphical/audio backends where appropriate.
- Note: full cross-platform native packaging matrices, production host robustness with live profile switches, and deeper security implementation are follow-on concerns.

*This phase delivers the unifying creative control surface (Fidelity Profiles) that makes the retro authenticity vision (math + visuals + audio + quirks) first-class and cartridge-declarable, completes the production half of the native extensibility story (packaging + controlled richer FFI on top of P3/P4 foundations), gives the AUDIT "Ongoing" principle a concrete home and validation, and does so while keeping everything strictly optional and additive so that modern cartridges and the default engine path remain completely unaffected.*

---

**End of Phase 5 planning document (following PHASE_REPORT_TEMPLATE.md and the established PHASE1–PHASE4 pattern).**
