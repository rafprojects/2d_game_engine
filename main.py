# Main entry point for the game engine
from direct.showbase.ShowBase import ShowBase
from direct.showbase.ShowBaseGlobal import globalClock
from panda3d.core import Vec2, Filename, ClockObject # Import ClockObject for globalClock
import os # Import os for path manipulation

from engine.core.system import World
from engine.graphics.components.transform_component import TransformComponent
from engine.core.components.movement_component import MovementComponent
from engine.core.systems.movement_system import MovementSystem
from engine.graphics.components.sprite_component import SpriteComponent
from engine.graphics.systems.render_system import RenderSystem
from engine.input.components.input_component import InputComponent
from engine.input.systems.input_system import InputSystem
from engine.input.input_bindings import InputBinding

# Audio system imports
try:
    from engine.audio.audio_manager import AudioManager
    from engine.audio.systems.audio_system import AudioSystem
    from engine.audio.systems.music_system import MusicSystem
    from engine.audio.components.audio_listener_component import AudioListenerComponent
    AUDIO_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Audio system not available - running without audio: {e}")
    AUDIO_AVAILABLE = False

# Asset pipeline imports
try:
    from engine.assets.resource_manager import ResourceManager
    from engine.assets.asset_streaming import AssetStreamingSystem
    from engine.assets.texture_atlas import TextureAtlas
    ASSETS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Asset pipeline not available - running without advanced asset management: {e}")
    ASSETS_AVAILABLE = False

# Optional tweening for visual effects
try:
    from engine.animation.movement_tweening import MovementTweenComponent
    from engine.animation.tweening import global_tween_manager
    TWEENING_AVAILABLE = True
except ImportError:
    print("⚠️  Tweening system not available - running without visual effects")
    TWEENING_AVAILABLE = False
    MovementTweenComponent = None
