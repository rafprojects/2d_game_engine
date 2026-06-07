# Cartridge Configuration Formats

This note summarizes candidate data formats for cartridge descriptors (per-game metadata, system registration, asset mounts, etc.) so we can pick the default authoring format with eyes wide open. Each section covers developer ergonomics, tooling availability, validation options, and runtime considerations, plus a small snippet that illustrates how a cartridge might declare itself.

---

## TOML

**Highlights**
- Human friendly with strong typing (numbers vs strings vs booleans are explicit, arrays are ordered, inline tables exist).
- Excellent fit for Python thanks to `tomllib` (standard library in 3.11+) and mature third-party validators such as `pydantic` or `tomli-w`.
- Easy to diff/merge in Git because structure is shallow and punctuation noise is minimal.

**Tradeoffs**
- Limited support for complex anchors/aliases (unlike YAML) and no comments-in-arrays spec quirk.
- Parser availability is great in Python/Rust, but less universal in some engines/tools.

**Sample**
```toml
[cartridge]
name = "Guardian Legends"
version = "0.2.0"
entrypoint = "guardian_legends.main:Cartridge"

[assets]
mount = "./cartridges/guardian_legends/assets"
virtual_root = "guardian"

[systems]
register = [
  "guardian_legends.systems.BossSystem",
  "guardian_legends.systems.DialogSystem"
]
```

---

## YAML

**Highlights**
- Extremely flexible syntax: nested objects, anchors/aliases, multiline strings.
- Many non-Python tools already produce/consume YAML, making it attractive for artists or level designers who use off-the-shelf editors.

**Tradeoffs**
- Whitespace sensitive; indentation mistakes cause subtle bugs.
- Anchors/aliases can obscure diffs; malicious YAML features (like `!!python/object`) must be disabled to avoid code injection.
- Requires third-party libs (`PyYAML`, `ruamel`) and careful safe-loading.

**Sample**
```yaml
cartridge:
  name: Guardian Legends
  version: 0.2.0
  entrypoint: guardian_legends.main:Cartridge
assets:
  mount: ./cartridges/guardian_legends/assets
  virtual_root: guardian
systems:
  register:
    - guardian_legends.systems.BossSystem
    - guardian_legends.systems.DialogSystem
```

---

## JSON

**Highlights**
- Universally supported; trivial to parse in every language and environment.
- Strict syntax eliminates indentation ambiguity and works well with tooling, linters, and schema validation (JSON Schema).

**Tradeoffs**
- Verbose when comments are needed; spec disallows inline comments (though some parsers accept `//`).
- Harder for humans to edit quickly, especially for long arrays/objects.

**Sample**
```json
{
  "cartridge": {
    "name": "Guardian Legends",
    "version": "0.2.0",
    "entrypoint": "guardian_legends.main:Cartridge"
  },
  "assets": {
    "mount": "./cartridges/guardian_legends/assets",
    "virtual_root": "guardian"
  },
  "systems": {
    "register": [
      "guardian_legends.systems.BossSystem",
      "guardian_legends.systems.DialogSystem"
    ]
  }
}
```

---

## Decision Inputs

When we choose the default format, consider:
1. **Editor experience** for designers (TOML/YAML more pleasant than JSON).
2. **Validation story**: JSON Schema is mature; TOML has `pydantic` support; YAML needs extra care.
3. **Runtime footprint**: JSON/TOML parsers are lightweight; YAML parsers are heavier but still fine for config-time use.
4. **Tool chain**: do we expect to auto-generate configs from CLI tools? JSON/TOML easier to emit programmatically.

We can also support multiple formats by defining a loader registry keyed by extension, but committing to one canonical format keeps documentation coherent.
