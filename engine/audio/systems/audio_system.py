from engine.core.system import System
from engine.graphics.components.transform_component import TransformComponent
from engine.audio.components.sound_component import SoundComponent, SoundType
from engine.audio.components.audio_listener_component import AudioListenerComponent
from panda3d.core import AudioManager, AudioSound, Vec3
from typing import Dict, Optional, List, Tuple
import os

class AudioSystem(System):
    """
    System for managing sound effects and 3D positional audio.
    
    Features:
    - Sound loading and caching
    - 3D positional audio
    - Sound pooling for performance
    - Category-based volume control
    - Distance-based attenuation
    """
    
    def __init__(self, world, audio_manager: Optional[AudioManager] = None):
        super().__init__(world)
        self.audio_manager = audio_manager
        
        # Sound cache and pools
        self.loaded_sounds: Dict[str, AudioSound] = {}
        self.sound_pools: Dict[str, List[AudioSound]] = {}
        
        # 3D Audio state
        self.listener_position = Vec3(0, 0, 0)
        self.listener_forward = Vec3(0, 1, 0)
        self.listener_up = Vec3(0, 0, 1)
        self.listener_velocity = Vec3(0, 0, 0)
        
        # Global audio settings
        self.master_volume = 1.0
        self.category_volumes = {
            SoundType.EFFECT: 1.0,
            SoundType.AMBIENT: 0.8,
            SoundType.VOICE: 1.0,
            SoundType.UI: 0.9
        }
        
        # Performance settings
        self.max_simultaneous_sounds = 32
        self.sound_distance_cutoff = 100.0
        
        # Statistics
        self.sounds_playing = 0
        self.sounds_loaded = 0
        
    def update(self, dt: float):
        """Update the audio system."""
        # Update listener position from AudioListenerComponent
        self._update_listener()
        
        # Update 3D sound positions
        self._update_3d_audio()
        
        # Clean up finished sounds
        self._cleanup_finished_sounds()
        
        # Update sound component states
        self._update_sound_components()
    
    def _update_listener(self):
        """Update 3D audio listener from AudioListenerComponent."""
        # Find active audio listener
        listener_entities = self.world.get_entities_with_components(
            AudioListenerComponent, TransformComponent
        )
        
        for entity in listener_entities:
            listener_comp = self.world.get_component(entity.id, AudioListenerComponent)
            transform_comp = self.world.get_component(entity.id, TransformComponent)
            
            if listener_comp and listener_comp.is_active and transform_comp:
                # Update listener position
                self.listener_position = Vec3(
                    transform_comp.position.x,
                    transform_comp.position.y,
                    0  # 2D games typically have Z=0
                )
                
                # Update orientation
                self.listener_forward = listener_comp.forward_vector
                self.listener_up = listener_comp.up_vector
                self.listener_velocity = listener_comp.velocity
                
                # Update volume settings
                self.master_volume = listener_comp.master_volume
                self.category_volumes[SoundType.EFFECT] = listener_comp.sfx_volume
                self.category_volumes[SoundType.VOICE] = listener_comp.voice_volume
                self.category_volumes[SoundType.UI] = listener_comp.ui_volume
                
                # Set 3D audio properties in Panda3D
                if self.audio_manager:
                    self.audio_manager.set_listener_3d(
                        self.listener_position,
                        self.listener_velocity,
                        self.listener_forward,
                        self.listener_up
                    )
                
                break  # Use first active listener
    
    def _update_3d_audio(self):
        """Update positions of 3D sounds."""
        sound_entities = self.world.get_entities_with_components(
            SoundComponent, TransformComponent
        )
        
        for entity in sound_entities:
            sound_comp = self.world.get_component(entity.id, SoundComponent)
            transform_comp = self.world.get_component(entity.id, TransformComponent)
            
            if sound_comp and sound_comp.is_3d and transform_comp:
                sound_pos = Vec3(
                    transform_comp.position.x,
                    transform_comp.position.y,
                    0
                )
                
                # Update positions of playing sounds
                for sound_name, sound_info in sound_comp.playing_sounds.items():
                    audio_sound = sound_info.get('audio_sound')
                    if audio_sound and hasattr(audio_sound, 'set_3d_attributes'):
                        audio_sound.set_3d_attributes(sound_pos, Vec3(0, 0, 0))
    
    def _cleanup_finished_sounds(self):
        """Remove finished sounds from playing lists."""
        sound_entities = self.world.get_entities_with_components(SoundComponent)
        
        for entity in sound_entities:
            sound_comp = self.world.get_component(entity.id, SoundComponent)
            if not sound_comp:
                continue
                
            finished_sounds = []
            for sound_name, sound_info in sound_comp.playing_sounds.items():
                audio_sound = sound_info.get('audio_sound')
                if audio_sound and audio_sound.status() != AudioSound.PLAYING:
                    finished_sounds.append(sound_name)
            
            for sound_name in finished_sounds:
                del sound_comp.playing_sounds[sound_name]
                self.sounds_playing -= 1
    
    def _update_sound_components(self):
        """Update sound component states."""
        sound_entities = self.world.get_entities_with_components(SoundComponent)
        
        for entity in sound_entities:
            sound_comp = self.world.get_component(entity.id, SoundComponent)
            if not sound_comp:
                continue
            
            # Auto-play if enabled and no sounds playing
            if (sound_comp.auto_play and 
                not sound_comp.playing_sounds and 
                sound_comp.sound_files):
                first_sound = list(sound_comp.sound_files.keys())[0]
                self.play_sound(entity.id, first_sound)
    
    def load_sound(self, file_path: str) -> Optional[AudioSound]:
        """
        Load a sound file and cache it.
        
        Args:
            file_path: Path to the sound file
            
        Returns:
            AudioSound object or None if loading failed
        """
        if file_path in self.loaded_sounds:
            return self.loaded_sounds[file_path]
        
        if not self.audio_manager:
            print(f"Warning: No audio manager available to load {file_path}")
            return None
        
        if not os.path.exists(file_path):
            print(f"Warning: Sound file not found: {file_path}")
            return None
        
        try:
            audio_sound = self.audio_manager.get_sound(file_path)
            if audio_sound:
                self.loaded_sounds[file_path] = audio_sound
                self.sounds_loaded += 1
                return audio_sound
            else:
                print(f"Warning: Failed to load sound: {file_path}")
                return None
        except Exception as e:
            print(f"Error loading sound {file_path}: {e}")
            return None
    
    def play_sound(self, entity_id, sound_name: str, 
                   volume: Optional[float] = None,
                   pitch: Optional[float] = None,
                   loop: Optional[bool] = None) -> bool:
        """
        Play a sound from a SoundComponent.
        
        Args:
            entity_id: Entity with SoundComponent
            sound_name: Name of the sound to play
            volume: Override volume (0.0 to 1.0)
            pitch: Override pitch (0.1 to 4.0)
            loop: Override loop setting
            
        Returns:
            True if sound started playing successfully
        """
        sound_comp = self.world.get_component(entity_id, SoundComponent)
        if not sound_comp:
            return False
        
        if sound_name not in sound_comp.sound_files:
            print(f"Warning: Sound '{sound_name}' not found in component")
            return False
        
        # Check if we're at the limit for simultaneous sounds
        if self.sounds_playing >= self.max_simultaneous_sounds:
            print("Warning: Maximum simultaneous sounds reached")
            return False
        
        file_path = sound_comp.sound_files[sound_name]
        audio_sound = self.load_sound(file_path)
        
        if not audio_sound:
            return False
        
        # Calculate final volume
        final_volume = volume if volume is not None else sound_comp.effective_volume
        final_volume *= self.master_volume
        final_volume *= self.category_volumes.get(sound_comp.sound_type, 1.0)
        
        # Calculate final pitch
        final_pitch = pitch if pitch is not None else sound_comp.pitch
        
        # Calculate loop setting
        should_loop = loop if loop is not None else sound_comp.loop
        
        # Set audio properties
        audio_sound.set_volume(final_volume)
        audio_sound.set_play_rate(final_pitch)
        audio_sound.set_loop(should_loop)
        
        # Handle 3D audio
        if sound_comp.is_3d:
            transform_comp = self.world.get_component(entity_id, TransformComponent)
            if transform_comp:
                sound_pos = Vec3(
                    transform_comp.position.x,
                    transform_comp.position.y,
                    0
                )
                if hasattr(audio_sound, 'set_3d_attributes'):
                    audio_sound.set_3d_attributes(sound_pos, Vec3(0, 0, 0))
        
        # Play the sound
        audio_sound.play()
        
        # Track the playing sound
        sound_comp.playing_sounds[sound_name] = {
            'audio_sound': audio_sound,
            'start_time': 0.0,  # Could track actual time if needed
            'volume': final_volume,
            'pitch': final_pitch
        }
        
        self.sounds_playing += 1
        return True
    
    def stop_sound(self, entity_id, sound_name: str) -> bool:
        """Stop a specific sound."""
        sound_comp = self.world.get_component(entity_id, SoundComponent)
        if not sound_comp or sound_name not in sound_comp.playing_sounds:
            return False
        
        sound_info = sound_comp.playing_sounds[sound_name]
        audio_sound = sound_info.get('audio_sound')
        
        if audio_sound:
            audio_sound.stop()
        
        del sound_comp.playing_sounds[sound_name]
        self.sounds_playing -= 1
        return True
    
    def stop_all_sounds(self, entity_id) -> int:
        """Stop all sounds from an entity. Returns number of sounds stopped."""
        sound_comp = self.world.get_component(entity_id, SoundComponent)
        if not sound_comp:
            return 0
        
        stopped_count = 0
        for sound_name in list(sound_comp.playing_sounds.keys()):
            if self.stop_sound(entity_id, sound_name):
                stopped_count += 1
        
        return stopped_count
    
    def set_master_volume(self, volume: float):
        """Set master volume for all sounds."""
        self.master_volume = max(0.0, min(1.0, volume))
    
    def set_category_volume(self, sound_type: SoundType, volume: float):
        """Set volume for a sound category."""
        self.category_volumes[sound_type] = max(0.0, min(1.0, volume))
    
    def get_stats(self) -> Dict[str, int]:
        """Get audio system statistics."""
        return {
            'sounds_playing': self.sounds_playing,
            'sounds_loaded': self.sounds_loaded,
            'max_simultaneous': self.max_simultaneous_sounds
        }
