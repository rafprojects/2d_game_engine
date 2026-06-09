#!/usr/bin/env python3
"""
Movement Tweening Demo - Demonstrates visual movement effects and tweening.

This demo shows how to add visual polish to movement with tweening effects
including smooth acceleration, bounce effects, scaling, and more.

Controls:
- WASD / Arrow Keys: Move player
- Q: Apply slowdown effect (30% speed, 3 seconds)  
- E: Apply speed boost (250% speed, 2 seconds)
- 1-4: Switch between tweening presets
- R: Toggle rotation on movement
- T: Toggle all tweening effects
- Space: Fire action (debug output)

Tweening Presets:
1: Snappy - Quick, responsive with strong bounce
2: Smooth - Gentle, flowing movement
3: Bouncy - Exaggerated bounce effects
4: Elastic - Elastic spring-like effects
"""

from direct.showbase.ShowBase import ShowBase
from direct.showbase.ShowBaseGlobal import globalClock
from panda3d.core import Vec2, Filename
import os

from engine.core.system import World
from engine.graphics.components.transform_component import TransformComponent
from engine.core.components.movement_component import MovementComponent
from engine.core.systems.movement_system import MovementSystem
from engine.graphics.components.sprite_component import SpriteComponent
from engine.graphics.systems.render_system import RenderSystem
from engine.input.components.input_component import InputComponent
from engine.input.systems.input_system import InputSystem
from engine.input.input_bindings import InputBinding

# Import tweening components
try:
    from engine.animation.movement_tweening import MovementTweenComponent
    from engine.animation.tweening import global_tween_manager, EasingType
    TWEENING_AVAILABLE = True
except ImportError:
    print("⚠️  Tweening system not available - running without visual effects")
    TWEENING_AVAILABLE = False
    MovementTweenComponent = None

