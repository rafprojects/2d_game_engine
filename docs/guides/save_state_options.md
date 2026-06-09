# Save-State Format Options

The cartridge vision assumes players can pause, resume, and migrate progress across devices. Below is a curated comparison of serialization strategies suitable for save-state blobs within this Panda3D ECS engine. Pickle is intentionally excluded (see last section) due to security and portability concerns.

---

## JSON

**Pros**
- Human readable and easy to diff in Git or text editors.
- Standard library support (`json`) with optional schema validation via JSON Schema or `pydantic` models.
- Excellent interoperability with web services/cloud sync backends.

**Cons**
- No native binary encoding → larger payloads than binary formats.
- Floating-point precision limited to double; custom types require manual encoding.

**Ideal when** you want transparency and simple cloud sync without extra dependencies.

---

## TOML

**Pros**
- Slightly more ergonomic than JSON for nested configuration, with preserved typing and comments.
- Built-in parser (`tomllib`) in Python 3.11+.
- Works nicely if cartridge configs already use TOML (shared tooling).

**Cons**
- Not as widely supported in non-Python stacks for sync/backups.
- Lacks an officially sanctioned schema format (though `pydantic` works well).

**Ideal when** you want human-editable saves (e.g., for modding) and consistent format with cartridge metadata.

---

## YAML

**Pros**
- Supports anchors/aliases, multiline strings, and comments embedded inline.
- Many designers already comfortable with YAML from other tools.

**Cons**
- Indentation sensitive; dangerous tags (e.g., `!!python/object`) must be disabled for security.
- Harder to diff/merge when anchors used heavily; parsing requires third-party libs.

**Ideal when** you absolutely need anchors or want to stay close to existing YAML-based pipelines.

---

## XML

**Pros**
- Mature tooling for schema validation (XSD) and transformation (XSLT).
- Namespaces allow mixing cartridge-specific elements with engine-defined ones cleanly.
- Streaming read/write (SAX) makes handling large saves feasible without loading entire tree.

**Cons**
- Verbose; harder for humans to hand-edit.
- APIs in Python (`xml.etree`, `lxml`) exist but have footguns (entity expansion attacks) unless hardened.

**Ideal when** interoperability with legacy systems or strongly validated schemas is required.

---

## MessagePack / Binary Structs

**Pros**
- Compact and fast; ideal for large inventories or physics state.
- Preserves numeric types and handles nested structures similar to JSON.
- Libraries like `msgpack` and `cbor2` make encoding straightforward.

**Cons**
- Not human-readable; debugging requires tooling.
- Schema/version management must be explicit to avoid deserialization mismatches.

**Ideal when** file size or serialization throughput matters (e.g., handheld devices, cloud sync quotas).

---

## Hybrid Approach

Many engines adopt a dual strategy:
1. **Authoritative binary save** (MessagePack/CBOR) for runtime speed.
2. **Optional export/import** to JSON/TOML for modders and QA.

A version header plus checksum keeps both formats forward-compatible.

---

## Why Not Pickle?

- **Security**: Pickle executes arbitrary Python opcodes during load, making it unsafe for user-modifiable files.
- **Portability**: Tightly coupled to Python version and object layouts; subtle changes break old saves.
- **Determinism**: Non-Python cartridges or tooling cannot read pickle without embedding CPython.

Dropping pickle encourages deterministic, language-agnostic save data.

---

## Next Steps

1. Decide whether cartridge configs and save-states share the same format (easier for tooling) or diverge (e.g., TOML for config, MessagePack for saves).
2. Define a minimal `SaveState` schema (player stats, inventory, world seeds) and versioning metadata.
3. Implement serializers/deserializers behind an interface (`engine/save_state/manager.py`) so cartridges can override or extend behavior without touching engine internals.

## Current Implementation Snapshot

- The runtime now ships with `engine.save_state.manager.SaveStateManager`, which owns a storage root (default `./saves`), records cartridge metadata, and coordinates named providers.
- Providers implement a tiny `SaveStateProvider` protocol (`capture(world) -> dict`, `restore(world, payload) -> None`). Cartridges register them during their `initialize` hook to persist whatever data they own (player transforms, inventory, mission state, etc.).
- Binary saves default to MessagePack (`slot.sav`) for compactness, while JSON exports (`slot.json`) are available for QA and tooling. Both formats share the same `metadata` + `payload` envelope.
- The `CartridgeLoader` injects the manager into entrypoints (`entry.save_state_manager`) and keeps the reference on `LoadedCartridge`, so tooling/menus can surface save slots without bespoke wiring.
- Tests cover provider registration, msgpack/json persistence, and integration through the loader so regressions are caught automatically.
