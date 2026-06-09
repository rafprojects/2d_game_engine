# Phase 4 - Isolation & Multi-Cartridge Host Readiness

**Status:** Planned  
**Created:** 2026-06  
**Last updated:** 2026-06 (initial draft from vision extraction + user choices)

### Tracks

| Track | Description | Status | Effort |
|-------|-------------|--------|--------|
| P4-A | Explicit `unload_cartridge` / teardown support in `CartridgeLoader` and `LoadedCartridge` (symmetric cleanup for Python path, asset mounts via `ResourceManager.unmount_asset_root`, system deregistration hooks, SaveState attachments, native plugin handles, and optional `teardown` hook on entry instances) | Planned | Medium-Large |
| P4-B | Import isolation improvements (migrate or augment cartridge Python loading away from raw unconditional `sys.path.insert`; use `importlib.util` for module isolation where practical, or robust tracking + removal; document supported model and limitations clearly) | Planned | Medium |
| P4-C | CartridgeContext lifecycle integration (ensure the facade from prior phases exposes or enables self-unload / teardown; Context carries loader reference or unload capability so cartridges and native plugins can participate in their own cleanup) | Planned | Small-Medium |
| P4-D | Skeleton "Cartridge Host" example application (minimal runnable host under `examples/hosts/multi_cartridge_host.py` or equivalent that can list, load, run, unload, and switch between 2+ cartridges — one being tgl_demo or a stub — demonstrating clean re-load without pollution; simple console-driven or headless; comments on native plugin cleanup) | Planned | Medium |
| P4-E | Documentation, guide updates & verification (update `cartridge_loader_guide.md` Known Limitations and add "Unload & Multi-Cartridge" section; document the host skeleton and patterns; add or expand tests for full load/unload/reload cycles and host scenarios; sync `CARTRIDGE_VISION` pointers later) | Planned | Small |

---

## Rationale

Briefly explain why this phase exists now.

1. The cartridge vision has always treated the single-cartridge-per-process model as primary (NES/console mental model) while explicitly requiring that the architecture "must not preclude" secondary future uses: multi-cartridge "host" or menu applications that can load, switch, or compose cartridges. After Phase 1 (system polish including early loader hygiene plans), Phase 2 (retro layer), and Phase 3 (native boundary), the loader still only supports one-way loading: raw `sys.path.insert`, asset root stacking with no coordinated unmount in the cartridge path, `self.loaded` that only accumulates, no public `unload_cartridge`, and no symmetric `teardown` hook on entrypoints. This makes repeated dev loads, safe re-entrancy, and any host that switches games fragile or impossible without leaks and pollution. The AUDIT and vision both surface this as the "Hardening & Multi-Cartridge Future" / "Isolation & Multi-Cartridge Host Readiness" work.

2. These items belong together as one phase because they form the complete isolation seam: the unload/teardown mechanism (the action), import + asset + system + native cleanup (the hygiene), Context integration (the clean API surface for lifecycle), a concrete host skeleton that proves the seam works end-to-end, and the documentation that makes the capability usable and discoverable. Without the host skeleton the unload work remains unproven for the stated secondary use case.

3. Success looks like: `loader.unload(name_or_context)` (or `LoadedCartridge.unload()`) exists and is callable; after unload the injected python path is no longer polluting sys.path (or is properly managed), asset roots are unmounted, any registered systems/providers have had a chance to clean up via World hooks or explicit calls, native plugin handles (from Phase 3) are released, and a second (or the same) cartridge can be loaded cleanly in the same process. A minimal host skeleton can start, list cartridges, load tgl_demo (or a stub), exercise it, unload, load another, and demonstrate observable cleanup and re-entrancy. Existing single-cartridge usage (tgl_demo dir/.car, hot-restart inside a cartridge) is completely unaffected or improved.

## Key Decisions

