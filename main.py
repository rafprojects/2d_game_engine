# Main entry point for the game engine
from direct.showbase.ShowBase import ShowBase
from direct.showbase.ShowBaseGlobal import globalClock
from panda3d.core import Vec2, Filename, ClockObject # Import ClockObject for globalClock
import argparse
import os # Import os for path manipulation
from pathlib import Path

from engine.core.system import World
from engine.graphics.components.transform_component import TransformComponent
from engine.core.components.movement_component import MovementComponent
from engine.core.systems.movement_system import MovementSystem
from engine.graphics.components.sprite_component import SpriteComponent
from engine.graphics.systems.render_system import RenderSystem
from engine.input.components.input_component import InputComponent
from engine.input.systems.input_system import InputSystem
from engine.input.input_bindings import InputBinding
from engine.cartridge.loader import CartridgeLoader
from engine.cartridge.errors import CartridgeError
from engine.save_state.manager import SaveStateManager
from engine.save_state.world_provider import WorldSaveProvider

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
    def __init__(self, cartridge_path: str | None = None, extract_dir: str | None = None, dev_mode: bool = False):
        ShowBase.__init__(self)
        self.dev_mode = bool(dev_mode)
        if self.dev_mode:
            print("🛠️  Dev mode enabled (collision viz, debug features available)")
            print("    Keys: V = toggle collision outlines, R/F5 = restart, ESC = quit cleanly")
        print("🎮 Game initialized with enhanced movement system!")

        # Dev / quality-of-life input for shutdown and iteration
        self.accept("escape", self._request_exit)
        self.accept("window-close", self._request_exit)
        self.accept("r", self._request_restart)
        self.accept("R", self._request_restart)
        self.accept("f5", self._request_restart)
        self._restart_requested = False
        self._exit_requested = False
        
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

        # Asset systems first so RenderSystem (and future consumers) can resolve cartridge
        # assets via mounted roots. RenderSystem receives the RM (may be None if assets
        # pipeline unavailable) for precedence in _load_texture / egg loads.
        self.resource_manager = None
        self.asset_streaming_system = None
        if ASSETS_AVAILABLE:
            self.resource_manager = ResourceManager(self.world, self)
            self.world.add_system(self.resource_manager)
            self.asset_streaming_system = AssetStreamingSystem(self.world, self.resource_manager)
            self.world.add_system(self.asset_streaming_system)

        # Add systems (RenderSystem now after RM so it can use resolve_asset_path for cartridge mounts)
        self.render_system = RenderSystem(self.world, self, resource_manager=self.resource_manager) # Pass ShowBase + optional RM for asset precedence
        self.world.add_system(self.render_system)

        self.input_system = InputSystem(self.world, self) # Pass ShowBase instance
        self.world.add_system(self.input_system)
        
        self.movement_system = MovementSystem(self.world)
        self.world.add_system(self.movement_system)

        self.cartridge_loader = None
        self.cartridge_context = None
        self.save_state_manager = SaveStateManager(self.world, storage_root=Path("saves"))
        # Built-in provider: persists ECS entities + component data out of the box.
        # Cartridges may register additional providers under their own names.
        self.save_state_manager.register_provider("world", WorldSaveProvider())
        if cartridge_path:
            loaded = self._load_cartridge(cartridge_path, extract_dir)
            if not loaded:
                print("⚠️ Falling back to built-in demo entity")
                self._setup_default_demo()
        else:
            self._setup_default_demo()

        # Game loop task
        self.taskMgr.add(self.update_game, "update_game_task")

    def _request_restart(self):
        """Request a hot restart (works best for cartridges that implement .reset() on their entrypoint)."""
        self._restart_requested = True

    def _request_exit(self):
        """Request a clean exit (bound to ESC and window manager close)."""
        print("\n👋 Exit requested — shutting down cleanly...")
        self._exit_requested = True
        # Best-effort explicit cleanup of collision viz nodes etc. before Panda teardown
        try:
            for system in list(getattr(self.world, "systems", [])):
                if hasattr(system, "cleanup"):
                    system.cleanup()
        except Exception:
            pass
        self.userExit()

    def _do_restart(self):
        """Perform the actual restart work (called from the game task to keep it on the main thread)."""
        print("🔄 Restarting...")
        cartridge_context = getattr(self, "cartridge_context", None)
        entry = getattr(cartridge_context, "entry_instance", None) if cartridge_context else None
        if entry is not None and hasattr(entry, "reset") and callable(getattr(entry, "reset")):
            try:
                entry.reset()
                print("🔁 Cartridge reset complete.")
                return
            except Exception as e:
                print(f"⚠️ Cartridge-provided reset failed: {e} — falling back to entity clear.")
        # Fallback: just nuke entities (collision systems will clean their nodes via hooks).
        # New player etc. will only appear if the cartridge or default demo re-spawns on its own.
        try:
            for eid in list(self.world.entities.keys()):
                self.world.remove_entity(eid)
            print("🧹 Entities cleared (no cartridge .reset handler was available).")
        except Exception as e:
            print(f"Restart fallback error: {e}")

    def _setup_default_demo(self):
        """Spawn the legacy demo entity if no cartridge is provided."""
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
            return

        player_entity = self.world.create_entity("player")  # Named for easier debugging
        # Use center position like minimal.py, and scale that works with our render system
        self.world.add_component(player_entity.id, TransformComponent(x=0.0, y=0.0, scale_x=1.0, scale_y=1.0))
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
                InputBinding(input_type="mouse_button", event_name="mouse1"),  # Left mouse button
                InputBinding(input_type="gamepad_button", event_name="gamepad-face_x")  # 'X' on Xbox, Square on PS
            ],
            "alt_fire": [
                InputBinding(input_type="gamepad_button", event_name="gamepad-rtrigger"),  # Panda uses 'gamepad-rtrigger' for button press
                InputBinding(input_type="gamepad_axis", event_name="rtrigger", axis_direction="positive", axis_threshold=0.1)  # For analog trigger
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

    def _load_cartridge(self, cartridge_path: str, extract_dir: str | None) -> bool:
        cartridge_path = os.path.abspath(cartridge_path)
        extract_path = Path(extract_dir) if extract_dir else None
        try:
            self.cartridge_loader = CartridgeLoader(
                world=self.world,
                base=self,
                resource_manager=self.resource_manager,
                save_state_manager=self.save_state_manager,
                extract_root=extract_path,
            )
            if Path(cartridge_path).is_dir():
                self.cartridge_context = self.cartridge_loader.load_directory(cartridge_path)
            else:
                self.cartridge_context = self.cartridge_loader.load_archive(cartridge_path)
            print(f"🧩 Loaded cartridge '{self.cartridge_context.manifest.name}' v{self.cartridge_context.manifest.version}")
            return True
        except CartridgeError as exc:
            print(f"❌ Failed to load cartridge: {exc}")
            return False

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

        # Handle requested hot-restart (R / F5) before the normal frame.
        if getattr(self, "_restart_requested", False):
            self._restart_requested = False
            self._do_restart()
            return task.cont

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
    parser = argparse.ArgumentParser(description="2D Panda3D Engine Launcher")
    parser.add_argument("--cartridge", help="Path to a cartridge archive", default=None)
    parser.add_argument("--cartridge-extract", help="Directory used for cartridge extraction cache", default=None)
    parser.add_argument(
        "--dev-mode", "--dev",
        action="store_true",
        dest="dev_mode",
        help="Enable developer/debug mode. For cartridges that support it (e.g. tgl_demo), "
             "this turns on visual collision hitboxes with per-layer colors (blue=player, red=enemies, yellow=bullets). "
             "Keys: V=toggle viz, R/F5=restart cartridge, ESC=quit cleanly."
    )
    args = parser.parse_args()

    app = Game(
        cartridge_path=args.cartridge,
        extract_dir=args.cartridge_extract,
        dev_mode=args.dev_mode,
    )
    try:
        app.run()
    except KeyboardInterrupt:
        print("\n🛑 KeyboardInterrupt — requesting clean shutdown...")
        try:
            app.userExit()
        except Exception:
            pass
        # Fast exit: some Panda threads (audio, etc.) can otherwise delay process death for seconds.
        import sys as _sys
        _sys.exit(0)
