from enum import Enum

# asset_streaming.py
class StreamingPriority(Enum):
    """Priority levels for asset streaming."""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


# resource_manager.py
class AssetType(Enum):
    """Types of assets supported by the resource manager."""
    TEXTURE = "texture"
    AUDIO = "audio"
    DATA = "data"
    FONT = "font"
    SPRITE_SHEET = "sprite_sheet"
    ANIMATION = "animation"
    SHADER = "shader"
    MODEL = "model"

class AssetState(Enum):
    """States of asset loading."""
    UNLOADED = "unloaded"
    LOADING = "loading"
    LOADED = "loaded"
    ERROR = "error"
    STREAMING = "streaming"


# texture_atlas.py
class TexturePackingStrategy(Enum):
    """Strategies for packing textures into atlas."""
    BEST_FIT = "best_fit"
    BOTTOM_LEFT = "bottom_left"
    SHELF = "shelf"
    MAXRECTS = "maxrects"