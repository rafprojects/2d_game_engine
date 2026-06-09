#!/usr/bin/env python3
"""
Scene Management Integration Tutorial

Step-by-step tutorial showing how to integrate scene management into your game.
This tutorial builds a simple multi-scene example with transitions and persistence.

Learning Objectives:
- Set up the scene management system
- Create multiple scenes with content
- Implement scene transitions
- Add scene persistence (save/load)
- Handle scene lifecycle events
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

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

# Step 1: Import Scene Management Components
from engine.scene.components.scene_component import SceneComponent, SceneState
from engine.scene.components.scene_transition_component import SceneTransitionComponent, TransitionType
from engine.scene.components.scene_persistence_component import ScenePersistenceComponent
from engine.scene.systems.scene_manager import SceneManager
from engine.scene.systems.scene_transition_system import SceneTransitionSystem
from engine.scene.systems.scene_persistence_system import ScenePersistenceSystem

class SceneTutorial(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        print("🎓 Scene Management Tutorial")
        print("=" * 50)
        
        print("Step 1: Setting up the scene management system...")
        self.setup_scene_systems()
        
        print("Step 2: Creating multiple scenes...")
        self.create_scenes()
        
        print("Step 3: Setting up scene transitions...")
        self.setup_transitions()
        
        print("Step 4: Adding scene persistence...")
        self.setup_persistence()
        
        print("Step 5: Creating scene controls...")
        self.setup_controls()
        
        print("\\n🎮 TUTORIAL CONTROLS:")
        print("  1: Switch to Main Menu")
        print("  2: Switch to Game Level")
        print("  3: Switch to Pause Menu")
        print("  S: Save current scene")
        print("  L: Load saved scene")
        print("  T: Test fade transition")
        print("=" * 50)
        
        # Start with main menu
        self.scene_manager.load_scene("main_menu", activate=True)
        
        # Tutorial update loop
        self.taskMgr.add(self.update_tutorial, "update_tutorial")
    
    def setup_scene_systems(self):
        """Step 1: Initialize the scene management systems"""
        print("  📋 Creating world and core systems...")
        self.world = World()
        
        # Core systems
        self.render_system = RenderSystem(self.world, self)
        self.world.add_system(self.render_system)
        
        self.input_system = InputSystem(self.world, self)
        self.world.add_system(self.input_system)
        
        print("  🎬 Creating scene management systems...")
        # Scene management systems
        self.scene_manager = SceneManager(self.world)
        self.world.add_system(self.scene_manager)
        
        self.transition_system = SceneTransitionSystem(self.world, self)
        self.world.add_system(self.transition_system)
        
        self.persistence_system = ScenePersistenceSystem(self.world)
        self.world.add_system(self.persistence_system)
        
        print("  ✅ Scene systems initialized")
    
    def create_scenes(self):
        """Step 2: Create multiple scenes with content"""
        print("  🏠 Creating Main Menu scene...")
        
        # Register scene creation functions
        self.scene_manager.register_scene_template("main_menu", self.create_main_menu_scene)
        self.scene_manager.register_scene_template("game_level", self.create_game_level_scene)
        self.scene_manager.register_scene_template("pause_menu", self.create_pause_menu_scene)
        
        # Create scene instances
        self.main_menu_id = self.scene_manager.create_scene(
            scene_name="main_menu",
            scene_id="main_menu",
            is_persistent=True,  # Keep menu in memory
            priority=1
        )
        
        self.game_level_id = self.scene_manager.create_scene(
            scene_name="game_level", 
            scene_id="game_level",
            is_persistent=False,  # Can be unloaded
            priority=1
        )
        
        self.pause_menu_id = self.scene_manager.create_scene(
            scene_name="pause_menu",
            scene_id="pause_menu",
            is_overlay=True,  # Renders over other scenes
            priority=2
        )
        
        print("  ✅ All scenes created")
    
    def create_main_menu_scene(self, scene_comp: SceneComponent, world: World):
        """Create main menu scene content"""
        print("    🏠 Building main menu...")
        
        # Menu background
        bg_entity = world.create_entity("menu_bg")
        world.add_component(bg_entity.id, TransformComponent(
            position=Vec2(0, 0),
            scale=Vec2(3, 2)
        ))
        world.add_component(bg_entity.id, SpriteComponent(
            image_path="assets/player.png",  # Using available asset
            color=Vec4(0.1, 0.2, 0.4, 1.0)  # Dark blue background
        ))
        scene_comp.add_entity(bg_entity.id, "background")
        
        # Menu title
        title_entity = world.create_entity("menu_title")
        world.add_component(title_entity.id, TransformComponent(
            position=Vec2(0, 150),
            scale=Vec2(1.5, 1.5)
        ))
        world.add_component(title_entity.id, SpriteComponent(
            image_path="assets/player.png",
            color=Vec4(1.0, 1.0, 1.0, 1.0)  # White title
        ))
        scene_comp.add_entity(title_entity.id, "title")
        
        # Menu buttons (visual representation)
        button_names = ["Start Game", "Settings", "Exit"]
        for i, button_name in enumerate(button_names):
            button_entity = world.create_entity(f"button_{button_name.lower().replace(' ', '_')}")
            world.add_component(button_entity.id, TransformComponent(
                position=Vec2(0, 50 - i * 60),
                scale=Vec2(1.2, 0.4)
            ))
            world.add_component(button_entity.id, SpriteComponent(
                image_path="assets/player.png",
                color=Vec4(0.3, 0.3, 0.3, 1.0)  # Gray buttons
            ))
            scene_comp.add_entity(button_entity.id, f"button_{i}")
        
        # Store menu-specific data
        scene_comp.scene_data["scene_type"] = "main_menu"
        scene_comp.scene_data["selected_option"] = 0
        
        print("    ✅ Main menu built")
    
    def create_game_level_scene(self, scene_comp: SceneComponent, world: World):
        """Create game level scene content"""
        print("    🎮 Building game level...")
        
        # Game background
        bg_entity = world.create_entity("game_bg")
        world.add_component(bg_entity.id, TransformComponent(
            position=Vec2(0, 0),
            scale=Vec2(3, 2)
        ))
        world.add_component(bg_entity.id, SpriteComponent(
            image_path="assets/player.png",
            color=Vec4(0.2, 0.6, 0.2, 1.0)  # Green game background
        ))
        scene_comp.add_entity(bg_entity.id, "background")
        
        # Player character
        player_entity = world.create_entity("player")
        world.add_component(player_entity.id, TransformComponent(
            position=Vec2(-200, 0),
            scale=Vec2(1, 1)
        ))
        world.add_component(player_entity.id, SpriteComponent(
            image_path="assets/player.png",
            color=Vec4(1.0, 0.8, 0.8, 1.0)  # Light pink player
        ))
        scene_comp.add_entity(player_entity.id, "player")
        
        # Game objects
        for i in range(4):
            obj_entity = world.create_entity(f"object_{i}")
            world.add_component(obj_entity.id, TransformComponent(
                position=Vec2(100 + i * 80, 50 - i * 25),
                scale=Vec2(0.6, 0.6)
            ))
            world.add_component(obj_entity.id, SpriteComponent(
                image_path="assets/player.png",
                color=Vec4(0.9, 0.9, 0.2, 1.0)  # Yellow objects
            ))
            scene_comp.add_entity(obj_entity.id, f"object_{i}")
        
        # HUD elements
        hud_entity = world.create_entity("hud")
        world.add_component(hud_entity.id, TransformComponent(
            position=Vec2(-300, 200),
            scale=Vec2(0.8, 0.3)
        ))
        world.add_component(hud_entity.id, SpriteComponent(
            image_path="assets/player.png",
            color=Vec4(0.1, 0.1, 0.1, 0.8)  # Semi-transparent HUD
        ))
        scene_comp.add_entity(hud_entity.id, "hud")
        
        # Store game-specific data
        scene_comp.scene_data["scene_type"] = "game_level"
        scene_comp.scene_data["player_score"] = 0
        scene_comp.scene_data["level_number"] = 1
        scene_comp.scene_data["game_time"] = 0.0
        
        print("    ✅ Game level built")
    
    def create_pause_menu_scene(self, scene_comp: SceneComponent, world: World):
        """Create pause menu overlay scene"""
        print("    ⏸️ Building pause menu...")
        
        # Semi-transparent overlay background
        overlay_entity = world.create_entity("pause_overlay")
        world.add_component(overlay_entity.id, TransformComponent(
            position=Vec2(0, 0),
            scale=Vec2(3, 2)
        ))
        world.add_component(overlay_entity.id, SpriteComponent(
            image_path="assets/player.png",
            color=Vec4(0.0, 0.0, 0.0, 0.7)  # Semi-transparent black overlay
        ))
        scene_comp.add_entity(overlay_entity.id, "overlay")
        
        # Pause menu panel
        panel_entity = world.create_entity("pause_panel")
        world.add_component(panel_entity.id, TransformComponent(
            position=Vec2(0, 0),
            scale=Vec2(1.5, 1.2)
        ))
        world.add_component(panel_entity.id, SpriteComponent(
            image_path="assets/player.png",
            color=Vec4(0.2, 0.2, 0.2, 1.0)  # Gray panel
        ))
        scene_comp.add_entity(panel_entity.id, "panel")
        
        # Pause menu options
        option_names = ["Resume", "Settings", "Main Menu"]
        for i, option_name in enumerate(option_names):
            option_entity = world.create_entity(f"pause_option_{option_name.lower().replace(' ', '_')}")
            world.add_component(option_entity.id, TransformComponent(
                position=Vec2(0, 40 - i * 40),
                scale=Vec2(1.0, 0.3)
            ))
            world.add_component(option_entity.id, SpriteComponent(
                image_path="assets/player.png",
                color=Vec4(0.4, 0.4, 0.4, 1.0)  # Lighter gray options
            ))
            scene_comp.add_entity(option_entity.id, f"option_{i}")
        
        # Store pause menu data
        scene_comp.scene_data["scene_type"] = "pause_menu"
        scene_comp.scene_data["selected_option"] = 0
        
        print("    ✅ Pause menu built")
    
    def setup_transitions(self):
        """Step 3: Set up scene transitions"""
        print("  🎬 Setting up scene transitions...")
        
        # Add transition components to each scene
        scenes_info = [
            (self.main_menu_id, "main_menu", TransitionType.FADE),
            (self.game_level_id, "game_level", TransitionType.SLIDE_LEFT),
            (self.pause_menu_id, "pause_menu", TransitionType.FADE)
        ]
        
        for scene_id, scene_name, transition_type in scenes_info:
            if scene_id:
                entity_id = self.scene_manager.active_scenes[scene_id]
                
                # Create transition component
                transition_comp = SceneTransitionComponent(
                    transition_type=transition_type,
                    duration=1.0,
                    easing="ease_in_out"
                )
                
                # Customize transition for each scene
                if transition_type == TransitionType.FADE:
                    transition_comp.set_fade_color(Vec4(0, 0, 0, 1))
                elif transition_type == TransitionType.SLIDE_LEFT:
                    transition_comp.set_slide_distance(Vec2(800, 600))
                
                # Set transition callbacks
                transition_comp.on_transition_start = lambda comp, direction, name=scene_name: self.on_transition_start(comp, direction, name)
                transition_comp.on_transition_complete = lambda comp, direction, name=scene_name: self.on_transition_complete(comp, direction, name)
                
                self.world.add_component(entity_id, transition_comp)
                print(f"    ✅ Added {transition_type.value} transition to {scene_name}")
    
    def setup_persistence(self):
        """Step 4: Set up scene persistence (save/load)"""
        print("  💾 Setting up scene persistence...")
        
        # Add persistence components to scenes that should be saved
        persistable_scenes = [
            (self.main_menu_id, "main_menu"),
            (self.game_level_id, "game_level")
            # Skip pause menu as it's just an overlay
        ]
        
        for scene_id, scene_name in persistable_scenes:
            if scene_id:
                entity_id = self.scene_manager.active_scenes[scene_id]
                
                # Create persistence component
                persistence_comp = ScenePersistenceComponent(
                    auto_save=False,  # Manual save for tutorial
                    save_format="json",
                    max_save_slots=3
                )
                
                # Configure save settings
                persistence_comp.save_filename_prefix = f"tutorial_{scene_name}"
                persistence_comp.save_directory = "saves/tutorial"
                
                # Set persistence callbacks
                persistence_comp.on_save_complete = lambda scene_id, slot, path, name=scene_name: self.on_save_complete(scene_id, slot, path, name)
                persistence_comp.on_load_complete = lambda scene_id, slot, path, name=scene_name: self.on_load_complete(scene_id, slot, path, name)
                
                # Add some persistent data
                persistence_comp.add_persistent_data("tutorial_step", 4)
                persistence_comp.add_persistent_data("creation_time", globalClock.getFrameTime())
                
                self.world.add_component(entity_id, persistence_comp)
                print(f"    ✅ Added persistence to {scene_name}")
    
    def setup_controls(self):
        """Step 5: Create tutorial input controls"""
        print("  🎮 Setting up tutorial controls...")
        
        # Create controller entity
        self.controller = self.world.create_entity("tutorial_controller")
        
        # Define input bindings
        input_bindings = {
            "switch_main_menu": [InputBinding(input_type="key", event_name="1")],
            "switch_game_level": [InputBinding(input_type="key", event_name="2")],
            "switch_pause_menu": [InputBinding(input_type="key", event_name="3")],
            "save_scene": [InputBinding(input_type="key", event_name="s")],
            "load_scene": [InputBinding(input_type="key", event_name="l")],
            "test_transition": [InputBinding(input_type="key", event_name="t")],
            "print_stats": [InputBinding(input_type="key", event_name="space")]
        }
        
        input_comp = InputComponent(action_bindings=input_bindings)
        self.world.add_component(self.controller.id, input_comp)
        
        print("  ✅ Tutorial controls ready")
    
    def update_tutorial(self, task):
        """Main tutorial update loop"""
        dt = globalClock.getDt()
        
        # Update world and all systems
        self.world.update(dt)
        
        # Handle tutorial input
        self.handle_tutorial_input()
        
        # Update game time in game level
        self.update_game_time(dt)
        
        return task.cont
    
    def handle_tutorial_input(self):
        """Handle tutorial-specific input"""
        input_comp = self.world.get_component(self.controller.id, InputComponent)
        if not input_comp:
            return
        
        # Scene switching
        if input_comp.action_just_pressed.get("switch_main_menu"):
            print("🏠 Switching to Main Menu...")
            self.switch_scene_with_transition("main_menu")
        
        if input_comp.action_just_pressed.get("switch_game_level"):
            print("🎮 Switching to Game Level...")
            self.switch_scene_with_transition("game_level")
        
        if input_comp.action_just_pressed.get("switch_pause_menu"):
            print("⏸️ Switching to Pause Menu...")
            self.switch_scene_with_transition("pause_menu")
        
        # Save/Load operations
        if input_comp.action_just_pressed.get("save_scene"):
            self.save_current_scene()
        
        if input_comp.action_just_pressed.get("load_scene"):
            self.load_current_scene()
        
        # Test transition
        if input_comp.action_just_pressed.get("test_transition"):
            self.test_fade_transition()
        
        # Print statistics
        if input_comp.action_just_pressed.get("print_stats"):
            self.print_scene_stats()
    
    def switch_scene_with_transition(self, target_scene_id: str):
        """Switch to a scene with proper transition"""
        current_scene_id = self.scene_manager.get_current_scene_id()
        
        if current_scene_id == target_scene_id:
            print(f"  Already in {target_scene_id}")
            return
        
        # Start transition out of current scene (if any)
        if current_scene_id:
            current_entity_id = self.scene_manager.active_scenes[current_scene_id]
            self.transition_system.start_transition(current_scene_id, current_entity_id, "out")
        
        # Load and activate target scene
        self.scene_manager.load_scene(target_scene_id, activate=True)
        
        # Start transition into target scene
        target_entity_id = self.scene_manager.active_scenes[target_scene_id]
        self.transition_system.start_transition(target_scene_id, target_entity_id, "in")
    
    def save_current_scene(self):
        """Save the current scene state"""
        current_scene_id = self.scene_manager.get_current_scene_id()
        if current_scene_id:
            print(f"💾 Saving scene: {current_scene_id}")
            success = self.persistence_system.save_scene(current_scene_id, slot=0)
            if success:
                print("  ✅ Scene saved successfully")
            else:
                print("  ❌ Failed to save scene")
        else:
            print("  ❌ No active scene to save")
    
    def load_current_scene(self):
        """Load the current scene state"""
        current_scene_id = self.scene_manager.get_current_scene_id()
        if current_scene_id:
            print(f"📂 Loading scene: {current_scene_id}")
            success = self.persistence_system.load_scene(current_scene_id, slot=0)
            if success:
                print("  ✅ Scene loaded successfully")
            else:
                print("  ❌ Failed to load scene (save file might not exist)")
        else:
            print("  ❌ No active scene to load")
    
    def test_fade_transition(self):
        """Test a fade transition on current scene"""
        current_scene_id = self.scene_manager.get_current_scene_id()
        if current_scene_id:
            print("✨ Testing fade transition...")
            entity_id = self.scene_manager.active_scenes[current_scene_id]
            
            # Set to fade transition temporarily
            transition_comp = self.world.get_component(entity_id, SceneTransitionComponent)
            if transition_comp:
                original_type = transition_comp.transition_type
                transition_comp.transition_type = TransitionType.FADE
                transition_comp.duration = 1.0
                
                # Start fade out and back in
                self.transition_system.start_transition(current_scene_id, entity_id, "out")
                
                # Restore original transition type after a delay
                def restore_transition():
                    transition_comp.transition_type = original_type
                
                # Note: In a real implementation, you'd want to schedule this properly
    
    def update_game_time(self, dt: float):
        """Update game time in game level scene"""
        game_scene_comp = self.scene_manager.get_scene_component("game_level")
        if game_scene_comp and game_scene_comp.is_active():
            current_time = game_scene_comp.scene_data.get("game_time", 0.0)
            game_scene_comp.scene_data["game_time"] = current_time + dt
    
    def print_scene_stats(self):
        """Print current scene management statistics"""
        print("\\n📊 SCENE MANAGEMENT STATS:")
        
        # Scene manager stats
        scene_stats = self.scene_manager.get_scene_stats()
        print(f"  Total Scenes: {scene_stats['total_scenes']}")
        print(f"  Active Scenes: {scene_stats['active_scenes']}")
        print(f"  Current Scene: {scene_stats['current_scene']}")
        
        # Transition stats
        transition_stats = self.transition_system.get_transition_stats()
        print(f"  Active Transitions: {transition_stats['active_transitions']}")
        
        # Persistence stats
        persistence_stats = self.persistence_system.get_persistence_stats()
        print(f"  Save Files: {persistence_stats['total_save_files']}")
        print(f"  Saves Performed: {persistence_stats['total_saves_performed']}")
        
        # Current scene details
        current_scene_id = self.scene_manager.get_current_scene_id()
        if current_scene_id:
            scene_comp = self.scene_manager.get_scene_component(current_scene_id)
            if scene_comp:
                print(f"  Current Scene Data: {scene_comp.scene_data}")
        
        print()
    
    def on_transition_start(self, transition_comp, direction: str, scene_name: str):
        """Callback when transition starts"""
        print(f"  🎬 {scene_name}: Transition {direction} started")
    
    def on_transition_complete(self, transition_comp, direction: str, scene_name: str):
        """Callback when transition completes"""
        print(f"  ✅ {scene_name}: Transition {direction} completed")
    
    def on_save_complete(self, scene_id: str, slot: int, filepath: str, scene_name: str):
        """Callback when save completes"""
        filename = os.path.basename(filepath)
        print(f"  💾 {scene_name}: Saved to {filename}")
    
    def on_load_complete(self, scene_id: str, slot: int, filepath: str, scene_name: str):
        """Callback when load completes"""
        filename = os.path.basename(filepath)
        print(f"  📂 {scene_name}: Loaded from {filename}")

if __name__ == '__main__':
    print("🎓 Starting Scene Management Tutorial...")
    print("This tutorial demonstrates step-by-step scene management integration.")
    print("\\nNote: Tutorial uses simplified placeholder assets")
    print("\\n" + "="*60)
    
    app = SceneTutorial()
    app.run()
