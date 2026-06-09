#!/usr/bin/env python3
"""CLI utility for cartridges: init (scaffold) + pack (validated .car archives).

Primary authoring entrypoint for the cartridge model.

Examples:
    py2d-cartridge init my-first-game
    cd my-first-game
    py2d-cartridge .                 # (or: py2d-cartridge pack .)
    python -m main --cartridge /path/to/my-first-game

See PHASE1_CARTRIDGE_SYSTEM_POLISH.md (P1-D) for the scaffolding track.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import zipfile
from pathlib import Path
from typing import Iterable, List, Set

from jsonschema import Draft202012Validator

try:
    from tools.cli import (
        get_project_root,
        print_error,
        print_header,
        print_info,
        print_success,
        print_warning,
    )
except ImportError:  # pragma: no cover - direct invocation fallback
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from tools.cli import (  # type: ignore
        get_project_root,
        print_error,
        print_header,
        print_info,
        print_success,
        print_warning,
    )

DEFAULT_EXCLUDES = {
    "__pycache__",
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    "dist",
    "build",
    "temp",
}
DEFAULT_FILE_EXCLUDES = {
    ".DS_Store",
    "Thumbs.db",
}
DEFAULT_SUFFIX_EXCLUDES = {
    ".pyc",
    ".pyo",
}


class ManifestValidator:
    """Helper to load and validate manifest data against the shared schema."""

    def __init__(self) -> None:
        schema_path = Path(get_project_root()) / "engine" / "cartridge" / "schema.json"
        with schema_path.open("r", encoding="utf-8") as fp:
            schema = json.load(fp)
        self._validator = Draft202012Validator(schema)

    def load_and_validate(self, manifest_path: Path) -> dict:
        with manifest_path.open("r", encoding="utf-8") as fp:
            data = json.load(fp)
        errors = sorted(self._validator.iter_errors(data), key=lambda err: err.path)
        if errors:
            formatted = "; ".join(
                f"{'/'.join(str(p) for p in err.path) or '<root>'}: {err.message}" for err in errors
            )
            raise ValueError(f"Manifest validation failed: {formatted}")
        return data


def slugify(value: str) -> str:
    safe = [ch if ch.isalnum() or ch in {"-", "_"} else "-" for ch in value.strip()]
    slug = "".join(safe).strip("-")
    return slug or "cartridge"


def compute_output_path(source: Path, manifest: dict, explicit: str | None) -> Path:
    if explicit:
        return Path(explicit).expanduser().resolve()

    cartridge = manifest.get("cartridge", {})
    name = slugify(cartridge.get("name", "cartridge"))
    version = cartridge.get("version", "0.0.0")
    dist_dir = source / "dist"
    dist_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{name}-{version}.car"
    return (dist_dir / filename).resolve()


def collect_ignore_names(extra: Iterable[str]) -> Set[str]:
    base = set(DEFAULT_EXCLUDES)
    for item in extra:
        if item:
            base.add(item.strip())
    return base


def should_skip(path: Path, ignore_names: Set[str]) -> bool:
    parts = set(path.parts)
    if parts & ignore_names:
        return True
    if path.name in DEFAULT_FILE_EXCLUDES:
        return True
    if path.suffix in DEFAULT_SUFFIX_EXCLUDES:
        return True
    return False


def ensure_structure(source: Path, manifest: dict) -> None:
    config_path = source / "config" / "cartridge.json"
    if not config_path.exists():
        raise FileNotFoundError(f"Missing manifest file at {config_path}")

    assets_cfg = manifest.get("assets", {})
    mount_path = assets_cfg.get("mount")
    if not mount_path:
        raise ValueError("Manifest must define assets.mount")
    assets_dir = source / mount_path
    if not assets_dir.exists():
        raise FileNotFoundError(f"Declared assets.mount directory missing: {assets_dir}")

    python_dir = source / manifest.get("python_path", "python")
    if not python_dir.exists():
        print_warning(f"Python path '{python_dir}' not found; continuing but imports may fail")


def package_cartridge(source: Path, output: Path, ignore: Set[str], dry_run: bool = False) -> int:
    files_written: List[Path] = []
    if dry_run:
        print_warning("Dry-run mode enabled; no archive will be written")

    if not dry_run:
        if output.exists():
            output.unlink()
        output.parent.mkdir(parents=True, exist_ok=True)
        zf = zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED)
    else:
        zf = None

    try:
        for path in sorted(source.rglob("*")):
            if path.is_dir():
                continue
            rel_path = path.relative_to(source)
            if should_skip(rel_path, ignore):
                continue
            files_written.append(rel_path)
            if not dry_run and zf:
                zf.write(path, arcname=str(rel_path))
    finally:
        if zf:
            zf.close()

    print_info(f"Included {len(files_written)} files")
    if not dry_run and output.exists():
        size_kb = output.stat().st_size / 1024
        print_success(f"Created archive: {output} ({size_kb:.1f} KiB)")
    return len(files_written)


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Package a validated cartridge archive")
    parser.add_argument(
        "source",
        nargs="?",
        default=".",
        help="Path to cartridge project folder (default: current directory)",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Target archive path (.car). Defaults to dist/<name>-<version>.car inside source",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite the output archive if it exists")
    parser.add_argument(
        "--ignore",
        action="append",
        default=[],
        help="Folder names to exclude (can be repeated)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Validate without writing an archive")
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> int:
    argv = list(argv) if argv is not None else sys.argv[1:]

    # Support `py2d-cartridge init <name>` (P1-D) while preserving legacy
    # `py2d-cartridge .` (and `py2d-cartridge pack .`) for the pack side.
    if argv and argv[0] == "init":
        return _cmd_init(argv[1:])
    if argv and argv[0] == "pack":
        argv = argv[1:]  # strip subcommand for the pack parser

    args = parse_args(argv)
    source = Path(args.source).expanduser().resolve()
    if not source.exists():
        print_error(f"Source directory not found: {source}")
        return 1

    manifest_path = source / "config" / "cartridge.json"

    print_header("Cartridge Packager")
    print_info(f"Source: {source}")

    validator = ManifestValidator()

    try:
        manifest = validator.load_and_validate(manifest_path)
    except FileNotFoundError:
        print_error(f"Manifest not found: {manifest_path}")
        return 1
    except ValueError as exc:
        print_error(str(exc))
        return 1

    try:
        ensure_structure(source, manifest)
    except (FileNotFoundError, ValueError) as exc:
        print_error(str(exc))
        return 1

    output_path = compute_output_path(source, manifest, args.output)
    if output_path.exists() and not args.force and not args.dry_run:
        print_error(f"Output archive already exists: {output_path}. Use --force to overwrite.")
        return 1

    ignore_names = collect_ignore_names(args.ignore)
    included = package_cartridge(source, output_path, ignore_names, dry_run=args.dry_run)

    if included == 0:
        print_warning("No files were included. Check ignore patterns or source directory structure.")
    return 0


# ------------------------------------------------------------------
# P1-D: Cartridge scaffolding (py2d-cartridge init)
# ------------------------------------------------------------------

def _cmd_init(argv: List[str] | None = None) -> int:
    """Handle `py2d-cartridge init <name>` (and optional flags)."""
    parser = argparse.ArgumentParser(
        prog="py2d-cartridge init",
        description="Scaffold a new self-contained cartridge project (config + python package + assets + sample provider + sprite).",
    )
    parser.add_argument("name", help="Name of the new cartridge (used for dir and package slug)")
    parser.add_argument(
        "-o", "--out", "--output",
        dest="out_dir",
        default=None,
        help="Parent directory in which to create the cartridge folder (default: current directory)",
    )
    parser.add_argument(
        "--template",
        choices=["minimal"],
        default="minimal",
        help="Template to use (currently only 'minimal' is implemented)",
    )
    args = parser.parse_args(argv)

    try:
        created = create_new_cartridge(args.name, target=args.out_dir)
        print_success(f"Cartridge scaffolded at: {created}")
        print_info("Next steps:")
        print(f"  cd {created}")
        print("  py2d-cartridge .                 # pack to dist/<name>-<ver>.car")
        print(f"  python /path/to/2d_game_engine/main.py --cartridge {created}")
        print_info("  (Run the above from the 2d_game_engine source checkout; main.py is not")
        print_info("   installed as an importable module under the package distribution.)")
        print_info("The generated entrypoint uses the modern CartridgeContext (P1-C) and registers a SaveStateProvider.")
        print_info("A small sprite asset was copied in so it renders something visible immediately.")
        return 0
    except Exception as exc:
        print_error(f"Failed to create cartridge: {exc}")
        return 1


def create_new_cartridge(name: str, target: str | Path | None = None) -> Path:
    """Create a minimal, complete, packable + runnable cartridge tree.

    Layout produced (modern cartridge model):
      <target>/<slug>/
        config/cartridge.json
        assets/sprites/<copied-sprite>.png   (for immediate visible content)
        python/<slug>/
          __init__.py
          entrypoint.py
          components/
            __init__.py
            player_component.py
          systems/
            __init__.py
            gameplay_system.py
        README.md

    The entrypoint demonstrates:
    - CartridgeContext usage (initialize(self, context))
    - SaveStateProvider registration
    - A PlayerComponent + a tiny registered system
    - SpriteComponent using a cartridge-private asset (exercises P1-A mount/resolve)

    After creation the tree can be packed with `py2d-cartridge .` and loaded with
    `python main.py --cartridge <dir>` with no further edits.
    """
    safe = slugify(name)
    if not safe:
        raise ValueError("Invalid cartridge name")

    # Python package names and dotted entrypoint/system paths cannot contain "-".
    # Use a filesystem/python-safe slug for directories and import paths.
    # Keep the user-supplied `name` for the human-readable manifest "name".
    python_slug = safe.replace("-", "_")
    if not python_slug:
        python_slug = "cartridge"

    base = Path(target).expanduser().resolve() if target else Path.cwd()
    cartridge_dir = base / python_slug   # safe dir name (also nice for `cd`)
    if cartridge_dir.exists():
        raise FileExistsError(f"Directory already exists: {cartridge_dir}")

    cartridge_dir.mkdir(parents=True)
    slug = python_slug  # used for package dir + dotted paths in manifest/entrypoint

    # 1. config/cartridge.json (include requires for good hygiene, even if P1-F not yet enforced)
    cartridge_json = {
        "cartridge": {
            "name": name,
            "version": "0.1.0",
            "entrypoint": f"{slug}.entrypoint:Cartridge",
            "requires": {"engine": "^0.1.0"},
        },
        "assets": {"mount": "assets"},
        "python_path": "python",
        "systems": {"register": [f"{slug}.systems.gameplay_system"]},
    }
    (cartridge_dir / "config").mkdir()
    (cartridge_dir / "config" / "cartridge.json").write_text(
        json.dumps(cartridge_json, indent=2) + "\n", encoding="utf-8"
    )

    # 2. Assets: copy a small real sprite so the scaffold has visible content out of the box
    #    (exercises cartridge asset mount + ResourceManager resolution after P1-A)
    assets_dir = cartridge_dir / "assets" / "sprites"
    assets_dir.mkdir(parents=True, exist_ok=True)
    try:
        from tools.cli import get_assets_dir as _get_assets
        src = Path(_get_assets()) / "player.png"
        if src.exists():
            shutil.copy(src, assets_dir / "player.png")
        else:
            # fallback tiny valid 1x1 PNG (red) so scaffold runs out-of-the-box
            # without texture load errors. User can replace with real art.
            tiny_png = (
                b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
                b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00"
                b"\x00\x01\x01\x00\x05\xfe\xdc\xdc\x00\x00\x00\x00IEND\xaeB`\x82"
            )
            (assets_dir / "player.png").write_bytes(tiny_png)
    except Exception:
        (assets_dir / ".gitkeep").write_text("", encoding="utf-8")

    # 3. Python package
    py_root = cartridge_dir / "python" / slug
    (py_root / "components").mkdir(parents=True)
    (py_root / "systems").mkdir(parents=True)

    (py_root / "__init__.py").write_text("", encoding="utf-8")
    (py_root / "components" / "__init__.py").write_text(
        "# Game-specific components\n", encoding="utf-8"
    )
    (py_root / "systems" / "__init__.py").write_text(
        "# Game-specific systems (registered via manifest)\n", encoding="utf-8"
    )

    # 4. Sample PlayerComponent (demonstrates custom component in a cartridge)
    (py_root / "components" / "player_component.py").write_text(
        '''from engine.core.component import Component


class PlayerComponent(Component):
    """Example player state component (lives in the cartridge package)."""

    def __init__(self, health: int = 3, score: int = 0):
        self.health = health
        self.score = score
        self.invulnerable_timer = 0.0
''',
        encoding="utf-8",
    )

    # 5. Tiny system + register hook (exercises systems.register path)
    (py_root / "systems" / "gameplay_system.py").write_text(
        f'''from engine.core.system import System


class SimpleGameplaySystem(System):
    """Minimal system to demonstrate cartridge-provided systems."""

    def __init__(self, world):
        super().__init__(world)
        self._ticks = 0

    def update(self, dt: float):
        self._ticks += 1
        # In a real cartridge you would query entities, apply rules, etc.
        if self._ticks % 120 == 0:
            # Occasional heartbeat so you know the registered system is alive
            pass


def register(context):
    """Called by CartridgeLoader for modules listed under systems.register.

    Accepts CartridgeContext (P1-C) or falls back for older loaders.
    """
    world = getattr(context, "world", None) if context is not None else None
    if world is None and hasattr(context, "world"):
        world = context.world
    if world is not None:
        sys = SimpleGameplaySystem(world)
        world.add_system(sys)
''',
        encoding="utf-8",
    )

    # 6. Entrypoint (modern context style + demo of provider + visible sprite + component)
    # Plain string + .replace (avoids the generator's f-string trying to eval names like "e" or "name"
    # that only exist inside the *generated* cartridge's runtime scope).
    entrypoint_code = '''"""Minimal cartridge entrypoint generated by py2d-cartridge init.