class Game(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        print("🎮 Game initialized with enhanced movement system!")
        
        if TWEENING_AVAILABLE:
            print("✨ Visual tweening effects available!")
            print("Controls:")
            print("  WASD/Arrows: Move player")
            print("  Q: Apply slowdown effect")
            print("  E: Apply speed boost effect")
            print("  1-4: Switch tweening presets (Snappy/Smooth/Bouncy/Elastic)")
            print("  T: Toggle all tweening effects")
            print("  Space: Fire (debug)")
        else:
            print("Basic movement system loaded (no visual effects)")
            print("Controls: WASD/Arrows to move, Q/E for speed effects")

        self.world = World()

        # Add systems
        self.render_system = RenderSystem(self.world, self) # Pass ShowBase instance
        self.world.add_system(self.render_system)

        self.input_system = InputSystem(self.world, self) # Pass ShowBase instance
        self.world.add_system(self.input_system)
        
        self.movement_system = MovementSystem(self.world)
        self.world.add_system(self.movement_system)

        # Try to find an assets directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        assets_dir = os.path.join(script_dir, "assets")
        if not os.path.exists(assets_dir):
            os.makedirs(assets_dir)
            print(f"Created assets directory at: {assets_dir}")
            print("Please add a test image (e.g., 'player.png') to this directory.")

        test_image_path = Filename.fromOsSpecific(os.path.join(assets_dir, "player.png")).getFullpath()
        print("TEST IMAGE PATH: ", test_image_path)
        # Check if the placeholder image exists, if not, we can't run the example entity
        if not os.path.exists(test_image_path):
            print(f"ERROR: Test image not found at {test_image_path}")
            print("Please create a placeholder image (e.g., 'player.png') in the 'assets' directory to see the sprite.")
        else:
            player_entity = self.world.create_entity("player") # Named for easier debugging
            # Use center position like minimal.py, and scale that works with our render system
            self.world.add_component(player_entity.id, TransformComponent(position=Vec2(0, 0), scale=Vec2(1, 1)))
            self.world.add_component(player_entity.id, SpriteComponent(image_path=test_image_path, layer=1))
            
            # Add movement component with reasonable values for aspect2d
            self.world.add_component(player_entity.id, MovementComponent(
                base_speed=1.0,  # 1 unit per second in aspect2d coordinates
                acceleration=5.0,  # Fast response
                deceleration=8.0,  # Quick stop
                max_speed_multiplier=3.0  # Allow up to 3x speed boost
            ))
            
            # Add optional tweening effects for visual polish
            if TWEENING_AVAILABLE:
                tween_comp = MovementTweenComponent()
                tween_comp.set_base_transform(Vec2(0, 0), Vec2(1, 1), 0.0)
                tween_comp.set_preset("smooth")  # Start with smooth preset
                self.world.add_component(player_entity.id, tween_comp)
                print("✅ Tweening effects enabled - Use number keys (1-4) for presets!")
            else:
                print("ℹ️  Running without tweening effects")
            
            # Add optional tweening effects for visual polish
            if TWEENING_AVAILABLE:
                tween_comp = MovementTweenComponent()
                tween_comp.set_base_transform(Vec2(0, 0), Vec2(1, 1), 0.0)
                tween_comp.set_preset("smooth")  # Use smooth preset for polished feel
                self.world.add_component(player_entity.id, tween_comp)
                print("✅ Movement tweening effects enabled")

            # Setup Input for the player entity
            player_input_bindings = {
                "move_left": [
                    InputBinding(input_type="key", event_name="a"),
                    InputBinding(input_type="key", event_name="arrow_left"),
                    InputBinding(input_type="gamepad_button", event_name="gamepad-dpad_left"),
                    InputBinding(input_type="gamepad_axis", event_name="lstick_x", axis_direction="negative", axis_threshold=0.3)
                ],
                "move_right": [
                    InputBinding(input_type="key", event_name="d"),
                    InputBinding(input_type="key", event_name="arrow_right"),
                    InputBinding(input_type="gamepad_button", event_name="gamepad-dpad_right"),
                    InputBinding(input_type="gamepad_axis", event_name="lstick_x", axis_direction="positive", axis_threshold=0.3)
                ],
                "move_up": [
                    InputBinding(input_type="key", event_name="w"),
                    InputBinding(input_type="key", event_name="arrow_up"),
                    InputBinding(input_type="gamepad_button", event_name="gamepad-dpad_up"),
                    InputBinding(input_type="gamepad_axis", event_name="lstick_y", axis_direction="positive", axis_threshold=0.3)
                ],
                "move_down": [
                    InputBinding(input_type="key", event_name="s"),
                    InputBinding(input_type="key", event_name="arrow_down"),
                    InputBinding(input_type="gamepad_button", event_name="gamepad-dpad_down"),
                    InputBinding(input_type="gamepad_axis", event_name="lstick_y", axis_direction="negative", axis_threshold=0.3)
                ],
                "fire": [
                    InputBinding(input_type="key", event_name="space"),
                    InputBinding(input_type="mouse_button", event_name="mouse1"), # Left mouse button
                    InputBinding(input_type="gamepad_button", event_name="gamepad-face_x") # 'X' on Xbox, Square on PS
                ],
                "alt_fire": [
                    InputBinding(input_type="gamepad_button", event_name="gamepad-rtrigger"), # Panda uses 'gamepad-rtrigger' for button press
                    InputBinding(input_type="gamepad_axis", event_name="rtrigger", axis_direction="positive", axis_threshold=0.1) # For analog trigger
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
                "toggle_tweening": [
                    InputBinding(input_type="key", event_name="t"),
                ]
            }
            self.world.add_component(player_entity.id, InputComponent(action_bindings=player_input_bindings))
            print(f"Added InputComponent to entity: {player_entity.id}")


        # Game loop task
        self.taskMgr.add(self.update_game, "update_game_task")

    def _handle_player_input_debug(self, input_comp: InputComponent):
        """Helper to print player input states for debugging."""
        if input_comp.action_just_pressed.get("fire"):
            print(f"[{globalClock.getFrameTime():.2f}] Player FIRE just pressed!")
        if input_comp.action_active.get("move_left"):
            print(f"[{globalClock.getFrameTime():.2f}] Player MOVE_LEFT active")
        if input_comp.action_active.get("move_right"):
            print(f"[{globalClock.getFrameTime():.2f}] Player MOVE_RIGHT active")
        if input_comp.action_active.get("move_up"):
            print(f"[{globalClock.getFrameTime():.2f}] Player MOVE_UP active")
        if input_comp.action_active.get("move_down"):
            print(f"[{globalClock.getFrameTime():.2f}] Player MOVE_DOWN active")
        if input_comp.action_just_released.get("fire"):
            print(f"[{globalClock.getFrameTime():.2f}] Player FIRE just released!")
        if input_comp.action_active.get("alt_fire"):
            print(f"[{globalClock.getFrameTime():.2f}] Player ALT_FIRE active (check gamepad trigger)")
        if input_comp.action_just_pressed.get("apply_slowdown"):
            print(f"[{globalClock.getFrameTime():.2f}] Player SLOWDOWN effect (Q) pressed!")
        if input_comp.action_just_pressed.get("apply_speed_boost"):
            print(f"[{globalClock.getFrameTime():.2f}] Player SPEED BOOST effect (E) pressed!")
        
        # Show tweening key hints periodically
        if TWEENING_AVAILABLE and int(globalClock.getFrameTime()) % 10 == 0:
            print("💡 Tweening Controls: 1=Snappy, 2=Smooth, 3=Bouncy, 4=Elastic, T=Toggle")
        if input_comp.action_just_pressed.get("toggle_tweening"):
            print(f"[{globalClock.getFrameTime():.2f}] Player TOGGLE TWEENING (T) pressed!")

    def update_game(self, task):
        # Access globalClock directly as it's part of ShowBase
        dt = globalClock.getDt()
        self.world.update(dt)
        
        # Update global tween manager if tweening is available
        if TWEENING_AVAILABLE:
            global_tween_manager.update(dt)

        # Optional: Debug input for the first entity with input component
        entities = self.world.get_entities_with_components(InputComponent)
        if entities:
            entity = entities[0]
            input_comp = self.world.get_component(entity.id, InputComponent)
            if input_comp:
                self._handle_player_input_debug(input_comp)
                
                # Handle speed effect demonstrations
                if input_comp.action_just_pressed.get("apply_slowdown"):
                    print("Applying slowdown effect!")
                    self.movement_system.apply_speed_effect(entity.id, "slowdown", 0.3, 3.0)
                
                if input_comp.action_just_pressed.get("apply_speed_boost"):
                    print("Applying speed boost effect!")
                    self.movement_system.apply_speed_effect(entity.id, "speed_boost", 2.5, 2.0)
                
                # Handle tweening controls
                if TWEENING_AVAILABLE:
                    tween_comp = self.world.get_component(entity.id, MovementTweenComponent)
                    if tween_comp:
                        # Preset controls
                        if input_comp.action_just_pressed.get("preset_snappy"):
                            tween_comp.set_preset("snappy")
                            print("📱 Set to Snappy preset - Quick and responsive!")
                        
                        if input_comp.action_just_pressed.get("preset_smooth"):
                            tween_comp.set_preset("smooth")
                            print("🌊 Set to Smooth preset - Gentle and flowing!")
                        
                        if input_comp.action_just_pressed.get("preset_bouncy"):
                            tween_comp.set_preset("bouncy")
                            print("🏀 Set to Bouncy preset - Fun and exaggerated!")
                        
                        if input_comp.action_just_pressed.get("preset_elastic"):
                            tween_comp.set_preset("elastic")
                            print("🎯 Set to Elastic preset - Spring-like effects!")
                        
                        # Toggle all effects
                        if input_comp.action_just_pressed.get("toggle_tweening"):
                            if tween_comp.position_smoothing:
                                tween_comp.disable_all_effects()
                                print("❌ All tweening effects disabled")
                            else:
                                tween_comp.enable_juice_effects()
                                print("✅ All tweening effects enabled")

        return task.cont

if __name__ == '__main__':
    app = Game()
    app.run()
