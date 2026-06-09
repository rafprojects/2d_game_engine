# Phase 3 - Native Plugin Boundary

**Status:** Planned  
**Created:** 2026-06  
**Last updated:** 2026-06 (initial draft from vision extraction + user choices)

### Tracks

| Track | Description | Status | Effort |
|-------|-------------|--------|--------|
| P3-A | CartridgeContext / EngineAPI facade (the clean, versioned Python surface passed to hooks and register; becomes the stable target that both advanced Python cartridges and the future native FFI design against) | Planned | Medium |
| P3-B | Minimal stable native surface / ABI design (narrow C ABI or Python capsules / pyo3-exposed traits limited to registration + basic safe queries; no full cross-language ECS) | Planned | Large (design-heavy) |
| P3-C | Manifest + JSON schema extension for native plugins (`plugins` or `native_plugins` section declaring entry symbols, required ABI version, and optional metadata) | Planned | Small |
| P3-D | Minimal PluginHost / NativeModuleLoader (thin integration that lives alongside or inside CartridgeLoader; discovers, loads native artifacts via platform dlopen/ctypes/cffi/pyo3, resolves symbols, and invokes the native register equivalent with a safe opaque handle) | Planned | Medium |
| P3-E | Reference skeleton + toy bidirectional "hello" (small C header + Rust crate skeleton demonstrating Python → native register call and native → safe world handle query / callback; buildable cdylib example) | Planned | Medium |
| P3-F | Documentation and author guide ("Writing Native Plugins for Cartridges" or equivalent; covers the surface contract, building from the skeleton, declaring in manifest, loading, and limitations of the v1 boundary) | Planned | Small |

---

## Rationale

Briefly explain why this phase exists now.

1. The cartridge vision explicitly positions native (Rust/C++ ) plugins as a first-class future authoring path: "the same registration surface that Python cartridges use today becomes the target for native plugins." After Phase 1 (cartridge system polish — the Python foundation, Context, tooling, asset fidelity) and Phase 2 (the novel retro emergent layer), the next strategic piece is the stable, narrow boundary that allows cartridge authors to ship high-performance or low-level systems without rewriting the engine. This is the explicit long-term extensibility story.

2. These items belong together as one phase because they form the complete "native plugin boundary slice": the clean Python target facade (Context), the ABI surface definition, the manifest declaration mechanism, the minimal host/loader glue, a concrete reference skeleton that proves the contract is usable, and the documentation that makes it adoptable. Delivering only the design spec without the skeleton + docs would leave the work theoretical; shipping a too-broad FFI would violate the "narrow v1" and "do not over-implement" guidance.

3. Success looks like: a cartridge manifest can list a native plugin; the (thin) host loads a compiled artifact built from the provided C header + Rust skeleton; the native code successfully participates in registration (e.g. supplies an update callback or registers a trivial native-driven entity); a safe, versioned handle allows limited queries back into the world without leaking raw Python objects; pure-Python cartridges and the rest of the engine continue to work exactly as before with zero impact. The surface is intentionally small, versioned, and documented so future expansion can be done deliberately.

## Key Decisions

| # | Decision | Resolution |
|---|----------|------------|
| A | Filename / title for the tracking doc | `docs/PHASE3_NATIVE_PLUGIN_BOUNDARY.md` titled "Phase 3 - Native Plugin Boundary" (direct match to AUDIT language "Phase 3 – Native Plugin Boundary (Parallel Track)" and the pointer already present in CARTRIDGE_VISION.md). |
| B | Scope for PHASE3 | Strict to the AUDIT's Phase 3 definition: narrow ABI surface design, manifest extension, minimal PluginHost/loader support, toy reference skeleton (C header + Rust) + docs. "Do not over-implement." Broader isolation / Python module GC hygiene / multi-cartridge host application skeleton (AUDIT Phase 4 / vision's Phase 3 "Hardening & Multi-Cartridge Future") intentionally offloaded to a clean task queue in FUTURE_TASKS.md. |
| C | Representation of prior work / prerequisite phases | Hybrid context section (short). Credit the foundational cartridge polish (PHASE1) and retro layer (PHASE2) at a high level and note overlap with the Context facade work planned in P1-C. Keep the active tracks focused on new native boundary items without bloating the document with full history. |
| D | Vision reference / cross-linking | Leave the thin `docs/CARTRIDGE_VISION.md` as-is for now (its existing pointer "Phase 3: Native plugin boundary design (narrow ABI + manifest extensions)" plus link to the AUDIT is sufficient; the new PHASE3 doc will self-reference the AUDIT as the detailed source). |
| E | Reference "toy native hello" scope & languages | Both a small C header and a Rust crate skeleton. The hello must demonstrate bidirectional flow per choice: Python side loads and invokes the native register path; the native side receives a safe world handle / capsule and can perform a basic, controlled query or register a trivial callback that Python-side code can observe. Surface remains extremely narrow (registration + minimal safe queries only; no full component/system type crossing yet). |
| F | Parallel-track nature & testing pragmatism | The phase is explicitly a "design + thin implementation + proof" effort that can proceed in parallel with retro landing. Validation will include being able to build the reference skeleton (cargo for Rust, gcc for C header usage) and exercise a minimal cartridge-declared native plugin; full cross-platform CI matrices, richer FFI, and production packaging of native artifacts inside .car files are noted as follow-on. |