| # | Decision | Resolution |
|---|----------|------------|
| A | Filename / title for the tracking doc | `PHASE4_ISOLATION_MULTI_CARTRIDGE.md` titled "Phase 4 - Isolation & Multi-Cartridge Host Readiness" (close match to AUDIT "Phase 4 – Isolation & Multi-Cartridge Host Readiness" and the "Phase 4+" pointer in CARTRIDGE_VISION.md). |
| B | Scope for PHASE4 | Strict to the AUDIT Phase 4 core (proper module unloading / import isolation via importlib.util, explicit `unload_cartridge` / teardown hooks, skeleton "Cartridge Host" example app). Synthesize and promote the items already pre-populated in FUTURE_TASKS (from the Phase 3 offload choice). Per the "Other" scoping answer: bring the core FUTURE isolation items into the formal PHASE4 tracks and delete those items from FUTURE_TASKS.md to keep the task queue clean. Offload broader concerns (full security/sandbox models for untrusted multi-cartridge hosts, advanced GUI/menu host polish, production hot-swapping, etc.) or leave them in FUTURE if they surface. |
| C | Representation of prior phases | "Assume PHASE1 (polish), PHASE2 (retro), and PHASE3 (native boundary) complete; PHASE4 focuses on new isolation/host work with minimal backward references" (like the PHASE2 precedent). Light acknowledgments only where a direct dependency is required (e.g. Context for self-unload, native handles from P3 needing cleanup, P1-B loader hygiene as foundation). |
| D | Vision reference / cross-linking | Leave the thin `docs/CARTRIDGE_VISION.md` as-is for now (its current "Phase 4+: Isolation / multi-cartridge host readiness" pointer + link to the AUDIT is sufficient; the new PHASE4 doc will self-reference the AUDIT). |
| E | Cartridge Host skeleton scope, location, and demonstration | Minimal runnable host skeleton at `examples/hosts/multi_cartridge_host.py` (or similar conventional location). It must be able to list/load/run/unload/switch between 2+ cartridges (one being tgl_demo or a representative stub), use the new unload API + Context, demonstrate clean re-load without sys.path/asset/system pollution, and include comments on native plugin cleanup (if Phase 3 artifacts are present). Keep it headless or very simple console-driven (no full GUI). |
| F | FUTURE_TASKS hygiene | When formalizing the pre-existing "Isolation, Unload Hygiene & Multi-Cartridge Host Readiness" subsection from the Phase 3 FUTURE append, remove or substantially trim those specific items from FUTURE_TASKS.md so the queue stays clean and non-duplicative. The PHASE4 doc becomes the authoritative tracking surface for this work. |

## Execution Priority

1. P4-A - Core unload / teardown hooks in the loader. Everything else (isolation hygiene, Context integration, host, docs) depends on having a working, observable unload path and entrypoint teardown hook.

2. P4-B - Import isolation. Critical for preventing the pollution that currently makes re-loading or multi-cartridge scenarios unsafe; pairs directly with unload.

3. P4-C - CartridgeContext lifecycle tie-in. Makes the prior-phase facade the sanctioned place for cartridges (and future native code) to participate in their own cleanup without reaching into loader internals.

4. P4-D - Host skeleton. The proof that the isolation seam supports the documented secondary mental model; without a runnable example that actually switches cartridges cleanly the phase is incomplete.

5. P4-E - Documentation + verification. Updates the public "Known Limitations," provides patterns, and ensures the full load/unload/reload + host cycle is tested and documented.

## Track P4-A - Explicit Unload / Teardown Hooks

### Problem

`CartridgeLoader` only implements one-way loading (`load_directory`, `load_archive`). It unconditionally does `sys.path.insert`, calls `mount_asset_root(prepend=True)`, populates `self.loaded`, runs `initialize`/`register` hooks, and attaches manifests to the SaveStateManager. There is:

- No `unload_cartridge(name)` or equivalent on the loader or on `LoadedCartridge`.
- No symmetric `teardown` / `unload` hook called on the entry instance (only `mount`/`load`/`initialize`).
- No coordinated unmount of the cartridge's asset root (even though `ResourceManager.unmount_asset_root` exists).
- No cleanup of injected sys.path entries, registered systems (beyond what World entity removal provides), SaveState attachments, or (future) native plugin handles.

The cartridge_loader_guide explicitly documents this as a limitation: "Only one cartridge overlay is active at a time; ... does not tear down previously loaded systems." "Mounted overlays remain until the session ends."

This directly blocks safe repeated loading in dev, hot-restart patterns beyond cartridge-internal `.reset()`, and any multi-cartridge host.

### Fix

Add to `CartridgeLoader`:

- `unload(self, name_or_context: str | LoadedCartridge) -> bool`
- Or an instance method on `LoadedCartridge`: `def unload(self) -> bool`

Implementation responsibilities for unload:

