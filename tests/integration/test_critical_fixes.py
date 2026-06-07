#!/usr/bin/env python3
"""
Test script to verify the critical fixes are working correctly.
This script tests sprite rendering with proper scaling and error handling.
"""

from direct.showbase.ShowBase import ShowBase
from direct.showbase.ShowBaseGlobal import globalClock
from panda3d.core import loadPrcFileData, Vec2
import os
import sys

# Add project root to path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)

from engine.core.system import World
from engine.graphics.components.transform_component import TransformComponent
from engine.graphics.components.sprite_component import SpriteComponent
from engine.graphics.systems.render_system import RenderSystem

# Set window properties
loadPrcFileData("", "win-size 800 600")
loadPrcFileData("", "window-title Critical Fixes Test")

class CriticalFixesTest(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        print("=== Critical Fixes Test Started ===")
        
        # Set background color
        self.setBackgroundColor(0.2, 0.2, 0.2)  # Dark gray
        
        # Create world and render system
        self.world = World()
        self.render_system = RenderSystem(self.world, self)
        self.world.add_system(self.render_system)
        
        # Test 1: Create sprite with proper error handling
        self.test_sprite_creation()
        
        # Test 2: Test component validation
        self.test_component_validation()
        
        # Test 3: Test scaling improvements
        self.test_scaling_improvements()
        
        # Add update task
        self.taskMgr.add(self.update, "update")
        
        print("=== All tests completed ===")
        
    def test_sprite_creation(self):
        """Test sprite creation with error handling"""
        print("\n--- Test 1: Sprite Creation ---")
        
        # Find or create a test sprite
        assets_dir = os.path.join(os.path.dirname(__file__), "assets")
        test_sprite_path = os.path.join(assets_dir, "player.png")
        
        if not os.path.exists(test_sprite_path):
            print("Creating test sprite...")
            if not os.path.exists(assets_dir):
                os.makedirs(assets_dir)
            
            # Create a simple test sprite
            try:
                from examples.create_player_sprite import create_simple_player_sprite
                create_simple_player_sprite(test_sprite_path)
                print(f"Test sprite created at: {test_sprite_path}")
            except Exception as e:
                print(f"Failed to create test sprite: {e}")
                return
        
        # Test valid sprite creation
        try:
            player_entity = self.world.create_entity("test_player")
            transform = TransformComponent(position=Vec2(0, 0), scale=Vec2(1, 1))
            sprite = SpriteComponent(image_path=test_sprite_path, layer=1)
            
            self.world.add_component(player_entity.id, transform)
            self.world.add_component(player_entity.id, sprite)
            print("✓ Valid sprite creation successful")
            
        except Exception as e:
            print(f"✗ Valid sprite creation failed: {e}")
        
        # Test invalid sprite creation (should show proper error)
        try:
            invalid_entity = self.world.create_entity("invalid_sprite")
            invalid_sprite = SpriteComponent(image_path="nonexistent.png", layer=1)
            self.world.add_component(invalid_entity.id, invalid_sprite)
            print("✓ Invalid sprite handled gracefully")
            
        except Exception as e:
            print(f"✗ Invalid sprite not handled properly: {e}")
    
    def test_component_validation(self):
        """Test component validation"""
        print("\n--- Test 2: Component Validation ---")
        
        # Test 1: No image_path or sprite_sheet (should fail)
        try:
            invalid_sprite = SpriteComponent()
            print("✗ Empty SpriteComponent should have failed validation")
        except ValueError as e:
            print(f"✓ Empty SpriteComponent properly rejected: {e}")
        except Exception as e:
            print(f"✗ Unexpected error: {e}")
        
        # Test 2: Invalid layer type (should fail)
        try:
            invalid_sprite = SpriteComponent(image_path="test.png", layer="invalid")
            print("✗ Invalid layer type should have failed validation")
        except TypeError as e:
            print(f"✓ Invalid layer type properly rejected: {e}")
        except Exception as e:
            print(f"✗ Unexpected error: {e}")
        
        # Test 3: Invalid opacity range (should fail)
        try:
            invalid_sprite = SpriteComponent(image_path="test.png", opacity=1.5)
            print("✗ Invalid opacity should have failed validation")
        except ValueError as e:
            print(f"✓ Invalid opacity properly rejected: {e}")
        except Exception as e:
            print(f"✗ Unexpected error: {e}")
    
    def test_scaling_improvements(self):
        """Test the improved scaling system"""
        print("\n--- Test 3: Scaling Improvements ---")
        
        assets_dir = os.path.join(os.path.dirname(__file__), "assets")
        test_sprite_path = os.path.join(assets_dir, "player.png")
        
        if os.path.exists(test_sprite_path):
            # Test different scale values
            test_scales = [
                (Vec2(1, 1), "normal size"),
                (Vec2(0.5, 0.5), "half size"),
                (Vec2(2, 2), "double size"),
            ]
            
            for i, (scale, description) in enumerate(test_scales):
                try:
                    entity = self.world.create_entity(f"scale_test_{i}")
                    transform = TransformComponent(
                        position=Vec2(-1 + i * 1, 0),  # Spread them horizontally
                        scale=scale
                    )
                    sprite = SpriteComponent(image_path=test_sprite_path, layer=1)
                    
                    self.world.add_component(entity.id, transform)
                    self.world.add_component(entity.id, sprite)
                    print(f"✓ Created sprite with {description}: scale={scale}")
                    
                except Exception as e:
                    print(f"✗ Failed to create sprite with {description}: {e}")
        else:
            print("No test sprite available for scaling test")
    
    def update(self, task):
        """Update the world"""
        dt = globalClock.getDt()
        self.world.update(dt)
        return task.cont

if __name__ == '__main__':
    app = CriticalFixesTest()
    app.run()
