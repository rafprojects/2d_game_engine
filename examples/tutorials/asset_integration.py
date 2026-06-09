"""
Asset Integration Tutorial for 2D Game Engine

This tutorial demonstrates how to integrate the asset pipeline into your game,
step by step, showing practical usage patterns and best practices.
"""

import os
import sys

# Add the parent directory to the path so we can import engine modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from engine.core.system import World
from engine.assets.resource_manager import ResourceManager, AssetType
from engine.assets.texture_atlas import TextureAtlas, TextureInfo, TexturePackingStrategy
from engine.assets.asset_streaming import AssetStreamingSystem, StreamingPriority

class AssetTutorial:
    """Step-by-step asset integration tutorial."""
    
    def __init__(self):
        """Initialize the tutorial."""
        print("🎓 Asset Integration Tutorial")
        print("=" * 50)
        
        # Create the core engine systems
        self.world = World()
        self.setup_asset_systems()
        
    def setup_asset_systems(self):
        """Step 1: Set up the asset pipeline systems."""
        print("\n📚 Step 1: Setting up Asset Pipeline Systems")
        print("-" * 40)
        
        # Initialize ResourceManager
        print("1️⃣  Creating ResourceManager...")
        self.resource_manager = ResourceManager(self.world)
        self.world.add_system(self.resource_manager)
        print("   ✅ ResourceManager created and added to world")
        
        # Initialize TextureAtlas
        print("2️⃣  Creating TextureAtlas...")
        self.texture_atlas = TextureAtlas(
            max_width=1024,
            max_height=1024,
            padding=2,
            strategy=TexturePackingStrategy.BEST_FIT
        )
        print("   ✅ TextureAtlas created (1024x1024, 2px padding, BEST_FIT)")
        
        # Initialize AssetStreamingSystem
        print("3️⃣  Creating AssetStreamingSystem...")
        self.streaming_system = AssetStreamingSystem(self.world, self.resource_manager)
        self.world.add_system(self.streaming_system)
        print("   ✅ AssetStreamingSystem created and added to world")
        
        print("✨ Asset pipeline systems ready!")
    
    def step_2_basic_asset_loading(self):
        """Step 2: Learn basic asset loading."""
        print("\n📚 Step 2: Basic Asset Loading")
        print("-" * 40)
        
        # Create assets directory if it doesn't exist
        assets_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'assets')
        if not os.path.exists(assets_dir):
            os.makedirs(assets_dir)
            print(f"📁 Created assets directory: {assets_dir}")
        
        # Example 1: Loading a texture
        print("1️⃣  Loading a texture asset...")
        texture_path = os.path.join(assets_dir, "player.png")
        
        if os.path.exists(texture_path):
            success = self.resource_manager.load_asset("player_sprite", texture_path, AssetType.TEXTURE)
            if success:
                print("   ✅ Player sprite loaded successfully!")
                
                # Get asset information
                asset_info = self.resource_manager.get_asset_info("player_sprite")
                if asset_info:
                    print(f"   📄 Asset type: {asset_info.asset_type.value}")
                    print(f"   📏 File size: {asset_info.size_bytes} bytes")
                    print(f"   ⏱️  Load time: {asset_info.load_time:.3f}s")
            else:
                print("   ❌ Failed to load player sprite")
        else:
            print(f"   ℹ️  Texture not found at {texture_path}")
            print("   💡 Tip: Add a 'player.png' file to see this in action")
        
        # Example 2: Batch loading
        print("\n2️⃣  Batch loading multiple assets...")
        asset_files = [
            ("background", "background.png", AssetType.TEXTURE),
            ("sfx_jump", "jump.wav", AssetType.AUDIO),
            ("level_data", "level1.json", AssetType.DATA),
        ]
        
        loaded_count = 0
        for asset_id, filename, asset_type in asset_files:
            file_path = os.path.join(assets_dir, filename)
            if os.path.exists(file_path):
                if self.resource_manager.load_asset(asset_id, file_path, asset_type):
                    loaded_count += 1
                    print(f"   ✅ {asset_id} loaded")
            else:
                print(f"   ⚠️  {filename} not found (optional)")
        
        print(f"   📊 Loaded {loaded_count}/{len(asset_files)} assets")
        
        # Show resource manager statistics
        stats = self.resource_manager.get_manager_statistics()
        print(f"\n📈 Resource Manager Stats:")
        print(f"   📦 Total assets: {stats['total_assets']}")
        print(f"   💾 Memory usage: {stats['memory_usage_mb']:.2f} MB")
        print(f"   ⚡ Cache hit rate: {stats['cache_hit_rate']:.1f}%")
    
    def step_3_texture_atlas_usage(self):
        """Step 3: Learn texture atlas usage."""
        print("\n📚 Step 3: Texture Atlas Usage")
        print("-" * 40)
        
        print("1️⃣  Creating sample sprite data...")
        
        # Create sample texture data for demonstration
        sample_textures = [
            TextureInfo("ui_button", 128, 32, "button_texture_data"),
            TextureInfo("ui_icon_1", 32, 32, "icon1_texture_data"),
            TextureInfo("ui_icon_2", 32, 32, "icon2_texture_data"),
            TextureInfo("ui_icon_3", 32, 32, "icon3_texture_data"),
            TextureInfo("player_idle", 64, 64, "player_idle_data"),
            TextureInfo("player_walk", 64, 64, "player_walk_data"),
            TextureInfo("enemy_sprite", 48, 48, "enemy_sprite_data"),
            TextureInfo("projectile", 16, 16, "projectile_data"),
        ]
        
        print(f"   📦 Created {len(sample_textures)} sample textures")
        
        print("\n2️⃣  Packing textures into atlas...")
        pack_success = self.texture_atlas.pack_textures(sample_textures)
        
        if pack_success:
            print("   ✅ All textures packed successfully!")
            
            # Show atlas statistics
            atlas_info = self.texture_atlas.get_atlas_info()
            print(f"\n📊 Atlas Statistics:")
            print(f"   🗂️  Atlas count: {atlas_info['atlas_count']}")
            print(f"   🖼️  Total textures: {atlas_info['total_textures']}")
            print(f"   📈 Packing efficiency: {atlas_info['efficiency']:.1f}%")
            
            # Show some texture regions
            print(f"\n🎯 Texture Regions (sample):")
            for texture in sample_textures[:4]:  # Show first 4
                region = self.texture_atlas.get_region(texture.name)
                if region:
                    print(f"   {texture.name:15}: pos=({region.x:3}, {region.y:3}) size={region.width}x{region.height}")
            
            print("\n3️⃣  Getting UV coordinates for rendering...")
            # Demonstrate getting UV coordinates
            for texture_name in ["ui_button", "player_idle"]:
                uv_coords = self.texture_atlas.get_uv_coordinates(texture_name)
                if uv_coords:
                    u1, v1, u2, v2 = uv_coords
                    print(f"   {texture_name}: UV=({u1:.3f}, {v1:.3f}) to ({u2:.3f}, {v2:.3f})")
        else:
            print("   ❌ Failed to pack textures")
    
    def step_4_asset_streaming(self):
        """Step 4: Learn asset streaming."""
        print("\n📚 Step 4: Asset Streaming")
        print("-" * 40)
        
        print("1️⃣  Configuring streaming system...")
        
        # Configure streaming parameters
        self.streaming_system.set_streaming_distance(150.0)
        self.streaming_system.set_unload_distance(300.0)
        self.streaming_system.set_max_concurrent_loads(2)
        
        print(f"   ⚙️  Stream distance: {self.streaming_system.stream_distance}")
        print(f"   ⚙️  Unload distance: {self.streaming_system.unload_distance}")
        print(f"   ⚙️  Max concurrent loads: {self.streaming_system.max_concurrent_loads}")
        
        print("\n2️⃣  Setting up streaming zones...")
        
        # Define game areas with their assets
        game_zones = [
            {
                "name": "spawn_area",
                "center": (0, 0),
                "radius": 100,
                "assets": ["spawn_bg", "spawn_music", "tutorial_sprites"]
            },
            {
                "name": "forest_level",
                "center": (300, 100),
                "radius": 150,
                "assets": ["forest_bg", "tree_sprites", "forest_ambience"]
            },
            {
                "name": "boss_arena",
                "center": (600, 200),
                "radius": 120,
                "assets": ["boss_bg", "boss_music", "boss_sprites", "special_effects"]
            }
        ]
        
        for zone in game_zones:
            self.streaming_system.add_streaming_zone(
                zone["name"],
                center=zone["center"],
                radius=zone["radius"],
                assets=zone["assets"]
            )
            print(f"   🗺️  Added zone '{zone['name']}' at {zone['center']} (radius {zone['radius']})")
        
        print("\n3️⃣  Simulating player movement and streaming...")
        
        # Simulate player moving through the world
        player_positions = [
            (0, 0),      # Start at spawn
            (50, 50),    # Move within spawn area
            (150, 75),   # Move towards forest
            (300, 100),  # Enter forest
            (450, 150),  # Move towards boss
            (600, 200),  # Enter boss arena
        ]
        
        for i, (x, y) in enumerate(player_positions):
            print(f"\n   🏃 Player position {i+1}: ({x}, {y})")
            
            # Update player position for streaming
            self.streaming_system.update_player_position(x, y)
            
            # Request some priority assets based on player action
            if i == 0:  # Start of game
                self.streaming_system.request_asset("player_spawn_effect", StreamingPriority.CRITICAL, 0)
            elif i == 3:  # Entering forest
                self.streaming_system.request_asset("forest_entrance_cutscene", StreamingPriority.HIGH, 50)
            elif i == 5:  # Boss fight
                self.streaming_system.request_asset("boss_intro_video", StreamingPriority.CRITICAL, 0)
            
            # Simulate game update
            self.streaming_system.update(0.016)  # 60 FPS
            
            # Show streaming statistics
            stats = self.streaming_system.get_streaming_statistics()
            print(f"      📊 Queued: {stats['queued_requests']}, Active: {stats['active_loads']}")
            print(f"      💾 Memory pressure: {stats['memory_pressure']:.1f}%")
    
    def step_5_integration_patterns(self):
        """Step 5: Learn integration patterns."""
        print("\n📚 Step 5: Integration Patterns")
        print("-" * 40)
        
        print("1️⃣  Game Scene Integration Pattern...")
        self.demo_scene_integration()
        
        print("\n2️⃣  Level-of-Detail (LOD) Pattern...")
        self.demo_lod_pattern()
        
        print("\n3️⃣  Asset Lifecycle Management...")
        self.demo_asset_lifecycle()
    
    def demo_scene_integration(self):
        """Demonstrate scene-based asset management."""
        
        class GameScene:
            """Example game scene with asset management."""
            
            def __init__(self, scene_name, resource_manager, streaming_system):
                self.scene_name = scene_name
                self.resource_manager = resource_manager
                self.streaming_system = streaming_system
                self.scene_assets = {
                    "main_menu": ["menu_bg", "menu_music", "ui_elements"],
                    "gameplay": ["level_bg", "game_music", "player_sprites", "enemy_sprites"],
                    "credits": ["credits_bg", "credits_music", "staff_images"]
                }
            
            def load_scene(self):
                """Load all assets for this scene."""
                print(f"   🎬 Loading scene: {self.scene_name}")
                
                assets = self.scene_assets.get(self.scene_name, [])
                for asset_name in assets:
                    # Load critical assets immediately
                    self.resource_manager.acquire_asset(asset_name)
                    print(f"      ✅ Loaded {asset_name}")
                
                print(f"   📦 Loaded {len(assets)} assets for {self.scene_name}")
            
            def unload_scene(self):
                """Unload scene-specific assets."""
                print(f"   🗑️  Unloading scene: {self.scene_name}")
                
                assets = self.scene_assets.get(self.scene_name, [])
                for asset_name in assets:
                    self.resource_manager.release_asset(asset_name)
                    print(f"      ♻️  Released {asset_name}")
        
        # Demonstrate scene transitions
        scenes = ["main_menu", "gameplay", "credits"]
        current_scene = None
        
        for scene_name in scenes:
            # Unload previous scene
            if current_scene:
                current_scene.unload_scene()
            
            # Load new scene
            current_scene = GameScene(scene_name, self.resource_manager, self.streaming_system)
            current_scene.load_scene()
    
    def demo_lod_pattern(self):
        """Demonstrate Level-of-Detail asset management."""
        
        class LODManager:
            """Example LOD manager."""
            
            def __init__(self, streaming_system):
                self.streaming_system = streaming_system
                self.lod_thresholds = {
                    "high": 100.0,     # High detail within 100 units
                    "medium": 250.0,   # Medium detail 100-250 units
                    "low": 500.0       # Low detail 250-500 units
                }
            
            def update_entity_lod(self, entity_id, entity_pos, camera_pos):
                """Update entity LOD based on camera distance."""
                distance = ((entity_pos[0] - camera_pos[0])**2 + 
                           (entity_pos[1] - camera_pos[1])**2)**0.5
                
                # Determine LOD level
                if distance <= self.lod_thresholds["high"]:
                    lod_level = "high"
                    priority = StreamingPriority.HIGH
                elif distance <= self.lod_thresholds["medium"]:
                    lod_level = "medium"
                    priority = StreamingPriority.NORMAL
                else:
                    lod_level = "low"
                    priority = StreamingPriority.LOW
                
                # Request appropriate asset
                asset_name = f"{entity_id}_texture_{lod_level}"
                self.streaming_system.request_asset(asset_name, priority, distance)
                
                return lod_level
        
        # Demonstrate LOD system
        lod_manager = LODManager(self.streaming_system)
        camera_pos = (0, 0)
        
        entities = [
            ("building_1", (50, 50)),
            ("building_2", (150, 100)),
            ("building_3", (400, 200)),
            ("tree_1", (600, 300)),
        ]
        
        for entity_id, entity_pos in entities:
            lod_level = lod_manager.update_entity_lod(entity_id, entity_pos, camera_pos)
            distance = ((entity_pos[0] - camera_pos[0])**2 + 
                       (entity_pos[1] - camera_pos[1])**2)**0.5
            print(f"      🏠 {entity_id}: distance={distance:.1f}, LOD={lod_level}")
    
    def demo_asset_lifecycle(self):
        """Demonstrate asset lifecycle management."""
        
        print("   📋 Asset Lifecycle Example:")
        
        # 1. Asset acquisition
        print("      1️⃣  Acquiring assets...")
        self.resource_manager.acquire_asset("shared_texture")
        self.resource_manager.acquire_asset("shared_texture")  # Second reference
        print("         ✅ Acquired 'shared_texture' (ref count: 2)")
        
        # 2. Asset usage
        print("      2️⃣  Using assets...")
        asset_data = self.resource_manager.get_asset("shared_texture")
        print(f"         📦 Asset data available: {asset_data is not None}")
        
        # 3. Asset release
        print("      3️⃣  Releasing assets...")
        self.resource_manager.release_asset("shared_texture")  # ref count: 1
        print("         ♻️  Released one reference (ref count: 1)")
        
        self.resource_manager.release_asset("shared_texture")  # ref count: 0
        print("         ♻️  Released final reference (asset unloaded)")
        
        # 4. Verify cleanup
        asset_data = self.resource_manager.get_asset("shared_texture")
        print(f"         🗑️  Asset data after cleanup: {asset_data is not None}")
    
    def step_6_best_practices(self):
        """Step 6: Best practices and tips."""
        print("\n📚 Step 6: Best Practices and Tips")
        print("-" * 40)
        
        practices = [
            "🎯 Use appropriate asset types for automatic optimization",
            "⚡ Preload critical assets during loading screens",
            "🔄 Enable predictive loading for smooth gameplay",
            "💾 Set memory limits to prevent excessive RAM usage",
            "📊 Monitor asset statistics to identify bottlenecks",
            "🗂️  Use texture atlases for small sprites and UI elements",
            "📏 Configure streaming distances based on your game's scale",
            "🎨 Use LOD systems for performance in large worlds",
            "♻️  Implement proper reference counting for shared assets",
            "🔧 Enable hot-reload during development for faster iteration"
        ]
        
        print("💡 Key Best Practices:")
        for practice in practices:
            print(f"   {practice}")
        
        print("\n🚀 Performance Tips:")
        perf_tips = [
            "Pack UI sprites into atlases to reduce draw calls",
            "Use streaming zones to automatically manage level assets",
            "Enable memory pressure management for mobile platforms",
            "Preload assets based on player progression patterns",
            "Use asset manifests to organize and batch load resources"
        ]
        
        for tip in perf_tips:
            print(f"   ⚡ {tip}")
    
    def run_tutorial(self):
        """Run the complete tutorial."""
        try:
            # Run all tutorial steps
            self.step_2_basic_asset_loading()
            self.step_3_texture_atlas_usage()
            self.step_4_asset_streaming()
            self.step_5_integration_patterns()
            self.step_6_best_practices()
            
            # Final summary
            print("\n" + "=" * 50)
            print("🎉 Asset Integration Tutorial Complete!")
            print("=" * 50)
            
            print("\nYou've learned:")
            print("✅ Basic asset loading with ResourceManager")
            print("✅ Texture packing with TextureAtlas")
            print("✅ Dynamic streaming with AssetStreamingSystem")
            print("✅ Integration patterns for real games")
            print("✅ Best practices and performance tips")
            
            print("\n🚀 Next Steps:")
            print("• Integrate asset pipeline into your game")
            print("• Experiment with different streaming strategies")
            print("• Optimize texture atlases for your assets")
            print("• Monitor performance and adjust settings")
            
            print("\n📚 Additional Resources:")
            print("• docs/guides/asset_pipeline_guide.md - Complete API reference")
            print("• examples/demos/asset_pipeline_demo.py - Feature demonstrations")
            print("• examples/games/ - Real game implementations")
            
        except KeyboardInterrupt:
            print("\n\n👋 Tutorial interrupted by user")
        except Exception as e:
            print(f"\n❌ Tutorial failed with error: {e}")
            import traceback
            traceback.print_exc()

def main():
    """Run the asset integration tutorial."""
    tutorial = AssetTutorial()
    tutorial.run_tutorial()

if __name__ == "__main__":
    main()