## Execution Priority

1. P3-A - CartridgeContext / EngineAPI facade. The Python surface must be stable, versioned, and narrow first; the entire native design (ABI, handle passing, what "safe query" means) is defined against this facade. Any remaining gaps from P1-C are resolved here or driven by this work.

2. P3-B / P3-C - ABI surface definition + manifest/schema extension. These are the contract. Everything else (host, skeleton, docs) implements or consumes the contract.

3. P3-D - Minimal PluginHost / NativeModuleLoader. The thin glue that makes a declared native plugin actually load and run inside the existing cartridge boot flow.

4. P3-E - Reference skeleton + bidirectional hello. The concrete proof that the boundary is usable by real native authors and that the "toy" can do the minimal interesting thing (register + observe effect via safe handle).

5. P3-F - Documentation and guide. Makes the boundary adoptable by cartridge authors who want Rust/C++ systems. Completes the phase.

## Track P3-A - CartridgeContext / EngineAPI Facade

### Problem

Entrypoint hooks (`mount`/`load`/`initialize`) and `register(world, base)` still receive raw `world` (ECS World) and the Panda3D `ShowBase` subclass (`Game` / `base`). This works for pure-Python cartridges today but:

- Leaks engine internals.
- Provides no stable, versioned surface.
- Makes future native interop painful (raw Python objects do not cross FFI boundaries cleanly or safely).
- The vision and AUDIT both call for a small `CartridgeContext` (or `EngineAPI`) object as the official target.

PHASE1 planning (track P1-C) already identified this as a core deliverable for "loader lifecycle + Context facade." The gap remains in the live loader.py (raw passes in `_run_entry_hook` and `_register_system_modules`).

Without the facade, native boundary design has no clean "what does the native side talk to?" answer.

### Fix

Introduce (or finalize) `engine/cartridge/context.py` defining a minimal, versioned `CartridgeContext` (dataclass or protocol / small class) that exposes only what cartridge code (Python or via FFI) is intended to use:

- `world` (or a safe proxy/handle)
- `base` (or a restricted view)
- `manifest`
- `save_state_manager`
- `resource_manager`
- (later) loader or self-unload hook

Update the loader and main.py cartridge wiring to construct and pass a `CartridgeContext` instance instead of (or in addition to) the raw tuple for all hooks and register calls.

The Context becomes the single sanctioned surface. Native code will eventually receive an opaque handle that maps to (a subset of) this surface via the ABI.

Keep the object small and forward-compatible (version field or explicit evolution rules).

### Acceptance criteria

- `from engine.cartridge.context import CartridgeContext` succeeds.
- New and updated cartridges can be written exclusively against the Context object (no direct reliance on raw world/base except for transitional compatibility).
- Loader / entry hook / register paths all flow through the Context.
- The Context type (or a narrow FFI-friendly view of it) is usable as the foundation for the native ABI design in P3-B.

### Validation

- Existing tgl_demo and any other cartridges continue to load and run (with or without a small adapter shim during transition).
- Grep / static check confirms raw `(world, base)` hand-offs are no longer the primary documented path for cartridge code.
- The Context is referenced from the new native guide and the loader guide updates.
- PHASE1 P1-C acceptance criteria are satisfied (or explicitly closed here if the track was still open).

## Track P3-B - Minimal Stable Native Surface / ABI Design

### Problem

There is zero FFI surface, no mention of Rust / C++ / ctypes / pyo3 / capsules / `#[no_mangle]` etc. in the source (confirmed by search). The only registration contract is the Python-only `register(world, base)` function.