- Locate the matching `LoadedCartridge`.
- If the entry instance has a callable `teardown` (or `unload`), invoke it with appropriate args (world, base, manifest or Context).
- Remove the cartridge's python_path from `sys.path` if it was the one we inserted (track what we added).
- Call `resource_manager.unmount_asset_root(...)` for the cartridge's assets mount (if resource_manager present and method exists).
- Remove the entry from `self.loaded`.
- For systems that were registered via the manifest, either rely on World `on_entity_removed` + system hooks for entity cleanup or provide an explicit deregistration opportunity.
- If a SaveStateManager is attached, give providers a chance to unregister or snapshot final state.
- For Phase 3 native plugins: release any loaded native handles / call native unload symbols if the surface defined them (defensive; keep narrow).
- Return success/failure and leave clear diagnostics.

Also consider adding an optional `teardown` hook support symmetrically to the existing hook runner.

`LoadedCartridge` can grow a `unload(self)` convenience that delegates to its loader.

Make unload safe to call multiple times (idempotent).

### Acceptance criteria

- After `loader.unload(cartridge_name)` (or `context.unload()`), the cartridge's python path is no longer at the front of `sys.path` (or is fully removed if we were the only inserter).
- Asset roots no longer contain the cartridge mount (verifiable via `resource_manager.asset_roots`).
- Any `teardown` hook the cartridge provided was invoked.
- A subsequent `load` of the same or a different cartridge succeeds without duplicate systems or path collisions.
- Single-cartridge usage (current tgl_demo flows, including its internal hot-restart) continues to work unchanged.

### Validation

- Manual: `python main.py --cartridge examples/cartridges/tgl_demo`, exercise, request unload (new CLI or direct in a test), inspect `sys.path` and resource roots, load again or a second cartridge.
- Unit/integration test: load → exercise (spawn entities, register providers) → unload → assert no path pollution, no lingering asset roots from the cartridge, re-load succeeds, World entities from the cartridge are gone or properly cleaned via hooks.
- If native plugins (P3) are present in the test cartridge, their handles are released without crash.
- Existing cartridge tests continue to pass.

## Track P4-B - Import Isolation Improvements

### Problem

Both `load_directory` and `load_archive` do:

```python
if path_str not in sys.path:
    sys.path.insert(0, path_str)
```

This is unconditional, global, and irreversible within the process. Multiple loads (or a host switching cartridges) accumulate entries, shadow standard library / engine modules, and make deterministic re-execution impossible. The vision plan and AUDIT both call out the need for "isolated import machinery (importlib.util)" or at least robust hygiene as part of hardening.

Raw `sys.path` mutation is the classic source of "cartridge A pollutes cartridge B" and "can't load the same cartridge twice cleanly."

### Fix

In the loader (and any helpers):

- Track exactly which paths were inserted by this loader instance for each `LoadedCartridge`.
- On unload, remove only the entries we own (prefer `sys.path.remove` with guards; handle duplicates).
- Preferred long-term: switch the cartridge Python loading to `importlib.util.spec_from_file_location` + `module_from_spec` + `exec_module` (or a small `CartridgeImporter` meta path finder) so that the cartridge's `python/` tree is isolated under its own package namespace or at least does not require mutating the global `sys.path` at all. This also enables proper `unload` by dropping the module from `sys.modules` (with care around references).

Provide a clear documented fallback or compatibility mode if full isolation proves too disruptive for existing cartridges that rely on absolute imports from the cartridge root.

At minimum, make the current raw-insert path fully reversible on unload, and add prominent warnings + guidance in the loader guide and new host docs.

If full `importlib` isolation is implemented, ensure it still allows the cartridge's `register` modules and entrypoint to be importable exactly as today, and that native plugins (P3) can still be declared/loaded from the same cartridge tree.

### Acceptance criteria

- After unload, the cartridge's python path entry is no longer present in `sys.path` (or the isolation mechanism has dropped its modules).
- Re-loading the identical cartridge (or a different one) in the same process does not cause import shadowing or "module already loaded with different state" surprises for cartridge code.
- The change is transparent to existing pure-Python cartridges (tgl_demo continues to import its `tgl.*` modules the same way).

### Validation

- Test that repeatedly does: load tgl_demo, exercise (imports succeed), unload, assert path clean, load again, imports still succeed, no duplicate modules in sys.modules for the cartridge package.
- A second distinct cartridge can be loaded after the first is unloaded without the first's modules shadowing the second.
- If `importlib` isolation is used, a smoke that the cartridge entrypoint and its `systems.register` modules are still found and executed.

## Track P4-C - CartridgeContext Lifecycle Integration

### Problem

