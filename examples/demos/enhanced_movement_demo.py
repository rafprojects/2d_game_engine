#!/usr/bin/env python3
"""
Enhanced Movement Demo with Tweening Effects

This demonstrates the integration of the movement system with optional tweening
for smooth visual effects and game feel enhancements.

Controls:
- WASD / Arrow Keys: Move player
- Q: Apply slowdown effect (30% speed, 3 seconds)
- E: Apply speed boost (250% speed, 2 seconds)  
- 1: Snappy preset (quick, responsive)
- 2: Smooth preset (gentle, flowing)
- 3: Bouncy preset (fun, exaggerated)
- 4: Elastic preset (spring-like effects)
- T: Toggle all tweening effects on/off
- Space: Fire action (debug output)

The tweening system adds visual polish without affecting gameplay mechanics:
- Position smoothing for fluid movement
- Bounce effects on direction changes
- Scale effects during movement
- Multiple easing function options
"""

from direct.showbase.ShowBase import ShowBase
from direct.showbase.ShowBaseGlobal import globalClock
from panda3d.core import Vec2, Filename
import os

from engine.core.system import World
from engine.core.components.transform_component import TransformComponent
from engine.core.components.movement_component import MovementComponent
from engine.core.systems.movement_system import MovementSystem
from engine.graphics.components.sprite_component import SpriteComponent
from engine.graphics.systems.render_system import RenderSystem
from engine.input.components.input_component import InputComponent
from engine.input.systems.input_system import InputSystem
from engine.input.input_bindings import InputBinding

# Optional tweening for enhanced visual effects
try:
    from engine.animation.movement_tweening import MovementTweenComponent
    from engine.animation.tweening import global_tween_manager
    TWEENING_AVAILABLE = True
    print("✅ Tweening system loaded - Enhanced visual effects available!")
except ImportError:
    print("⚠️  Tweening system not available - running with basic movement")
    TWEENING_AVAILABLE = False
    MovementTweenComponent = None

