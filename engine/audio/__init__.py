"""
Audio Module for the 2D Game Engine

This module provides comprehensive audio functionality including:
- Sound effects management
- Background music system
- 3D positional audio
- Dynamic music based on game state
- Volume control and mixing

Main Components:
- AudioManager: High-level interface for audio operations
- AudioSystem: Handles sound effects and 3D audio
- MusicSystem: Manages background music and playlists
- Components: SoundComponent, MusicComponent, AudioListenerComponent
"""

from .audio_manager import AudioManager
from .components.sound_component import SoundComponent, SoundType
from .components.music_component import MusicComponent, MusicState, MusicTransition
from .components.audio_listener_component import AudioListenerComponent
from .systems.audio_system import AudioSystem
from .systems.music_system import MusicSystem

__all__ = [
    'AudioManager',
    'AudioSystem',
    'MusicSystem',
    'SoundComponent',
    'MusicComponent', 
    'AudioListenerComponent',
    'SoundType',
    'MusicState',
    'MusicTransition'
]
