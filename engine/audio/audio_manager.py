from typing import Dict, Optional, List
from engine.audio.components.sound_component import SoundType
from engine.audio.components.music_component import MusicComponent
import os

class AudioManager:
    """
    High-level audio manager for the game engine.
    
    Provides simplified interface for common audio operations
    and manages global audio state.
    """
    
    def __init__(self, world, audio_system, music_system):
        self.world = world
        self.audio_system = audio_system
        self.music_system = music_system
        
        # Global settings
        self.master_volume = 1.0
        self.music_volume = 1.0
        self.sfx_volume = 1.0
        
        # Audio entity for global music
        self.global_music_entity = None
        
    def initialize_global_music_entity(self):
        """Create a global entity for music management."""
        if not self.global_music_entity:
            self.global_music_entity = self.world.create_entity("global_music")
            music_comp = MusicComponent(
                volume=self.music_volume,
                auto_play=False,
                fade_duration=2.0
            )
            self.world.add_component(self.global_music_entity.id, music_comp)
    
    def play_sound(self, file_path: str, 
                   sound_type: SoundType = SoundType.EFFECT,
                   volume: float = 1.0,
                   pitch: float = 1.0,
                   loop: bool = False) -> bool:
        """
        Play a one-shot sound effect.
        
        Creates a temporary entity with SoundComponent for the sound.
        """
        from engine.audio.components.sound_component import SoundComponent
        
        # Create temporary entity for the sound
        sound_entity = self.world.create_entity("temp_sound")
        
        sound_comp = SoundComponent(
            sound_files={"temp_sound": file_path},
            sound_type=sound_type,
            volume=volume,
            pitch=pitch,
            loop=loop,
            auto_play=True
        )
        
        self.world.add_component(sound_entity.id, sound_comp)
        
        # The AudioSystem will handle playing the sound
        success = self.audio_system.play_sound(sound_entity.id, "temp_sound")
        
        # Clean up entity if not looping (looping sounds need manual cleanup)
        if not loop:
            # Schedule entity removal after sound finishes
            # This would need a more sophisticated cleanup system in practice
            pass
        
        return success
    
    def play_music(self, file_path: str, loop: bool = True, fade_in: bool = True) -> bool:
        """Play background music."""
        self.initialize_global_music_entity()
        
        music_comp = self.world.get_component(self.global_music_entity.id, MusicComponent)
        if not music_comp:
            return False
        
        # Add the track to the music component
        track_name = os.path.basename(file_path)
        music_comp.add_music(track_name, file_path)
        music_comp.loop_current = loop
        
        if fade_in:
            return self.music_system.transition_to_track(music_comp, track_name)
        else:
            return self.music_system.play_music(self.global_music_entity.id, track_name)
    
    def stop_music(self, fade_out: bool = True) -> bool:
        """Stop background music."""
        if not self.global_music_entity:
            return False
        
        return self.music_system.stop_music(self.global_music_entity.id)
    
    def set_master_volume(self, volume: float):
        """Set master volume for all audio."""
        self.master_volume = max(0.0, min(1.0, volume))
        self.audio_system.set_master_volume(self.master_volume)
        self.music_system.set_global_music_volume(self.master_volume)
    
    def set_music_volume(self, volume: float):
        """Set music volume."""
        self.music_volume = max(0.0, min(1.0, volume))
        self.music_system.set_global_music_volume(self.music_volume)
    
    def set_sfx_volume(self, volume: float):
        """Set sound effects volume."""
        self.sfx_volume = max(0.0, min(1.0, volume))
        self.audio_system.set_category_volume(SoundType.EFFECT, self.sfx_volume)
    
    def add_music_to_playlist(self, file_paths: List[str], shuffle: bool = False):
        """Add multiple tracks to the music playlist."""
        self.initialize_global_music_entity()
        
        music_comp = self.world.get_component(self.global_music_entity.id, MusicComponent)
        if not music_comp:
            return
        
        track_names = []
        for file_path in file_paths:
            track_name = os.path.basename(file_path)
            music_comp.add_music(track_name, file_path)
            track_names.append(track_name)
        
        music_comp.create_playlist(track_names, shuffle)
    
    def create_music_mood(self, mood_name: str, file_paths: List[str]):
        """Create a music mood with associated tracks."""
        self.initialize_global_music_entity()
        
        music_comp = self.world.get_component(self.global_music_entity.id, MusicComponent)
        if not music_comp:
            return
        
        for file_path in file_paths:
            track_name = os.path.basename(file_path)
            music_comp.add_music(track_name, file_path, mood=mood_name)
    
    def set_music_mood(self, mood_name: str):
        """Set the current music mood for dynamic music."""
        if not self.global_music_entity:
            return
        
        music_comp = self.world.get_component(self.global_music_entity.id, MusicComponent)
        if music_comp:
            music_comp.set_mood(mood_name)
    
    def get_audio_stats(self) -> Dict:
        """Get comprehensive audio statistics."""
        stats = {
            'master_volume': self.master_volume,
            'music_volume': self.music_volume,
            'sfx_volume': self.sfx_volume,
            'audio_system': self.audio_system.get_stats(),
            'music_system': self.music_system.get_stats()
        }
        return stats
