from panda3d.core import Vec3
from engine.core.component import Component
from typing import Optional

class AudioListenerComponent(Component):
    """
    Component that defines the audio listener position for 3D audio.
    
    Usually attached to the player or camera entity to provide
    proper 3D audio positioning and orientation.
    """
    
    def __init__(self,
                 is_active: bool = True,
                 forward_vector: Optional[Vec3] = None,
                 up_vector: Optional[Vec3] = None,
                 velocity: Optional[Vec3] = None):
        """
        Initialize AudioListenerComponent.
        
        Args:
            is_active: Whether this listener is currently active
            forward_vector: Direction the listener is facing (for 3D audio)
            up_vector: Up direction for the listener
            velocity: Velocity of the listener (for Doppler effects)
        """
        self.is_active = is_active
        self.forward_vector = forward_vector or Vec3(0, 1, 0)  # Looking forward (Y+)
        self.up_vector = up_vector or Vec3(0, 0, 1)  # Up is Z+
        self.velocity = velocity or Vec3(0, 0, 0)
        
        # Audio settings
        self.master_volume = 1.0
        self.music_volume = 1.0
        self.sfx_volume = 1.0
        self.voice_volume = 1.0
        self.ui_volume = 1.0
        
        # 3D Audio settings
        self.doppler_factor = 1.0  # Strength of Doppler effect
        self.distance_model = "inverse"  # Audio attenuation model
        self.rolloff_factor = 1.0  # How quickly audio fades with distance
        
    def set_master_volume(self, volume: float):
        """Set master volume (affects all audio)."""
        self.master_volume = max(0.0, min(1.0, volume))
    
    def set_category_volume(self, category: str, volume: float):
        """
        Set volume for a specific audio category.
        
        Args:
            category: One of 'music', 'sfx', 'voice', 'ui'
            volume: Volume level (0.0 to 1.0)
        """
        volume = max(0.0, min(1.0, volume))
        
        if category == "music":
            self.music_volume = volume
        elif category == "sfx":
            self.sfx_volume = volume
        elif category == "voice":
            self.voice_volume = volume
        elif category == "ui":
            self.ui_volume = volume
    
    def get_category_volume(self, category: str) -> float:
        """Get volume for a specific audio category."""
        volumes = {
            "music": self.music_volume,
            "sfx": self.sfx_volume,
            "voice": self.voice_volume,
            "ui": self.ui_volume
        }
        return volumes.get(category, 1.0)
    
    def set_orientation(self, forward: Vec3, up: Vec3):
        """Set the listener's orientation."""
        self.forward_vector = forward
        self.up_vector = up
    
    def set_velocity(self, velocity: Vec3):
        """Set the listener's velocity for Doppler effects."""
        self.velocity = velocity
    
    def activate(self):
        """Activate this audio listener."""
        self.is_active = True
    
    def deactivate(self):
        """Deactivate this audio listener."""
        self.is_active = False
