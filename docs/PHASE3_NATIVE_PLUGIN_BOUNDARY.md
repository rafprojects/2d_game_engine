# Phase 3 - Native Plugin Boundary

**Status:** Planned  
**Created:** 2026-06  
**Last updated:** 2026-06-10 (viability evaluation pass: P3-A rescoped — the Context facade already landed via P1-C; new P3-B0 mechanism-spike track; v1 ABI safety rules folded into P3-B/P3-D; performance rationale reframed honestly — see Implementation Notes)

### Tracks

| Track | Description | Status | Effort |
|-------|-------------|--------|--------|
| P3-A | Version & freeze the CartridgeContext facade (the facade itself landed with P1-C and is wired context-first through hook/register/teardown paths; remaining: `api_version` field, documented evolution rules, and naming the FFI-exposed subset that P3-B designs against) | Planned | Small |
| P3-B0 | Mechanism spike + decision record (build BOTH minimal hellos: a pyo3 extension module loaded through the existing `systems.register` path — works today with zero engine changes — and a C-ABI cdylib loaded via a ctypes harness; record the v1 mechanism decision from two working artifacts; sanctioned early-exit/pause point for the phase) | Planned | Small |
| P3-B | Minimal stable native surface / ABI design (narrow C ABI: host-API vtable of function pointers passed INTO the plugin — a Python host exports no linkable symbols; two-symbol handshake `engine_plugin_abi_version()` + `engine_plugin_register()`; v1 safety rules: main-thread-only, callback pinning, no-unload, panic safety, u64 interned entity ids, error codes; batched query op; ABI explicitly marked experimental; no full cross-language ECS) | Planned | Medium (design-heavy, de-risked by P3-B0) |
| P3-C | Manifest + JSON schema extension for native plugins (`native_plugins` section declaring `name`, `entry` symbol, `abi_version`, `required: bool`, optional `path` and `metadata`) | Planned | Small |
| P3-D | Minimal PluginHost / NativeModuleLoader (thin integration alongside CartridgeLoader; loads native artifacts via ctypes, version-checks before register, builds the vtable + opaque handle, pins callback objects for process lifetime, enforces the v1 no-unload rule with a visible warning on cartridge unload) | Planned | Small-Medium |
| P3-E | Reference skeleton + toy bidirectional "hello" (small C header + Rust crate skeleton demonstrating Python → native register call and native → safe world handle query / callback; buildable cdylib example; plus a one-file C test plugin compiled via `cc -shared` in a pytest fixture so the host has fast always-on unit tests without requiring cargo) | Planned | Medium |
| P3-F | Documentation and author guide ("Writing Native Plugins for Cartridges" or equivalent; covers the surface contract, building from the skeleton, declaring in manifest, loading, an explicit "what v1 cannot do" section, and the trust-model note: native plugins are the same arbitrary-code-execution trust level as Python cartridges) | Planned | Small |

---

## Rationale

Briefly explain why this phase exists now.

1. The cartridge vision explicitly positions native (Rust/C++ ) plugins as a first-class future authoring path: "the same registration surface that Python cartridges use today becomes the target for native plugins." After Phase 1 (cartridge system polish — the Python foundation, Context, tooling, asset fidelity) and Phase 2 (the novel retro emergent layer), the next strategic piece is the stable, narrow boundary itself. **Honesty note (2026-06-10 evaluation):** v1 of this boundary proves a *loading, registration, and contract* story — extensibility, language diversity, future-proofing — not a *performance* story. The World stores components as dicts of Python objects, and a single FFI crossing costs more than a Python attribute access, so per-entity native access through the v1 handle would be slower than pure Python. The real performance path (contiguous component storage + a Rust core layer) is owned by FUTURE_TASKS Task D's spike; the batched query op in P3-B is what keeps that door structurally open. The boundary pattern itself is industrially proven — the same shape as libretro cores, SDL's dynamic API, and VST plugins — and libretro's API is the explicit design reference.

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

1. P3-A - Version & freeze the Context facade. The facade itself already landed (P1-C); what the native design needs from it is a version field, evolution rules, and a named FFI-exposed subset. Small, and first.

2. P3-B0 - Mechanism spike. Build both minimal hellos (pyo3-module-via-`systems.register` and C-ABI-via-ctypes) before designing anything on paper. The pyo3 route needs zero engine changes, so this also delivers the first working native-in-cartridge proof almost immediately — and is a clean pause point for the phase if game work takes priority.

3. P3-B / P3-C - ABI surface definition + manifest/schema extension. These are the contract, now designed from two working artifacts instead of paper. Everything else (host, skeleton, docs) implements or consumes the contract.

4. P3-D - Minimal PluginHost / NativeModuleLoader. The thin glue that makes a declared native plugin actually load and run inside the existing cartridge boot flow.

5. P3-E - Reference skeleton + bidirectional hello. The concrete proof that the boundary is usable by real native authors and that the "toy" can do the minimal interesting thing (register + observe effect via safe handle).

6. P3-F - Documentation and guide. Makes the boundary adoptable by cartridge authors who want Rust/C++ systems. Completes the phase.

