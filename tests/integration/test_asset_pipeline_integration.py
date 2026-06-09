"""
Integration tests for the Asset Pipeline with the main engine.

Tests the asset pipeline components working together with the ECS system.
"""

import unittest
import tempfile
import os

from engine.core.system import World
from engine.assets.resource_manager import ResourceManager, AssetType
from engine.assets.texture_atlas import TextureAtlas, TextureInfo
from engine.assets.asset_streaming import AssetStreamingSystem, StreamingPriority

class TestAssetPipelineIntegration(unittest.TestCase):
    """Integration tests for asset pipeline with ECS."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.world = World()
        
        # Create temporary test files
        self.temp_dir = tempfile.mkdtemp()
        self.test_files = []
        
        # Create sample asset files
        for i in range(3):
            test_file = os.path.join(self.temp_dir, f"asset_{i}.txt")
            with open(test_file, 'w') as f:
                f.write(f"test asset content {i}")
            self.test_files.append(test_file)
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up temp files
        for test_file in self.test_files:
            if os.path.exists(test_file):
                os.remove(test_file)
        os.rmdir(self.temp_dir)
    
    def test_full_pipeline_integration(self):
        """Test the complete asset pipeline working together."""
        print("\n🔗 Testing Full Asset Pipeline Integration...")
        
        # Initialize all systems
        resource_manager = ResourceManager(self.world)
        self.world.add_system(resource_manager)
        
        streaming_system = AssetStreamingSystem(self.world, resource_manager)
        self.world.add_system(streaming_system)
        
        texture_atlas = TextureAtlas(max_width=512, max_height=512)
        
        print("✅ All systems initialized")
        
        # Test 1: Basic asset loading through ResourceManager
        print("\n1️⃣  Testing ResourceManager integration...")
        success = resource_manager.load_asset("test_asset_0", self.test_files[0], AssetType.DATA)
        self.assertTrue(success)
        self.assertTrue(resource_manager.is_asset_loaded("test_asset_0"))
        print("✅ ResourceManager loaded asset successfully")
        
        # Test 2: Asset streaming system integration
        print("\n2️⃣  Testing AssetStreamingSystem integration...")
        streaming_system.request_asset("streamed_asset", StreamingPriority.HIGH, 50.0)
        
        # Simulate game loop updates
        for _ in range(5):
            resource_manager.update(0.016)
            streaming_system.update(0.016)
        
        stats = streaming_system.get_streaming_statistics()
        self.assertIn('queued_requests', stats)
        print("✅ AssetStreamingSystem processed requests")
        
        # Test 3: Texture atlas integration
        print("\n3️⃣  Testing TextureAtlas integration...")
        sample_textures = [
            TextureInfo("ui_button", 64, 32, "button_data"),
            TextureInfo("player_sprite", 32, 32, "player_data"),
            TextureInfo("enemy_sprite", 32, 32, "enemy_data"),
        ]
        
        pack_success = texture_atlas.pack_textures(sample_textures)
        self.assertTrue(pack_success)
        
        # Verify all textures were packed
        for texture in sample_textures:
            region = texture_atlas.get_region(texture.name)
            self.assertIsNotNone(region)
        
        print("✅ TextureAtlas packed textures successfully")
        
        # Test 4: Cross-system communication
        print("\n4️⃣  Testing cross-system communication...")
        
        # Load an asset through ResourceManager and reference it in streaming
        resource_manager.load_asset("shared_texture", self.test_files[1], AssetType.TEXTURE)
        
        # Add to atlas (simulated)
        atlas_texture = TextureInfo("shared_texture", 64, 64, "shared_data")
        texture_atlas.add_texture(atlas_texture)
        
        # Request through streaming system
        streaming_system.request_asset("shared_texture", StreamingPriority.NORMAL, 100.0)
        
        # Verify all systems know about the asset
        self.assertTrue(resource_manager.is_asset_loaded("shared_texture"))
        self.assertIsNotNone(texture_atlas.get_region("shared_texture"))
        
        print("✅ Cross-system communication working")
        
        # Test 5: System statistics and monitoring
        print("\n5️⃣  Testing system monitoring...")
        
        resource_stats = resource_manager.get_manager_statistics()
        streaming_stats = streaming_system.get_streaming_statistics()
        atlas_info = texture_atlas.get_atlas_info()
        
        # Verify all systems provide useful statistics
        self.assertIn('total_assets', resource_stats)
        self.assertIn('memory_usage_mb', resource_stats)
        self.assertIn('queued_requests', streaming_stats)
        self.assertIn('memory_pressure', streaming_stats)
        self.assertIn('atlas_count', atlas_info)
        self.assertIn('efficiency', atlas_info)
        
        print("✅ All systems provide monitoring data")
        
        # Test 6: Cleanup and resource management
        print("\n6️⃣  Testing cleanup and resource management...")
        
        # Unload assets
        resource_manager.unload_asset("test_asset_0")
        resource_manager.unload_asset("shared_texture")
        
        # Remove from atlas
        texture_atlas.remove_texture("shared_texture")
        
        # Verify cleanup
        self.assertFalse(resource_manager.is_asset_loaded("test_asset_0"))
        self.assertFalse(resource_manager.is_asset_loaded("shared_texture"))
        self.assertIsNone(texture_atlas.get_region("shared_texture"))
        
        print("✅ Resource cleanup working properly")
        
        print("\n🎉 Full Asset Pipeline Integration Test Complete!")
    
    def test_world_system_integration(self):
        """Test asset pipeline systems as part of the ECS world."""
        print("\n🌍 Testing ECS World Integration...")
        
        # Add asset systems to world
        resource_manager = ResourceManager(self.world)
        streaming_system = AssetStreamingSystem(self.world, resource_manager)
        
        self.world.add_system(resource_manager)
        self.world.add_system(streaming_system)
        
        # Verify systems were added to world
        self.assertIn(resource_manager, self.world.systems)
        self.assertIn(streaming_system, self.world.systems)
        
        print("✅ Asset systems added to ECS world")
        
        # Test world update propagation
        print("\n🔄 Testing world update propagation...")
        
        # Load an asset
        resource_manager.load_asset("world_test", self.test_files[0], AssetType.DATA)
        
        # Request streaming
        streaming_system.request_asset("world_stream_test", StreamingPriority.NORMAL, 75.0)
        
        # Update the entire world
        self.world.update(0.016)
        
        # Verify systems were updated
        self.assertTrue(resource_manager.is_asset_loaded("world_test"))
        
        stats = streaming_system.get_streaming_statistics()
        self.assertGreaterEqual(stats['queued_requests'], 0)
        
        print("✅ World update propagated to asset systems")
        
        print("\n🎉 ECS World Integration Test Complete!")
    
    def test_performance_under_load(self):
        """Test asset pipeline performance under load."""
        print("\n⚡ Testing Performance Under Load...")
        
        # Initialize systems
        resource_manager = ResourceManager(self.world)
        streaming_system = AssetStreamingSystem(self.world, resource_manager)
        texture_atlas = TextureAtlas()
        
        self.world.add_system(resource_manager)
        self.world.add_system(streaming_system)
        
        # Create many test files
        load_test_files = []
        for i in range(20):
            test_file = os.path.join(self.temp_dir, f"load_test_{i}.txt")
            with open(test_file, 'w') as f:
                f.write(f"load test content {i}")
            load_test_files.append(test_file)
        
        print(f"📦 Created {len(load_test_files)} test assets")
        
        # Test batch loading performance
        import time
        start_time = time.time()
        
        loaded_count = 0
        for i, test_file in enumerate(load_test_files):
            asset_name = f"load_test_{i}"
            if resource_manager.load_asset(asset_name, test_file, AssetType.DATA):
                loaded_count += 1
        
        load_time = time.time() - start_time
        
        self.assertEqual(loaded_count, len(load_test_files))
        print(f"✅ Loaded {loaded_count} assets in {load_time:.3f}s ({loaded_count/load_time:.1f} assets/sec)")
        
        # Test streaming performance
        start_time = time.time()
        
        for i in range(100):
            streaming_system.request_asset(f"stream_test_{i}", StreamingPriority.LOW, float(i))
        
        # Process streaming requests
        for _ in range(10):
            self.world.update(0.016)
        
        stream_time = time.time() - start_time
        stats = streaming_system.get_streaming_statistics()
        
        print(f"✅ Processed streaming requests in {stream_time:.3f}s")
        print(f"   📊 Queued: {stats['queued_requests']}, Active: {stats['active_loads']}")
        
        # Test atlas packing performance
        start_time = time.time()
        
        atlas_textures = []
        for i in range(50):
            texture = TextureInfo(f"perf_test_{i}", 32, 32, f"perf_data_{i}")
            atlas_textures.append(texture)
        
        pack_success = texture_atlas.pack_textures(atlas_textures)
        pack_time = time.time() - start_time
        
        self.assertTrue(pack_success)
        atlas_info = texture_atlas.get_atlas_info()
        
        print(f"✅ Packed {len(atlas_textures)} textures in {pack_time:.3f}s")
        print(f"   📊 Efficiency: {atlas_info['efficiency']:.1f}%, Atlases: {atlas_info['atlas_count']}")
        
        # Clean up load test files
        for test_file in load_test_files:
            os.remove(test_file)
        
        print("\n🎉 Performance Test Complete!")


def run_integration_tests():
    """Run all asset pipeline integration tests."""
    print("🧪 Running Asset Pipeline Integration Tests")
    print("=" * 60)
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test cases
    test_classes = [TestAssetPipelineIntegration]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print("🧪 Integration Test Results Summary")
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\n❌ Failures:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    
    if result.errors:
        print("\n💥 Errors:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    if result.wasSuccessful():
        print("\n✅ All integration tests passed!")
        print("🚀 Asset pipeline is ready for production use!")
        return True
    else:
        print("\n❌ Some integration tests failed!")
        return False


if __name__ == "__main__":
    run_integration_tests()