Demonstrates the full happy path after P1-A/B/C:
- CartridgeContext (preferred)
- Custom PlayerComponent
- Registered system via manifest
- SaveStateProvider registration
- Sprite using a cartridge-private asset (mounted at highest priority)
"""
from __future__ import annotations

from engine.core.component import Component
from engine.graphics.components.transform_component import TransformComponent
from engine.graphics.components.sprite_component import SpriteComponent
from engine.physics.components.collider_component import ColliderComponent
from engine.physics.typesg import ColliderType
from panda3d.core import Vec2

# Local cartridge components
from {slug}.components.player_component import PlayerComponent


class Cartridge:
    """Cartridge entrypoint. initialize receives a CartridgeContext (or legacy args during transition)."""

    def __init__(self):
        self.world = None
        self.base = None
        self._provider_registered = False

    def initialize(self, context=None, world=None, base=None, manifest=None):
        # P1-C+ preferred path
        ctx = context
        if ctx is None:
            # Legacy fallback (three-kw style) - still supported by the loader
            class _LegacyCtx:
                pass
            ctx = _LegacyCtx()
            ctx.world = world
            ctx.base = base
            ctx.manifest = manifest
            ctx.save_state_manager = getattr(base, "save_state_manager", None) if base else None
            ctx.resource_manager = getattr(base, "resource_manager", None) if base else None

        self.world = ctx.world
        self.base = ctx.base
        self.manifest = getattr(ctx, "manifest", manifest)

        _cartridge_name = (getattr(self.manifest, "name", None) if self.manifest else None) or "{name}"
        print("🧩 Cartridge '" + _cartridge_name + "' initialized via context.")

        # --- Demonstrate SaveStateProvider registration (full happy path) ---
        ssm = getattr(ctx, "save_state_manager", None)
        if ssm is not None:
            class _DemoSaveProvider:
                """Trivial provider so the cartridge participates in the save system."""
                def capture(self, world):
                    # In real code you would walk entities or your own state
                    return {"demo_score": 42, "note": "scaffold-generated provider"}

                def restore(self, world, payload):
                    print("  [demo provider] restore called with", payload)

            try:
                ssm.register_provider("demo", _DemoSaveProvider())
                self._provider_registered = True
                print("  ✓ Registered SaveStateProvider 'demo'")
            except Exception as e:
                print("  (provider already registered or ssm not ready: " + str(e) + ")")

        # --- Create a visible sprite entity using the cartridge's own asset ---
        # The asset was copied into assets/sprites/ during `init` so the cartridge
        # is self-contained. After mount (P1-A) this path resolves from the cartridge root.
        player = self.world.create_entity("player")
        self.world.add_component(player.id, TransformComponent(x=0.0, y=0.0, scale_x=0.8, scale_y=0.8))
        self.world.add_component(
            player.id,
            SpriteComponent(image_path="assets/sprites/player.png", layer=5),
        )
        self.world.add_component(
            player.id,
            PlayerComponent(health=3, score=0),
        )
        # Optional collider so it participates in any collision viz / systems
        self.world.add_component(
            player.id,
            ColliderComponent(
                collider_type=ColliderType.RECTANGLE,
                size=Vec2(0.6, 0.6),
                is_trigger=True,
            ),
        )

        print("  ✓ Spawned demo player entity with cartridge-private sprite + PlayerComponent")
        print("  Tip: use --dev-mode and press V to see collision outlines if the host supports it.")


    # Optional: a reset() makes hot-restart (R/F5) nice during development, like tgl_demo.
    # The loader/main will call entry.reset() on hot-restart requests if present.
    def reset(self):
        print("🔄 (scaffold) reset() called — in a real cartridge you would clear/re-spawn here.")
        # For the absolute minimal we leave entities as-is; a full cartridge would
        # destroy + re-create like tgl_demo does.
'''.replace("{name}", name).replace("{slug}", slug)

    (py_root / "entrypoint.py").write_text(entrypoint_code, encoding="utf-8")

    # 7. Cartridge-local README (points at the new workflow)
    readme = f"""# {name}

