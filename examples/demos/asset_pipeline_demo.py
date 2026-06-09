"""
Asset Pipeline Demo for 2D Game Engine

This demo shows how to use the asset pipeline system including:
- ResourceManager for centralized asset loading
- TextureAtlas for texture packing
- AssetStreamingSystem for dynamic loading
"""

import os
import sys

# Add the parent directory to the path so we can import engine modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from engine.core.system import World
from engine.assets.resource_manager import ResourceManager, AssetType
from engine.assets.texture_atlas import TextureAtlas, TextureInfo, TexturePackingStrategy
from engine.assets.asset_streaming import AssetStreamingSystem, StreamingPriority

def main():
    """Run the asset pipeline demo."""
    print("🎮 2D Game Engine - Asset Pipeline Demo")
    print("=" * 50)
    
    # Create world and systems
    world = World()
    
    # Initialize resource manager
    print("\n📦 Initializing Resource Manager...")
    resource_manager = ResourceManager(world)
    world.add_system(resource_manager)
    
    # Initialize asset streaming system
    print("🔄 Initializing Asset Streaming System...")
    streaming_system = AssetStreamingSystem(world, resource_manager)
    world.add_system(streaming_system)
    
    # Initialize texture atlas
    print("🖼️  Initializing Texture Atlas...")
    texture_atlas = TextureAtlas(
        max_width=1024,
        max_height=1024,
        strategy=TexturePackingStrategy.BEST_FIT
    )
    
    # Demo 1: Resource Manager Features
    print("\n" + "=" * 50)
    print("Demo 1: Resource Manager Features")
    print("=" * 50)
    
    # Check if assets directory exists
    assets_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'assets')
    if not os.path.exists(assets_dir):
        print(f"ℹ️  Creating assets directory: {assets_dir}")
        os.makedirs(assets_dir)
    
    # Try to load an asset
    test_asset_path = os.path.join(assets_dir, "player.png")
    if os.path.exists(test_asset_path):
        print(f"✅ Loading asset: {test_asset_path}")
        success = resource_manager.load_asset("player", test_asset_path, AssetType.TEXTURE)
        if success:
            print("✅ Asset loaded successfully!")
            
            # Get asset info
            asset_info = resource_manager.get_asset_info("player")
            if asset_info:
                print(f"   📄 Asset Type: {asset_info.asset_type.value}")
                print(f"   📏 Size: {asset_info.size_bytes} bytes")
                print(f"   ⏱️  Load Time: {asset_info.load_time:.3f}s")
                print(f"   🔗 Ref Count: {asset_info.ref_count}")
        else:
            print("❌ Failed to load asset")
    else:
        print(f"⚠️  Test asset not found: {test_asset_path}")
        print("   Please add a 'player.png' file to the assets directory to see loading demo")
    
    # Demo resource management features
    print(f"\n📊 Resource Manager Statistics:")
    stats = resource_manager.get_manager_statistics()
    print(f"   📦 Total Assets: {stats['total_assets']}")
    print(f"   💾 Memory Usage: {stats['memory_usage_mb']:.2f} MB")
    print(f"   ⚡ Cache Hit Rate: {stats['cache_hit_rate']:.1f}%")
    
    # Demo 2: Texture Atlas Features
    print("\n" + "=" * 50)
    print("Demo 2: Texture Atlas Features")
    print("=" * 50)
    
    # Create some sample texture data for the atlas
    sample_textures = [
        TextureInfo("sprite_1", 64, 64, "dummy_data_1"),
        TextureInfo("sprite_2", 32, 32, "dummy_data_2"),
        TextureInfo("sprite_3", 128, 64, "dummy_data_3"),
        TextureInfo("sprite_4", 48, 48, "dummy_data_4"),
        TextureInfo("sprite_5", 96, 96, "dummy_data_5"),
    ]
    
    print(f"📋 Packing {len(sample_textures)} textures into atlas...")
    success = texture_atlas.pack_textures(sample_textures)
    
    if success:
        print("✅ All textures packed successfully!")
        
        # Get atlas info
        atlas_info = texture_atlas.get_atlas_info()
        print(f"\n📊 Atlas Statistics:")
        print(f"   🗂️  Atlas Count: {atlas_info['atlas_count']}")
        print(f"   🖼️  Total Textures: {atlas_info['total_textures']}")
        print(f"   📈 Efficiency: {atlas_info['efficiency']:.1f}%")
        print(f"   🎯 Regions: {atlas_info['regions']}")
        
        # Show some texture regions
        print(f"\n🎯 Texture Regions:")
        for texture in sample_textures[:3]:  # Show first 3
            region = texture_atlas.get_region(texture.name)
            if region:
                print(f"   {texture.name}: ({region.x}, {region.y}) {region.width}x{region.height}")
    else:
        print("❌ Failed to pack textures")
    
    # Demo 3: Asset Streaming Features
    print("\n" + "=" * 50)
    print("Demo 3: Asset Streaming Features")
    print("=" * 50)
    
    # Configure streaming
    streaming_system.set_streaming_distance(150.0)
    streaming_system.set_max_concurrent_loads(2)
    
    print(f"⚙️  Streaming Configuration:")
    print(f"   📏 Stream Distance: {streaming_system.stream_distance}")
    print(f"   🔄 Max Concurrent Loads: {streaming_system.max_concurrent_loads}")
    print(f"   ⏹️  Unload Distance: {streaming_system.unload_distance}")
    
    # Queue some assets for streaming
    test_assets = [
        ("background_1", StreamingPriority.HIGH, 50.0),
        ("background_2", StreamingPriority.NORMAL, 120.0),
        ("effect_1", StreamingPriority.LOW, 200.0),
    ]
    
    print(f"\n📥 Queuing assets for streaming:")
    for asset_name, priority, distance in test_assets:
        streaming_system.request_asset(asset_name, priority, distance)
        print(f"   📦 {asset_name} (Priority: {priority.name}, Distance: {distance})")
    
    # Show streaming statistics
    streaming_stats = streaming_system.get_streaming_statistics()
    print(f"\n📊 Streaming Statistics:")
    print(f"   📥 Queued Requests: {streaming_stats['queued_requests']}")
    print(f"   🔄 Active Loads: {streaming_stats['active_loads']}")
    print(f"   💾 Memory Pressure: {streaming_stats['memory_pressure']:.1f}%")
    
    # Demo 4: Integration Example
    print("\n" + "=" * 50)
    print("Demo 4: Integration Example")
    print("=" * 50)
    
    print("🔗 Demonstrating system integration...")
    
    # Update systems (simulate game loop)
    print("⚡ Running simulation update...")
    dt = 0.016  # 60 FPS
    
    resource_manager.update(dt)
    streaming_system.update(dt)
    
    print("✅ Systems updated successfully!")
    
    # Show final statistics
    print(f"\n📈 Final System Statistics:")
    print(f"   🎯 Resource Manager: {len(resource_manager.assets)} assets")
    print(f"   🗂️  Texture Atlas: {texture_atlas.atlas_count} atlases")
    print(f"   🔄 Streaming System: Active and monitoring")
    
    print("\n" + "=" * 50)
    print("🎉 Asset Pipeline Demo Complete!")
    print("=" * 50)
    print("\nThe asset pipeline provides:")
    print("✨ Centralized resource management")
    print("✨ Efficient texture atlasing") 
    print("✨ Dynamic asset streaming")
    print("✨ Seamless ECS integration")
    print("\nReady for production use! 🚀")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
