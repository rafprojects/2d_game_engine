"""Save-state manager that coordinates serialization providers and persistence."""

from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, MutableMapping, Optional, Protocol

import msgpack

from .errors import SaveStateError, ensure


class SaveStateProvider(Protocol):
    """Interface cartridges implement to serialize/restore their state."""

    def capture(self, world) -> Dict[str, Any]:  # pragma: no cover - protocol
        ...

    def restore(self, world, payload: Dict[str, Any]) -> None:  # pragma: no cover - protocol
        ...


@dataclass(slots=True)
class SaveStateMetadata:
    version: str
    slot: str
    created_at: float
    cartridge: Optional[str] = None
    cartridge_version: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class SaveState:
    metadata: SaveStateMetadata
    payload: Dict[str, Any]


class SaveStateManager:
    """Coordinates save providers and persistence backends."""

    def __init__(
        self,
        world,
        storage_root: str | os.PathLike[str] | None = None,
        serializer_version: str = "1.0.0",
    ):
        self.world = world
        self.storage_root = Path(storage_root or Path.cwd() / "saves").expanduser().resolve()
        self.storage_root.mkdir(parents=True, exist_ok=True)
        self.serializer_version = serializer_version
        self.providers: MutableMapping[str, SaveStateProvider] = {}
        self._cartridge_name: Optional[str] = None
        self._cartridge_version: Optional[str] = None

    @property
    def cartridge_name(self) -> Optional[str]:
        return self._cartridge_name

    @property
    def cartridge_version(self) -> Optional[str]:
        return self._cartridge_version

    # Cartridge lifecycle -------------------------------------------------
    def attach_manifest(self, manifest) -> None:
        """Record cartridge metadata for future saves."""
        self._cartridge_name = getattr(manifest, "name", None)
        self._cartridge_version = getattr(manifest, "version", None)

    # Provider management -------------------------------------------------
    def register_provider(self, name: str, provider: SaveStateProvider) -> None:
        ensure(name not in self.providers, f"Provider '{name}' already registered")
        self.providers[name] = provider

    def unregister_provider(self, name: str) -> None:
        self.providers.pop(name, None)

    # Persistence helpers -------------------------------------------------
    def capture_state(self, slot: str, extra: Optional[Dict[str, Any]] = None) -> SaveState:
        payload = {}
        for name, provider in self.providers.items():
            payload[name] = provider.capture(self.world)
        metadata = SaveStateMetadata(
            version=self.serializer_version,
            slot=slot,
            created_at=time.time(),
            cartridge=self._cartridge_name,
            cartridge_version=self._cartridge_version,
            extra=extra or {},
        )
        return SaveState(metadata=metadata, payload=payload)

    def apply_state(self, state: SaveState) -> None:
        for name, provider in self.providers.items():
            provider_state = state.payload.get(name, {})
            provider.restore(self.world, provider_state)

    def save(self, slot: str, fmt: str = "msgpack", extra: Optional[Dict[str, Any]] = None) -> Path:
        state = self.capture_state(slot, extra)
        data = {
            "metadata": asdict(state.metadata),
            "payload": state.payload,
        }
        path = self._resolve_slot_path(slot, fmt)
        path.parent.mkdir(parents=True, exist_ok=True)
        if fmt == "msgpack":
            with path.open("wb") as fp:
                msgpack.pack(data, fp, use_bin_type=True)
        elif fmt == "json":
            with path.open("w", encoding="utf-8") as fp:
                json.dump(data, fp, indent=2)
        else:
            raise SaveStateError(f"Unsupported format '{fmt}'")
        return path

    def load(self, slot: str, fmt: str = "msgpack") -> SaveState:
        path = self._resolve_slot_path(slot, fmt)
        ensure(path.exists(), f"Save slot '{slot}' not found for format {fmt}")
        if fmt == "msgpack":
            with path.open("rb") as fp:
                raw = msgpack.unpack(fp, raw=False)
        elif fmt == "json":
            with path.open("r", encoding="utf-8") as fp:
                raw = json.load(fp)
        else:
            raise SaveStateError(f"Unsupported format '{fmt}'")
        metadata_dict = raw.get("metadata", {})
        metadata = SaveStateMetadata(
            version=metadata_dict.get("version", self.serializer_version),
            slot=metadata_dict.get("slot", slot),
            created_at=metadata_dict.get("created_at", time.time()),
            cartridge=metadata_dict.get("cartridge"),
            cartridge_version=metadata_dict.get("cartridge_version"),
            extra=metadata_dict.get("extra", {}),
        )
        payload = raw.get("payload", {})
        return SaveState(metadata=metadata, payload=payload)

    def restore(self, slot: str, fmt: str = "msgpack") -> SaveState:
        state = self.load(slot, fmt)
        self.apply_state(state)
        return state

    def list_saves(self, fmt: str = "msgpack") -> Iterable[str]:
        suffix = self._format_suffix(fmt)
        slot_dir = self._slot_dir()
        if not slot_dir.exists():
            return []
        slots = []
        for file in slot_dir.glob(f"*{suffix}"):
            slots.append(file.stem)
        return sorted(slots)

    def delete(self, slot: str, fmt: str = "msgpack") -> None:
        path = self._resolve_slot_path(slot, fmt)
        if path.exists():
            path.unlink()

    # Internal helpers ----------------------------------------------------
    def _slot_dir(self) -> Path:
        cartridge_folder = self._cartridge_name or "__global__"
        return self.storage_root / cartridge_folder

    def _format_suffix(self, fmt: str) -> str:
        if fmt == "msgpack":
            return ".sav"
        if fmt == "json":
            return ".json"
        raise SaveStateError(f"Unsupported format '{fmt}'")

    def _resolve_slot_path(self, slot: str, fmt: str) -> Path:
        suffix = self._format_suffix(fmt)
        safe_slot = slot.replace("/", "_")
        return self._slot_dir() / f"{safe_slot}{suffix}"
