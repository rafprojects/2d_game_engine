"""Cartridge package

Provides helpers to load self-contained "game cartridges" packaged as archives.
"""

from .manifest import CartridgeManifest
from .errors import CartridgeError, CartridgeValidationError, CartridgeLoadError
from .loader import CartridgeLoader, LoadedCartridge

__all__ = [
    "CartridgeManifest",
    "CartridgeError",
    "CartridgeValidationError",
    "CartridgeLoadError",
    "CartridgeLoader",
    "LoadedCartridge",
]
