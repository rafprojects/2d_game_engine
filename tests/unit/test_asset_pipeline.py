"""
Unit tests for the Asset Pipeline components.

Tests cover ResourceManager, TextureAtlas, and AssetStreamingSystem functionality.
"""

import unittest
import tempfile
import os
from unittest.mock import Mock
import sys

# Add the parent directory to the path so we can import engine modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from engine.core.system import World
from engine.assets.resource_manager import ResourceManager, AssetType, AssetState, AssetInfo
from engine.assets.texture_atlas import TextureAtlas, TextureInfo, TexturePackingStrategy, AtlasRegion
from engine.assets.asset_streaming import AssetStreamingSystem, StreamingPriority, StreamingRequest

class TestResourceManager(unittest.TestCase):
    """Test cases for ResourceManager (path-keyed API)."""

    def setUp(self):
        """Set up test fixtures."""
        self.world = World()
        # ResourceManager needs a ShowBase for its loader; DATA assets are read
        # from disk directly, so a mock base is sufficient here.
        self.resource_manager = ResourceManager(self.world, Mock())

        # Create temporary test files
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test.txt")
        with open(self.test_file, 'w') as f:
            f.write("test content")

    def tearDown(self):
        """Clean up test fixtures."""
        for name in os.listdir(self.temp_dir):
            os.remove(os.path.join(self.temp_dir, name))
        os.rmdir(self.temp_dir)

    def test_load_asset_success(self):
        """Test successful asset loading (keyed by path)."""
        data = self.resource_manager.load_asset(self.test_file)
        self.assertIsNotNone(data)
        self.assertTrue(self.resource_manager.is_loaded(self.test_file))

    def test_load_asset_nonexistent_file(self):
        """Test loading a non-existent file returns None."""
        data = self.resource_manager.load_asset("/nonexistent/file.txt")
        self.assertIsNone(data)
        self.assertFalse(self.resource_manager.is_loaded("/nonexistent/file.txt"))

    def test_get_asset_info(self):
        """Test getting asset information."""
        self.resource_manager.load_asset(self.test_file)

        asset_info = self.resource_manager.get_asset_info(self.test_file)
        self.assertIsNotNone(asset_info)
        self.assertEqual(asset_info.asset_type, AssetType.DATA)
        self.assertEqual(asset_info.path, self.test_file)
        self.assertEqual(asset_info.state, AssetState.LOADED)

    def test_reference_counting(self):
        """Test asset reference counting via load/get/unload."""
        self.resource_manager.load_asset(self.test_file)  # ref -> 1
        info = self.resource_manager.get_asset_info(self.test_file)
        self.assertEqual(info.ref_count, 1)

        self.resource_manager.get_asset(self.test_file)  # ref -> 2
        self.assertEqual(info.ref_count, 2)

        self.resource_manager.unload_asset(self.test_file)  # ref -> 1, still loaded
        self.assertTrue(self.resource_manager.is_loaded(self.test_file))
        self.assertEqual(info.ref_count, 1)

        self.resource_manager.unload_asset(self.test_file)  # ref -> 0, unloaded
        self.assertFalse(self.resource_manager.is_loaded(self.test_file))

    def test_unload_asset(self):
        """Test manual asset unloading once references reach zero."""
        self.resource_manager.load_asset(self.test_file)
        self.assertTrue(self.resource_manager.is_loaded(self.test_file))

        success = self.resource_manager.unload_asset(self.test_file)
        self.assertTrue(success)
        self.assertFalse(self.resource_manager.is_loaded(self.test_file))

    def test_load_multiple_assets(self):
        """Test loading several assets and the load statistics."""
        test_files = [self.test_file]
        for i in range(2):
            path = os.path.join(self.temp_dir, f"test_{i}.txt")
            with open(path, 'w') as f:
                f.write(f"test content {i}")
            test_files.append(path)

        for path in test_files:
            self.assertIsNotNone(self.resource_manager.load_asset(path))
            self.assertTrue(self.resource_manager.is_loaded(path))

        stats = self.resource_manager.get_load_statistics()
        self.assertEqual(stats['assets_loaded'], len(test_files))

    def test_statistics(self):
        """Test memory and load statistics."""
        second_file = os.path.join(self.temp_dir, "second.txt")
        with open(second_file, 'w') as f:
            f.write("more content")

        self.resource_manager.load_asset(self.test_file)
        self.resource_manager.load_asset(second_file)

        memory = self.resource_manager.get_memory_usage()
        self.assertIn('total_registered', memory)
        self.assertIn('total_mb', memory)
        self.assertEqual(memory['total_registered'], 2)

        load_stats = self.resource_manager.get_load_statistics()
        self.assertIn('assets_loaded', load_stats)
        self.assertEqual(load_stats['assets_loaded'], 2)


