from enum import Enum

class MusicState(Enum):
    """States for music playback."""
    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"
    FADING_IN = "fading_in"
    FADING_OUT = "fading_out"

class MusicTransition(Enum):
    """Types of music transitions."""
    IMMEDIATE = "immediate"    # Instant switch
    CROSSFADE = "crossfade"   # Fade out old, fade in new
    FADE_OUT_IN = "fade_out_in"  # Fade out, silence, fade in