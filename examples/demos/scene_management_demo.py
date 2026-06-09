#!/usr/bin/env python3
"""
Scene Management Demo

This demo showcases the complete scene management system including:
- Multiple scenes with transitions
- Scene persistence (save/load)
- Dynamic scene loading
- Scene state management
- Visual transition effects

Controls:
- 1-3: Switch between scenes
- S: Save current scene
- L: Load saved scene
- T: Change transition type
- F: Toggle fade transition
- ESC: Exit demo

Scenes Demonstrated:
- Menu Scene: Main menu with options
- Game Scene: Simple gameplay area
- Settings Scene: Configuration options

Features:
- Smooth scene transitions
- Scene state persistence
- Asset preloading
- Multi-scene coordination
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from direct.showbase.ShowBase import ShowBase
from direct.showbase.ShowBaseGlobal import globalClock
from panda3d.core import Vec2, Vec4

from engine.core.system import World
from engine.graphics.components.transform_component import TransformComponent
from engine.graphics.components.sprite_component import SpriteComponent
from engine.graphics.systems.render_system import RenderSystem
from engine.input.components.input_component import InputComponent
from engine.input.systems.input_system import InputSystem
from engine.input.input_bindings import InputBinding

# Scene management imports
from engine.scene.components.scene_component import SceneComponent, SceneState
from engine.scene.components.scene_transition_component import SceneTransitionComponent, TransitionType
from engine.scene.components.scene_persistence_component import ScenePersistenceComponent
from engine.scene.systems.scene_manager import SceneManager
from engine.scene.systems.scene_transition_system import SceneTransitionSystem
from engine.scene.systems.scene_persistence_system import ScenePersistenceSystem

class SceneManagementDemo(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        print("🎬 Scene Management Demo")
        print("=" * 50)
        print("Controls:")
        print("  1: Switch to Menu Scene")
        print("  2: Switch to Game Scene") 
        print("  3: Switch to Settings Scene")
        print("  S: Save current scene state")
        print("  L: Load saved scene state")
        print("  T: Change transition type")
        print("  F: Quick fade transition")
        print("  ESC: Exit demo")
        print("=" * 50)

        self.world = World()
        
        # Initialize core systems
        self.render_system = RenderSystem(self.world, self)
        self.world.add_system(self.render_system)
        
        self.input_system = InputSystem(self.world, self)
        self.world.add_system(self.input_system)
        
        # Initialize scene management systems
        self.scene_manager = SceneManager(self.world)
        self.world.add_system(self.scene_manager)
        
        self.transition_system = SceneTransitionSystem(self.world, self)
        self.world.add_system(self.transition_system)
        
        self.persistence_system = ScenePersistenceSystem(self.world)
        self.world.add_system(self.persistence_system)
        
        # Demo state
        self.current_transition_type = 0
        self.transition_types = [
            TransitionType.FADE,
            TransitionType.SLIDE_LEFT,
            TransitionType.SLIDE_RIGHT,
            TransitionType.SLIDE_UP,
            TransitionType.SLIDE_DOWN
        ]
        
        # Create demo scenes
        self.create_demo_scenes()
        
        # Create demo controller
        self.create_demo_controller()
        
        # Start with menu scene
        self.scene_manager.load_scene("menu_scene", activate=True)
        
        # Game loop
        self.taskMgr.add(self.update_demo, "update_demo")
    
    def create_demo_scenes(self):
        """Create demonstration scenes."""
        # Register scene templates
        self.scene_manager.register_scene_template("menu", self.create_menu_scene)
        self.scene_manager.register_scene_template("game", self.create_game_scene)
        self.scene_manager.register_scene_template("settings", self.create_settings_scene)
        
        # Create scenes
        self.menu_scene_id = self.scene_manager.create_scene(
            "menu", 
            scene_id="menu_scene",
            is_persistent=True,
            priority=1
        )
        
        self.game_scene_id = self.scene_manager.create_scene(
            "game",
            scene_id="game_scene", 
            is_persistent=False,
            priority=1
        )
        
        self.settings_scene_id = self.scene_manager.create_scene(
            "settings",
            scene_id="settings_scene",
            is_overlay=True,
            priority=2
        )
        
        # Add transitions to scenes
        self.add_transition_components()
        
        # Add persistence to scenes
        self.add_persistence_components()
    
    def create_menu_scene(self, scene_comp: SceneComponent, world: World):
        """Create menu scene content."""
        print("🏠 Creating menu scene...")
        
        # Menu background
        bg_entity = world.create_entity("menu_background")
        world.add_component(bg_entity.id, TransformComponent(
            position=Vec2(0, 0),
            scale=Vec2(2, 1.5)
        ))
        world.add_component(bg_entity.id, SpriteComponent(
            image_path="assets/player.png",  # Placeholder
            color=Vec4(0.2, 0.3, 0.8, 1.0)
        ))
        scene_comp.add_entity(bg_entity.id, "background")
        
        # Menu title
        title_entity = world.create_entity("menu_title")
        world.add_component(title_entity.id, TransformComponent(
            position=Vec2(0, 200),
            scale=Vec2(1.5, 1.5)
        ))
        world.add_component(title_entity.id, SpriteComponent(
            image_path="assets/player.png",  # Placeholder
            color=Vec4(1.0, 1.0, 1.0, 1.0)
        ))
        scene_comp.add_entity(title_entity.id, "title")
        
        # Store some scene-specific data
        scene_comp.scene_data["scene_type"] = "menu"
        scene_comp.scene_data["creation_time"] = globalClock.getFrameTime()
        
    def create_game_scene(self, scene_comp: SceneComponent, world: World):
        """Create game scene content."""
        print("🎮 Creating game scene...")
        
        # Game background
        bg_entity = world.create_entity("game_background")
        world.add_component(bg_entity.id, TransformComponent(
            position=Vec2(0, 0),
            scale=Vec2(2, 1.5)
        ))
        world.add_component(bg_entity.id, SpriteComponent(
            image_path="assets/player.png",  # Placeholder
            color=Vec4(0.2, 0.8, 0.3, 1.0)
        ))
        scene_comp.add_entity(bg_entity.id, "background")
        
        # Player in game scene
        player_entity = world.create_entity("game_player")
        world.add_component(player_entity.id, TransformComponent(
            position=Vec2(0, 0),
            scale=Vec2(1, 1)
        ))
        world.add_component(player_entity.id, SpriteComponent(
            image_path="assets/player.png",
            color=Vec4(1.0, 0.5, 0.5, 1.0)
        ))
        scene_comp.add_entity(player_entity.id, "player")
        
        # Game objects
        for i in range(3):
            obj_entity = world.create_entity(f"game_object_{i}")
            world.add_component(obj_entity.id, TransformComponent(
                position=Vec2(200 * (i - 1), 100),
                scale=Vec2(0.5, 0.5)
            ))
            world.add_component(obj_entity.id, SpriteComponent(
                image_path="assets/player.png",  # Placeholder
                color=Vec4(0.8, 0.8, 0.2, 1.0)
            ))
            scene_comp.add_entity(obj_entity.id, f"object_{i}")
        
        # Game scene data
        scene_comp.scene_data["scene_type"] = "game"
        scene_comp.scene_data["player_score"] = 0
        scene_comp.scene_data["level"] = 1
        
    def create_settings_scene(self, scene_comp: SceneComponent, world: World):
        """Create settings scene content."""
        print("⚙️ Creating settings scene...")
        
        # Settings background (semi-transparent overlay)
        bg_entity = world.create_entity("settings_background")
        world.add_component(bg_entity.id, TransformComponent(
            position=Vec2(0, 0),
            scale=Vec2(1.5, 1.2)
        ))
        world.add_component(bg_entity.id, SpriteComponent(
            image_path="assets/player.png",  # Placeholder
            color=Vec4(0.1, 0.1, 0.1, 0.8)
        ))
        scene_comp.add_entity(bg_entity.id, "background")
        
        # Settings panel
        panel_entity = world.create_entity("settings_panel")
        world.add_component(panel_entity.id, TransformComponent(
            position=Vec2(0, 0),
            scale=Vec2(1, 0.8)
        ))
        world.add_component(panel_entity.id, SpriteComponent(
            image_path="assets/player.png",  # Placeholder
            color=Vec4(0.4, 0.4, 0.4, 1.0)
        ))
        scene_comp.add_entity(panel_entity.id, "panel")
        
        # Settings options
        for i, option in enumerate(["Audio", "Graphics", "Controls"]):
            option_entity = world.create_entity(f"setting_{option.lower()}")
            world.add_component(option_entity.id, TransformComponent(
                position=Vec2(0, 100 - i * 60),
                scale=Vec2(0.8, 0.4)
            ))
            world.add_component(option_entity.id, SpriteComponent(
                image_path="assets/player.png",  # Placeholder
                color=Vec4(0.6, 0.6, 0.6, 1.0)
            ))
            scene_comp.add_entity(option_entity.id, f"option_{option.lower()}")
        
        # Settings scene data
        scene_comp.scene_data["scene_type"] = "settings"
        scene_comp.scene_data["audio_volume"] = 0.8
        scene_comp.scene_data["graphics_quality"] = "medium"
    
    def add_transition_components(self):
        """Add transition components to scenes."""
        scenes = [
            (self.menu_scene_id, "menu_scene"),
            (self.game_scene_id, "game_scene"), 
            (self.settings_scene_id, "settings_scene")
        ]
        
        for scene_id, scene_name in scenes:
            if scene_id:
                entity_id = self.scene_manager.active_scenes[scene_id]
                
                # Create transition component
                transition_comp = SceneTransitionComponent(
                    transition_type=TransitionType.FADE,
                    duration=1.0,
                    easing="ease_in_out"
                )
                
                # Set callbacks
                transition_comp.on_transition_start = self.on_transition_start
                transition_comp.on_transition_complete = self.on_transition_complete
                
                self.world.add_component(entity_id, transition_comp)
                print(f"  ✅ Added transition to {scene_name}")
    
    def add_persistence_components(self):
        """Add persistence components to scenes."""
        scenes = [
            (self.menu_scene_id, "menu_scene"),
            (self.game_scene_id, "game_scene"),
            (self.settings_scene_id, "settings_scene")
        ]
        
        for scene_id, scene_name in scenes:
            if scene_id:
                entity_id = self.scene_manager.active_scenes[scene_id]
                
                # Create persistence component
                persistence_comp = ScenePersistenceComponent(
                    auto_save=True,
                    auto_save_interval=30.0,
                    save_format="json",
                    max_save_slots=5
                )
                
                # Set save directory for this scene
                persistence_comp.save_filename_prefix = f"scene_{scene_name}"
                
                # Set callbacks
                persistence_comp.on_save_complete = self.on_save_complete
                persistence_comp.on_load_complete = self.on_load_complete
                
                # Register for auto-save
                self.world.add_component(entity_id, persistence_comp)
                self.persistence_system.register_auto_save(scene_id)
                
                print(f"  ✅ Added persistence to {scene_name}")
    
    def create_demo_controller(self):
        """Create demo input controller."""
        controller_entity = self.world.create_entity("demo_controller")
        
        input_bindings = {
            "scene_menu": [InputBinding(input_type="key", event_name="1")],
            "scene_game": [InputBinding(input_type="key", event_name="2")],
            "scene_settings": [InputBinding(input_type="key", event_name="3")],
            "save_scene": [InputBinding(input_type="key", event_name="s")],
            "load_scene": [InputBinding(input_type="key", event_name="l")],
            "change_transition": [InputBinding(input_type="key", event_name="t")],
            "quick_fade": [InputBinding(input_type="key", event_name="f")],
            "exit_demo": [InputBinding(input_type="key", event_name="escape")]
        }
        
        input_comp = InputComponent(action_bindings=input_bindings)
        self.world.add_component(controller_entity.id, input_comp)
        
        self.controller_entity = controller_entity
    
    def update_demo(self, task):
        """Main demo update loop."""
        dt = globalClock.getDt()
        self.world.update(dt)
        
        # Handle demo input
        self.handle_demo_input()
        
        # Display current scene info
        self.display_scene_info()
        
        return task.cont
    
    def handle_demo_input(self):
        """Handle demo-specific input."""
        input_comp = self.world.get_component(self.controller_entity.id, InputComponent)
        if not input_comp:
            return
        
        # Scene switching
        if input_comp.action_just_pressed.get("scene_menu"):
            self.switch_to_scene("menu_scene", "Menu Scene")
        
        if input_comp.action_just_pressed.get("scene_game"):
            self.switch_to_scene("game_scene", "Game Scene")
        
        if input_comp.action_just_pressed.get("scene_settings"):
            self.switch_to_scene("settings_scene", "Settings Scene")
        
        # Save/Load
        if input_comp.action_just_pressed.get("save_scene"):
            self.save_current_scene()
        
        if input_comp.action_just_pressed.get("load_scene"):
            self.load_current_scene()
        
        # Transition controls
        if input_comp.action_just_pressed.get("change_transition"):
            self.change_transition_type()
        
        if input_comp.action_just_pressed.get("quick_fade"):
            self.quick_fade_transition()
        
        # Exit
        if input_comp.action_just_pressed.get("exit_demo"):
            self.userExit()
    
    def switch_to_scene(self, scene_id: str, scene_name: str):
        """Switch to a specific scene with transition."""
        print(f"🔄 Switching to {scene_name}...")
        
        # Get current scene for transition out
        current_scene_id = self.scene_manager.get_current_scene_id()
        if current_scene_id and current_scene_id != scene_id:
            # Start transition out of current scene
            current_entity_id = self.scene_manager.active_scenes[current_scene_id]
            self.transition_system.start_transition(current_scene_id, current_entity_id, "out")
        
        # Load and activate new scene
        self.scene_manager.load_scene(scene_id, activate=True)
        
        # Start transition into new scene
        new_entity_id = self.scene_manager.active_scenes[scene_id]
        self.transition_system.start_transition(scene_id, new_entity_id, "in")
    
    def save_current_scene(self):
        """Save current scene state."""
        current_scene_id = self.scene_manager.get_current_scene_id()
        if current_scene_id:
            success = self.persistence_system.save_scene(current_scene_id, slot=0)
            if success:
                print(f"💾 Saved scene: {current_scene_id}")
            else:
                print(f"❌ Failed to save scene: {current_scene_id}")
        else:
            print("❌ No active scene to save")
    
    def load_current_scene(self):
        """Load current scene state."""
        current_scene_id = self.scene_manager.get_current_scene_id()
        if current_scene_id:
            success = self.persistence_system.load_scene(current_scene_id, slot=0)
            if success:
                print(f"📂 Loaded scene: {current_scene_id}")
            else:
                print(f"❌ Failed to load scene: {current_scene_id}")
        else:
            print("❌ No active scene to load")
    
    def change_transition_type(self):
        """Change the transition type for scene changes."""
        self.current_transition_type = (self.current_transition_type + 1) % len(self.transition_types)
        new_type = self.transition_types[self.current_transition_type]
        
        # Update all scene transition components
        for scene_id in self.scene_manager.active_scenes.keys():
            entity_id = self.scene_manager.active_scenes[scene_id]
            transition_comp = self.world.get_component(entity_id, SceneTransitionComponent)
            if transition_comp:
                transition_comp.transition_type = new_type
        
        print(f"🎬 Changed transition type to: {new_type.value}")
    
    def quick_fade_transition(self):
        """Perform a quick fade transition on current scene."""
        current_scene_id = self.scene_manager.get_current_scene_id()
        if current_scene_id:
            entity_id = self.scene_manager.active_scenes[current_scene_id]
            transition_comp = self.world.get_component(entity_id, SceneTransitionComponent)
            
            if transition_comp:
                # Quick fade out and in
                transition_comp.transition_type = TransitionType.FADE
                transition_comp.duration = 0.5
                self.transition_system.start_transition(current_scene_id, entity_id, "out")
                print("✨ Quick fade transition!")
    
    def display_scene_info(self):
        """Display current scene information."""
        current_scene_id = self.scene_manager.get_current_scene_id()
        if current_scene_id:
            scene_comp = self.scene_manager.get_scene_component(current_scene_id)
            if scene_comp:
                # Update title bar with scene info
                scene_info = f"Current: {scene_comp.scene_name} | State: {scene_comp.state.value}"
                if hasattr(self, 'win') and self.win:
                    props = self.win.getProperties()
                    props.setTitle(f"Scene Demo - {scene_info}")
                    self.win.requestProperties(props)
    
    def on_transition_start(self, transition_comp, direction):
        """Callback for transition start."""
        print(f"🎬 Transition {direction} started")
    
    def on_transition_complete(self, transition_comp, direction):
        """Callback for transition complete."""
        print(f"✅ Transition {direction} completed")
    
    def on_save_complete(self, scene_id: str, slot: int, filepath: str):
        """Callback for save complete."""
        print(f"💾 Save completed: {scene_id} -> {os.path.basename(filepath)}")
    
    def on_load_complete(self, scene_id: str, slot: int, filepath: str):
        """Callback for load complete."""
        print(f"📂 Load completed: {scene_id} <- {os.path.basename(filepath)}")

if __name__ == '__main__':
    print("🎬 Starting Scene Management Demo...")
    print("This demo showcases multi-scene support with transitions and persistence.")
    print("\\nNote: Demo uses placeholder assets")
    print("\\n" + "="*60)
    
    app = SceneManagementDemo()
    app.run()