class TestTextureAtlas(unittest.TestCase):
    """Test cases for TextureAtlas."""

    def setUp(self):
        """Set up test fixtures."""
        self.atlas = TextureAtlas(
            max_width=512,
            max_height=512,
            padding=1,
            strategy=TexturePackingStrategy.BEST_FIT
        )

    def test_atlas_initialization(self):
        """Test atlas initialization."""
        self.assertEqual(self.atlas.max_width, 512)
        self.assertEqual(self.atlas.max_height, 512)
        self.assertEqual(self.atlas.padding, 1)
        self.assertEqual(self.atlas.strategy, TexturePackingStrategy.BEST_FIT)
        self.assertEqual(self.atlas.atlas_count, 0)

    def test_single_texture_packing(self):
        """Test packing a single texture."""
        texture = TextureInfo("test_sprite", 64, 64, "test_data")
        success = self.atlas.add_texture(texture)

        self.assertTrue(success)
        self.assertEqual(self.atlas.atlas_count, 1)

        region = self.atlas.get_region("test_sprite")
        self.assertIsNotNone(region)
        self.assertEqual(region.name, "test_sprite")
        self.assertEqual(region.width, 64)
        self.assertEqual(region.height, 64)

    def test_multiple_texture_packing(self):
        """Test packing multiple textures."""
        textures = [
            TextureInfo("sprite1", 32, 32, "data1"),
            TextureInfo("sprite2", 64, 32, "data2"),
            TextureInfo("sprite3", 32, 64, "data3"),
            TextureInfo("sprite4", 48, 48, "data4"),
        ]

        success = self.atlas.pack_textures(textures)
        self.assertTrue(success)

        # All textures should be packed
        for texture in textures:
            region = self.atlas.get_region(texture.name)
            self.assertIsNotNone(region)
            self.assertEqual(region.width, texture.width)
            self.assertEqual(region.height, texture.height)

    def test_texture_too_large(self):
        """Test handling texture that's too large for atlas."""
        large_texture = TextureInfo("huge_sprite", 600, 600, "huge_data")
        success = self.atlas.add_texture(large_texture)

        # Should fail because texture is larger than atlas
        self.assertFalse(success)
        self.assertIsNone(self.atlas.get_region("huge_sprite"))

    def test_texture_removal(self):
        """Test removing textures from atlas."""
        texture = TextureInfo("removable", 32, 32, "data")
        self.atlas.add_texture(texture)

        self.assertIsNotNone(self.atlas.get_region("removable"))

        success = self.atlas.remove_texture("removable")
        self.assertTrue(success)
        self.assertIsNone(self.atlas.get_region("removable"))

    def test_uv_coordinates(self):
        """Test UV coordinate generation."""
        texture = TextureInfo("uv_test", 64, 64, "data")
        self.atlas.add_texture(texture)

        uv_coords = self.atlas.get_uv_coordinates("uv_test")
        self.assertIsNotNone(uv_coords)
        self.assertEqual(len(uv_coords), 4)  # u1, v1, u2, v2

    def test_atlas_info(self):
        """Test getting atlas information."""
        textures = [
            TextureInfo("info1", 32, 32, "data1"),
            TextureInfo("info2", 32, 32, "data2"),
        ]
        self.atlas.pack_textures(textures)

        info = self.atlas.get_atlas_info()

        self.assertIn('atlas_count', info)
        self.assertIn('total_textures', info)
        self.assertIn('efficiency', info)
        self.assertIn('regions', info)

        self.assertEqual(info['total_textures'], 2)
        self.assertEqual(info['regions'], 2)
        self.assertGreater(info['efficiency'], 0)


