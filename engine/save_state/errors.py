"""Custom exception types for save-state operations."""


class SaveStateError(Exception):
    """Base error for save-state failures."""


def ensure(condition: bool, message: str) -> None:
    """Helper that raises SaveStateError when condition is False."""
    if not condition:
        raise SaveStateError(message)
