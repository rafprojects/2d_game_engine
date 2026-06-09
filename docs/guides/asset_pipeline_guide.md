# Asset Pipeline Guide

The 2D Game Engine includes a comprehensive asset pipeline that provides centralized resource management, texture atlasing, and dynamic asset streaming. This guide covers how to use all the asset pipeline features effectively.

## Overview

The asset pipeline consists of three main components:

1. **ResourceManager**: Centralized asset loading, caching, and validation
2. **TextureAtlas**: Texture packing and atlas management for optimized rendering
3. **AssetStreamingSystem**: Dynamic asset loading/unloading based on proximity and need

## Quick Start

```python
from engine.core.system import World
from engine.assets import ResourceManager, AssetStreamingSystem, TextureAtlas

# Initialize systems
world = World()
resource_manager = ResourceManager(world)
streaming_system = AssetStreamingSystem(world, resource_manager)
texture_atlas = TextureAtlas()

# Add to world
world.add_system(resource_manager)
world.add_system(streaming_system)
```

## ResourceManager

The ResourceManager provides centralized asset loading with automatic caching, validation, and hot-reload support.

### Basic Usage

```python
from engine.assets import ResourceManager, AssetType

# Load an asset
success = resource_manager.load_asset("player_sprite", "assets/player.png", AssetType.TEXTURE)

# Get loaded asset
sprite_data = resource_manager.get_asset("player_sprite")

# Check if asset is loaded
if resource_manager.is_asset_loaded("player_sprite"):
    print("Asset is ready!")

# Unload when done
resource_manager.unload_asset("player_sprite")
```

### Asset Types

The ResourceManager supports multiple asset types:

```python
from engine.assets import AssetType

AssetType.TEXTURE        # Images, sprites
AssetType.AUDIO          # Sound effects, music
AssetType.DATA           # JSON, XML, custom formats
AssetType.FONT           # Font files
AssetType.SPRITE_SHEET   # Sprite sheet definitions
AssetType.ANIMATION      # Animation data
AssetType.SHADER         # Shader programs
AssetType.MODEL          # 3D models
```

### Advanced Features

**Asset Validation:**
```python
# Enable validation
resource_manager.enable_validation()

# Load with validation
success = resource_manager.load_asset_validated("texture", "path.png", AssetType.TEXTURE)
```

**Hot Reload:**
```python
# Enable hot reload
resource_manager.enable_hot_reload()

# Assets will automatically reload when files change
```

**Reference Counting:**
```python
# Acquire reference
resource_manager.acquire_asset("shared_texture")

# Release reference
resource_manager.release_asset("shared_texture")

# Asset is automatically unloaded when ref count reaches 0
```

**Preloading:**
```python
# Preload multiple assets
asset_list = ["texture1.png", "sound1.wav", "data1.json"]
resource_manager.preload_assets(asset_list)
```

**Asset Manifests:**
```python
# Load from manifest file
resource_manager.load_manifest("assets/game_assets.json")

# Manifest format:
{
    "assets": [
        {
            "id": "player_sprite",
            "path": "sprites/player.png",
            "type": "texture",
            "metadata": {"size": [64, 64]}
        }
    ]
}
```

### Statistics and Monitoring

```python
# Get detailed statistics
stats = resource_manager.get_manager_statistics()
print(f"Total assets: {stats['total_assets']}")
print(f"Memory usage: {stats['memory_usage_mb']:.2f} MB")
print(f"Cache hit rate: {stats['cache_hit_rate']:.1f}%")
```

## TextureAtlas

The TextureAtlas system packs multiple textures into single atlas textures for optimized rendering performance.

### Basic Usage

```python
from engine.assets import TextureAtlas, TextureInfo, TexturePackingStrategy

# Create atlas
atlas = TextureAtlas(
    max_width=2048,
    max_height=2048,
    strategy=TexturePackingStrategy.BEST_FIT
)

# Prepare texture data
textures = [
    TextureInfo("sprite1", 64, 64, texture_data_1),
    TextureInfo("sprite2", 32, 32, texture_data_2),
    TextureInfo("sprite3", 128, 64, texture_data_3)
]

# Pack textures
success = atlas.pack_textures(textures)

if success:
    print("All textures packed successfully!")
```

### Packing Strategies

```python
from engine.assets import TexturePackingStrategy

# Available strategies:
TexturePackingStrategy.BEST_FIT     # Minimize wasted space
TexturePackingStrategy.BOTTOM_LEFT  # Simple bottom-left placement
TexturePackingStrategy.SHELF        # Shelf-based packing
TexturePackingStrategy.MAXRECTS     # Maximum rectangles algorithm
```