Passing raw Python objects across an FFI boundary is unsafe and non-portable. A stable, narrow, versioned surface is required so that native code can participate in the cartridge model without the engine having to expose its entire internals.

The vision is explicit: "Keep the first boundary extremely narrow (registration only). ... Do not implement full cross-language ECS yet — just the boundary + one toy native 'hello system'."

### Fix

Design (and lightly implement) the v1 native surface:

- Choose a concrete mechanism: Python capsules for opaque handles + a small C struct layout, or a pyo3-exposed trait / `#[pymethods]` surface, or a pure C ABI with well-known symbol names. Document the choice and the stability guarantees.
- Define the minimal entry point symbol(s) a native plugin must export (e.g. `int engine_plugin_register(void* context_handle, uint32_t abi_version)` or equivalent).
- Define the narrow operations the handle supports in v1 (e.g. "log a message", "register a system name/callback", "perform a basic entity query returning opaque ids + a couple of scalar fields", "publish a simple event"). No full component type registration or arbitrary Python object creation from native in v1.
- Version the surface (ABI version constant or symbol) and make the host/loader enforce a basic compatibility check.
- Produce the machine-readable + human-readable contract (header + prose in the guide).

The design is captured in code (the header + Rust bindings) and docs rather than a giant design doc.

### Acceptance criteria

- A clear, small public surface exists that a native author can target.
- The surface is narrow by construction: registration + a handful of safe, documented operations.
- Versioning / compatibility story is defined and enforced at load time (at minimum a warning or error on mismatch).
- The same surface is what the reference skeleton (P3-E) implements.

### Validation

- The header / Rust crate compiles cleanly and the symbols match the documented contract.
- Review of the surface by reading the produced artifacts + guide confirms it matches the "narrow v1" intent (no massive ECS mirroring).
- A future cartridge author following the guide can implement the register symbol without reverse-engineering engine internals.

## Track P3-C - Manifest + Schema Extension for Native Plugins

### Problem

`CartridgeManifest` and `schema.json` only understand `systems.register` (Python dotted modules). There is no declared way for a cartridge to say "this archive also ships (or depends on) a native plugin that must be loaded."

Without a manifest surface, even a perfect ABI and host would have no way for cartridge authors to express the dependency declaratively. Packaging and validation would also be blind to native artifacts.

### Fix

Extend the manifest model and schema (non-breaking):

- Add an optional top-level or `cartridge.plugins` / `native_plugins` array (or object) in the JSON.
- Each entry minimally carries: `name`, `entry` (symbol or module), `abi_version`, optional `path` (relative inside the archive or system library name), and `metadata`.
- Update `CartridgeManifest` dataclass + `from_dict` to parse the new section (store as list of small dataclasses or raw dicts for flexibility).
- Update `engine/cartridge/schema.json` (add the new property under the existing permissive `additionalProperties: true` or explicitly model it).
- Update the packer (`cartridge_pack.py`) to at minimum pass the new section through (and optionally validate that declared native artifacts exist in the tree for archive mode).
- The loader will later (P3-D) consume the parsed plugins list.

Because `additionalProperties: true` already exists, basic manifests with the new key will not break current validation.

### Acceptance criteria

- A cartridge.json containing a `plugins` (or `native_plugins`) section with a native entry validates and parses into `CartridgeManifest` without error.
- The parsed manifest carries the plugin declarations through to `LoadedCartridge`.
- The packer accepts and round-trips the new fields.
- Old manifests (no plugins section) continue to work exactly as before.

### Validation

- Add a test case (or extend existing manifest tests) with a plugins section; assert round-trip and presence of the data.
- Run the packer against a cartridge tree that includes a plugins declaration (even if the native artifact is a stub); it succeeds.
- `CartridgeManifest` type / repr shows the plugins when present.

## Track P3-D - Minimal PluginHost / NativeModuleLoader

### Problem

Even with a defined ABI, a manifest declaration, and a Context facade, there is no code that actually loads a native shared library, resolves the register symbol, constructs a safe handle from the Context, and invokes it during the cartridge boot sequence (after or alongside the Python `systems.register` step).

Without this thin host glue, native plugins are undeclarable and unloadable in practice.

### Fix

Add a small, well-isolated module (e.g. `engine/cartridge/native_loader.py` or a `plugin_host` submodule) that:

- Given a manifest's plugins list + the cartridge's extract or assets path + a `CartridgeContext`, attempts to load each declared native artifact using the platform-appropriate mechanism (ctypes, cffi, or pyo3 `PyModule` / `from_abi` style).
- Resolves the well-known register symbol.
- Builds a safe, opaque handle (Python capsule or ctypes pointer wrapper) that exposes only the v1 surface.
- Calls the native register entry, passing the handle + ABI version.
- Records loaded native modules for later cleanup (even if full unload is Phase 4 work).
- Integrates into the existing `CartridgeLoader` flow (or is called from the entrypoint initialize path) so that a cartridge declaring a native plugin gets it activated automatically.

Keep the implementation minimal and defensive: log clear errors on missing symbols / ABI mismatch / load failure, but do not crash the whole cartridge unless the plugin is marked required.

### Acceptance criteria

- A cartridge whose manifest lists a (buildable) native plugin under the new key causes the host to attempt load + symbol resolution + register call during `load_directory` or `load_archive`.
- The native side receives a usable handle and can perform its v1 operations.
- Failure to load an optional native plugin is reported but does not prevent the rest of the (Python) cartridge from running.
- Pure Python cartridges (no plugins key) are completely unaffected — no import or dlopen cost.

### Validation

- Manual or scripted test: build the P3-E hello, place the resulting .so next to a minimal test cartridge that declares it in manifest, load the cartridge, observe the hello side-effect (log message or observable state change).
- Existing Python-only cartridges (tgl_demo etc.) load with identical behavior and no new warnings/errors related to native loading.
- Error paths (bad symbol, wrong ABI, missing file) produce actionable messages.

## Track P3-E - Reference Skeleton + Toy Bidirectional "Hello"

### Problem

A paper design + host is not enough. Cartridge authors (and the engine team) need a concrete, buildable, copy-pastable example that proves the boundary works end-to-end. The vision and AUDIT both require "one toy native 'hello system'" and "a small reference header + Rust crate skeleton".

Without it, the phase delivers no demonstrable artifact that a real native author can start from.

### Fix

