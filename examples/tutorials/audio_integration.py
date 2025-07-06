#!/usr/bin/env python3
"""
Audio Integration Tutorial

Step-by-step tutorial showing how to integrate audio into your game.
This tutorial builds a simple example with sound effects and background music.

Learning Objectives:
- Set up the audio system
- Add sound effects to game entities
- Implement background music
- Use 3D positional audio
- Handle audio controls and volume
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from direct.showbase.ShowBase import ShowBase
from direct.showbase.ShowBaseGlobal import globalClock
from panda3d.core import Vec2, Vec3
from engine.core.system import World
from engine.core.components.transform_component import TransformComponent
from engine.graphics.components.sprite_component import SpriteComponent
from engine.graphics.systems.render_system import RenderSystem
from engine.input.components.input_component import InputComponent
from engine.input.systems.input_system import InputSystem
from engine.input.input_bindings import InputBinding

# Step 1: Import Audio Components
from engine.audio.audio_manager import AudioManager
from engine.audio.systems.audio_system import AudioSystem
from engine.audio.systems.music_system import MusicSystem
from engine.audio.components.sound_component import SoundComponent, SoundType
from engine.audio.components.music_component import MusicComponent
from engine.audio.components.audio_listener_component import AudioListenerComponent

class AudioTutorial(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        print("🎓 Audio Integration Tutorial")
        print("=" * 40)
        
        # Step 2: Initialize the World and Core Systems
        self.world = World()
        
        # Graphics system
        self.render_system = RenderSystem(self.world, self)
        self.world.add_system(self.render_system)
        
        # Input system
        self.input_system = InputSystem(self.world, self)
        self.world.add_system(self.input_system)
        
        # Step 3: Initialize Audio Systems
        print("Step 1: Setting up audio systems...")
        self.setup_audio_systems()
        
        # Step 4: Create Game Entities with Audio
        print("Step 2: Creating entities with audio...")
        self.create_player_with_audio()
        self.create_background_music()
        self.create_ambient_sounds()
        
        # Step 5: Set up Controls
        print("Step 3: Setting up audio controls...")
        self.print_controls()
        
        # Game loop
        self.taskMgr.add(self.update_tutorial, "update_tutorial")
        print("✅ Audio tutorial ready!")
        
    def setup_audio_systems(self):
        """Step 3: Initialize the audio systems"""
        # Create audio systems
        self.audio_system = AudioSystem(self.world)
        self.music_system = MusicSystem(self.world)
        
        # Create audio manager for high-level operations
        self.audio_manager = AudioManager(
            self.world, 
            self.audio_system, 
            self.music_system
        )
        
        # Add systems to world (important!)
        self.world.add_system(self.audio_system)
        self.world.add_system(self.music_system)
        
        print("  ✅ Audio systems initialized")
        
    def create_player_with_audio(self):
        """Step 4: Create player entity with sound effects and audio listener"""
        # Create player entity
        self.player = self.world.create_entity("player")
        
        # Add transform component (for position)
        self.world.add_component(
            self.player.id,
            TransformComponent(position=Vec2(0, 0), scale=Vec2(50, 50))
        )
        
        # Try to add visual component (optional if sprite exists)
        try:
            self.world.add_component(
                self.player.id,
                SpriteComponent(image_path="assets/player.png", layer=1)
            )
            print("  ✅ Player sprite loaded")
        except Exception:
            print("  ⚠️  Player sprite not found (continuing without visual)")
        
        # Step 4a: Add Audio Listener Component
        # This makes the player the "ears" for 3D audio
        audio_listener = AudioListenerComponent(
            is_active=True,
            forward_vector=Vec3(0, 1, 0),  # Looking forward
            up_vector=Vec3(0, 0, 1)        # Up is Z direction
        )
        self.world.add_component(self.player.id, audio_listener)
        print("  ✅ Audio listener added to player")
        
        # Step 4b: Add Sound Component for Player Actions
        # Create a dictionary of sound effects
        player_sounds = {
            "jump": "assets/audio/jump.wav",
            "land": "assets/audio/land.wav", 
            "hurt": "assets/audio/hurt.wav",
            "pickup": "assets/audio/pickup.wav"
        }
        
        sound_component = SoundComponent(
            sound_files=player_sounds,
            sound_type=SoundType.EFFECT,  # This is a sound effect
            volume=0.8,                   # 80% volume
            is_3d=False,                  # Player sounds are typically 2D
            auto_play=False               # Don't auto-play
        )
        self.world.add_component(self.player.id, sound_component)
        print("  ✅ Player sound effects added")
        
        # Step 4c: Add Input Component for Controls
        input_bindings = {
            "move_left": [InputBinding(input_type="key", event_name="a")],
            "move_right": [InputBinding(input_type="key", event_name="d")],
            "move_up": [InputBinding(input_type="key", event_name="w")],
            "move_down": [InputBinding(input_type="key", event_name="s")],
            "jump": [InputBinding(input_type="key", event_name="space")],
            "hurt": [InputBinding(input_type="key", event_name="h")],
            "pickup": [InputBinding(input_type="key", event_name="p")],
            "toggle_music": [InputBinding(input_type="key", event_name="m")],
            "volume_up": [InputBinding(input_type="key", event_name="equals")],
            "volume_down": [InputBinding(input_type="key", event_name="minus")],
        }
        
        input_component = InputComponent(action_bindings=input_bindings)
        self.world.add_component(self.player.id, input_component)
        print("  ✅ Player input controls added")
        
    def create_background_music(self):
        """Step 5: Create background music entity"""
        # Create a dedicated entity for music
        self.music_entity = self.world.create_entity("background_music")
        
        # Define music tracks
        music_tracks = {
            "menu": "assets/audio/music/menu.ogg",
            "gameplay": "assets/audio/music/gameplay.ogg",
            "victory": "assets/audio/music/victory.ogg"
        }
        
        # Create music component
        music_component = MusicComponent(
            music_files=music_tracks,
            volume=0.5,                    # 50% volume for background music
            loop_current=True,             # Loop the current track
            auto_play=True,                # Start playing automatically
            fade_duration=2.0              # 2-second fade transitions
        )
        
        # Set up a simple playlist
        music_component.create_playlist(["menu", "gameplay"], shuffle=False)
        
        self.world.add_component(self.music_entity.id, music_component)
        print("  ✅ Background music system created")
        
    def create_ambient_sounds(self):
        """Step 6: Create 3D ambient sound sources"""
        # Create ambient sound sources at different positions
        ambient_sources = [
            {
                "name": "fountain",
                "position": Vec2(-150, 100),
                "sound_file": "assets/audio/ambient/water.wav",
                "volume": 0.6
            },
            {
                "name": "wind", 
                "position": Vec2(200, -50),
                "sound_file": "assets/audio/ambient/wind.wav",
                "volume": 0.4
            }
        ]
        
        self.ambient_entities = []
        
        for source in ambient_sources:
            # Create entity
            entity = self.world.create_entity(f"ambient_{source['name']}")
            
            # Add position
            self.world.add_component(
                entity.id,
                TransformComponent(position=source["position"])
            )
            
            # Add 3D sound component
            sound_component = SoundComponent(
                sound_files={source["name"]: source["sound_file"]},
                sound_type=SoundType.AMBIENT,
                volume=source["volume"],
                is_3d=True,                    # Enable 3D positioning
                max_distance=250.0,            # Audio fades out beyond this distance
                loop=True,                     # Ambient sounds typically loop
                auto_play=True                 # Start playing automatically
            )
            
            self.world.add_component(entity.id, sound_component)
            self.ambient_entities.append(entity)
            
        print(f"  ✅ Created {len(ambient_sources)} 3D ambient sound sources")
        
    def print_controls(self):
        """Display the tutorial controls"""
        print("\\nControls:")
        print("  WASD - Move player (affects 3D audio positioning)")
        print("  Space - Jump sound")
        print("  H - Hurt sound") 
        print("  P - Pickup sound")
        print("  M - Toggle background music")
        print("  +/- - Adjust master volume")
        print("\\nMove around to hear 3D audio effects!")
        
    def update_tutorial(self, task):
        """Main tutorial update loop"""
        dt = globalClock.getDt()
        
        # Update all systems
        self.world.update(dt)
        
        # Handle input
        self.handle_audio_input()
        
        # Update player movement
        self.update_player_movement(dt)
        
        return task.cont
        
    def handle_audio_input(self):
        """Handle audio-related input"""
        input_comp = self.world.get_component(self.player.id, InputComponent)
        if not input_comp:
            return
            
        # Sound effect triggers
        if input_comp.action_just_pressed.get("jump"):
            success = self.audio_system.play_sound(self.player.id, "jump")
            if success:
                print("🔊 Jump!")
            else:
                print("❌ Jump sound not available")
                
        if input_comp.action_just_pressed.get("hurt"):
            success = self.audio_system.play_sound(self.player.id, "hurt") 
            if success:
                print("🔊 Ouch!")
            else:
                print("❌ Hurt sound not available")
                
        if input_comp.action_just_pressed.get("pickup"):
            success = self.audio_system.play_sound(self.player.id, "pickup")
            if success:
                print("🔊 Item picked up!")
            else:
                print("❌ Pickup sound not available")
        
        # Music controls
        if input_comp.action_just_pressed.get("toggle_music"):
            music_comp = self.world.get_component(self.music_entity.id, MusicComponent)
            if music_comp:
                if music_comp.music_state.name == "PLAYING":
                    self.music_system.stop_music(self.music_entity.id)
                    print("🎵 Music stopped")
                else:
                    # Start first track in playlist
                    if music_comp.playlist:
                        track = music_comp.playlist[0]
                        self.music_system.play_music(self.music_entity.id, track)
                        print(f"🎵 Playing: {track}")
        
        # Volume controls
        if input_comp.action_just_pressed.get("volume_up"):
            new_volume = min(1.0, self.audio_manager.master_volume + 0.1)
            self.audio_manager.set_master_volume(new_volume)
            print(f"🔊 Volume: {new_volume:.1f}")
            
        if input_comp.action_just_pressed.get("volume_down"):
            new_volume = max(0.0, self.audio_manager.master_volume - 0.1)
            self.audio_manager.set_master_volume(new_volume)
            print(f"🔊 Volume: {new_volume:.1f}")
            
    def update_player_movement(self, dt):
        """Update player position based on input"""
        input_comp = self.world.get_component(self.player.id, InputComponent)
        transform_comp = self.world.get_component(self.player.id, TransformComponent)
        
        if not input_comp or not transform_comp:
            return
            
        # Movement speed
        speed = 150.0  # pixels per second
        movement = Vec2(0, 0)
        
        # Check input states
        if input_comp.action_active.get("move_left"):
            movement.x -= speed * dt
        if input_comp.action_active.get("move_right"):
            movement.x += speed * dt
        if input_comp.action_active.get("move_up"):
            movement.y += speed * dt
        if input_comp.action_active.get("move_down"):
            movement.y -= speed * dt
            
        # Apply movement
        if movement.length() > 0:
            old_pos = transform_comp.position
            transform_comp.position += movement
            
            # Show position change for 3D audio demonstration
            if abs(old_pos.x - transform_comp.position.x) > 10 or abs(old_pos.y - transform_comp.position.y) > 10:
                print(f"📍 Player position: ({transform_comp.position.x:.0f}, {transform_comp.position.y:.0f})")

if __name__ == '__main__':
    print("🎓 Starting Audio Integration Tutorial...")
    print("This tutorial demonstrates the complete audio system integration.")
    print("\\nNote: Audio files are expected in assets/audio/")
    print("If files are missing, you'll see warnings but the tutorial will continue.")
    print("\\n" + "="*60)
    
    app = AudioTutorial()
    app.run()
