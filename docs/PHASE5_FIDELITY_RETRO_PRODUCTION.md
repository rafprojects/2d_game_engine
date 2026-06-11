# Phase 5 - Fidelity Profiles, Retro Authenticity & Production Ecosystem Readiness

**Status:** Planned  
**Created:** 2026-06  
**Last updated:** 2026-06-10 (viability evaluation pass: three premises corrected — RetroProfile already exists so P5-A composes instead of competing; the NSF player is a mock so P5-C commits to procedural samples; the packer already includes native artifacts so P5-E shrank and split into E1/E2 with E2 gated on a real consumer; P5-B restaged around a real 256×240 render-to-texture pipeline; per-track Risks added — see Implementation Notes)

### Tracks

| Track | Description | Status | Effort |
|-------|-------------|--------|--------|
| P5-A | Core "Fidelity Profile" coordinator system (umbrella over the EXISTING `RetroProfile` from P2 — `FidelityProfile` composes optional dimensions `math: RetroProfile`, `video: EffectsConfig`, `audio: ChipConfig`; cartridge-scoped; manifest `fidelity` key + Context declaration + runtime switch; baselines "NES/8-bit", "Modern Smooth", "Arcade" as presets; opt-in everywhere; compose, don't compete) | Planned | Medium |
| P5-B | Visual retro effects, staged (B0: WSLg render-to-texture spike FIRST; B1: CardMaker scanline overlay — hours, no RTT, permanent fallback; B2 headline: render the game into a real 256×240 offscreen buffer matching P2's VirtualPlayfield + nearest-neighbor upscale — authentic pixelation by construction; B3: GLSL on the upscale quad for scanlines/curvature/palette — palette REQUIRES a shader pass; strictly optional, default path 100% unaffected) | Planned | Medium-Large (staged) |
| P5-C | Audio chip voices via procedurally generated samples (corrected premise: the "NSF player" is a MOCK — API skeleton, zero synthesis; real backend is Panda3D AudioSound sample playback; v1: synthesize square/pulse/triangle/noise samples at load time with stdlib only, play through the existing AudioSystem with `play_rate` for pitch and per-duty samples; the mock's channel API becomes the target surface backed by real voices; API-level, not cycle-accurate) | Planned | Medium |
| P5-D | Retro layer expansion + profile integration (integer-overflow wrap as a FixedPoint mode — 8.8 wraps at its natural 16-bit width; revive the `momentum_residual` quirk dropped in the P2 rebuild; timing-window behaviors on the tick-callback architecture; each quirk ships with reproducible test/demo + exact rule description; opt-in exclusively via profile or explicit flag) | Planned | Small-Medium |
| P5-E1 | Native packaging validation, ABI gating & security sketch (the packer ALREADY includes .so/.dylib/.dll via rglob — inclusion is free, validation is the work; pack-time check that declared artifacts exist; conventional `native/` layout — NOT `build/`, which the packer excludes; load-time ABI/engine-version gating with actionable errors; add the `py2d-cartridge` console script via `[project.scripts]` — the name the docs already use but which does not exist; docs-only security/provenance sketch anchored on P3's trust-model note) | Planned | Small-Medium |
| P5-E2 | Richer FFI surfaces — GATED, not scheduled (native events on the bus, native SaveStateProvider, batched component accessors — per-field handle access is slower than Python, see the P3 evaluation; every addition versioned + exercised from a hello example; **gate: do not start until at least one real non-toy native plugin exists and wants the surface**; per-frame native callbacks removed from the list — already in P3's v1 vtable) | Planned | Medium (deferred) |
| P5-F | Documentation, "cartridge-usable" principle, production packaging example & validation (update cartridge_loader_guide + guides for profiles + native packaging; the cartridge-usable checklist + enforcement example; TGL ZIP packaging item #10 as the concrete consumer; profile-exercising ref cartridge or tgl_demo smoke; security notes; `py2d-cartridge` console script documented) | Planned | Small |

---

## Rationale

Briefly explain why this phase exists now.

1. After Phase 4 (Isolation & Multi-Cartridge Host Readiness) the architecture has a clean load/unload seam and a proven secondary "host" mental model. The two largest bodies of work that were deliberately offloaded from earlier focused phases (P2 retro math layer and P3 narrow native boundary) are now the highest-leverage remaining surfaces for the original vision: deliberate creative constraints (fidelity profiles + retro authenticity) and production/ecosystem readiness (native packaging + richer FFI + initial security thinking). The AUDIT explicitly calls out the "Ongoing Principles" bucket ("Every new engine feature ... must be usable from a cartridge without engine modification") as the perpetual north star; formalizing the coordinator (profiles) + effects + packaging makes that principle concrete and enforceable rather than aspirational. **Honesty note (2026-06-10 evaluation):** this phase bundles two unrelated workstreams. Tracks A–D depend only on Phase 2, which is complete — they can begin immediately, before or in parallel with P3/P4, and they are the part that serves the game-first thesis (visible scanlines and audible chiptunes are cartridge-#1 payoff). Only E1/E2 depend on the native phases, and E2 is additionally gated on a real native consumer existing. The bundling rationale below is queue hygiene, not an engineering dependency.

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

*(Resequenced 2026-06-10: A–D depend only on the completed Phase 2 and can begin immediately; E1 follows P3; E2 is gated on evidence, not calendar.)*

1. P5-B0 spike (inside P5-B) - a ~20-line `make_texture_buffer` + trivial GLSL smoke under WSLg, run FIRST. It retires the one platform unknown that decides whether B2/B3 are dev-machine work or wait for verified hardware.

2. P5-A - Fidelity Profile umbrella over RetroProfile. The coordinator everything else hangs on; Medium once it composes rather than competes.

3. P5-B - Visual effects in stages (B1 overlay → B2 256×240 RTT upscale → B3 shaders). B2 is the headline payoff and unifies P2's virtual pixel space with the visual fidelity story.

4. P5-C - Chip voices via procedural samples through the existing AudioSystem. Pairs with B for the "NES/8-bit" demonstration.

5. P5-D - Retro quirk expansion (overflow wrap, momentum_residual revival, timing windows), each profile-gated with a reproducible demo.

6. P5-E1 - Native packaging validation + ABI gating + security sketch. Sequenced after P3 lands; small because artifact inclusion already works.

7. P5-E2 - Richer FFI. Explicitly gated on a real non-toy native consumer existing; not started on schedule.

8. P5-F - Docs, cartridge-usable checklist, TGL packaging consumer, validation smoke. Closes the phase.

## Track P5-A - Core Fidelity Profile Coordinator System

### Problem

*(Premise corrected 2026-06-10.)* The cartridge vision's novel creative thesis ("deliberately opt into constrained simulation rules ... that produce emergent 'NES-style' gameplay side-effects") and the AUDIT's Ongoing principle both require a unifying, cartridge-author-friendly mechanism to select and activate coordinated behaviors across math precision, rendering style, audio, and simulation rules.

The original draft claimed "there is still no standard 'fidelity profile' ... or 'opt-in' surface." Stale: `engine/retro/profile.py` defines `RetroProfile(name, frac_bits, tick_hz, enable_quirks, options)` — exactly that surface for the math/simulation dimension, built in P2 and load-bearing in retro_sidescroller_demo today. What does not exist is the coordinator **across** dimensions: nothing ties retro math to visual effects and audio voices, and there is no declarative manifest surface ("run me under NES/8-bit rules + visuals + sound"). A P5-A that introduced a competing profile object would leave authors asking "which profile do I declare?"

Without the umbrella, retro math remains an isolated dimension, effects and audio emulation have no consistent activation story, and the "every new engine feature must be cartridge-usable" principle has no hook to hang on.

### Fix

Compose, don't compete: `FidelityProfile` (new `engine/fidelity/`) is an umbrella dataclass over optional per-dimension configs —

- `math: RetroProfile | None` — the existing P2 object, unchanged; the umbrella holds it, never mirrors its fields.
- `video: EffectsConfig | None` — P5-B's controls (stage, intensity, scanline count, curvature, palette levels).
- `audio: ChipConfig | None` — P5-C's voice configuration.
- Simulation-rule flags only where they don't already belong to `RetroProfile.enable_quirks`.

Canonical baselines ("NES/8-bit", "Modern Smooth", "Arcade") are presets/constructors producing filled-in umbrellas. Declarative surface: a manifest `fidelity` key for the default; CartridgeContext set/switch at initialize or runtime (e.g. TGL corridor vs. labyrinth). Each dimension activates its subsystem exactly the way it does today (`register_retro_systems(profile=...)` for math) — the umbrella coordinates, it does not reimplement. Absent dimensions mean the modern default; absent umbrella means everything behaves exactly as before.

Update `CartridgeManifest` + schema lightly for the declarative default. Wire the active profile through CartridgeContext (and optionally the event bus) so interested systems can react. New engine features must be profile-aware or profile-neutral from day one (enforced via the P5-F checklist).

### Risks

- **Dual-profile confusion** is the one design sin to avoid: a second object overlapping `RetroProfile`'s fields. The umbrella *holds* a RetroProfile; review explicitly for field mirroring.
- **Migration churn**: retro_sidescroller_demo and its tests must declare through the umbrella with zero behavior change (the same RetroProfile inside).
- **Premature override granularity**: implement only the cartridge-scoped case until a real need appears — per-entity/per-system profile mixing multiplies the test surface for no current consumer.

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

Verified 2026-06-10: the engine has **zero** shader, FilterManager, or offscreen-buffer code anywhere, and sprites render in **aspect2d** — which Panda3D's stock post-processing (FilterManager/CommonFilters) does not cover by default; post-processing 2D content requires rendering it into an offscreen buffer first. Adding effects directly into the main RenderSystem would violate the "strictly optional" requirement.

That render-to-texture "requirement" is actually the prize: P2 built a 256×240 `VirtualPlayfield`, and rendering the game into a REAL 256×240 buffer makes the virtual pixel space literal — authentic pixelation by construction, not simulated on a high-res render.

### Fix

Three stages, each independently shippable, all off by default and activated via the P5-A `video` dimension (or explicit API), with a dev-mode debug toggle:

- **B0 — the spike, run first**: ~20 lines proving `base.win.make_texture_buffer` + a trivial GLSL shader work under WSLg on this machine. Decides everything below.
- **B1 — scanline overlay** (hours): a CardMaker quad over the scene with an alpha-striped texture. No RTT, no shaders; the cheap first visible win and the permanent fallback if B0 fails.
- **B2 — the headline: 256×240 render-to-texture + nearest-neighbor upscale.** Render game content into an offscreen buffer at exactly the VirtualPlayfield's dimensions, display it on a fullscreen quad with nearest filtering. Sprites cannot be sub-pixel-smooth because the framebuffer is genuinely 256×240 — the retro look stops being an effect and becomes the actual pipeline. This unifies P2's virtual pixel space with the visual fidelity story.
- **B3 — GLSL on the upscale quad**: scanlines-in-shader, CRT curvature (UV distortion), palette quantization — which REQUIRES a shader pass and cannot be done with overlays. Controls: intensity, scanline count, curvature amount, palette levels.

Zero changes to the default RenderSystem path or any cartridge that does not opt in.

### Risks

- **WSLg/driver support is the gating unknown**: offscreen buffers + GLSL under WSLg (llvmpipe or GPU passthrough) are unverified on this machine. B0 retires this in an hour; if it fails, B1 ships alone and B2/B3 wait for verified hardware. Panda3D 1.10.16 supports the APIs themselves.
- **Coordinate-space migration**: B2 changes where sprites render (the buffer's own 2D scene instead of the window's aspect2d). `VirtualPlayfield`'s mapping was built for aspect2d; the buffer path needs an equivalent mapping, and the demos must opt in without breaking the non-profile path.
- **Playfield vs overlay split**: anything that should stay crisp (debug overlays, future HUD text) must render OUTSIDE the 256×240 buffer — the design needs a two-layer split from day one or text becomes unreadable mush.

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

*(Premise corrected 2026-06-10.)* Authentic retro sound is part of the "Fidelity Profiles & Retro Authenticity" FUTURE item and the original TGL vision (NSF + chiptune SFX).

The original draft claimed "the engine already has ... NSF player support." Structurally true, sonically false: `engine/audio/nsf_player.py` is built around `MockNSFLibrary` ("for demonstration purposes") — the right API shape (channels, duty, volume, envelope, mute) with **zero synthesis; no sound comes out**. The real audio path is ~800 lines of Panda3D `AudioSound` sample playback (AudioSystem, MusicSystem, audio_manager) with no streaming-synthesis capability at all.

The audio story is therefore further from done than the draft implied — but the mock's channel API is a good target surface, and the sample-playback backend points directly at the right v1 design.

### Fix

**Procedurally generated samples, not real-time synthesis** (new `engine/audio/chip_voices.py` or submodule):

- At load time, synthesize short waveform samples with stdlib only (`wave` + math): square/pulse at the standard NES duty cycles (12.5/25/50/75%), triangle, and a noise burst.
- Play them through the **existing** AudioSystem/AudioSound path: `play_rate` for pitch, per-duty samples for timbre, existing volume/mute/mixing shared for free.
- API surface as planned (`set_frequency(voice, hz)`, `set_duty`, `set_volume`, envelope-lite, `trigger`) — implemented against the generated-sample backend, and **replacing or backing the mock NSF channel API** so there is one channel model with real sound behind it.
- Profile-driven via the P5-A `audio` dimension; non-profile cartridges keep existing sample/MIDI paths with zero change.
- Extension points (SNES SPC, real NSF playback via an external decoder) stay out of v1; the module stays small and self-contained.

### Risks

- **The real-time synthesis trap**: streaming synthesis in Python (sounddevice/pyaudio callbacks) means a new dependency, GIL-vs-buffer-underrun fights, and a second mixer fighting Panda3D's. The generated-sample approach avoids all of it — do not drift into "just a small callback path" without treating that as a separate, justified track.
- **Looping artifacts**: clean loops need exact-period samples (generate at frequencies whose period divides the sample length) or short crossfades; cheap to handle, audible if ignored.
- **Envelope fidelity**: ADSR via per-frame volume stepping on AudioSound is approximate; document it as such (consistent with the API-level, not-cycle-accurate scope).
- **Expectation management**: this delivers chip *timbre*, not APU emulation — NSF files still do not play. Docs must say so plainly to keep the mock's old implied promise from leaking back in.

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

The P2 phase delivered the core novel part (FixedPointVec2, the Subpixel Transform/Movement/Collider components, `QuirkMovementSystem` with the midline-ejection resolver, opt-in via `RetroProfile`, and retro_sidescroller_demo demonstrating one genuinely emergent mechanic — the subpixel wall clip).

The FUTURE "Additional Legacy Math & Glitch Priorities" item (offloaded from P2) calls for expanding that layer with more well-documented practical approximations (integer overflow effects, specific collision quirks, timing-window behaviors, other classic console "features").

Without the expansion + explicit tying to the P5-A profile coordinator, the retro math story is incomplete and the "powerful creative constraints" promise of the vision is only partially delivered.

### Fix

In `engine/retro/` (or a `quirks/` subpackage):

- Add 2–4 additional well-chosen, high-memorable quirks. Concrete first candidates, grounded in the current code (2026-06-10): **integer-overflow wrap as a FixedPoint mode** (8.8 wraps at its natural 16-bit width — position/velocity accumulator wraparound exactly like the hardware); **revival of the `momentum_residual` quirk** that was deleted in the P2 rebuild and recorded as follow-on; **narrow timing windows** for jumps/attacks built on the tick-callback architecture.
- For each: a reproducible test or demo scenario (unit test + a tiny cartridge or example script that triggers the exact condition).
- Clear rationale + exact rule description in code comments and docs (so authors understand the preconditions under which the emergent behavior fires).
- Opt-in exclusively through the fidelity profile (or an explicit component/system flag that profiles set); non-profile / modern paths are completely unaffected.
- Integrate with P5-A: the profile object (or a derived "retro_quirks_enabled" / "math_mode" value) is the documented activation mechanism.

Prioritize behaviors that enabled memorable gameplay, speedruns, or creative mechanics in historical titles.

All additions remain "practical, API-level approximations (not bit/cycle-accurate full hardware emulation)" per the original scoping.

### Risks

- **Determinism keystone**: every new quirk must stay inside the fixed-tick, raw-integer world — a quirk implemented with float math or frame-time would silently break the deterministic keystone P2 established. The P2 test pattern (worked raw-integer arithmetic pinned in unit tests) is the bar for each addition.
- **Quirk creep**: each quirk multiplies interaction surface with the axis resolver. Cap the track at the stated 2–4 and require the reproducible demo per quirk before merging the next.

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

## Track P5-E1 - Native Packaging Validation, ABI Gating & Security Sketch

*(Split 2026-06-10 from the original P5-E; packaging turns out to be much smaller than drafted.)*

### Problem

P3 (when it lands) gives cartridges a declared native plugin and a host that loads it from a directory tree. The production gap is the .car story — but it is narrower than the original draft claimed: **the packer already includes native artifacts.** `package_cartridge` walks `rglob("*")` and its exclude lists (`__pycache__`/`.git`/etc directories, `.DS_Store`, `.pyc`/`.pyo` suffixes) do not filter `.so`/`.dylib`/`.dll`. Inclusion is free; what is missing is validation, convention, and gating. One verified trap: the packer excludes any directory named **`build`** — a native layout using `build/` for artifacts gets silently dropped from the .car.

Also: the docs refer to a `py2d-cartridge` CLI that does not exist — pyproject.toml has no `[project.scripts]`; the real entry point is `tools/cli/cartridge_pack.py`.

### Fix

- **Pack-time validation**: when the manifest declares `native_plugins` (P3-C), verify each declared artifact exists in the tree and lands in the archive; clear error if missing; warn if a declared path sits under an excluded directory name.
- **Convention**: `native/` (optionally `native/<platform>/`, e.g. `native/linux-x86_64/`) as the documented layout — explicitly NOT `build/`. Single-platform v1; per-platform manifest path maps stay deferred (consistent with P3-C).
- **Load-time gating**: the P3 host already checks `engine_plugin_abi_version()` before register; add `cartridge.requires.engine` cross-checks with actionable errors ("built against ABI v2; this engine provides v1").
- **Build hooks deferred**: document "build before pack" (`cargo build`, copy into `native/`) rather than driving builds from the packer in v1.
- **`[project.scripts]`**: add the `py2d-cartridge` console script mapping to the existing CLI so the name the docs already use becomes real.
- **Security / provenance sketch (docs only)**: signing and hash verification at load = *provenance*; capability restrictions via the vtable = *containment surface*; process isolation = the only real sandbox. Anchored on P3's trust-model note: native and Python cartridges are the same arbitrary-code-execution trust level, so signing changes who you trust, not what code can do. Lives in the native plugins guide (P5-F); no implementation claimed.

### Risks

- **Stale-artifact confusion**: nothing ties the packed .so to the source it was built from; a forgotten rebuild ships old native code silently. Mitigation: pack-time warning when the artifact is older than the newest source file under `native/`.
- **Premature ABI promises**: P3's v1 ABI is explicitly experimental; the original draft's "compatibility matrix" language implies a stability that does not exist yet. Gate on exact-version match until the ABI is declared stable.

### Acceptance criteria

- A cartridge tree with a declared native plugin + compiled artifact packs successfully and the .car contains the artifact at the conventional path; a missing declared artifact fails the pack with a clear error.
- Loading the packaged .car discovers and loads the native plugin with ABI/engine checks (against the P3 host).
- `py2d-cartridge` works as an installed console script.
- The security sketch exists in the native guide and is referenced from this doc.
- Pure-Python cartridges and default paths are completely unaffected.

### Validation

- Packer tests: declared-artifact present / missing / under-excluded-dir cases; .car content inspection.
- End-to-end: pack the P3 test cartridge with its C test plugin → load from .car → hello observed.
- Existing pack/loader tests pass unchanged for non-native cartridges.

## Track P5-E2 - Richer FFI Surfaces (gated)

*(Split 2026-06-10 from the original P5-E. **Gate: do not start until at least one real, non-toy native plugin exists and concretely wants a listed surface.** The gate is evidence, not calendar — the same "design only after real usage" rule the original draft applied to full cross-language ECS, applied consistently to the whole list.)*

### Problem

P3's v1 surface is deliberately tiny (log, tick-callback registration, one batched query). Real native plugins will eventually want more. Expanding before any real consumer exists is the classic premature-abstraction trap and burns ABI-evolution budget on guesses.

### Fix

When the gate is met, expand opt-in and versioned, in demand order — the original draft's candidates, corrected against the restructured P3:

- Native code publishing events onto the world event bus (safe scalar/string payloads only).
- Native-implemented `SaveStateProvider` registration (byte-buffer snapshots across the boundary).
- Controlled component data access for a pre-declared set of core components — **batched accessors only** (fill/write caller-provided buffers): per-field handle access costs more than a Python attribute access against the dict-of-Python-objects World (see the P3 evaluation).
- *(Removed: "native system update callbacks driven each frame" — already in P3's v1 vtable as tick-callback registration; not a P5 item.)*

Every addition: ABI bump per the versioning rules, header + Rust bindings + guide updated, exercised from a hello-style example. Full cross-language component & system type registration remains out (significantly larger; design only after real usage of these narrower surfaces).

### Risks

- **ABI lock-in**: every surface added is frozen by compatibility promises once the ABI is declared stable; adding late is cheap, removing is impossible. The evidence gate is the mitigation.
- **Performance theater**: component accessors that are not batched would be slower than pure Python while looking "native fast"; the batched-only rule is load-bearing, not stylistic.

### Acceptance criteria

- (At gate time) the requesting plugin's use case is documented; the chosen surface lands versioned with a working example; the v1-only path continues to work for plugins that ignore it.

### Validation

- Updated hello exercises the new surface; ABI version checks reject mismatched builds; existing native tests pass.

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
  - Documents the packaging story for natives (the `native/` layout convention — not `build/`, which the packer excludes; pack step via the new `py2d-cartridge` console script; manifest declaration; loader consumption; the E1 security sketch).
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
- **2026-06-10 viability evaluation pass** — three premises corrected against the live tree. (1) P5-A: `RetroProfile` already exists (engine/retro/profile.py, load-bearing in retro_sidescroller_demo), so the track was rescoped from "introduce a profile" to "umbrella over RetroProfile" (compose, don't compete; Medium-Large → Medium). (2) P5-C: the "NSF player" is `MockNSFLibrary` — API skeleton, zero synthesis; the real backend is ~800 lines of Panda3D AudioSound sample playback — so the track commits to procedurally generated samples through the existing AudioSystem rather than real-time synthesis. (3) P5-E: the packer already includes .so/.dylib/.dll (rglob; excludes don't filter them — verified), so packaging shrank to validation + the `native/` convention (the `build` directory is excluded by the packer — verified trap) + ABI gating; `py2d-cartridge` does not exist as a console script (no `[project.scripts]` in pyproject.toml) and is added in E1. P5-B was restaged around the key design insight: render into a real 256×240 offscreen buffer matching P2's VirtualPlayfield and upscale nearest-neighbor — authentic pixelation by construction — with a WSLg RTT spike (B0) run first because offscreen buffers + GLSL under WSLg are unverified on the dev machine (Panda3D 1.10.16 supports the APIs). P5-D names its first candidates: FixedPoint overflow-wrap mode and revival of the `momentum_residual` quirk dropped in the P2 rebuild. P5-E split into E1 (packaging; follows P3) and E2 (richer FFI; **gated on a real non-toy native consumer existing** — evidence, not calendar; per-frame native callbacks removed from the candidate list because they are already in P3's v1 vtable). Phase-level dependency honesty added to the Rationale: A–D depend only on the completed P2 and can begin immediately; only E1/E2 depend on the native phases. Per-track Risks subsections added throughout.
- This phase turns the cartridge vision's creative constraint thesis (profiles + retro authenticity) and its production extensibility thesis (native packaging + controlled richer FFI on top of a clean isolation seam) from offloaded FUTURE items into a single, coordinated, documented, and demonstrable body of work, while giving the "every new engine feature must be cartridge-usable" Ongoing principle a living home and enforcement mechanism.

## Outcome

*(To be filled when the phase is complete.)*

- What shipped.
- What was deferred (moved to Follow-On or remaining FUTURE items).
- What should happen next (e.g. full security model implementation, bit-accurate emulation spike, advanced concurrent host polish, integration of profiles into tgl_demo labyrinth or main TGL flow, richer native surfaces beyond the P5-E set, ongoing "cartridge-usable" enforcement as a standing review item for every new engine PR).

---

## Optional Sections (populated for signal)

**Files affected (initial map)**

- New or primary engine: `engine/fidelity/` (umbrella `FidelityProfile` composing the existing `engine/retro/profile.py` RetroProfile), `engine/graphics/effects/` (B1 overlay + B2 256×240 RTT pipeline + B3 shaders), `engine/audio/chip_voices.py` (procedural samples; replaces/backs the mock NSF channel API), expansion inside `engine/retro/` (FixedPoint overflow-wrap mode, momentum_residual revival)
- Modified: `engine/cartridge/manifest.py` + `schema.json` (`fidelity` key), `tools/cli/cartridge_pack.py` (declared-artifact validation — inclusion already works), `pyproject.toml` (`[project.scripts]` → `py2d-cartridge`), loader / PluginHost (profile wiring + ABI gating)
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
