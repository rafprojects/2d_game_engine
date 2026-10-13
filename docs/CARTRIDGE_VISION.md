# Cartridge Vision

**Status**: Living reference pointer  
**Date**: 2026  
**Primary canonical source**: [CARTRIDGE_ARCHITECTURE_VISION_AND_AUDIT.md](CARTRIDGE_ARCHITECTURE_VISION_AND_AUDIT.md)  
**Related tracking**: `docs/PHASE1_CARTRIDGE_SYSTEM_POLISH.md` (and future PHASE docs)  
**Origin**: Synthesized from stored session plans (including 019e612c vision feasibility plan) + project audit + execution history on feat/M0-vision-calibration.

## Core Concept (executive summary)

A **cartridge** is the atomic unit of game distribution, versioning, and execution:

- Self-contained bundle of game-specific code (Python today; later Rust/C++ via narrow plugin surface), assets, metadata, and configuration.
- Declares an entrypoint class with standard lifecycle hooks (`mount`/`load`/`initialize` receiving world + base + manifest) and optional `register(world, base)` modules.
- Assets are mounted with highest priority via `ResourceManager` (overlay on engine roots).
- Participates in persistence by registering `SaveStateProvider`(s) with the injected manager.
- Can deliberately opt into (or implement) constrained/retro simulation rules (fixed-point, subpixel, NES-style collision quirks) to produce interesting emergent gameplay "side effects" — a core creative thesis of the project.

The engine provides the **stable framework** (ECS + events, rendering, input, audio, physics/collision, save-state coordination, resource management, cartridge loader/packer, dev tooling). Cartridges provide **the game**.

**Mental model (primary)**: One cartridge per engine process (classic console cartridge metaphor). A future multi-cartridge "host" or menu application is explicitly supported by the same extension points but is secondary.

## Why This Model
- Strong separation + easy distribution (single `.car` file).
- Versioning & compatibility via manifest (`requires.engine` etc.) + cartridge-scoped saves.
- Creative constraints: retro precision layers become a feature, not a bug to paper over.
- Extensibility path: the same `register` + hook surface becomes the target for native plugins.

Non-goals (for clarity): The engine core does **not** force retro math on all users. Cartridges are not expected to re-implement core systems.

## Current State (high level)
The vision is already **substantially realized**:
- `CartridgeLoader` + manifest schema + validation (dir mode for dev, archive `.car` for distribution).
- `python/` path injection + `assets/` mount (prepend priority).
- Entrypoint hooks + `systems.register`.
- `SaveStateManager` + provider protocol (injected into entry instances).
- `py2d-cartridge` packer (validation + zip).
- Launcher support via `--cartridge` / `--cartridge-extract`.
- Reference usage in `examples/cartridges/tgl_demo/` (with custom components/systems, hot-restart via `.reset()`, CollisionLayer adoption, config-driven setup, dev-mode integration).

**Major remaining gaps** (see the full AUDIT for the detailed table with severity, locations, and recommendations):
- Asset loading bypasses (RenderSystem and other direct Panda `loadTexture` / load paths ignore mounted cartridge roots).
- Loader lacks unload/teardown and import isolation (raw `sys.path.insert`, only one active semantic).
- No clean `CartridgeContext` / `EngineAPI` facade (raw `world`/`base` passed everywhere).
- Authoring tooling still promotes the old `examples/games/` model (`project_gen`); no `py2d-cartridge init` scaffolder.
- Primary documentation (README, DEVELOPER_ONBOARDING, PROJECT_ORGANIZATION) does not lead with the cartridge story.
- No enforcement of `cartridge.requires.engine`.
- Complete absence of `engine/retro/` reference implementations for the emergent retro mechanics vision.
- No native/FFI surface yet.

## Roadmap Pointer (from vision + audit)
- **Phase 0 (done-ish)**: Vision docs, initial Context facade spike.
- **Phase 1 – Cartridge System Polish** (this phase): See `PHASE1_CARTRIDGE_SYSTEM_POLISH.md` for the detailed tracking document (asset consistency, loader hygiene + Context, tooling, docs leadership, enforcement, reference validation via tgl_demo).
- **Phase 2**: Retro / emergent gameplay layer (`engine/retro/` + reference impls + at least one cartridge exercising a deliberate quirk).
- **Phase 3**: Native plugin boundary design (narrow ABI + manifest extensions).
- **Phase 4+**: Isolation / multi-cartridge host readiness + ongoing "every new feature must be cartridge-usable".

## Quick Navigation
- Detailed audit + full gap table + verification criteria: [CARTRIDGE_ARCHITECTURE_VISION_AND_AUDIT.md](CARTRIDGE_ARCHITECTURE_VISION_AND_AUDIT.md)
- Phase tracking (starting here): `PHASE1_CARTRIDGE_SYSTEM_POLISH.md`
- Guides: `docs/guides/cartridge_loader_guide.md`, `cartridge_config_options.md`, `save_state_options.md`, `collision_layers_and_bounds.md`, `docs/guides/retro_mechanics_guide.md` (the Phase 2 emergent retro layer + reference cartridge walkthrough)
- Example cartridge: `examples/cartridges/tgl_demo/` (run with `python main.py --cartridge examples/cartridges/tgl_demo`)
- Packaging: `py2d-cartridge .` (or `python -m tools.cli.cartridge_pack`)
- Core code: `engine/cartridge/`, `engine/save_state/manager.py`, `engine/assets/resource_manager.py`, `main.py` (_load_cartridge)
- Future TGL scope (one consumer of the polished system): `docs/FUTURE_TASKS.md`

*All substantive vision, feasibility assessment, gap analysis, and long-term roadmap live in the AUDIT document. This file is intentionally a stable, short-lived pointer + update surface.*