Prior phases introduced (or planned) `CartridgeContext` as the clean, versioned surface passed to hooks and register. For isolation and host scenarios to be first-class, the Context must participate in lifecycle: a cartridge (or its native plugin) should be able to ask "unload me" or register cleanup without holding a raw reference to the private `CartridgeLoader` instance.

Currently the loader still passes raw `world`/`base`/`manifest` in hooks (or will be updated by P1/P3 work). Without Context owning or exposing the unload capability, cartridges that want to support host-driven switching have no sanctioned way to participate in their own teardown.

### Fix

Ensure / extend `CartridgeContext` (from the P1-C / P3-A work) so that it:

- Holds a reference (or weakref) back to the loader (or a narrow "lifecycle manager" protocol).
- Exposes `unload()` or `request_unload()` that delegates safely.
- During construction in the loader, the Context is what gets passed to `initialize(world=..., base=..., manifest=..., context=...)` or however the prior phases evolved the signature (keep backward compat if needed).
- Native plugin surface (P3) can be given a safe handle that allows requesting unload or registering a native cleanup callback.

The Context becomes the single place a cartridge author looks for "how do I participate in being unloaded by a host?"

Update the loader to always create and pass a Context (per prior phase decisions) and to use it for the unload flow.

### Acceptance criteria

- A cartridge entry instance received via its `initialize` (or stored) a `CartridgeContext` that has a usable `unload()` (or the loader is reachable via the context in a supported way).
- Calling context-driven unload performs the same cleanup as direct `loader.unload`.
- Native "hello" style plugins (or real ones) from Phase 3 can be extended to request or react to unload via the safe handle.

### Validation

- In the new host skeleton and in tests, cartridges use the Context to participate in lifecycle.
- Documentation examples show the supported pattern.

## Track P4-D - Skeleton "Cartridge Host" Example Application

### Problem

The AUDIT and vision both require a "Skeleton 'Cartridge Host' example application" as the concrete demonstration that the architecture supports the secondary multi-cartridge model. Without a runnable, copyable example that actually loads one cartridge, unloads it cleanly, loads another, and shows observable isolation, the unload + import work remains theoretical for the stated use case. The vision verification criteria even call out a stretch: "A second minimal cartridge can be loaded in the same session (or after explicit unload) without crashing."

### Fix

Create a minimal, self-contained runnable skeleton, e.g.:

`examples/hosts/multi_cartridge_host.py`

Requirements per user choice:

- Simple console-driven or key-driven interface (headless-friendly; e.g. numbered menu: 1=load tgl_demo, 2=load other_stub, u=unload current, s=switch, q=quit, or command-line args for scripted runs).
- Discover/list a small set of cartridges (hard-coded paths for the example, or scan a dir; one entry is `examples/cartridges/tgl_demo` or a packaged variant; another is a tiny stub cartridge that exists or is generated for the example).
- Use the (new) public loader + Context + unload APIs.
- Load a cartridge, let it run for a bit (or until a switch key), call unload, verify/ print observable cleanup (e.g. "sys.path cleaned", "asset root gone", "entities removed").
- Load the second (or same) cartridge and demonstrate that it runs cleanly (no duplicate systems, no path shadowing, fresh state).
- Include prominent comments / docstring explaining:
  - How the host uses the unload API.
  - What a well-behaved cartridge should implement (`teardown` hook).
  - Notes on native plugin (Phase 3) handle cleanup.
  - Limitations (still single active at a time for v1 host; full concurrent composition is later).
- Keep the host tiny — its only job is to prove the lifecycle seam works for the documented secondary model. It can drive the engine's `Game` / ShowBase in a simple loop or use the existing main machinery where possible.

Optionally provide a tiny second "stub" cartridge (or reuse tgl_demo with different config) so the example is runnable out of the box without extra setup.

### Acceptance criteria

- The host script can be run and successfully load → exercise → unload → load a different (or same) cartridge → exercise again without crashes, duplicate registrations, or obvious pollution.
- Cleanup is observable (printed diagnostics or assertions in a test wrapper).
- The example is referenced from the updated loader guide and the PHASE4 doc.

### Validation

- Manual run of the host skeleton on the current platform: follow the on-screen instructions, switch cartridges, watch cleanup messages, confirm second cartridge behaves as a fresh load.
- Automated smoke (if feasible without interactive input): a test harness that drives the host logic or directly exercises the same load/unload/switch sequence using the public APIs and asserts post-unload state.
- tgl_demo (or the stub) continues to be usable both standalone (`--cartridge`) and when driven from the host.

