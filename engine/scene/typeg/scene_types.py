from enum import Enum

class SceneState(Enum):
    """States for scene lifecycle."""
    INACTIVE = "inactive"       # Scene not loaded or visible
    LOADING = "loading"         # Scene is being loaded
    ACTIVE = "active"           # Scene is active and running
    PAUSED = "paused"          # Scene is paused (background scene)
    TRANSITIONING_IN = "transitioning_in"    # Scene is transitioning in
    TRANSITIONING_OUT = "transitioning_out"  # Scene is transitioning out
    UNLOADING = "unloading"     # Scene is being unloaded
