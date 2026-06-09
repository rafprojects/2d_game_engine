# Cartridge Loader Guide

This document explains how the prototype loader ingests self-contained "game cartridges" and boots them inside the Panda3D ECS runtime.

## Archive Layout

Cartridges are zip archives (extension `.car` or `.zip`) with the following structure:

```
cartridge.car
├── config/
│   └── cartridge.json      # Required descriptor (JSON)
├── assets/                 # All textures/audio/data referenced by the cartridge
│   └── ...
└── python/                 # Cartridge-specific Python modules
    └── guardian_legends/
        └── main.py         # Contains the entrypoint class
```

### `config/cartridge.json`

Minimal descriptor example (full schema doc is in `docs/guides/cartridge_config_options.md`):

```json
{
  "cartridge": {
    "name": "Guardian Legends",
    "version": "0.2.0",
    "entrypoint": "guardian_legends.main:Cartridge"
  },
  "assets": {
    "mount": "assets",
    "virtual_root": "guardian"
  },
  "systems": {
    "register": [
      "guardian_legends.systems.boss_system"
    ]
  }
}
```

Fields used by the loader today:
- `cartridge.name`, `cartridge.version`, `cartridge.entrypoint` (module:Class format)
- `assets.mount`: relative folder inside the archive that is mounted above any existing `ResourceManager` roots (layered overlay)
- `systems.register`: dotted module paths with an optional `register(world, base)` function that can add ECS systems/components.

The manifest is validated against `docs/schemas/cartridge.schema.json` (the same schema ships inside `engine/cartridge/schema.json`). Validation errors show the JSON pointer path and reason so you can catch mistakes before the loader extracts assets.

## Runtime Boot Flow

1. **Extraction** – `CartridgeLoader` unpacks the archive to `~/.cache/tmp/2dge_cartridges/{name}-{version}-{uid}` (override with `--cartridge-extract`).
2. **Python Path Mount** – The loader prepends `<extract>/python` to `sys.path` so imports resolve cartridge modules.
3. **Asset Mount** – If a `ResourceManager` system exists, `mount_asset_root` is invoked so `<extract>/assets/<mount>` becomes the highest-priority search path while previous roots remain available as fallbacks.
4. **Entrypoint Instantiation** – The loader imports the entrypoint class and instantiates it. A `CartridgeContext` is constructed (exposing `world`, `base`, `manifest`, `resource_manager`, `save_state_manager`, and `loader`). If the instance exposes any of `mount`, `load`, or `initialize`, the first available hook is invoked. New cartridges may accept a single `context` argument (`def initialize(self, context): ...`). For backward compatibility during transition, the legacy `world`/`base`/`manifest` kwargs are still supplied via fallback so existing cartridges continue to run unchanged.
5. **System Registration** – Each module listed under `systems.register` is imported. If the module defines `register(world, base)` (or the new `register(context)` form), it is executed so the module can add systems/components/events. Same context + legacy fallback calling convention as entry hooks.
6. **Save-State Wiring** – When the host constructs the loader with a `SaveStateManager`, the manifest metadata is attached automatically and the instantiated entry receives `save_state_manager` as an attribute so cartridges can register snapshot providers during `initialize`.

## CLI Usage

### Running a cartridge

```bash
python main.py --cartridge cartridges/guardian_legends.car
```

Optional extraction cache directory:

```bash
python main.py --cartridge cartridges/guardian_legends.car --cartridge-extract /tmp/guardian_cache
```

If loading fails, the engine logs the exception and falls back to the built-in demo entity.

### Creating a new cartridge (P1-D)

```bash
py2d-cartridge init "My Awesome Game"
cd my-awesome-game
# Edit config/cartridge.json, python/.../entrypoint.py, drop art in assets/
```

The scaffold includes a working `config/cartridge.json`, a `python/<slug>/entrypoint.py` (using CartridgeContext), a tiny custom component + registered system, a SaveStateProvider example, and a private sprite asset so it renders immediately.

### Packaging a cartridge

Use the `py2d-cartridge` helper (or `python -m tools.cli.cartridge_pack`) from the root of a cartridge project that contains `config/cartridge.json`, an assets folder, and a python module tree:

```bash
# From cartridge workspace
py2d-cartridge .                 # pack (or: py2d-cartridge pack .)

# Explicit output + overwrite
py2d-cartridge . -o ../cartridges/my-game-0.1.0.car --force
```

The packer performs the same JSON Schema validation as the runtime loader before emitting `dist/<name>-<version>.car`. Hidden build folders (`dist`, `build`, `__pycache__`, etc.) are skipped automatically; additional folders can be excluded via `--ignore foo`. Use `--dry-run` to validate a project without creating an archive.

## Loader API

Use programmatically:

```python
from engine.cartridge.loader import CartridgeLoader

loader = CartridgeLoader(world, base, resource_manager)
context = loader.load_archive("cartridges/guardian_legends.car")
print(context.manifest.name)
```

`LoadedCartridge` contains the manifest, archive path, extraction path, instantiated entry object, list of system modules that were imported, and (optionally) the `SaveStateManager` reference that was passed into the loader.

After a successful load, the entry instance also receives a `.context` attribute (a `CartridgeContext`). The same context object is passed to hooks (as the `context` kwarg for new-style code). `CartridgeContext` is the recommended stable surface for cartridge authors (see `engine/cartridge/context.py`).

## Known Limitations

- **(Addressed in P1-B)** `CartridgeLoader.unload(name_or_context)` now exists. It removes any python path we inserted, calls an optional `teardown`/`unload`/`cleanup` hook on the entrypoint instance (if present), unmounts the cartridge's asset root (via `ResourceManager.unmount_asset_root`), and drops the `LoadedCartridge` record. Both directory and archive loads are supported. Call it as `loader.unload("my_cartridge")` or `loader.unload(loaded_context)`.
- **(Addressed in P1-C)** `CartridgeContext` is now the primary object passed to entrypoint hooks (`initialize`/`load`/`mount`) and `systems.register` functions. The entry instance also gets `.context` set. Legacy `(world, base, manifest)` calling convention continues to work via automatic fallback so cartridges like tgl_demo are unaffected. New code can be written as `def initialize(self, context): ...` (and similarly for register/teardown). `context` also carries `resource_manager`, `save_state_manager`, and `loader` for self-unload scenarios.
- The "one cartridge at a time" mental model is still the primary supported mode (classic console cartridge). Loading a second cartridge while one is active will stack python paths and asset roots; explicit `unload` of the previous one is required for a clean switch.
- Python modules are not unloaded from `sys.modules` (Python does not support clean package unload in general). A future iteration may adopt `importlib.util` for more isolated loading.
- Cartridge archives must already contain compiled Python modules/assets; there is no build pipeline yet beyond the existing packer. 
- No high-level host/menu UI for cartridge switching yet (see PHASE4 for multi-cartridge host sketches).

Use this doc as the reference while iterating on the loader; future updates will flesh out schema validation, save-state integration, and CLI packaging. See `PHASE1_CARTRIDGE_SYSTEM_POLISH.md` (tracks P1-B and P1-C) for the current lifecycle + context work.