## Track P3-A - Version & Freeze the CartridgeContext Facade

*(Rescoped 2026-06-10 — the original premise is stale. The original track text called for introducing the facade; it already exists.)*

### Problem

`engine/cartridge/context.py` defines `CartridgeContext` (world, base, manifest, resource_manager, save_state_manager, loader) and loader.py passes it context-first (with legacy fallback) through all three paths — entry hooks, `systems.register`, and teardown. That landed with P1-C and survived the Phase 2 audit.

What is genuinely missing for FFI purposes:

- No `api_version` field or written evolution rules — native code cannot ask "which Context am I talking to?".
- `world` and `base` are raw `Any` passes; nothing names the narrow subset a non-Python consumer is allowed to rely on.
- No statement of which Context capabilities the native vtable (P3-B) will mirror in v1.

### Fix

Version and freeze, rather than introduce:

- Add `api_version: int` (start at 1) to `CartridgeContext` plus a short evolution-rules docstring (add-only within a version; bump on any removal/retype).
- Name the FFI-exposed subset explicitly in the docstring (v1: cartridge_name, logging, and the registration/query operations P3-B defines — nothing Panda-flavored crosses the boundary).
- Leave the Python-side surface otherwise as-is; it already does its job.

### Acceptance criteria

- `CartridgeContext.api_version` exists and is documented with evolution rules.
- The FFI-exposed subset is named in one place that P3-B's header references as its source of truth.
- No behavior change for existing cartridges (purely additive).

### Validation

- tgl_demo and retro_sidescroller_demo load and run unchanged; full unit suite green.
- P3-B's header comments point back at the Context docstring (single-source-of-truth check).

## Track P3-B0 - Mechanism Spike + Decision Record

*(New track from the 2026-06-10 evaluation.)*

### Problem

Two viable mechanisms exist with very different costs, and the original plan deferred the choice into P3-B's design work. Designing the contract on paper before holding both working artifacts is the riskiest ordering.

Key discovery: a pyo3-built extension module is just an importable Python module, and the existing `systems.register` path already imports dotted modules from the cartridge's `python/` dir — so the pyo3 route works **today with zero engine changes**. What does not exist is the language-neutral, Python-free C ABI; that is the genuinely new artifact of this phase. The mechanism decision is therefore really a decision about what the phase is *for*, and it should be made from evidence, not deferred.

### Fix

Build both minimal hellos (≈30 lines each) before any contract design:

- **pyo3 route**: a Rust crate building an abi3 extension module exposing `register(context)`; drop the built .so into a stub cartridge's `python/` dir, list it under `systems.register`, load normally, observe the hello. No engine changes.
- **C-ABI route**: a cdylib exporting `engine_plugin_abi_version()` + `engine_plugin_register()`; a ~30-line ctypes harness (not yet the real host) that loads it, passes a one-function vtable (log callback), and observes the round-trip.
- Record the decision in a short note: which mechanism is the v1 contract, and what the other becomes (e.g. pyo3 documented as the "easy mode" path in P3-F).

### Acceptance criteria

- Both hellos build and run on the dev machine (rustup toolchain at `~/.cargo/bin`; gcc present).
- A written decision record exists (mechanism, rationale, fate of the other route).
- The phase has a sanctioned pause point here: spike done = native-in-cartridge proven end-to-end, with the remaining tracks deferrable if game work takes priority.

### Validation

- The pyo3 hello is observable through a normal cartridge load (windowed or the headless test path).
- The C-ABI hello round-trips through the ctypes harness; `nm` shows exactly the two expected exported symbols.

## Track P3-B - Minimal Stable Native Surface / ABI Design

### Problem

There is zero FFI surface, no mention of Rust / C++ / ctypes / pyo3 / capsules / `#[no_mangle]` etc. in the source (confirmed by search). The only registration contract is the Python-only `register(world, base)` function.

Passing raw Python objects across an FFI boundary is unsafe and non-portable. A stable, narrow, versioned surface is required so that native code can participate in the cartridge model without the engine having to expose its entire internals.

The vision is explicit: "Keep the first boundary extremely narrow (registration only). ... Do not implement full cross-language ECS yet — just the boundary + one toy native 'hello system'."

### Fix

Design (and lightly implement) the v1 native surface, starting from the P3-B0 artifacts and libretro's API shape as prior art:

- **The host exports no symbols** — the engine is Python, so there is nothing for a plugin to link against. All host services are passed INTO the plugin as a struct of function pointers (`EngineHostApi` vtable) at register time. This is the load-bearing architectural fact of the whole design.
- Two-symbol handshake: `uint32_t engine_plugin_abi_version(void)` (host checks this BEFORE calling anything else — the libretro `retro_api_version()` pattern) and `int32_t engine_plugin_register(const EngineHostApi*, EngineContextHandle)`.
- Define the narrow vtable operations for v1: log a message, register a named tick/update callback, and ONE entity query — **batched by construction** (fill a caller-provided buffer with `(id, x, y)` tuples in a single call). A per-entity FFI call costs more than a Python attribute access; the batched shape is what keeps a future performance story structurally possible. No component type registration or Python object creation from native in v1.
- Entity identity across the boundary: opaque `uint64` handles interned by the host (engine entity ids are `uuid.UUID` objects — never pass them as strings).
- v1 safety rules, stated in the header and enforced/documented by the host: the vtable and handle are valid only on the thread that invoked register/tick (GIL rule); the host pins all ctypes callback objects for process lifetime; native libraries are never dlclosed in v1; Rust plugins must not let panics unwind across `extern "C"` (`catch_unwind` → error code); all entry points return error codes, never throw.
- Version the surface and mark it **experimental/unstable** in the header and guide — ABI promises are effectively forever once declared stable; v1 must remain free to change.
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

