#!/usr/bin/env python3
"""
Final test of the sprite animation system to verify all critical fixes work.
"""
from direct.showbase.ShowBase import ShowBase
from direct.showbase.ShowBaseGlobal import globalClock
from panda3d.core import Vec2, Filename, loadPrcFileData
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engine.core.system import World
from engine.core.components.transform_component import TransformComponent
from engine.graphics.components.sprite_component import SpriteComponent
from engine.graphics.systems.render_system import RenderSystem
from engine.graphics.sprite_sheet import SpriteSheet

# Set window properties
loadPrcFileData("", "win-size 800 600")
loadPrcFileData("", "window-title Final Implementation Test")

class FinalTest(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        print("=== FINAL SPRITE ANIMATION SYSTEM TEST ===")
        
        # Set background for visibility
        self.setBackgroundColor(0.2, 0.2, 0.2)
        
        # Create world and systems
        self.world = World()
        self.render_system = RenderSystem(self.world, self)
        self.world.add_system(self.render_system)
        
        # Test 1: Static Sprite
        print("\n1. Testing Static Sprite...")
        self.test_static_sprite()
        
        # Test 2: Animated Sprite (if sprite sheet exists)
        sprite_sheet_path = os.path.join("assets", "player_sheet.png")
        if os.path.exists(sprite_sheet_path):
            print("\n2. Testing Animated Sprite...")
            self.test_animated_sprite(sprite_sheet_path)
        else:
            print("\n2. Skipping animated sprite test - no sprite sheet found")
        
        # Test 3: Component Validation
        print("\n3. Testing Component Validation...")
        self.test_component_validation()
        
        # Add update task
        self.taskMgr.add(self.update, "update")
        
        print("\n=== TEST SETUP COMPLETE ===")
        print("Check the window for visual confirmation of sprites")
        print("Console will show validation and error handling tests")
    
    def test_static_sprite(self):
        """Test 1: Static sprite rendering with fixed scaling"""
        player_sprite_path = os.path.join("assets", "player.png")
        
        if not os.path.exists(player_sprite_path):
            print("❌ Static sprite test failed - player.png not found")
            return
            
        # Create static sprite entity
        entity = self.world.create_entity("test_static")
        
        # Use scale=1.0 which should now produce a visible sprite
        transform = TransformComponent(position=Vec2(-200, 0), scale=Vec2(1, 1))
        sprite = SpriteComponent(image_path=player_sprite_path, layer=1)
        
        self.world.add_component(entity.id, transform)
        self.world.add_component(entity.id, sprite)
        
        print("✅ Static sprite test setup complete")
    
    def test_animated_sprite(self, sprite_sheet_path):
        """Test 2: Animated sprite with sprite sheet"""
        try:
            # Load sprite sheet
            texture = self.loader.loadTexture(sprite_sheet_path)
            if not texture:
                print("❌ Failed to load sprite sheet texture")
                return
                
            sprite_sheet = SpriteSheet(texture)
            
            # Create animations
            sprite_sheet.create_grid_animation("idle", rows=4, cols=4, 
                                             row_start=0, col_start=0, 
                                             frame_count=4, frame_duration=0.2)
            
            # Create animated sprite entity
            entity = self.world.create_entity("test_animated")
            
            transform = TransformComponent(position=Vec2(200, 0), scale=Vec2(1, 1))
            sprite = SpriteComponent(image_path=sprite_sheet_path, sprite_sheet=sprite_sheet, layer=1)
            
            # Start animation
            success = sprite.play_animation("idle")
            if success:
                print("✅ Animation started successfully")
            else:
                print("❌ Failed to start animation")
            
            self.world.add_component(entity.id, transform)
            self.world.add_component(entity.id, sprite)
            
            print("✅ Animated sprite test setup complete")
            
        except Exception as e:
            print(f"❌ Animated sprite test failed: {e}")
    
    def test_component_validation(self):
        """Test 3: Component validation and error handling"""
        print("Testing component validation...")
        
        # Test 1: Invalid SpriteComponent (no image_path or sprite_sheet)
        try:
            invalid_sprite = SpriteComponent()
            print("❌ Validation test failed - should have thrown error")
        except ValueError as e:
            print(f"✅ Validation test passed: {e}")
        
        # Test 2: Invalid layer type
        try:
            invalid_sprite = SpriteComponent(image_path="test.png", layer="invalid")
            print("❌ Layer validation test failed - should have thrown error")
        except TypeError as e:
            print(f"✅ Layer validation test passed: {e}")
        
        # Test 3: Invalid opacity range
        try:
            invalid_sprite = SpriteComponent(image_path="test.png", opacity=2.0)
            print("❌ Opacity validation test failed - should have thrown error")
        except ValueError as e:
            print(f"✅ Opacity validation test passed: {e}")
        
        # Test 4: Animation error handling
        sprite = SpriteComponent(image_path="assets/player.png")
        success = sprite.play_animation("nonexistent")
        if not success:
            print("✅ Animation error handling test passed")
        else:
            print("❌ Animation error handling test failed")
    
    def update(self, task):
        """Update loop"""
        dt = globalClock.getDt()
        self.world.update(dt)
        return task.cont

if __name__ == '__main__':
    test = FinalTest()
    test.run()