### Getting UV Coordinates

```python
# Get UV coordinates for rendering
uv_coords = atlas.get_uv_coordinates("sprite1")
if uv_coords:
    u1, v1, u2, v2 = uv_coords
    # Use coordinates for texture mapping
```

### Runtime Management

```python
# Add texture at runtime
new_texture = TextureInfo("dynamic_sprite", 48, 48, data)
atlas.add_texture(new_texture)

# Remove texture (creates fragmentation)
atlas.remove_texture("old_sprite")

# Rebuild atlas to reduce fragmentation
atlas.rebuild_atlas("atlas_0")
```

### Atlas Information

```python
# Get atlas statistics
info = atlas.get_atlas_info()
print(f"Atlas count: {info['atlas_count']}")
print(f"Total textures: {info['total_textures']}")
print(f"Packing efficiency: {info['efficiency']:.1f}%")
```

## AssetStreamingSystem

The AssetStreamingSystem provides dynamic asset loading and unloading based on proximity, prediction, and memory pressure.

### Basic Setup

```python
from engine.assets import AssetStreamingSystem, StreamingPriority

# Initialize with resource manager
streaming = AssetStreamingSystem(world, resource_manager)

# Configure streaming distances
streaming.set_streaming_distance(200.0)    # Load assets within 200 units
streaming.set_unload_distance(400.0)       # Unload assets beyond 400 units
streaming.set_max_concurrent_loads(3)      # Max 3 concurrent loads
```

### Requesting Assets

```python
from engine.assets import StreamingPriority

# Request asset with priority
streaming.request_asset("level_background", StreamingPriority.HIGH, distance=50.0)

# Request with callback
def on_loaded(asset_path, data):
    print(f"Asset {asset_path} loaded!")

streaming.request_asset("effect_sprite", StreamingPriority.NORMAL, 
                       distance=100.0, callback=on_loaded)
```

### Priority Levels

```python
StreamingPriority.CRITICAL  # Must load immediately
StreamingPriority.HIGH      # High priority, load soon
StreamingPriority.NORMAL    # Normal priority
StreamingPriority.LOW       # Low priority, load when convenient
```

### Streaming Zones

```python
# Define streaming zones
streaming.add_streaming_zone("town", center=(100, 100), radius=150.0, 
                           assets=["town_bg", "town_music", "npc_sprites"])

streaming.add_streaming_zone("forest", center=(500, 200), radius=200.0,
                           assets=["forest_bg", "forest_ambience", "tree_sprites"])

# Update player position for automatic streaming
streaming.update_player_position(player_x, player_y)
```

### Predictive Loading

```python
# Enable predictive loading
streaming.enable_predictive_loading()

# Set player velocity for prediction
streaming.set_player_velocity(velocity_x, velocity_y)

# Prediction will automatically load assets the player is moving towards
```

### Memory Management

```python
# Set memory limits
streaming.set_memory_limit(512 * 1024 * 1024)  # 512 MB limit

# Enable memory pressure management
streaming.enable_memory_pressure_management()

# System will automatically unload assets when memory is low
```

### Statistics and Monitoring

```python
# Get streaming statistics
stats = streaming.get_streaming_statistics()
print(f"Queued requests: {stats['queued_requests']}")
print(f"Active loads: {stats['active_loads']}")
print(f"Memory pressure: {stats['memory_pressure']:.1f}%")
print(f"Cache hits: {stats['cache_hits']}")
print(f"Prediction accuracy: {stats['prediction_accuracy']:.1f}%")
```

## Integration Examples

### Scene-Based Asset Management

```python
class GameScene:
    def __init__(self, world, resource_manager, streaming_system):
        self.world = world
        self.resource_manager = resource_manager
        self.streaming_system = streaming_system
    
    def load_scene_assets(self, scene_name):
        """Load all assets for a scene."""
        # Load critical assets immediately
        critical_assets = self.get_critical_assets(scene_name)
        for asset_path in critical_assets:
            self.resource_manager.load_asset(asset_path, asset_path, AssetType.TEXTURE)
        
        # Queue non-critical assets for streaming
        optional_assets = self.get_optional_assets(scene_name)
        for asset_path in optional_assets:
            self.streaming_system.request_asset(asset_path, StreamingPriority.LOW)
    
    def unload_scene_assets(self, scene_name):
        """Unload scene-specific assets."""
        scene_assets = self.get_scene_assets(scene_name)
        for asset_name in scene_assets:
            self.resource_manager.release_asset(asset_name)
```

### Level-of-Detail (LOD) Management

