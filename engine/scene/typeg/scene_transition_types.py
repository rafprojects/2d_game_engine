from enum import Enum

class TransitionType(Enum):
    """Types of scene transitions."""
    IMMEDIATE = "immediate"          # Instant switch
    FADE = "fade"                   # Fade to black/color
    FADE_THROUGH_COLOR = "fade_through_color"  # Fade to custom color
    SLIDE_LEFT = "slide_left"       # Slide scenes left
    SLIDE_RIGHT = "slide_right"     # Slide scenes right
    SLIDE_UP = "slide_up"           # Slide scenes up
    SLIDE_DOWN = "slide_down"       # Slide scenes down
    PUSH_LEFT = "push_left"         # Push scenes left
    PUSH_RIGHT = "push_right"       # Push scenes right
    WIPE_LEFT = "wipe_left"         # Wipe transition left
    WIPE_RIGHT = "wipe_right"       # Wipe transition right
    CIRCLE_CLOSE = "circle_close"   # Circular close transition
    CIRCLE_OPEN = "circle_open"     # Circular open transition
    CUSTOM = "custom"               # Custom transition function
