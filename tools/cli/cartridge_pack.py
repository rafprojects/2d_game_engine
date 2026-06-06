#!/usr/bin/env python3
"""CLI utility to package validated cartridge archives."""

from __future__ import annotations

import argparse
import json
import os
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


if __name__ == "__main__":
    sys.exit(main())