## Track P4-E - Documentation, Guide Updates & Verification

### Problem

The public `cartridge_loader_guide.md` still lists the old limitations ("Only one cartridge overlay...", "Mounted overlays remain until the session ends"). There is no documented pattern for writing a `teardown` hook, using the new unload API, or building a minimal host. Without updated docs and a verification story (tests that actually exercise multi-cartridge cycles), the capability will be under-used and the "Known Limitations" will become stale rather than being retired.

### Fix

- Update `docs/guides/cartridge_loader_guide.md`:
  - Revise or remove the "Known Limitations" bullets that are now addressed.
  - Add a new section "Unload, Teardown, and Multi-Cartridge Hosts" describing the new APIs, the optional `teardown` hook contract, best practices for cartridges that want to be host-friendly (idempotent cleanup, using Context for self-unload), and a pointer to the host skeleton example.
- Add light cross-references in the thin `CARTRIDGE_VISION.md` or other guides only as needed (per choice to leave CARTRIDGE_VISION largely as-is for now).
- Ensure the new `examples/hosts/multi_cartridge_host.py` has a good README comment block or sibling `.md`.
- Add or expand tests (unit for loader unload paths + integration that exercises a full pack/load/unload/reload or host-driven switch cycle). These can live under `tests/integration/test_cartridge_lifecycle.py` or similar.
- In the host skeleton and tests, exercise the native plugin cleanup comments (even if just a no-op when no native is present).

### Acceptance criteria

- The loader guide no longer claims "no teardown" as a hard limitation; instead it documents the supported unload story.
- A developer can read the guide + look at the host skeleton and understand how to make a cartridge host-safe and how to write a simple switcher.
- The host example appears in any "examples" or "cartridges" navigation.

### Validation

- Link / content review of the updated guide.
- A reader (or the author) following the new host + guide material can run the skeleton and see a clean switch.
- New tests for the unload + host scenarios are part of the regular test suite and pass in CI.

## Follow-On Candidates

List items that were surfaced but intentionally left out of this phase.

| Candidate | Why it is deferred |
|-----------|--------------------|
| Full security / sandbox / provenance model for untrusted cartridges and native plugins in a host | Ecosystem-level concern (signing, capability restrictions, process isolation for native code). Becomes relevant only after real multi-cartridge usage and at least one non-toy host exist. Some aspects were already noted in the Phase 3 FUTURE append. |
| Advanced / production "Cartridge Host" (GUI menu, live hot-swap while a cartridge is running, concurrent composition of multiple active cartridges, save-state handoff across switches) | The phase delivers the minimal skeleton that proves the seam. Richer host UX and live-swapping are natural follow-on engineering once the basic unload/isolation contract is stable and exercised. |
| Automatic hot-reload / watch support across cartridge boundaries in a host | Existing `HotReloadManager` is per-process; extending it cleanly for host-driven cartridge trees is valuable but secondary to getting basic unload working. |
| Subprocess + IPC isolation model as an alternative to in-process import isolation | One of the options called out in the vision and in the pre-populated FUTURE items. Can be explored later as a higher-safety deployment mode for hosts; the in-process `importlib` + unload path is the pragmatic first step. |
| Richer lifecycle events (CartridgeLoadedEvent, CartridgeUnloadedEvent, etc.) on the World event bus | Nice-to-have for host authors and for cartridges that want to react to being switched in/out. Can be added on top of the basic unload hooks once the core mechanism exists. |

## Implementation Notes

