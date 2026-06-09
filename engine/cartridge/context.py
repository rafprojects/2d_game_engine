"""CartridgeContext - stable surface for cartridge entrypoint hooks and system registration.

This provides a narrow, versioned facade instead of leaking raw World / Game (ShowBase)
instances and ad-hoc setattr patterns into cartridge code. It is the sanctioned object
passed to initialize/load/mount hooks (and register functions) going forward.

During a short transition, legacy (world, base, manifest) kwargs continue to work for
existing cartridges. New cartridges may be written against `context` only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:  # pragma: no cover - imported only for type checkers
    from engine.assets.resource_manager import ResourceManager
    from engine.cartridge.loader import CartridgeLoader
    from engine.cartridge.manifest import CartridgeManifest
    from engine.save_state.manager import SaveStateManager


@dataclass
class CartridgeContext:
    """Minimal context object injected into cartridge lifecycle hooks.

    Attributes:
        world: The active ECS World (for entity/component/system operations).
        base: The host Panda3D ShowBase/Game instance. Available during transition
              for direct access to window, loader, aspect2d, input accept, etc.
              Cartridges should migrate Panda-specific needs behind context helpers
              over time.
        manifest: The parsed CartridgeManifest for the loaded cartridge (name,
                  version, entrypoint, asset mount info, declared engine requirement, etc.).
        resource_manager: The ResourceManager (if available in the host) with the
                          cartridge's assets already mounted at highest priority.
                          Use for resolve_asset_path etc. when present.
        save_state_manager: The SaveStateManager (if provided by host). Cartridges
                            register their SaveStateProvider(s) here during initialize.
        loader: The CartridgeLoader that loaded this cartridge. Enables self-unload
                patterns in future hosts (e.g. context.loader.unload(self.manifest.name)).

    Convenience:
        .cartridge_name -> manifest.name when present.
    """

    world: Any
    base: Any
    manifest: "CartridgeManifest"
    resource_manager: Optional["ResourceManager"] = None
    save_state_manager: Optional["SaveStateManager"] = None
    loader: Optional["CartridgeLoader"] = None

    @property
    def cartridge_name(self) -> Optional[str]:
        m = self.manifest
        if m is None:
            return None
        return getattr(m, "name", None)
