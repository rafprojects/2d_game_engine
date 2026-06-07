#!/usr/bin/env python3
"""
Comprehensive Audio System Demo

This demo showcases all features of the 2D Game Engine's audio system:
- Sound effects with different categories
- Background music with transitions
- 3D positional audio
- Dynamic music moods
- Audio controls and volume management

Controls:
- WASD / Arrow Keys: Move player (affects 3D audio)
- 1-4: Play different sound effects
- M: Toggle background music
- N: Next music track
- P: Previous music track
- +/-: Master volume
- Space: Fire sound effect at player position
- C: Change music mood
- R: Random ambient sound
- ESC: Exit demo

Features Demonstrated:
- SoundComponent with multiple sound types
- MusicComponent with playlist management
- AudioListenerComponent for 3D audio
- Dynamic music mood system
- Volume controls and audio mixing
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from direct.showbase.ShowBase import ShowBase
from panda3d.core import Vec2, Vec3
from engine.core.system import World
from engine.core.components.transform_component import TransformComponent
from engine.graphics.components.sprite_component import SpriteComponent
from engine.graphics.systems.render_system import RenderSystem
from engine.input.components.input_component import InputComponent
from engine.input.systems.input_system import InputSystem
from engine.input.input_bindings import InputBinding

# Audio system imports
from engine.audio.audio_manager import AudioManager
from engine.audio.systems.audio_system import AudioSystem
from engine.audio.systems.music_system import MusicSystem
from engine.audio.components.sound_component import SoundComponent, SoundType
from engine.audio.components.music_component import MusicComponent
from engine.audio.components.audio_listener_component import AudioListenerComponent

class AudioDemo(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        print("🎵 Audio System Demo")
        print("=" * 50)
        print("Controls:")
        print("  WASD/Arrows: Move player (3D audio)")
        print("  1-4: Play sound effects")
        print("  M: Toggle music")
        print("  N/P: Next/Previous track")
        print("  +/-: Master volume")
        print("  C: Change music mood")
        print("  R: Random ambient sound")
        print("  Space: Fire sound at position")
        print("=" * 50)

        self.world = World()
        
        # Initialize audio systems
        self.audio_system = AudioSystem(self.world)
        self.music_system = MusicSystem(self.world)
        self.audio_manager = AudioManager(self.world, self.audio_system, self.music_system)
        
        self.world.add_system(self.audio_system)
        self.world.add_system(self.music_system)
        
        # Initialize other systems
        self.render_system = RenderSystem(self.world, self)
        self.world.add_system(self.render_system)
        
        self.input_system = InputSystem(self.world, self)
        self.world.add_system(self.input_system)
        
        # Create demo entities
        self.create_player()
        self.create_music_entity()
        self.create_ambient_sources()
        
        # Demo state
        self.current_mood = "calm"
        self.available_moods = ["calm", "action", "mysterious"]
        
        # Game loop
        self.taskMgr.add(self.update_demo, "update_demo")
        
    def create_player(self):
        """Create player entity with audio listener."""
        self.player = self.world.create_entity("player")
        
        # Transform component
        self.world.add_component(
            self.player.id,
            TransformComponent(position=Vec2(0, 0), scale=Vec2(50, 50))
        )
        
        # Visual component (if assets exist)
        try:
            self.world.add_component(
                self.player.id,
                SpriteComponent(image_path="assets/player.png", layer=1)
            )
        except:
            print("Note: Player sprite not found, creating invisible player")
        
        # Audio listener component
        self.world.add_component(
            self.player.id,
            AudioListenerComponent(
                is_active=True,
                forward_vector=Vec3(0, 1, 0),
                up_vector=Vec3(0, 0, 1)
            )
        )
        
        # Sound component for player sounds
        player_sounds = {
            "jump": "assets/audio/jump.wav",
            "hurt": "assets/audio/hurt.wav",
            "pickup": "assets/audio/pickup.wav",
            "fire": "assets/audio/fire.wav"
        }
        
        self.world.add_component(
            self.player.id,
            SoundComponent(
                sound_files=player_sounds,
                sound_type=SoundType.EFFECT,
                volume=0.8,
                is_3d=False  # Player sounds are typically 2D
            )
        )
        
        # Input component
        input_bindings = {
            "move_left": [InputBinding(input_type="key", event_name="a"),
                         InputBinding(input_type="key", event_name="arrow_left")],
            "move_right": [InputBinding(input_type="key", event_name="d"),
                          InputBinding(input_type="key", event_name="arrow_right")],
            "move_up": [InputBinding(input_type="key", event_name="w"),
                       InputBinding(input_type="key", event_name="arrow_up")],
            "move_down": [InputBinding(input_type="key", event_name="s"),
                         InputBinding(input_type="key", event_name="arrow_down")],
            
            # Audio controls
            "sound1": [InputBinding(input_type="key", event_name="1")],
            "sound2": [InputBinding(input_type="key", event_name="2")],
            "sound3": [InputBinding(input_type="key", event_name="3")],
            "sound4": [InputBinding(input_type="key", event_name="4")],
            "toggle_music": [InputBinding(input_type="key", event_name="m")],
            "next_track": [InputBinding(input_type="key", event_name="n")],
            "prev_track": [InputBinding(input_type="key", event_name="p")],
            "volume_up": [InputBinding(input_type="key", event_name="equals")],
            "volume_down": [InputBinding(input_type="key", event_name="minus")],
            "change_mood": [InputBinding(input_type="key", event_name="c")],
            "random_ambient": [InputBinding(input_type="key", event_name="r")],
            "fire": [InputBinding(input_type="key", event_name="space")],
        }
        
        self.world.add_component(
            self.player.id,
            InputComponent(action_bindings=input_bindings)
        )
        
    def create_music_entity(self):
        """Create entity for background music management."""
        self.music_entity = self.world.create_entity("background_music")
        
        # Music tracks with different moods
        music_files = {
            "calm_track1": "assets/audio/music/calm1.ogg",
            "calm_track2": "assets/audio/music/calm2.ogg",
            "action_track1": "assets/audio/music/action1.ogg",
            "action_track2": "assets/audio/music/action2.ogg",
            "mysterious_track1": "assets/audio/music/mystery1.ogg",
            "mysterious_track2": "assets/audio/music/mystery2.ogg",
        }
        
        music_comp = MusicComponent(
            music_files=music_files,
            volume=0.6,
            loop_current=True,
            auto_play=True,
            fade_duration=3.0
        )
        
        # Set up music moods
        music_comp.music_moods = {
            "calm": ["calm_track1", "calm_track2"],
            "action": ["action_track1", "action_track2"],
            "mysterious": ["mysterious_track1", "mysterious_track2"]
        }
        music_comp.set_mood("calm")
        
        # Create initial playlist
        music_comp.create_playlist(music_comp.music_moods["calm"], shuffle=False)
        
        self.world.add_component(self.music_entity.id, music_comp)
        
        print(f"🎵 Music system initialized with {len(music_files)} tracks")
        print(f"🎵 Available moods: {', '.join(self.available_moods)}")
        
    def create_ambient_sources(self):
        """Create 3D ambient sound sources."""
        ambient_positions = [
            (Vec2(-200, 100), "water", "assets/audio/ambient/water.wav"),
            (Vec2(200, -100), "wind", "assets/audio/ambient/wind.wav"),
            (Vec2(-100, -200), "fire", "assets/audio/ambient/fire.wav"),
            (Vec2(150, 150), "birds", "assets/audio/ambient/birds.wav"),
        ]
        
        self.ambient_entities = []
        
        for position, name, audio_file in ambient_positions:
            entity = self.world.create_entity(f"ambient_{name}")
            
            # Position
            self.world.add_component(
                entity.id,
                TransformComponent(position=position)
            )
            
            # 3D ambient sound
            self.world.add_component(
                entity.id,
                SoundComponent(
                    sound_files={name: audio_file},
                    sound_type=SoundType.AMBIENT,
                    volume=0.5,
                    is_3d=True,
                    max_distance=300.0,
                    loop=True,
                    auto_play=True
                )
            )
            
            self.ambient_entities.append(entity)
            
        print(f"🌍 Created {len(ambient_positions)} 3D ambient sound sources")
        
    def update_demo(self, task):
        """Main demo update loop."""
        dt = globalClock.getDt()
        self.world.update(dt)
        
        # Handle input
        self.handle_input()
        
        # Update player position based on input
        self.update_player_movement(dt)
        
        # Display audio info
        self.display_audio_info()
        
        return task.cont
        
    def handle_input(self):
        """Handle audio-related input."""
        input_comp = self.world.get_component(self.player.id, InputComponent)
        if not input_comp:
            return
            
        # Sound effects
        if input_comp.action_just_pressed.get("sound1"):
            self.audio_system.play_sound(self.player.id, "jump")
            print("🔊 Played jump sound")
            
        if input_comp.action_just_pressed.get("sound2"):
            self.audio_system.play_sound(self.player.id, "hurt")
            print("🔊 Played hurt sound")
            
        if input_comp.action_just_pressed.get("sound3"):
            self.audio_system.play_sound(self.player.id, "pickup")
            print("🔊 Played pickup sound")
            
        if input_comp.action_just_pressed.get("fire"):
            self.audio_system.play_sound(self.player.id, "fire")
            print("🔊 Played fire sound")
            
        # Music controls
        if input_comp.action_just_pressed.get("toggle_music"):
            music_comp = self.world.get_component(self.music_entity.id, MusicComponent)
            if music_comp:
                if music_comp.music_state.name == "PLAYING":
                    self.music_system.stop_music(self.music_entity.id)
                    print("🎵 Music stopped")
                else:
                    if music_comp.playlist:
                        track = music_comp.playlist[music_comp.playlist_index]
                        self.music_system.play_music(self.music_entity.id, track)
                        print(f"🎵 Playing: {track}")
                        
        if input_comp.action_just_pressed.get("next_track"):
            self.next_music_track()
            
        if input_comp.action_just_pressed.get("prev_track"):
            self.prev_music_track()
            
        # Volume controls
        if input_comp.action_just_pressed.get("volume_up"):
            new_volume = min(1.0, self.audio_manager.master_volume + 0.1)
            self.audio_manager.set_master_volume(new_volume)
            print(f"🔊 Master volume: {new_volume:.1f}")
            
        if input_comp.action_just_pressed.get("volume_down"):
            new_volume = max(0.0, self.audio_manager.master_volume - 0.1)
            self.audio_manager.set_master_volume(new_volume)
            print(f"🔊 Master volume: {new_volume:.1f}")
            
        # Mood changes
        if input_comp.action_just_pressed.get("change_mood"):
            self.change_music_mood()
            
        # Random ambient sound
        if input_comp.action_just_pressed.get("random_ambient"):
            self.play_random_ambient()
            
    def update_player_movement(self, dt):
        """Update player position based on input."""
        input_comp = self.world.get_component(self.player.id, InputComponent)
        transform_comp = self.world.get_component(self.player.id, TransformComponent)
        
        if not input_comp or not transform_comp:
            return
            
        move_speed = 200.0  # pixels per second
        movement = Vec2(0, 0)
        
        if input_comp.action_active.get("move_left"):
            movement.x -= move_speed * dt
        if input_comp.action_active.get("move_right"):
            movement.x += move_speed * dt
        if input_comp.action_active.get("move_up"):
            movement.y += move_speed * dt
        if input_comp.action_active.get("move_down"):
            movement.y -= move_speed * dt
            
        if movement.length() > 0:
            transform_comp.position += movement
            
    def next_music_track(self):
        """Switch to next music track."""
        music_comp = self.world.get_component(self.music_entity.id, MusicComponent)
        if music_comp and music_comp.playlist:
            next_index = (music_comp.playlist_index + 1) % len(music_comp.playlist)
            next_track = music_comp.playlist[next_index]
            
            if self.music_system.transition_to_track(music_comp, next_track):
                print(f"🎵 Transitioning to: {next_track}")
            else:
                print("❌ Failed to transition to next track")
                
    def prev_music_track(self):
        """Switch to previous music track."""
        music_comp = self.world.get_component(self.music_entity.id, MusicComponent)
        if music_comp and music_comp.playlist:
            prev_index = (music_comp.playlist_index - 1) % len(music_comp.playlist)
            prev_track = music_comp.playlist[prev_index]
            
            if self.music_system.transition_to_track(music_comp, prev_track):
                print(f"🎵 Transitioning to: {prev_track}")
            else:
                print("❌ Failed to transition to previous track")
                
    def change_music_mood(self):
        """Change to next music mood."""
        current_index = self.available_moods.index(self.current_mood)
        next_index = (current_index + 1) % len(self.available_moods)
        new_mood = self.available_moods[next_index]
        
        music_comp = self.world.get_component(self.music_entity.id, MusicComponent)
        if music_comp:
            music_comp.set_mood(new_mood)
            mood_tracks = music_comp.get_tracks_in_mood(new_mood)
            
            if mood_tracks:
                music_comp.create_playlist(mood_tracks, shuffle=True)
                first_track = mood_tracks[0]
                
                if self.music_system.transition_to_track(music_comp, first_track):
                    self.current_mood = new_mood
                    print(f"🎵 Changed to mood: {new_mood} -> {first_track}")
                else:
                    print(f"❌ Failed to change mood to: {new_mood}")
                    
    def play_random_ambient(self):
        """Play a random ambient sound."""
        import random
        if self.ambient_entities:
            entity = random.choice(self.ambient_entities)
            sound_comp = self.world.get_component(entity.id, SoundComponent)
            if sound_comp:
                sound_names = list(sound_comp.sound_files.keys())
                if sound_names:
                    sound_name = random.choice(sound_names)
                    self.audio_system.play_sound(entity.id, sound_name)
                    print(f"🌍 Played ambient: {sound_name}")
                    
    def display_audio_info(self):
        """Display current audio system information."""
        # This could be expanded to show on-screen info
        pass

if __name__ == '__main__':
    print("🎵 Starting Audio System Demo...")
    print("Note: This demo expects audio files in assets/audio/")
    print("Create placeholder files or modify paths as needed.")
    
    app = AudioDemo()
    app.run()