A cartridge built with the 2D Game Engine (scaffolded via `py2d-cartridge init`).

## Layout
- `config/cartridge.json` — manifest (name, entrypoint, assets mount, systems.register)
- `assets/` — private assets (highest priority when mounted)
- `python/{slug}/` — your code package (entrypoint + components + systems)
- `python/{slug}/entrypoint.py` — Cartridge class with `initialize(context)`

## Develop
```bash
# From inside this directory
py2d-cartridge .                 # validate + pack to dist/{slug}-0.1.0.car

# Run (from the 2d_game_engine source checkout root that contains main.py;
# main.py is not part of the installed package distribution, so `python -m main`
# will not work from a standalone cartridge directory):
python /path/to/2d_game_engine/main.py --cartridge {cartridge_dir}
# or: cd /path/to/2d_game_engine && python main.py --cartridge /abs/path/to/this/cartridge
```

Hotkeys (when host supports --dev-mode): R/F5 = hot restart, V = toggle collision viz, ESC = clean exit.

## What's in the scaffold (P1-D demo)
- Modern `initialize(self, context)` using CartridgeContext (post P1-C)
- Custom `PlayerComponent`
- A tiny system registered via the manifest (`systems.register`)
- `SaveStateProvider` registration on the injected manager
- A SpriteComponent pointing at a cartridge-private asset (exercises asset precedence)

Replace the sprite, expand the component/system, add your own mechanics, then pack & ship the .car.
"""
    (cartridge_dir / "README.md").write_text(readme, encoding="utf-8")

    # .gitkeep for assets if no sprite was copied
    if not (assets_dir / "player.png").exists():
        (assets_dir / ".gitkeep").write_text("", encoding="utf-8")

    return cartridge_dir



if __name__ == "__main__":
    sys.exit(main())