```python
class LODManager:
    def __init__(self, streaming_system):
        self.streaming_system = streaming_system
        self.lod_levels = {
            "high": 0.0,      # 0-100 units
            "medium": 100.0,  # 100-300 units  
            "low": 300.0      # 300+ units
        }
    
    def update_lod(self, entity_position, camera_position):
        """Update LOD based on distance from camera."""
        distance = self.calculate_distance(entity_position, camera_position)
        
        # Determine appropriate LOD level
        lod_level = self.get_lod_level(distance)
        
        # Request appropriate assets
        asset_name = f"entity_texture_{lod_level}"
        priority = StreamingPriority.HIGH if lod_level == "high" else StreamingPriority.NORMAL
        
        self.streaming_system.request_asset(asset_name, priority, distance)
```

### Texture Atlas Integration

```python
class SpriteRenderer:
    def __init__(self, resource_manager, texture_atlas):
        self.resource_manager = resource_manager
        self.texture_atlas = texture_atlas
    
    def render_sprite(self, sprite_name, position):
        """Render a sprite using atlas coordinates."""
        # Get UV coordinates from atlas
        uv_coords = self.texture_atlas.get_uv_coordinates(sprite_name)
        if not uv_coords:
            print(f"Warning: Sprite {sprite_name} not found in atlas")
            return
        
        # Get atlas texture
        region = self.texture_atlas.get_region(sprite_name)
        atlas_texture = self.resource_manager.get_asset(f"atlas_{region.atlas_id}")
        
        # Render with UV coordinates
        self.render_textured_quad(atlas_texture, position, uv_coords)
```

## Performance Tips

### ResourceManager Optimization

1. **Use preloading for known assets**
   ```python
   # Preload during loading screens
   resource_manager.preload_assets(level_assets)
   ```

2. **Enable reference counting for shared assets**
   ```python
   # Multiple entities can safely reference the same asset
   resource_manager.acquire_asset("shared_texture")
   ```

3. **Use asset manifests for organization**
   ```python
   # Organize assets in manifest files
   resource_manager.load_manifest("levels/level1_assets.json")
   ```

### TextureAtlas Optimization

1. **Choose appropriate atlas sizes**
   ```python
   # Consider target platform constraints
   atlas = TextureAtlas(max_width=2048, max_height=2048)  # Good for modern devices
   ```

2. **Use proper packing strategies**
   ```python
   # BEST_FIT for maximum efficiency
   atlas = TextureAtlas(strategy=TexturePackingStrategy.BEST_FIT)
   ```

3. **Add padding to prevent bleeding**
   ```python
   atlas = TextureAtlas(padding=2)  # 2-pixel padding
   ```

### AssetStreamingSystem Optimization

1. **Configure appropriate distances**
   ```python
   # Balance between performance and user experience
   streaming.set_streaming_distance(150.0)  # Not too far
   streaming.set_unload_distance(300.0)     # Not too close
   ```

2. **Use priority levels effectively**
   ```python
   # Critical for gameplay, High for visible, Normal for nearby, Low for distant
   streaming.request_asset("player_weapon", StreamingPriority.CRITICAL)
   ```

3. **Enable prediction for smooth experience**
   ```python
   streaming.enable_predictive_loading()
   streaming.set_prediction_time(2.0)  # 2 seconds ahead
   ```

## Troubleshooting

### Common Issues

**Assets not loading:**
- Check file paths are correct
- Verify asset type matches file format
- Enable validation to catch format issues

**Poor atlas packing efficiency:**
- Try different packing strategies
- Consider texture sizes and atlas dimensions
- Use power-of-two texture sizes when possible

**Streaming performance issues:**
- Reduce concurrent load limits
- Increase streaming distances
- Use appropriate priority levels

**Memory usage too high:**
- Enable memory pressure management
- Reduce asset cache sizes
- Implement proper asset unloading

### Debugging

Enable debug output for detailed information:

```python
# Enable debug logging
resource_manager.enable_debug_logging()
streaming_system.enable_debug_logging()

# Check system statistics regularly
print(resource_manager.get_manager_statistics())
print(streaming_system.get_streaming_statistics())
```

## API Reference

For complete API documentation, see the individual module documentation:

- `engine.assets.resource_manager` - ResourceManager class and utilities
- `engine.assets.texture_atlas` - TextureAtlas and packing algorithms  
- `engine.assets.asset_streaming` - AssetStreamingSystem and streaming logic

## Examples

See the following examples for practical usage:

- `examples/demos/asset_pipeline_demo.py` - Comprehensive demo of all features
- `examples/tutorials/asset_integration.py` - Step-by-step integration guide
- `examples/demos/texture_atlas_demo.py` - Texture atlasing examples
