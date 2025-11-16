"""Cartridge manifest dataclasses and helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(slots=True)
class AssetMount:
    mount_path: str
    virtual_root: str


@dataclass(slots=True)
class CartridgeManifest:
    name: str
    version: str
    entrypoint: str
    assets: AssetMount
    system_modules: List[str] = field(default_factory=list)
    python_path: str = "python"
    metadata: Dict[str, Any] = field(default_factory=dict)
    engine_requirement: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CartridgeManifest":
        cartridge = data.get("cartridge", {})
        assets = data.get("assets", {})
        systems = data.get("systems", {})

        required = {"name", "version", "entrypoint"}
        missing = [key for key in required if key not in cartridge]
        if missing:
            raise ValueError(f"Missing required cartridge keys: {', '.join(missing)}")

        if "mount" not in assets:
            raise ValueError("assets.mount is required in cartridge manifest")

        asset_mount = AssetMount(
            mount_path=assets["mount"],
            virtual_root=assets.get("virtual_root", cartridge["name"].lower()),
        )

        return cls(
            name=cartridge["name"],
            version=cartridge["version"],
            entrypoint=cartridge["entrypoint"],
            assets=asset_mount,
            system_modules=systems.get("register", []),
            python_path=data.get("python_path", "python"),
            metadata=data.get("metadata", {}),
            engine_requirement=cartridge.get("requires", {}).get("engine")
            if isinstance(cartridge.get("requires"), dict)
            else None,
        )
