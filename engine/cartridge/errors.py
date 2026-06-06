"""Cartridge-specific exception types."""


class CartridgeError(Exception):
    """Base class for cartridge errors."""


class CartridgeValidationError(CartridgeError):
    """Raised when the manifest fails schema validation."""


class CartridgeLoadError(CartridgeError):
    """Raised when a cartridge archive cannot be loaded."""