- This PHASE4 document was created following `docs/PHASE_REPORT_TEMPLATE.md` and the exact structure/tone of the prior PHASE1/PHASE2/PHASE3 tracking docs. Extraction sources: the original vision plan (019e612c.../plan.md) whose Phase 3 was "Hardening & Multi-Cartridge Future", the AUDIT (primary Phase 4 section and gap table), the current CARTRIDGE_VISION.md (still points to Phase 4+), PHASE3_NATIVE_PLUGIN_BOUNDARY.md (which explicitly offloaded this work), PHASE1 (which already had a P1-B "Loader lifecycle & isolation" track whose remaining items are now promoted here), FUTURE_TASKS.md (the "Isolation, Unload Hygiene & Multi-Cartridge Host Readiness" subsection that was pre-populated during Phase 3 planning), cartridge core sources (loader.py still has only load paths + raw inserts; no unload or teardown; ResourceManager has `unmount_asset_root` and `mount_asset_root`; World has strong `on_entity_removed` hooks), the cartridge_loader_guide.md Known Limitations, main.py `_load_cartridge` (load-only), greps confirming absence of any unload/teardown/host code, and the explicit user choices via ask_user_question.
- Scope was kept to the AUDIT Phase 4 definition. Per the "Other" scoping answer, the pre-existing isolation items in FUTURE_TASKS are being brought into the formal tracks here; those specific items will be deleted/trimmed from FUTURE_TASKS.md in the same turn to keep the queue clean and non-duplicative.
- Representation is "assume prior phases complete + minimal backward refs" per the user's choice (PHASE2 precedent). Only light mentions of Context (P3/P1), native handles (P3), and earlier loader hygiene appear where they are direct prerequisites.
- The host skeleton is deliberately minimal and console-driven per the exact user answer; it uses tgl_demo (or a stub) as one of the switchable cartridges and demonstrates the observable cleanup + clean re-load that the vision verification criteria called out as a stretch goal.
- ResourceManager already provides the `unmount_asset_root` primitive (confirmed in source), which the unload implementation can and should use. World removal hooks are already strong and will be leveraged by cartridge-registered systems.
- Keep this document as the executive record. Detailed design for the exact `teardown` signature, the importlib isolation strategy trade-offs, or the host's internal loop can live in the implementation PRs and the example itself.
- Update status, last-updated date, and tracks table as work lands. Move completed track details into the Outcome section when the phase is declared complete. After this phase lands, the "Phase 4+" language in CARTRIDGE_VISION can be updated in a follow-up pass.

## Outcome

*(To be filled when the phase is complete.)*

- What shipped.
- What was deferred (moved to Follow-On or remaining FUTURE items).
- What should happen next (e.g. richer host UX, security model for untrusted cartridges, full concurrent multi-cartridge composition, integration of unload into tgl_demo dev tooling or main.py, production packaging concerns for hosts).

---

## Optional Sections (populated for signal)

**Files affected (initial map)**

- Modified: `engine/cartridge/loader.py` (add `unload` / teardown logic, track inserted paths, possibly refactor load to support isolation), `engine/cartridge/context.py` (lifecycle / unload exposure if not already complete from prior phases)
- New: `examples/hosts/multi_cartridge_host.py` (or `examples/hosts/` package + the skeleton + comments)
- Possibly a minimal second stub cartridge under `examples/cartridges/` for the host example if a dedicated one is preferred over reusing tgl_demo
- Modified (docs): `docs/guides/cartridge_loader_guide.md` (Known Limitations + new unload/host section)
- Modified: `docs/FUTURE_TASKS.md` (trim / delete the "Isolation, Unload Hygiene & Multi-Cartridge Host Readiness" subsection whose items are now tracked here)
- Tests: new or expanded integration coverage for cartridge unload cycles and the host-driven switch scenario (e.g. `tests/integration/test_cartridge_lifecycle.py`)
- This PHASE4 tracking doc + the session plan.md record

**Testing Strategy**

- All existing cartridge, save-state, and loader unit tests continue to pass (unload is additive; single-cartridge flows are unaffected or improved).
- Dedicated tests for unload: load (dir + archive), assert state, unload, assert sys.path / asset_roots / loaded dict cleaned, re-load succeeds, no lingering entities or duplicate registrations.
- Host skeleton smoke: the example can be driven (manually or via a thin test harness) through list → load A (tgl_demo or stub) → exercise → unload → load B → exercise → unload → clean exit. Observable cleanup is asserted where possible.
- Native plugin interaction (if Phase 3 work is present): a cartridge declaring a native plugin can be loaded/unloaded in the host or via the loader without leaks or crashes on the native side (at minimum the handle is released).
- Manual verification on the development platform that the host skeleton works end-to-end and that tgl_demo remains usable both standalone and when hosted.
- Pre-push / CI runs the expanded lifecycle tests. Note that full cross-platform native dlclose behavior and production host robustness are follow-on.

*This phase completes the "secondary" half of the cartridge mental model: cartridges are not only self-contained units that can be packaged and run, but units that can be cleanly brought up and torn down inside a larger host process without permanently mutating the interpreter or engine state. The unload seam, import hygiene, Context lifecycle, and a working host skeleton turn the documented future use case into a demonstrable capability.*

---

**End of Phase 4 planning document (following PHASE_REPORT_TEMPLATE.md and the established PHASE1–PHASE3 pattern).**