class TestAssetStreamingSystem(unittest.TestCase):
    """Test cases for AssetStreamingSystem."""

    def setUp(self):
        """Set up test fixtures."""
        self.world = World()
        self.resource_manager = Mock()
        # Nothing is loaded yet, so streaming requests actually queue.
        self.resource_manager.is_loaded.return_value = False
        self.streaming_system = AssetStreamingSystem(self.world, self.resource_manager)

    def test_streaming_system_initialization(self):
        """Test streaming system initialization."""
        self.assertTrue(self.streaming_system.streaming_enabled)
        self.assertEqual(self.streaming_system.max_concurrent_loads, 3)
        self.assertEqual(self.streaming_system.stream_distance, 200.0)
        self.assertEqual(self.streaming_system.unload_distance, 400.0)

    def test_streaming_configuration(self):
        """Test streaming distance configuration."""
        self.streaming_system.set_streaming_distances(150.0, 300.0)

        self.assertEqual(self.streaming_system.stream_distance, 150.0)
        self.assertEqual(self.streaming_system.unload_distance, 300.0)

    def test_request_stream_queues_asset(self):
        """Test requesting an asset for streaming queues it."""
        self.streaming_system.request_stream(
            "test_asset", StreamingPriority.HIGH, distance=50.0
        )

        stats = self.streaming_system.get_streaming_statistics()
        self.assertGreater(stats['total_queued'], 0)
        self.assertIn("test_asset", self.streaming_system.active_streams)

    def test_streaming_zone_management(self):
        """Test registering and (de)activating a streaming zone."""
        self.streaming_system.register_asset_zone(
            "test_zone", ["zone_asset1", "zone_asset2"]
        )
        self.assertIn("test_zone", self.streaming_system.asset_zones)

        self.streaming_system.activate_zone("test_zone")
        self.assertIn("test_zone", self.streaming_system.active_zones)

        self.streaming_system.deactivate_zone("test_zone")
        self.assertNotIn("test_zone", self.streaming_system.active_zones)

    def test_player_position_update(self):
        """Test updating player position and velocity."""
        self.streaming_system.update_player_position(0, 0)
        self.assertEqual(self.streaming_system.player_position, (0, 0))

        self.streaming_system.update_player_position(100, 50, 10.0, 5.0)
        self.assertEqual(self.streaming_system.player_position, (100, 50))
        self.assertEqual(self.streaming_system.player_velocity, (10.0, 5.0))

    def test_streaming_statistics(self):
        """Test getting streaming statistics."""
        stats = self.streaming_system.get_streaming_statistics()

        required_keys = [
            'streaming_enabled', 'active_streams', 'total_queued',
            'queues', 'memory_pressure', 'streams_completed',
        ]
        for key in required_keys:
            self.assertIn(key, stats)

    def test_priority_queue_ordering(self):
        """Test that requests land in their priority queues."""
        requests = [
            ("low_asset", StreamingPriority.LOW),
            ("critical_asset", StreamingPriority.CRITICAL),
            ("high_asset", StreamingPriority.HIGH),
            ("normal_asset", StreamingPriority.NORMAL),
        ]
        for asset_name, priority in requests:
            self.streaming_system.request_stream(asset_name, priority, distance=100.0)

        total_requests = sum(
            len(queue) for queue in self.streaming_system.streaming_queues.values()
        )
        self.assertEqual(total_requests, len(requests))

    def test_memory_pressure_tracking(self):
        """Test memory pressure derived from the resource manager."""
        self.resource_manager.get_memory_usage.return_value = {
            'utilization_percent': 70.0
        }
        self.streaming_system._update_memory_pressure()

        self.assertAlmostEqual(self.streaming_system.memory_pressure, 0.7)
        # 0.6 < pressure <= 0.8 reduces concurrency to 2.
        self.assertEqual(self.streaming_system.max_concurrent_loads, 2)

    def test_predictive_velocity_tracking(self):
        """Test player velocity tracking that feeds predictive streaming."""
        self.streaming_system.update_player_position(0.0, 0.0, 10.0, 5.0)
        self.assertEqual(self.streaming_system.player_velocity, (10.0, 5.0))


