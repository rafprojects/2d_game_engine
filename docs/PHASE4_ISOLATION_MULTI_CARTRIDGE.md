# Phase 4 - Isolation & Multi-Cartridge Host Readiness

**Status:** Planned  
**Created:** 2026-06  
**Last updated:** 2026-06-10 (viability evaluation pass: core premise corrected — `loader.unload()` landed with P1-B; P4-A rescoped to ownership-tracked teardown and absorbs FUTURE_TASKS Task E; P4-B rescoped to sys.modules hygiene; P4-D split into D1 reboot-to-switch + D2 in-process; per-track Risks added — see Implementation Notes)

### Tracks

| Track | Description | Status | Effort |
|-------|-------------|--------|--------|
| P4-A | Ownership-tracked teardown (the unload skeleton landed with P1-B — `loader.unload()` already removes sys.path entries, unmounts assets, runs teardown hooks, unregisters save providers; this track adds what it cannot clean today: `World.remove_system` + Context-mediated creation wrappers recording systems/entities/event-subscriptions/`accept` bindings per cartridge, with unload walking the ledger; absorbs FUTURE_TASKS Task E, makes Task F a near-freebie) | Planned | Medium-Large |
| P4-B | Module hygiene + documented limits (the sys.path half is already tracked and reversible; the real gap is `sys.modules` — purge cartridge modules by package prefix on unload so re-load gets fresh code; ship a written "supported model & limitations" statement — best-effort by design; full importlib namespace isolation demoted to Follow-On) | Planned | Small-Medium |
| P4-C | CartridgeContext lifecycle integration (`context.loader` already exists on the facade; remaining: a sanctioned `context.unload()` convenience and housing the P4-A ownership wrappers — `context.add_system` / `context.create_entity` / `context.accept`; may fold into P4-A's PR) | Planned | Small |
| P4-D1 | Reboot-to-switch "Cartridge Host" (process-per-cartridge: a tiny menu/launcher spawning `main.py --cartridge <path>` per selection, reclaiming control on exit; leak-proof by construction — the authentic console power-cycle model; zero dependencies on other tracks, ships first) | Planned | Small |
| P4-D2 | In-process switch host (the original P4-D: load → unload → load another inside one process; depends on A/B/C plus window/camera/aspect2d state reset between cartridges — Panda3D allows exactly one ShowBase per process, so the host's `base` is shared and cartridge window-property mutations persist across switches) | Planned | Medium |
| P4-E | Documentation, guide updates & verification (update `cartridge_loader_guide.md` Known Limitations and add "Unload & Multi-Cartridge" section including the explicit CPython best-effort-unload statement; document both host models and the tracked-vs-untracked ownership contract; add or expand tests for full load/unload/reload cycles and host scenarios) | Planned | Small |

---

## Rationale

Briefly explain why this phase exists now.

1. The cartridge vision has always treated the single-cartridge-per-process model as primary (NES/console mental model) while explicitly requiring that the architecture "must not preclude" secondary future uses: multi-cartridge "host" or menu applications that can load, switch, or compose cartridges. **Honesty note (2026-06-10 evaluation):** the original draft claimed the loader "only supports one-way loading" — that is stale. `loader.unload()` landed with P1-B and already handles teardown hooks (context-first), asset unmount, tracked sys.path removal, and save-provider unregistration, with unit tests. What actually blocks safe re-loading and host switching is everything the loader never *tracked*: cartridge-registered systems (no `World.remove_system` exists), cartridge-created entities, event-manager subscriptions, raw `base.accept` hotkey bindings (both reference demos bind directly on `base`), and stale `sys.modules` entries. Those five leaks — plus the fact that Panda3D allows exactly one ShowBase per process — define the real work of this phase. The AUDIT and vision both surface this area as the "Hardening & Multi-Cartridge Future" / "Isolation & Multi-Cartridge Host Readiness" work.

2. These items belong together as one phase because they form the complete isolation seam: the unload/teardown mechanism (the action), import + asset + system + native cleanup (the hygiene), Context integration (the clean API surface for lifecycle), a concrete host skeleton that proves the seam works end-to-end, and the documentation that makes the capability usable and discoverable. Without the host skeleton the unload work remains unproven for the stated secondary use case.

3. Success looks like: *(already true today)* `loader.unload(name_or_context)` exists, removes the injected python path, unmounts asset roots, runs teardown hooks, and unregisters save providers; *(the Phase 4 bar)* after unload the cartridge's systems, entities, event subscriptions, and key bindings are gone, its modules are purged from `sys.modules`, and a second (or the same) cartridge loads cleanly in the same process with fresh state. The reboot-to-switch host (P4-D1) ships the user-visible switching story leak-proof from day one; the in-process host (P4-D2) demonstrates the deeper seam. Existing single-cartridge usage (tgl_demo dir/.car, hot-restart inside a cartridge) is completely unaffected or improved.

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

*(Resequenced 2026-06-10: the original order put the easiest, highest-value deliverable last and gated it on the hardest, least-bounded work.)*

1. P4-D1 - Reboot-to-switch host. Zero dependencies, ~50-100 lines, ships the user-visible multi-cartridge story immediately and leak-proof by construction. Delivering the product value first means the rest of the phase is judged as the developer-iteration feature it honestly is, not as a gate.

2. P4-A - Ownership-tracked teardown. The real engineering core: `World.remove_system` + `ensure_system`, ownership recording via Context wrappers, unload walks the ledger. Absorbs FUTURE_TASKS Task E.

3. P4-B - Module hygiene. `sys.modules` purge by cartridge package prefix + the documented best-effort model. Pairs with A: both are required before in-process reload is trustworthy — and B before A produces stale objects executing against fresh modules (see B's risks).

4. P4-C - Context lifecycle tie-in. The sanctioned author-facing surface for A's wrappers plus `context.unload()`. (Small; may be folded into A's PR.)

5. P4-D2 - In-process switch host. The proof that A/B/C actually compose: load → unload → load another in one process, with window/camera state reset. This is the original P4-D, now honestly sequenced after its dependencies.

6. P4-E - Documentation + verification. Updates "Known Limitations" to the new truth (including the CPython best-effort statement), documents both host models and the ownership contract, and locks the cycle in tests.

## Track P4-A - Ownership-Tracked Teardown

*(Rescoped 2026-06-10 — the original premise is stale. The original track called for introducing `unload()`; it landed with P1-B.)*

### Problem

`CartridgeLoader.unload()` exists (loader.py) and already does most of what this track originally asked for: optional `teardown`/`unload`/`cleanup` hook (context-first with legacy fallback, symmetric to the load hooks), asset unmount via `ResourceManager.unmount_asset_root`, exact-ownership sys.path removal (tracked per cartridge), best-effort SaveStateProvider unregistration, removal from `self.loaded`, and idempotency. Unit tests cover the path/loaded-entry cleanup and the teardown hook.

What unload **cannot** clean today is everything the loader never tracked. The verified gaps — the five leaks:

1. **Systems** — `World` (engine/core/system.py) has no `remove_system`, and the loader does not know which systems a cartridge's `register()` added. (This is FUTURE_TASKS Task E by another name; this track absorbs it.)
2. **Entities** — nothing records which entities cartridge code created, at load time or runtime. They keep simulating after unload. The cleanup primitive exists (RenderSystem removes Panda nodes on `EntityDestroyedEvent`); the missing piece is knowing *which* entities to destroy.
3. **Event-manager subscriptions** made by cartridge systems are never unsubscribed.
4. **ShowBase `accept` bindings** — both reference demos bind hotkeys directly on `base`; after unload those handlers dangle: they keep cartridge modules alive (defeating P4-B's purge) and fire ghost behavior on the next keypress.
5. **(Forward) native plugin handles** — P3's no-unload rule means these warn and stay resident regardless; dlclose stays out of scope even here.

### Fix

Make ownership explicit, then have `unload()` walk the records:

- Add `World.remove_system(system)` — and an idempotent `ensure_system(cls, factory)` while in there (Task E's ask; this also makes tgl_demo's double Render/Input registration (Task F) fixable as a near-freebie).
- Add Context-mediated creation wrappers that record ownership per cartridge: `context.add_system(...)`, `context.create_entity(...)`, `context.accept(key, fn)` (tracked ShowBase binding), and a tracked event-subscribe. Each appends to a per-cartridge ledger on the `LoadedCartridge`.
- Extend `unload()` to walk the ledger in reverse: ignore accepts, unsubscribe events, destroy entities (the existing `EntityDestroyedEvent` flow cleans the Panda nodes), remove systems.
- Migrate both reference demos to the wrappers — they are the compliance proof and the documentation examples.
- State the contract plainly: **resources created outside the wrappers are not cleaned by unload** — those are the cartridge's responsibility via its `teardown` hook. Tracked = engine's job; untracked = yours.

### Risks

- **Bypass risk**: nothing forces cartridge authors through the wrappers — raw `world.add_system` / `base.accept` still work and still leak. Mitigation: the contract line above, the migrated demos as the only documented pattern, and optionally a dev-mode warning when cartridge code registers systems directly during the load window.
- **Migration churn**: both demos and any fixtures that register systems must move to the wrappers; the transitional dual path keeps old cartridges loading but un-cleanable.
- **Runtime spawns**: entities created during play are only tracked if spawned via the wrapper; document this loudly or accept that gameplay-spawned entities need the cartridge's own teardown.

### Acceptance criteria

- After `loader.unload(name)`: the cartridge's systems are out of `world.systems`, its tracked entities are destroyed (Panda nodes removed via the existing event flow), its tracked accepts/subscriptions are gone — plus everything unload already did (path, assets, providers, loaded dict).
- `World.remove_system` and `ensure_system` exist with tests; FUTURE_TASKS Task E is closed by this track and Task F is fixed or trivially fixable.
- Both reference demos register exclusively through the Context wrappers and survive load → exercise → unload → re-load with no ghost hotkeys and no duplicate systems.
- Single-cartridge usage (current flows, including cartridge-internal hot-restart) continues unchanged.

### Validation

- Unit/integration: load → spawn entities + register systems + bind hotkeys via wrappers → unload → assert `world.systems` clean, entities gone, no handler fires on an injected keypress, re-load succeeds fresh.
- The pre-existing P1-B unload tests continue to pass untouched.

## Track P4-B - Module Hygiene + Documented Limits

*(Rescoped 2026-06-10 — the sys.path half of the original track is already done: insertion is tracked per cartridge and removed on unload, with tests. The unsolved half is `sys.modules`.)*

### Problem

The loader never touches `sys.modules` (verified: zero references in loader.py). After unload removes the sys.path entry, the cartridge's modules remain cached — a re-load of the same cartridge imports the **stale** module objects with their old code and old module-level state. This, not sys.path, is the real import-isolation gap, and it is the direct blocker for in-process reload during cartridge development.

### Fix

- Track which top-level packages a cartridge's `python/` tree provides (e.g. `retro_sidescroller`, `tgl`).
- On unload, purge `sys.modules` entries matching those package prefixes.
- Detect and warn when two cartridges ship a same-named top-level package (shadowing across switches).
- Write the "supported model & limitations" statement for the loader guide (P4-E carries it): unload is **best-effort by design** — see Risks.
- Demote full `importlib` namespace isolation (loading each cartridge under a synthetic package namespace) to Follow-On: it breaks intra-package imports unless done very carefully, and no current use case needs two live copies of one cartridge. Purge-by-prefix covers the actual need (fresh re-load).

### Risks

- **CPython truth (the load-bearing one)**: guaranteed module unload is impossible. Purging `sys.modules` drops the *cache*, but any surviving reference — a dangling `base.accept` handler (P4-A leak #4), a tick callback, a closure held by an engine system — keeps the module object and everything it references alive. C extension modules never unload at all. The ceiling is "fresh import next time + best-effort memory release"; the docs must say so rather than imply hot-swap-grade isolation.
- **Order dependency**: purging modules while P4-A's leaks still hold references produces the worst of both worlds — stale objects from the old module graph executing alongside freshly imported ones. Land B after or with A, never before.
- **Engine-module collateral**: the purge must match cartridge package prefixes only; a sloppy prefix (or a cartridge shipping a package named like an engine module) could evict engine modules. Guard with an explicit allowlist built at load time from the cartridge's own tree.

### Acceptance criteria

- After unload, no `sys.modules` entry remains for the cartridge's package prefixes; re-load imports fresh module objects (module-level state reset).
- Loading a second cartridge after unloading the first shows no shadowing from the first's modules; same-name collisions produce a load-time warning.
- The limitations statement exists and is linked from the loader guide.
- The change is transparent to existing pure-Python cartridges (tgl_demo continues to import its `tgl.*` modules the same way).

### Validation

- Test: load tgl_demo → mutate a module-level sentinel → unload → re-load → sentinel is back at its initial value (fresh module object).
- A second distinct cartridge loads after the first's unload without the first's modules shadowing it.
- Negative test: engine modules (`engine.*`) are untouched by the purge.

## Track P4-C - CartridgeContext Lifecycle Integration

*(Rescoped 2026-06-10 — `context.loader` already exists on the facade with the self-unload pattern described in its docstring, and the loader already constructs and passes the Context context-first through hooks, register, and teardown. The original Problem text claiming "the loader still passes raw world/base/manifest" is stale.)*

### Problem

The capability exists but is neither sanctioned nor ergonomic: a cartridge wanting to participate in host-driven switching must reach through `context.loader.unload(context.manifest.name)`, and the P4-A ownership wrappers need an author-facing home.

### Fix

- Add `context.unload()` (or `request_unload()`) delegating to the loader with the right name — one obvious call.
- House the P4-A wrappers on the Context (`add_system` / `create_entity` / `accept` / event-subscribe) so the facade is the single surface a host-friendly cartridge author needs.
- Bump `CartridgeContext.api_version` per the P3-A evolution rules when these land.

### Risks

- **Track-splitting overhead**: this is small enough that a separate track may cost more coordination than it saves — fold into P4-A's PR if A's review stays manageable.
- **Facade growth**: each wrapper added to Context is surface area frozen by P3-A's versioning rules; add only the four ownership wrappers + `unload()`, resist convenience creep.

### Acceptance criteria

- A cartridge can self-unload via `context.unload()` with identical effect to `loader.unload(name)`.
- The ownership wrappers live on Context and are what the demos and the guide use.

### Validation

- The host skeletons (D1/D2) and lifecycle tests drive cleanup exclusively through the Context surface.
- Documentation examples show the supported pattern.

## Track P4-D1 - Reboot-to-Switch Host (process-per-cartridge)

*(New track from the 2026-06-10 evaluation — promoted, in simplified form, from the Follow-On "subprocess isolation" row.)*

### Problem

Real consoles do not unload cartridges — they power-cycle. Every in-process isolation concern (the five leaks, the ShowBase singleton, window-state pollution, CPython's unload limits) vanishes at a process boundary. The vision's stretch criterion ("a second minimal cartridge can be loaded in the same session ... without crashing") is satisfiable immediately, before any isolation work lands, by a host that spawns one process per cartridge.

### Fix

`examples/hosts/cartridge_host.py` (~50-100 lines):

- Discover cartridges (scan `examples/cartridges/` for `config/cartridge.json`; print name/version from each manifest).
- Console menu: pick one → spawn `python main.py --cartridge <path>` as a subprocess → wait → on exit, return to the menu (ESC in-game already quits cleanly).
- Print the power-cycle framing in the banner: each selection is a fresh process, which *is* the cleanup story.
- Comments point at P4-D2 for the in-process model and at the loader guide for the teardown contract.

### Risks

- **WSLg window churn**: each switch closes and opens an OS window (brief flicker / the documented WSLg focus dance). Cosmetic, not functional.
- **No state handoff**: save-state across switches is out of scope (already a Follow-On row); the host must not pretend otherwise.
- **Venv/interpreter assumptions**: spawn with `sys.executable`, not a hardcoded `python`, or the host breaks outside the venv.

### Acceptance criteria

- From the menu: launch tgl_demo, quit it, launch retro_sidescroller_demo, quit, relaunch the first — three clean runs, zero pollution possible by construction.
- Runnable on the current platform with nothing but the repo and venv.
- The example is referenced from the updated loader guide and this doc.

### Validation

- Manual run-through on the dev machine.
- Optional headless smoke: drive the menu logic with a stub command in place of main.py and assert the spawn/wait/return loop.

## Track P4-D2 - In-Process Switch Host

*(The original P4-D, now honestly sequenced after its dependencies A/B/C.)*

### Problem

The in-process model — load → unload → load another inside one interpreter — is the developer-iteration story (fast reload while authoring a cartridge) and the real proof that A/B/C compose. It is also where every missed leak shows up.

### Fix

As originally specified (console-driven `examples/hosts/multi_cartridge_host.py`; list/load/exercise/unload/switch; observable cleanup printouts; prominent comments on the teardown contract and native-plugin notes), plus the requirements the original draft missed:

- **Reuse the host's ShowBase**: Panda3D allows exactly one ShowBase per process; the host owns `base` and passes it to every load. A second ShowBase is a hard error, not a design option.
- **Reset shared window/scene state between cartridges**: window properties (title/size — cartridges request their own, e.g. the retro demo's 1024×960), camera, and any leftover aspect2d children must be restored to a known baseline on each switch.
- Drive all cleanup through the Context surface (P4-C) and print each ledger category as it is torn down.
- After each unload, print a **post-unload diff** (world.systems count, entity count, cartridge-prefix sys.modules entries) so residue is visible rather than silent.

### Risks

- **Leak whack-a-mole**: any resource acquired outside the tracked wrappers survives the switch. The post-unload diff is the mitigation — leaks become a printed number, not a mystery crash two switches later.
- **Window-state bleed**: without the explicit reset, cartridge B inherits cartridge A's window properties — easy to miss under WSLg where focus behavior already varies.
- **Expectation management**: this host demonstrates best-effort isolation, not sandboxing or hot-swap-grade unloading; the banner and docs must say so (P4-B's limitations statement).

### Acceptance criteria

- tgl_demo → unload → retro_sidescroller_demo → unload → tgl_demo again in one process: no duplicate systems, no ghost hotkeys, fresh module state, correct window properties for each.
- The post-unload diff shows zero unexplained residue for the two reference demos.
- Both demos remain usable standalone (`--cartridge`) and when hosted.

### Validation

- Manual switch session on the dev machine.
- Automated lifecycle test driving the same sequence headless (DummyBase) and asserting the diff is clean.

## Track P4-E - Documentation, Guide Updates & Verification

### Problem

The public `cartridge_loader_guide.md` still lists the old limitations ("Only one cartridge overlay...", "Mounted overlays remain until the session ends"). There is no documented pattern for writing a `teardown` hook, using the new unload API, or building a minimal host. Without updated docs and a verification story (tests that actually exercise multi-cartridge cycles), the capability will be under-used and the "Known Limitations" will become stale rather than being retired.

### Fix

- Update `docs/guides/cartridge_loader_guide.md`:
  - Revise or remove the "Known Limitations" bullets that are now addressed.
  - Add a new section "Unload, Teardown, and Multi-Cartridge Hosts" describing the APIs, the optional `teardown` hook contract, the **tracked-vs-untracked ownership contract** (resources created via the Context wrappers are the engine's job to clean; everything else is the cartridge's job in `teardown`), best practices for host-friendly cartridges (idempotent cleanup, `context.unload()`), and pointers to **both** host examples (D1 reboot-to-switch as the leak-proof default; D2 in-process as the dev-iteration model).
  - Include the P4-B limitations statement verbatim: in-process unload is **best-effort by design** — CPython cannot guarantee module unload (surviving references keep modules alive; C extensions never unload); the reboot host is the model with hard guarantees.
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
| Subprocess + IPC isolation model (rich form: live IPC, shared services, state handoff) | The simplified form — process-per-cartridge with no IPC — was **promoted to P4-D1** in the 2026-06-10 evaluation as the leak-proof default host. The rich form (host keeps services alive and talks to the cartridge process over IPC) remains follow-on. |
| Full `importlib` namespace isolation (each cartridge under a synthetic package namespace; two live copies of one cartridge concurrently) | Demoted from P4-B in the 2026-06-10 evaluation: it breaks intra-package imports unless done very carefully, and no current use case requires concurrent copies. `sys.modules` purge-by-prefix covers the actual need (fresh re-load). |
| Richer lifecycle events (CartridgeLoadedEvent, CartridgeUnloadedEvent, etc.) on the World event bus | Nice-to-have for host authors and for cartridges that want to react to being switched in/out. Can be added on top of the basic unload hooks once the core mechanism exists. |

## Implementation Notes

- This PHASE4 document was created following `docs/PHASE_REPORT_TEMPLATE.md` and the exact structure/tone of the prior PHASE1/PHASE2/PHASE3 tracking docs. Extraction sources: the original vision plan (019e612c.../plan.md) whose Phase 3 was "Hardening & Multi-Cartridge Future", the AUDIT (primary Phase 4 section and gap table), the current CARTRIDGE_VISION.md (still points to Phase 4+), PHASE3_NATIVE_PLUGIN_BOUNDARY.md (which explicitly offloaded this work), PHASE1 (which already had a P1-B "Loader lifecycle & isolation" track whose remaining items are now promoted here), FUTURE_TASKS.md (the "Isolation, Unload Hygiene & Multi-Cartridge Host Readiness" subsection that was pre-populated during Phase 3 planning), cartridge core sources (loader.py still has only load paths + raw inserts; no unload or teardown; ResourceManager has `unmount_asset_root` and `mount_asset_root`; World has strong `on_entity_removed` hooks), the cartridge_loader_guide.md Known Limitations, main.py `_load_cartridge` (load-only), greps confirming absence of any unload/teardown/host code, and the explicit user choices via ask_user_question.
- Scope was kept to the AUDIT Phase 4 definition. Per the "Other" scoping answer, the pre-existing isolation items in FUTURE_TASKS are being brought into the formal tracks here; those specific items will be deleted/trimmed from FUTURE_TASKS.md in the same turn to keep the queue clean and non-duplicative.
- Representation is "assume prior phases complete + minimal backward refs" per the user's choice (PHASE2 precedent). Only light mentions of Context (P3/P1), native handles (P3), and earlier loader hygiene appear where they are direct prerequisites.
- The host skeleton is deliberately minimal and console-driven per the exact user answer; it uses tgl_demo (or a stub) as one of the switchable cartridges and demonstrates the observable cleanup + clean re-load that the vision verification criteria called out as a stretch goal.
- ResourceManager already provides the `unmount_asset_root` primitive (confirmed in source), which the unload implementation can and should use. World removal hooks are already strong and will be leveraged by cartridge-registered systems.
- Keep this document as the executive record. Detailed design for the exact `teardown` signature, the importlib isolation strategy trade-offs, or the host's internal loop can live in the implementation PRs and the example itself.
- Update status, last-updated date, and tracks table as work lands. Move completed track details into the Outcome section when the phase is declared complete. After this phase lands, the "Phase 4+" language in CARTRIDGE_VISION can be updated in a follow-up pass.
- **2026-06-10 viability evaluation pass**: corrected the stale core premise — `CartridgeLoader.unload()` landed with P1-B (teardown/unload/cleanup hook context-first, asset unmount, tracked sys.path removal, save-provider unregistration, idempotent; covered by unit tests), so the claims "no unload, no teardown hook, no coordinated unmount, no sys.path cleanup" in the original notes are superseded. Verified the five remaining leaks: no `World.remove_system` (and no tracking of cartridge-registered systems), no entity ownership records, event-manager subscriptions never unsubscribed, both demos bind hotkeys raw on `base.accept` (dangling handlers that also keep modules alive), and `sys.modules` never purged (the real import-isolation gap). Verified working: RenderSystem removes Panda nodes on `EntityDestroyedEvent`; `SaveStateManager.unregister_provider` exists and is called. P4-A rescoped to ownership-tracked teardown and **absorbs FUTURE_TASKS Task E** (Task F becomes a near-freebie). P4-D split: D1 reboot-to-switch (process-per-cartridge, promoted from the Follow-On subprocess row — leak-proof by construction, zero dependencies, sequenced FIRST) and D2 in-process host (sequenced after A/B/C, with the previously missing ShowBase-singleton and window-state-reset requirements). Phase-level risk named: chasing perfect in-process isolation is unwinnable in CPython — the documented best-effort model plus the reboot host is the grounded version of the same vision. Per-track Risks subsections added throughout.

## Outcome

*(To be filled when the phase is complete.)*

- What shipped.
- What was deferred (moved to Follow-On or remaining FUTURE items).
- What should happen next (e.g. richer host UX, security model for untrusted cartridges, full concurrent multi-cartridge composition, integration of unload into tgl_demo dev tooling or main.py, production packaging concerns for hosts).

---

## Optional Sections (populated for signal)

**Files affected (initial map)**

- Modified: `engine/core/system.py` (`World.remove_system` + `ensure_system` — Task E absorbed into P4-A), `engine/cartridge/loader.py` (ownership-ledger walk in unload; `sys.modules` purge-by-prefix), `engine/cartridge/context.py` (`unload()` + ownership wrappers; `api_version` bump per P3-A evolution rules)
- Modified: both reference demo entrypoints (migrate to the Context wrappers — they are the compliance proof)
- New: `examples/hosts/cartridge_host.py` (P4-D1 reboot-to-switch) and `examples/hosts/multi_cartridge_host.py` (P4-D2 in-process)
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