- Add an optional `native_plugins` array in the JSON (named unambiguously — `plugins` stays free for any future Python-level plugin concept).
- Each entry minimally carries: `name`, `entry` (symbol or module), `abi_version`, `required` (bool, default false — P3-D's error policy keys off this; the original draft referenced plugins "marked required" without declaring the field), optional `path` (relative inside the archive or system library name), and `metadata`. Per-platform path maps are deferred (v1 is single-platform dev).
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
- Builds the `EngineHostApi` vtable + a safe opaque handle (ctypes-based) exposing only the v1 surface, and **pins every ctypes callback object on the host for process lifetime** (a dropped CFUNCTYPE reference is a dangling function pointer and a segfault — the classic ctypes failure mode).
- Queries `engine_plugin_abi_version()` first; only on compatibility calls the register entry with vtable + handle.
- Records loaded native modules and **enforces the v1 no-unload rule**: native libraries are never dlclosed (ctypes has no supported dlclose, and registered callbacks make it unsafe regardless). `CartridgeLoader.unload()` on a cartridge with loaded native plugins emits a visible warning that the library remains resident for the process lifetime, deferring real teardown to P4-A — the loader's full-rollback symmetry is broken knowingly and loudly, not silently.
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
- A tiny build note or `build.rs` / Makefile snippet so a developer on the current platform (Linux) can `cargo build` and get a loadable artifact (note: rustup binaries live at `~/.cargo/bin`, not necessarily on the default shell PATH).
- The Rust skeleton demonstrates panic safety: `catch_unwind` at every `extern "C"` boundary, returning an error code.
- A **one-file C test plugin** (`test_plugin.c`, a few dozen lines) compiled in a pytest fixture via `cc -shared` (milliseconds; gcc already present) so the PluginHost gets fast, always-on unit tests in the standard suite. The Rust crate stays the authoring reference, verified manually or behind a toolchain-presence skip.
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
- Covers the loader integration points, error messages a developer will see, and an explicit "What v1 cannot do" section (no component registration from native, no Python objects across the boundary, no calling the vtable from native-spawned threads, no unload, no stable-ABI promise yet).
- States the trust model plainly: a native plugin is arbitrary code execution — exactly like a Python cartridge already is. No new trust boundary is crossed; sandboxing remains explicitly out of scope (see Follow-On).
- Documents the pyo3 "easy mode" alternative per the P3-B0 decision record (a compiled extension module loaded via plain `systems.register`), so authors who just want Rust-in-a-cartridge are not forced through the C ABI.
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
- **2026-06-10 viability evaluation pass**: corrected the stale P3-A premise — `engine/cartridge/context.py` exists and loader.py is context-first through hook/register/teardown paths (the "complete absence of context.py" claim in the note above predates P1-C landing; kept for historical honesty). Key discovery: a pyo3 abi3 extension module is loadable through the existing `systems.register` path with zero engine changes, so "native code in a cartridge" is already possible — the phase's genuinely new artifact is the language-neutral C ABI. New P3-B0 spike track de-risks P3-B from Large to Medium and gives the phase a sanctioned pause point. v1 safety rules (vtable-not-symbols, two-symbol handshake, thread/GIL rule, callback pinning, no-unload, panic safety, u64 interned ids, batched query, experimental marking) folded into P3-B/P3-D. Performance rationale reframed: the v1 boundary is a contract/extensibility story; the perf story belongs to FUTURE_TASKS Task D (dict-of-dicts World means per-entity FFI is slower than Python). Toolchain verified on the dev machine: gcc 13.3, Rust 1.96 via rustup (`~/.cargo/bin`), Python 3.14 + stdlib ctypes (zero new Python deps for the C-ABI route).

## Outcome

*(To be filled when the phase is complete.)*

- What shipped.
- What was deferred (moved to Follow-On or the new FUTURE_TASKS section).
- What should happen next (e.g. Phase 4 isolation/host work, richer FFI surfaces, first real cartridge using a native plugin for performance-critical logic, integration with tgl_demo or a new reference cartridge, ABI stability review).

---

## Optional Sections (populated for signal)

**Files affected (initial map)**

- Modified (light): `engine/cartridge/context.py` (version & freeze the existing facade — `api_version` + evolution rules; the facade itself already exists)
- New (spike, P3-B0): two throwaway hello artifacts (pyo3 crate + C-ABI cdylib with ctypes harness) and a short decision record (e.g. `docs/notes/native_mechanism_decision.md`)
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