Under a conventional location (e.g. `reference/native/` or `docs/reference/native_plugin_skeleton/` or inside the new guide's examples), deliver:

- `engine_plugin.h` — a small, self-contained C header declaring the v1 ABI types, the register entry symbol, the handle operations, version constants, and clear comments.
- A minimal Rust crate (Cargo.toml + src/lib.rs) that:
  - Builds as a cdylib (or the platform equivalent).
  - Uses `#[no_mangle]` (or pyo3) to export the register symbol.
  - Receives the handle, performs a safe "hello" action (e.g. logs via a provided callback or queries a basic world statistic through the v1 surface and stores it where Python can later read it).
  - Demonstrates the bidirectional nature chosen by the user: Python invokes the native path; native uses the safe handle to affect or report something observable from Python.
- A tiny build note or `build.rs` / Makefile snippet so a developer on the current platform (Linux) can `cargo build` and get a loadable artifact.
- The skeleton is intentionally tiny — its only job is to prove the contract is real and that the "hello" round-trips.

The skeleton lives outside the main engine source so it can be versioned / copied independently by cartridge authors.

### Acceptance criteria

- `cargo build` (or equivalent) of the Rust skeleton succeeds and produces a loadable native library.
- Using the C header from a small C caller (or just the Rust side) matches the documented ABI.
- When the produced artifact is declared in a test cartridge's manifest and the cartridge is loaded, the hello effect is visible (e.g. a console message "native plugin registered and queried world" or a counter incremented via the safe path that a Python system can later print).
- The same cartridge without the native plugin declaration (or with the native plugin commented out) shows no such effect.

### Validation

- On the development machine: build the skeleton, construct or temporarily edit a minimal cartridge manifest + tree that references the .so, run via `python main.py --cartridge ...`, observe the hello.
- The produced library can be inspected (nm / objdump / cargo-expand) to confirm the expected symbol(s) are exported.
- The hello is the smallest possible demonstration of the bidirectional contract; it does not implement a full native movement system or anything beyond "I can talk both ways through the v1 surface."

## Track P3-F - Documentation and Integration Guide

### Problem

Even with a working facade, ABI, manifest support, host, and skeleton, cartridge authors will not adopt native plugins if they do not know the surface exists, how to declare it, how to build the skeleton, what the limitations of v1 are, and how to debug load failures.

The current guides (cartridge_loader_guide.md etc.) are silent on native plugins. The AUDIT and vision both call for documentation as part of the phase.

### Fix

Create a new guide (e.g. `docs/guides/native_plugins_guide.md` or "writing_native_cartridge_plugins.md") that:

- Explains the mental model (native plugins as first-class cartridge extensions via the same registration idea).
- Documents the CartridgeContext as the Python target and the narrow v1 ABI surface (with the header as the source of truth).
- Walks through "start from the skeleton": copy the reference tree, add your logic in the register function, declare in cartridge.json, build, package (noting that native artifacts must be included in the archive for distribution).
- Covers the loader integration points, error messages a developer will see, and the explicit "narrow by design" limitations (what you cannot do yet in v1).
- Includes a minimal end-to-end example that matches the hello from P3-E.
- Updates the main cartridge_loader_guide.md "Known Limitations" or a new "Native Plugins" section with a forward pointer.
- Adds a short note in DEVELOPER_ONBOARDING or the thin CARTRIDGE_VISION (later) once the doc lands.

Keep the guide practical and copy-paste friendly.

### Acceptance criteria

- The new guide exists under `docs/guides/` and is linked from the cartridge guides README or the main navigation.
- A reader following the "hello" walkthrough can build the skeleton, declare it, load a cartridge, and see the effect.
- The guide explicitly states the v1 surface boundaries and points to FUTURE_TASKS / later phases for richer functionality and multi-cartridge host work.

### Validation

- Link check / navigation from existing cartridge docs.
- A reviewer (or the author) can follow the guide's hello example end-to-end on the current platform and observe the bidirectional effect.
- The guide is referenced from the PHASE3 doc's "Files affected" and from any updated loader documentation.

## Follow-On Candidates

List items that were surfaced but intentionally left out of this phase.

| Candidate | Why it is deferred |
|-----------|--------------------|
| Proper cartridge unload / Python module GC hygiene + import isolation namespaces (or subprocess+IPC model) | AUDIT Phase 4 / vision "Hardening & Multi-Cartridge Future" item. Kept out per the strict Phase 3 scope choice. Recorded as clean tasks in FUTURE_TASKS.md. |
| Full multi-cartridge "host" application skeleton that can switch or compose cartridges | Same as above; the current single-cartridge-per-process mental model remains primary. The boundary work here is a prerequisite but the host UX is follow-on. |
| Richer FFI surface (full component type registration from native, event publishing from native, arbitrary queries, save providers implemented in native, etc.) | v1 is deliberately registration + minimal safe queries only. Expansion is natural once the narrow contract is proven and stable. |
| Production packaging & distribution concerns (bundling .so/.dylib/.dll inside .car, platform-specific artifact selection, plugin signing / provenance, ABI matrix testing across engine versions) | The skeleton + host prove the contract; robust multi-platform shipping and security model are later engineering tasks. |
| Tooling (cargo integration in `py2d-cartridge`, automatic header generation / bindgen in the build, native hot-reload story) | Nice-to-have once the basic load/register path exists and authors are using the skeleton. |
| Security / sandbox considerations for untrusted native plugins | Important for a real modding ecosystem but out of scope for the initial narrow boundary design. |

## Implementation Notes

- This PHASE3 document was created following `docs/PHASE_REPORT_TEMPLATE.md` during a planning session that re-read the original vision plan (019e612c.../plan.md), the detailed `CARTRIDGE_ARCHITECTURE_VISION_AND_AUDIT.md` (primary source for the Phase 3 "Native Plugin Boundary (Parallel Track)" section and gap table 3.6), the thin `CARTRIDGE_VISION.md` (current roadmap pointer), `PHASE1_CARTRIDGE_SYSTEM_POLISH.md` and `PHASE2_RETRO_EMERGENT_GAMEPLAY_LAYER.md` (to mirror structure, tone, and the "strict scope + FUTURE_TASKS offload" pattern), `FUTURE_TASKS.md`, `PROJECT_ROADMAP.md` (generic older "Plugin System" mentions), cartridge core sources (loader.py, manifest.py, schema.json — still raw world/base passes, no plugins key, permissive schema), the cartridge loader guide, `tools/cli/cartridge_pack.py`, `main.py` cartridge wiring, live `engine/` tree (confirmed complete absence of any FFI, native, plugin, or context.py under cartridge/), greps for native/FFI terms (only documentation and prior planning mentions), and explicit user choices via interactive ask_user_question (5 questions).
- Scope was deliberately kept to the focused "Native Plugin Boundary" per the AUDIT and the "Strict AUDIT Phase 3" answer. Hardening, full isolation, and host application work were offloaded to FUTURE_TASKS.md as a clean queue (new section added in the same turn).
- A short hybrid context is included because the user chose that representation and because the Context facade (P1-C) is a direct prerequisite/overlap that this phase both depends on and helps finalize for FFI purposes.
- The bidirectional "hello" requirement (Python calls native register; native uses safe handle for a basic observable action) was honored exactly per the chosen answer while still respecting the "extremely narrow in v1" and "toy" constraints repeated across the vision and AUDIT.
- Tracks assume the Python cartridge foundation (PHASE1) and retro layer (PHASE2) provide the surrounding context; only light backward references appear.
- Keep this document as the executive record. Detailed ABI layout, exact capsule vs. pyo3 trade-offs, or the precise v1 operation list can live in the implementation PRs, the header comments, or a short design note alongside the skeleton.
- Update status, last-updated date, and the tracks table as work lands. Move completed track details into the Outcome section when the phase is declared complete.

## Outcome

*(To be filled when the phase is complete.)*

- What shipped.
- What was deferred (moved to Follow-On or the new FUTURE_TASKS section).
- What should happen next (e.g. Phase 4 isolation/host work, richer FFI surfaces, first real cartridge using a native plugin for performance-critical logic, integration with tgl_demo or a new reference cartridge, ABI stability review).

---

## Optional Sections (populated for signal)

**Files affected (initial map)**

- New or primary: `engine/cartridge/context.py` (finalize or introduce the facade)
- New: `engine/cartridge/native_loader.py` (or `plugin_host.py`) — the thin loader glue
- Modified: `engine/cartridge/loader.py` (wire Context; call native host at the right point in boot), `engine/cartridge/manifest.py` (parse plugins section), `engine/cartridge/schema.json` (document the new key)
- Modified (light): `tools/cli/cartridge_pack.py` (pass-through + optional existence check for declared native artifacts)
- New reference skeleton: `reference/native/` (or `docs/reference/native_plugin_skeleton/`) containing `engine_plugin.h`, `rust/Cargo.toml`, `rust/src/lib.rs` (cdylib hello), build notes
- New docs: `docs/guides/native_plugins_guide.md` (primary guide); light updates to `docs/guides/cartridge_loader_guide.md` (Known Limitations + forward pointer) and possibly `docs/guides/README.md`
- Tests: new or extended cartridge manifest tests for the plugins key; optional integration smoke (may be skipped when Rust toolchain not present); the hello exercise itself lives with the skeleton
- `docs/FUTURE_TASKS.md` (addition of the broader isolation + richer FFI + packaging items)
- This tracking doc + the session plan.md record of the planning turn

**Testing Strategy**

- All existing cartridge, save-state, and loader unit tests must continue to pass with zero behavior change for pure-Python cartridges (native support is strictly additive and opt-in).
- New coverage for manifest parsing of the plugins section and round-tripping.
- Skeleton build verification: `cargo check` / `cargo build` of the Rust reference (on platforms with toolchain); the resulting library is loadable by the host.
- End-to-end smoke for the hello: minimal cartridge (dir mode for dev, and ideally packaged .car) that declares the native plugin → load → observable bidirectional effect → no crash or leak on unload of that cartridge.
- Error-path testing: missing native artifact, wrong ABI version, missing symbol → clear actionable diagnostics; cartridge continues for non-required plugins.
- Manual verification on the current development OS (Linux) that a cartridge author can follow the new guide and see the hello work.
- Pre-push / CI continues to run the full suite; native-related tests are either always-on (Python side) or explicitly conditional (toolchain presence).
- Note: full matrix testing across Windows/macOS + multiple Rust/C Python ABIs is a follow-on concern once the v1 contract is stable.

*This phase turns the cartridge vision's long-term extensibility thesis — that the same clean registration surface used by Python cartridges can become a stable, narrow target for high-quality native (Rust/C++) plugins — from an architectural aspiration into a concrete, documented, and demonstrable boundary with a usable reference skeleton that cartridge authors can build upon without reverse-engineering the engine.*

---

**End of Phase 3 planning document (following PHASE_REPORT_TEMPLATE.md and the established PHASE1/PHASE2 pattern).**