"""
Asset Pipeline Module for 2D Game Engine

This module provides comprehensive asset management capabilities including:
- ResourceManager: Centralized asset loading, caching, and validation
- AssetStreamingSystem: Dynamic asset streaming based on proximity and need
- TextureAtlas: Texture packing and atlas management
- Asset validation and hot-reload support

The asset pipeline is designed to work seamlessly with the ECS architecture
and provides both high-level convenience methods and low-level control.
"""

from .resource_manager import ResourceManager, AssetInfo
from .asset_streaming import AssetStreamingSystem, StreamingRequest
from .texture_atlas import TextureAtlas, AtlasRegion
from .typesg import StreamingPriority, AssetType, AssetState, TexturePackingStrategy

__all__ = [
    # Types and States
    'AssetType',
    'AssetState',
    'TexturePackingStrategy',
    'StreamingPriority',
    
    # Classes
    'StreamingRequest',
    'AtlasRegion',
    'TextureAtlas',
    'AssetInfo', 

    # Managers and Systems
    'ResourceManager',
    'AssetStreamingSystem',
]
