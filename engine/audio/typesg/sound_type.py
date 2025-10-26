from enum import Enum

class SoundType(Enum):
    """Types of sound effects supported."""
    EFFECT = "effect"      # Short sound effects (gunshots, jumps, etc.)
    AMBIENT = "ambient"    # Looping ambient sounds (rain, wind, etc.)
    VOICE = "voice"        # Voice lines and speech
    UI = "ui"             # User interface sounds (clicks, beeps, etc.)
