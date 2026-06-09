#!/usr/bin/env python3
# Simple test of sprite rendering with the updated system
from direct.showbase.ShowBase import ShowBase
from direct.task.TaskManagerGlobal import taskMgr
from direct.showbase.ShowBaseGlobal import globalClock
from panda3d.core import CardMaker, TransparencyAttrib, Vec4, Filename, loadPrcFileData
import os
import sys

# Add repo root to path for imports (examples/demos/ -> repo root)
script_dir = os.path.dirname(os.path.abspath(__file__))
repo_root = os.path.dirname(os.path.dirname(os.path.dirname(script_dir)))
sys.path.insert(0, repo_root)

from engine.core.system import World
from engine.graphics.components.transform_component import TransformComponent
from engine.graphics.components.sprite_component import SpriteComponent
from engine.graphics.systems.render_system import RenderSystem

# Set window properties before initialization
loadPrcFileData("", "win-size 800 600")
loadPrcFileData("", "window-title Sprite Render Test")
loadPrcFileData("", "notify-level debug")  # Enable debug notifications

class SpriteRenderTest(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        print("Sprite Render Test initialized")
        
        # Set a background color other than the default blue to easily spot if content is rendering
        self.setBackgroundColor(0.2, 0.2, 0.2)  # Dark gray
        
        # Create a world
        self.world = World()
        
        # Add render system
        self.render_system = RenderSystem(self.world, self)
        self.world.add_system(self.render_system)
        
        # Find assets directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        assets_dir = os.path.join(os.path.dirname(script_dir), "assets")
        
        # Use the player sprite
        player_sprite_path = os.path.join(assets_dir, "player.png")
        if not os.path.exists(player_sprite_path):
            print(f"ERROR: No sprite found at {player_sprite_path}")
            print("Running the sprite creation script...")
            try:
                from examples.create_player_sprite import create_simple_player_sprite
                create_simple_player_sprite(player_sprite_path)
                print(f"Created player sprite at {player_sprite_path}")
            except Exception as e:
                print(f"Error creating sprite: {e}")
                return
        
        # Convert to Panda3D path format
        player_sprite_path = Filename.fromOsSpecific(player_sprite_path).getFullpath()
        print(f"Using sprite at: {player_sprite_path}")
        
        # Create a player entity
        player_entity = self.world.create_entity("player")
        
        # Add transform component - use Vec2 for position and scale in 2D
        from panda3d.core import Vec2
        transform = TransformComponent(x=0.0, y=0.0, scale_x=1.0, scale_y=1.0)
        self.world.add_component(player_entity.id, transform)
        
        # Add sprite component
        sprite = SpriteComponent(image_path=player_sprite_path, layer=1)
        self.world.add_component(player_entity.id, sprite)
        
        # Print debug information
        print(f"Created player entity with ID: {player_entity.id}")
        print(f"Added transform component: {transform}")
        print(f"Added sprite component with path: {sprite.image_path}")
        
        # Add update task
        self.taskMgr.add(self.update, "update")
        
        # Add render tree inspection task
        self.taskMgr.doMethodLater(1.0, self.check_render_tree, "check_render_tree")
        
    def update(self, task):
        dt = globalClock.getDt()
        self.world.update(dt)
        return task.cont
    
    def check_render_tree(self, task):
        """Print the entire render tree for debugging"""
        print("\nRender tree (render):")
        self.render.ls()
        print("\nRender tree (render2d):")
        self.render2d.ls()
        print("\nRender tree (aspect2d):")
        self.aspect2d.ls()
        
        # Check for any sprite components
        entities = self.world.get_entities_with_components(SpriteComponent)
        for entity in entities:
            sprite = self.world.get_component(entity.id, SpriteComponent)
            print(f"\nEntity {entity.id} sprite info:")
            print(f"  Image path: {sprite.image_path}")
            print(f"  Panda node: {sprite.panda_node}")
            if sprite.panda_node:
                print(f"  Node visible: {not sprite.panda_node.isHidden()}")
                print(f"  Has texture: {sprite.panda_node.hasTexture()}")
        
        return task.done

if __name__ == '__main__':
    # globalClock is already imported at the top
    app = SpriteRenderTest()
    app.run()