class EnhancedMovementDemo(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        
        print("\n" + "="*60)
        print("🚀 ENHANCED MOVEMENT SYSTEM DEMO")
        print("="*60)
        print("Movement + Speed Effects + Optional Visual Tweening")
        
        if TWEENING_AVAILABLE:
            print("\n🎨 VISUAL EFFECTS ENABLED")
            print("This demo shows smooth visual tweening effects:")
            print("  • Position smoothing for fluid motion")
            print("  • Bounce effects on direction changes")  
            print("  • Scale effects during movement")
            print("  • Multiple easing presets")
            
            print("\n🎮 TWEENING CONTROLS:")
            print("  1 = Snappy preset (quick, responsive)")
            print("  2 = Smooth preset (gentle, flowing)")
            print("  3 = Bouncy preset (fun, exaggerated)")
            print("  4 = Elastic preset (spring-like)")
            print("  T = Toggle all effects on/off")
        else:
            print("\n🎮 BASIC MOVEMENT DEMO")
            print("Tweening not available - showing core movement system")
        
        print("\n🕹️  MOVEMENT CONTROLS:")
        print("  WASD/Arrow Keys = Move player")
        print("  Q = Apply slowdown (30% speed, 3 sec)")
        print("  E = Apply speed boost (250% speed, 2 sec)")
        print("  Space = Fire action (debug output)")
        print("="*60)

        # Initialize world and systems
        self.world = World()
        
        self.render_system = RenderSystem(self.world, self)
        self.world.add_system(self.render_system)
        
        self.input_system = InputSystem(self.world, self)
        self.world.add_system(self.input_system)
        
        self.movement_system = MovementSystem(self.world)
        self.world.add_system(self.movement_system)

        # Setup player
        self._create_demo_player()
        
        # Game loop
        self.taskMgr.add(self.update_demo, "update_demo_task")

    def _create_demo_player(self):
        """Create the demo player with movement and optional tweening."""
        # Setup assets
        script_dir = os.path.dirname(os.path.abspath(__file__))
        assets_dir = os.path.join(script_dir, "assets")
        player_image = Filename.fromOsSpecific(os.path.join(assets_dir, "player.png")).getFullpath()

        # Create player entity
        self.player = self.world.create_entity("demo_player")
        
        # Core components
        transform = TransformComponent(position=Vec2(0, 0), scale=Vec2(1, 1), rotation=0.0)
        movement = MovementComponent(
            base_speed=1.2,  # Good speed for demo
            acceleration=8.0,  # Responsive
            deceleration=12.0,  # Quick stop
            max_speed_multiplier=4.0  # Allow big speed boosts
        )
        
        self.world.add_component(self.player.id, transform)
        self.world.add_component(self.player.id, movement)
        
        # Sprite (if available)
        if os.path.exists(player_image):
            sprite = SpriteComponent(image_path=player_image, layer=1)
            self.world.add_component(self.player.id, sprite)
            print(f"✅ Player sprite loaded from {player_image}")
        else:
            print(f"⚠️  Player sprite not found at {player_image}")
        
        # Optional tweening effects
        if TWEENING_AVAILABLE:
            tween_comp = MovementTweenComponent()
            tween_comp.set_base_transform(Vec2(0, 0), Vec2(1, 1), 0.0)
            tween_comp.set_preset("smooth")  # Start with smooth
            self.world.add_component(self.player.id, tween_comp)
            print("✅ Tweening effects enabled")
        
        # Input setup
        self._setup_input()

    def _setup_input(self):
        """Setup input bindings for the demo."""
        bindings = {
            "move_left": [InputBinding(input_type="key", event_name="a"),
                         InputBinding(input_type="key", event_name="arrow_left")],
            "move_right": [InputBinding(input_type="key", event_name="d"),
                          InputBinding(input_type="key", event_name="arrow_right")],
            "move_up": [InputBinding(input_type="key", event_name="w"),
                       InputBinding(input_type="key", event_name="arrow_up")],
            "move_down": [InputBinding(input_type="key", event_name="s"),
                         InputBinding(input_type="key", event_name="arrow_down")],
            "fire": [InputBinding(input_type="key", event_name="space")],
            "apply_slowdown": [InputBinding(input_type="key", event_name="q")],
            "apply_speed_boost": [InputBinding(input_type="key", event_name="e")],
        }
        
        # Add tweening controls if available
        if TWEENING_AVAILABLE:
            bindings.update({
                "preset_snappy": [InputBinding(input_type="key", event_name="1")],
                "preset_smooth": [InputBinding(input_type="key", event_name="2")],
                "preset_bouncy": [InputBinding(input_type="key", event_name="3")],
                "preset_elastic": [InputBinding(input_type="key", event_name="4")],
                "toggle_tweening": [InputBinding(input_type="key", event_name="t")],
            })
        
        input_comp = InputComponent(action_bindings=bindings)
        self.world.add_component(self.player.id, input_comp)

    def update_demo(self, task):
        """Update the demo."""
        dt = globalClock.getDt()
        
        # Update world (includes movement system with tweening)
        self.world.update(dt)
        
        # Update global tween manager if available
        if TWEENING_AVAILABLE:
            global_tween_manager.update(dt)

        # Handle demo controls
        input_comp = self.world.get_component(self.player.id, InputComponent)
        if input_comp:
            self._handle_demo_input(input_comp)

        return task.cont

    def _handle_demo_input(self, input_comp):
        """Handle demo-specific input."""
        # Speed effects
        if input_comp.action_just_pressed.get("apply_slowdown"):
            print("🐌 Applying SLOWDOWN effect (30% speed for 3 seconds)")
            self.movement_system.apply_speed_effect(self.player.id, "slowdown", 0.3, 3.0)
        
        if input_comp.action_just_pressed.get("apply_speed_boost"):
            print("⚡ Applying SPEED BOOST effect (250% speed for 2 seconds)")
            self.movement_system.apply_speed_effect(self.player.id, "speed_boost", 2.5, 2.0)
        
        if input_comp.action_just_pressed.get("fire"):
            movement = self.world.get_component(self.player.id, MovementComponent)
            current_speed = movement.get_effective_speed() if movement else 0
            active_effects = list(movement.speed_modifiers.keys()) if movement else []
            print(f"💥 FIRE! Current speed: {current_speed:.2f}, Effects: {active_effects}")
        
        # Tweening controls
        if TWEENING_AVAILABLE:
            tween_comp = self.world.get_component(self.player.id, MovementTweenComponent)
            if tween_comp:
                if input_comp.action_just_pressed.get("preset_snappy"):
                    tween_comp.set_preset("snappy")
                    print("📱 SNAPPY preset: Quick and responsive movement")
                
                if input_comp.action_just_pressed.get("preset_smooth"):
                    tween_comp.set_preset("smooth")
                    print("🌊 SMOOTH preset: Gentle and flowing movement")
                
                if input_comp.action_just_pressed.get("preset_bouncy"):
                    tween_comp.set_preset("bouncy")
                    print("🏀 BOUNCY preset: Fun and exaggerated effects")
                
                if input_comp.action_just_pressed.get("preset_elastic"):
                    tween_comp.set_preset("elastic")
                    print("🎯 ELASTIC preset: Spring-like movement effects")
                
                if input_comp.action_just_pressed.get("toggle_tweening"):
                    if tween_comp.position_smoothing:
                        tween_comp.disable_all_effects()
                        print("❌ ALL TWEENING EFFECTS DISABLED")
                    else:
                        tween_comp.enable_juice_effects()
                        print("✅ ALL TWEENING EFFECTS ENABLED")

if __name__ == '__main__':
    demo = EnhancedMovementDemo()
    demo.run()
