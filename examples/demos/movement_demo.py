#!/usr/bin/env python3
"""
Movement System Demo - Demonstrates the robust movement component with dynamic speed effects.

Controls:
- WASD / Arrow Keys: Move player
- Q: Apply 30% slowdown effect for 3 seconds  
- E: Apply 250% speed boost for 2 seconds
- Space: Fire action (debug output)

This demo shows:
1. Smooth acceleration and deceleration
2. Dynamic speed modifiers that can stack
3. Timed effects that automatically expire
4. Frame-rate independent movement
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

class MovementDemo(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        print("=== Movement System Demo ===")
        print("Controls:")
        print("  WASD / Arrow Keys: Move player")
        print("  Q: Apply slowdown effect (30% speed, 3 seconds)")
        print("  E: Apply speed boost (250% speed, 2 seconds)")
        print("  Space: Fire action")
        print("================================")

        self.world = World()

        # Initialize systems
        self.render_system = RenderSystem(self.world, self)
        self.world.add_system(self.render_system)

        self.input_system = InputSystem(self.world, self)
        self.world.add_system(self.input_system)

        self.movement_system = MovementSystem(self.world)
        self.world.add_system(self.movement_system)

        # Setup assets
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        assets_dir = os.path.join(script_dir, "assets")
        test_image_path = Filename.fromOsSpecific(os.path.join(assets_dir, "player.png")).getFullpath()

        if not os.path.exists(test_image_path):
            print(f"Warning: Player image not found at {test_image_path}")
            print("Demo will run but sprite may not be visible")

        # Create player entity with movement capabilities
        self.player_entity = self.world.create_entity("demo_player")
        
        # Transform component
        self.world.add_component(self.player_entity.id, TransformComponent(
            x=0.0, y=0.0, scale_x=1.0, scale_y=1.0
        ))
        
        # Sprite component
        self.world.add_component(self.player_entity.id, SpriteComponent(
            image_path=test_image_path, 
            layer=1
        ))
        
        # Movement component with fine-tuned values
        self.world.add_component(self.player_entity.id, MovementComponent(
            base_speed=1.2,  # Base movement speed
            acceleration=8.0,  # Quick response to input
            deceleration=12.0,  # Quick stop when input ends
            max_speed_multiplier=4.0  # Allow very fast speeds
        ))

        # Input component with movement and effect bindings
        player_input_bindings = {
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
            "apply_freeze": [
                InputBinding(input_type="key", event_name="f"),
            ],
            "reset_effects": [
                InputBinding(input_type="key", event_name="r"),
            ]
        }
        
        self.world.add_component(self.player_entity.id, InputComponent(
            action_bindings=player_input_bindings
        ))

        # Game loop
        self.taskMgr.add(self.update_demo, "update_demo_task")

    def update_demo(self, task):
        dt = globalClock.getDt()
        self.world.update(dt)

        # Handle demo-specific input
        input_comp = self.world.get_component(self.player_entity.id, InputComponent)
        movement_comp = self.world.get_component(self.player_entity.id, MovementComponent)
        
        if input_comp and movement_comp:
            # Status effect controls
            if input_comp.action_just_pressed.get("apply_slowdown"):
                print("🐌 Applying SLOWDOWN effect (30% speed for 3 seconds)")
                self.movement_system.apply_speed_effect(
                    self.player_entity.id, "slowdown", 0.3, 3.0
                )
            
            if input_comp.action_just_pressed.get("apply_speed_boost"):
                print("⚡ Applying SPEED BOOST effect (250% speed for 2 seconds)")
                self.movement_system.apply_speed_effect(
                    self.player_entity.id, "speed_boost", 2.5, 2.0
                )
                
            if input_comp.action_just_pressed.get("apply_freeze"):
                print("🧊 Applying FREEZE effect (0% speed for 1.5 seconds)")
                self.movement_system.apply_speed_effect(
                    self.player_entity.id, "freeze", 0.0, 1.5
                )
                
            if input_comp.action_just_pressed.get("reset_effects"):
                print("🔄 Clearing all effects")
                movement_comp.speed_modifiers.clear()
            
            if input_comp.action_just_pressed.get("fire"):
                current_speed = movement_comp.get_effective_speed()
                active_effects = list(movement_comp.speed_modifiers.keys())
                print(f"🎯 FIRE! Current speed: {current_speed:.2f}, Active effects: {active_effects}")
            
            # Display current speed info periodically
            if int(globalClock.getFrameTime() * 2) % 2 == 0:  # Every 0.5 seconds
                if movement_comp.speed_modifiers:
                    effects_info = []
                    for name, (mult, duration) in movement_comp.speed_modifiers.items():
                        effects_info.append(f"{name}({mult:.1f}x, {duration:.1f}s)")
                    
                    current_speed = movement_comp.get_effective_speed()
                    print(f"📊 Speed: {current_speed:.2f} | Effects: {', '.join(effects_info)}")

        return task.cont

if __name__ == '__main__':
    demo = MovementDemo()
    demo.run()
