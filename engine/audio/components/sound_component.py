from panda3d.core import Vec3
from engine.core.component import Component
from typing import Dict, List, Optional
from enum import Enum
import uuid

class SoundType(Enum):
    """Types of sound effects supported."""
    EFFECT = "effect"      # Short sound effects (gunshots, jumps, etc.)
    AMBIENT = "ambient"    # Looping ambient sounds (rain, wind, etc.)
    VOICE = "voice"        # Voice lines and speech
    UI = "ui"             # User interface sounds (clicks, beeps, etc.)

class SoundComponent(Component):
    """
    Component for sound effects and short audio clips.
    
    Supports:
    - Multiple sound files per component
    - 3D positional audio
    - Volume and pitch control
    - Sound pools for performance
    - Category-based audio management
    """
    
    def __init__(self, 
                 sound_files: Optional[Dict[str, str]] = None,
                 sound_type: SoundType = SoundType.EFFECT,
                 volume: float = 1.0,
                 pitch: float = 1.0,
                 is_3d: bool = False,
                 max_distance: float = 100.0,
                 loop: bool = False,
                 auto_play: bool = False):
        """
        Initialize SoundComponent.
        
        Args:
            sound_files: Dictionary mapping sound names to file paths
            sound_type: Category of sound for audio management
            volume: Base volume (0.0 to 1.0)
            pitch: Pitch multiplier (0.5 = half speed, 2.0 = double speed)
            is_3d: Whether to use 3D positional audio
            max_distance: Maximum distance for 3D audio attenuation
            loop: Whether sounds should loop by default
            auto_play: Whether to auto-play the first sound on component creation
        """
        self.sound_files = sound_files or {}
        self.sound_type = sound_type
        self.volume = max(0.0, min(1.0, volume))
        self.pitch = max(0.1, min(4.0, pitch))
        self.is_3d = is_3d
        self.max_distance = max_distance
        self.loop = loop
        self.auto_play = auto_play
        
        # Runtime state
        self.loaded_sounds = {}  # Sound name -> Panda3D AudioSound object
        self.playing_sounds = {}  # Sound name -> playback info
        self.is_muted = False
        self.effective_volume = self.volume
        
        # Performance optimization
        self.preload_sounds = True
        self.sound_pool_size = 3  # Number of identical sounds that can play simultaneously
    
    def add_sound(self, name: str, file_path: str):
        """Add a sound file to this component."""
        self.sound_files[name] = file_path
    
    def remove_sound(self, name: str):
        """Remove a sound from this component."""
        if name in self.sound_files:
            del self.sound_files[name]
        if name in self.loaded_sounds:
            del self.loaded_sounds[name]
        if name in self.playing_sounds:
            del self.playing_sounds[name]
    
    def set_volume(self, volume: float):
        """Set component volume (0.0 to 1.0)."""
        self.volume = max(0.0, min(1.0, volume))
        self._update_effective_volume()
    
    def set_pitch(self, pitch: float):
        """Set component pitch (0.1 to 4.0)."""
        self.pitch = max(0.1, min(4.0, pitch))
    
    def mute(self):
        """Mute all sounds in this component."""
        self.is_muted = True
        self._update_effective_volume()
    
    def unmute(self):
        """Unmute all sounds in this component."""
        self.is_muted = False
        self._update_effective_volume()
    
    def _update_effective_volume(self):
        """Update the effective volume based on mute state."""
        self.effective_volume = 0.0 if self.is_muted else self.volume
    
    def get_sound_names(self) -> List[str]:
        """Get list of available sound names."""
        return list(self.sound_files.keys())
    
    def is_playing(self, sound_name: Optional[str] = None) -> bool:
        """
        Check if sounds are playing.
        
        Args:
            sound_name: Specific sound to check, or None to check if any sound is playing
            
        Returns:
            True if the specified sound (or any sound) is playing
        """
        if sound_name:
            return sound_name in self.playing_sounds
        return len(self.playing_sounds) > 0