class TestAssetStreamingRequest(unittest.TestCase):
    """Test cases for StreamingRequest data class."""

    def test_streaming_request_creation(self):
        """Test creating streaming requests."""
        request = StreamingRequest(
            asset_path="test_asset.png",
            priority=StreamingPriority.HIGH,
            distance=100.0,
            required_by=1.5,
            callback=None
        )

        self.assertEqual(request.asset_path, "test_asset.png")
        self.assertEqual(request.priority, StreamingPriority.HIGH)
        self.assertEqual(request.distance, 100.0)
        self.assertEqual(request.required_by, 1.5)
        self.assertIsNone(request.callback)

    def test_streaming_request_with_callback(self):
        """Test streaming request with callback function."""
        def test_callback(path, data):
            pass

        request = StreamingRequest(
            asset_path="callback_asset.png",
            priority=StreamingPriority.NORMAL,
            callback=test_callback
        )

        self.assertEqual(request.callback, test_callback)


class TestAssetInfo(unittest.TestCase):
    """Test cases for AssetInfo data class."""

    def test_asset_info_creation(self):
        """Test creating asset info."""
        info = AssetInfo(
            path="/test/path.png",
            asset_type=AssetType.TEXTURE,
            state=AssetState.LOADED,
            size_bytes=1024,
            load_time=0.5
        )

        self.assertEqual(info.path, "/test/path.png")
        self.assertEqual(info.asset_type, AssetType.TEXTURE)
        self.assertEqual(info.state, AssetState.LOADED)
        self.assertEqual(info.size_bytes, 1024)
        self.assertEqual(info.load_time, 0.5)
        self.assertEqual(info.ref_count, 0)
        self.assertEqual(len(info.dependencies), 0)
        self.assertEqual(len(info.metadata), 0)


class TestAtlasRegion(unittest.TestCase):
    """Test cases for AtlasRegion data class."""

    def test_atlas_region_creation(self):
        """Test creating atlas regions."""
        region = AtlasRegion(
            name="test_sprite",
            x=10,
            y=20,
            width=64,
            height=64,
            rotated=False,
            atlas_id="atlas_0"
        )

        self.assertEqual(region.name, "test_sprite")
        self.assertEqual(region.x, 10)
        self.assertEqual(region.y, 20)
        self.assertEqual(region.width, 64)
        self.assertEqual(region.height, 64)
        self.assertFalse(region.rotated)
        self.assertEqual(region.atlas_id, "atlas_0")

    def test_uv_coordinates_property(self):
        """Test UV coordinates property."""
        region = AtlasRegion("test", 0, 0, 64, 64)
        uv_coords = region.uv_coords

        self.assertEqual(len(uv_coords), 4)
        # Note: This is a placeholder implementation
        self.assertEqual(uv_coords, (0.0, 0.0, 1.0, 1.0))


def run_tests():
    """Run all asset pipeline tests."""
    print("🧪 Running Asset Pipeline Unit Tests")
    print("=" * 50)

    # Create test suite
    suite = unittest.TestSuite()

    # Add test cases
    test_classes = [
        TestResourceManager,
        TestTextureAtlas,
        TestAssetStreamingSystem,
        TestAssetStreamingRequest,
        TestAssetInfo,
        TestAtlasRegion,
    ]

    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "=" * 50)
    print("🧪 Test Results Summary")
    print("=" * 50)
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
        print("\n✅ All tests passed!")
        return True
    else:
        print("\n❌ Some tests failed!")
        return False


if __name__ == "__main__":
    run_tests()