class MovementTweeningDemo(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        print("=== Movement Tweening Demo ===")
        print("Controls:")
        print("  WASD / Arrow Keys: Move player")
        print("  Q: Apply slowdown effect (30% speed, 3 seconds)")
        print("  E: Apply speed boost (250% speed, 2 seconds)")
        if TWEENING_AVAILABLE:
            print("  1-4: Switch between tweening presets")
            print("  R: Toggle rotation on movement")
            print("  T: Toggle all tweening effects")
        print("  Space: Fire action")
        print("=================================")

        self.world = World()
        self.player_entity = None

        # Initialize systems
        self.render_system = RenderSystem(self.world, self)
        self.world.add_system(self.render_system)

        self.input_system = InputSystem(self.world, self)
        self.world.add_system(self.input_system)

        self.movement_system = MovementSystem(self.world)
        self.world.add_system(self.movement_system)

        # Setup player entity
        self._create_player()

        # Game loop task
        self.taskMgr.add(self.update_game, "update_game_task")

    def _create_player(self):
        """Create the player entity with movement and tweening components."""
        # Setup assets
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        assets_dir = os.path.join(script_dir, "assets")
        test_image_path = Filename.fromOsSpecific(os.path.join(assets_dir, "player.png")).getFullpath()

        # Create player entity
        self.player_entity = self.world.create_entity("tweening_player")
        
        # Add core components
        transform = TransformComponent(x=0.0, y=0.0, scale_x=1.0, scale_y=1.0, rotation=0.0)
        self.world.add_component(self.player_entity.id, transform)
        
        # Add movement component with smooth settings
        movement = MovementComponent(
            base_speed=1.2,  # Slightly faster for better effect visibility
            acceleration=8.0,  # Responsive acceleration
            deceleration=12.0,  # Quick stop
            max_speed_multiplier=3.0
        )
        self.world.add_component(self.player_entity.id, movement)
        
        # Add sprite if available
        if os.path.exists(test_image_path):
            self.world.add_component(self.player_entity.id, 
                SpriteComponent(image_path=test_image_path, layer=1))
        else:
            print(f"⚠️  Player sprite not found at {test_image_path}")
        
        # Add tweening component if available
        if TWEENING_AVAILABLE:
            tween_comp = MovementTweenComponent()
            tween_comp.set_base_transform(Vec2(transform.x, transform.y), Vec2(transform.scale_x, transform.scale_y), transform.rotation)
            tween_comp.enable_juice_effects()  # Enable all visual effects
            self.world.add_component(self.player_entity.id, tween_comp)
            print("✅ Tweening effects enabled")
        
        # Setup input bindings
        input_bindings = {
            "move_left": [
                InputBinding(input_type="key", event_name="a"),
                InputBinding(input_type="key", event_name="arrow_left"),
            ],
            "move_right": [
                InputBinding(input_type="key", event_name="d"),
                InputBinding(input_type="key", event_name="arrow_right"),
            ],
            "move_up": [
                InputBinding(input_type="key", event_name="w"),
                InputBinding(input_type="key", event_name="arrow_up"),
            ],
            "move_down": [
                InputBinding(input_type="key", event_name="s"),
                InputBinding(input_type="key", event_name="arrow_down"),
            ],
            "fire": [
                InputBinding(input_type="key", event_name="space"),
            ],
            "apply_slowdown": [
                InputBinding(input_type="key", event_name="q"),
            ],
            "apply_speed_boost": [
                InputBinding(input_type="key", event_name="e"),
            ],
            "preset_snappy": [
                InputBinding(input_type="key", event_name="1"),
            ],
            "preset_smooth": [
                InputBinding(input_type="key", event_name="2"),
            ],
            "preset_bouncy": [
                InputBinding(input_type="key", event_name="3"),
            ],
            "preset_elastic": [
                InputBinding(input_type="key", event_name="4"),
            ],
            "toggle_rotation": [
                InputBinding(input_type="key", event_name="r"),
            ],
            "toggle_tweening": [
                InputBinding(input_type="key", event_name="t"),
            ],
        }
        
        self.world.add_component(self.player_entity.id, 
            InputComponent(action_bindings=input_bindings))

    def update_game(self, task):
        # Update world
        dt = globalClock.getDt()
        self.world.update(dt)
        
        # Update global tween manager if available
        if TWEENING_AVAILABLE:
            global_tween_manager.update(dt)

        # Handle player input and effects
        if self.player_entity:
            input_comp = self.world.get_component(self.player_entity.id, InputComponent)
            tween_comp = None
            if TWEENING_AVAILABLE:
                tween_comp = self.world.get_component(self.player_entity.id, MovementTweenComponent)
            
            if input_comp:
                # Speed effects
                if input_comp.action_just_pressed.get("apply_slowdown"):
                    print("🐌 Applying slowdown effect!")
                    self.movement_system.apply_speed_effect(self.player_entity.id, "slowdown", 0.3, 3.0)
                
                if input_comp.action_just_pressed.get("apply_speed_boost"):
                    print("🚀 Applying speed boost effect!")
                    self.movement_system.apply_speed_effect(self.player_entity.id, "speed_boost", 2.5, 2.0)
                
                # Tweening controls (only if tweening is available)
                if TWEENING_AVAILABLE and tween_comp:
                    if input_comp.action_just_pressed.get("preset_snappy"):
                        tween_comp.set_preset("snappy")
                        print("📱 Set to Snappy preset")
                    
                    if input_comp.action_just_pressed.get("preset_smooth"):
                        tween_comp.set_preset("smooth")
                        print("🌊 Set to Smooth preset")
                    
                    if input_comp.action_just_pressed.get("preset_bouncy"):
                        tween_comp.set_preset("bouncy")
                        print("🏀 Set to Bouncy preset")
                    
                    if input_comp.action_just_pressed.get("preset_elastic"):
                        tween_comp.set_preset("elastic")
                        print("🎯 Set to Elastic preset")
                    
                    if input_comp.action_just_pressed.get("toggle_rotation"):
                        tween_comp.rotate_on_movement = not tween_comp.rotate_on_movement
                        status = "enabled" if tween_comp.rotate_on_movement else "disabled"
                        print(f"🔄 Rotation on movement {status}")
                    
                    if input_comp.action_just_pressed.get("toggle_tweening"):
                        if tween_comp.position_smoothing:
                            tween_comp.disable_all_effects()
                            print("❌ All tweening effects disabled")
                        else:
                            tween_comp.enable_juice_effects()
                            print("✅ All tweening effects enabled")
                
                # Debug fire action
                if input_comp.action_just_pressed.get("fire"):
                    print(f"💥 Fire! [{globalClock.getFrameTime():.2f}]")

        return task.cont

if __name__ == '__main__':
    app = MovementTweeningDemo()
    app.run()
