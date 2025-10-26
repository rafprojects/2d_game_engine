from typing import Optional, Dict, List

from engine.core.component import Component
from engine.audio.typesg.music_type import MusicState, MusicTransition

class MusicComponent(Component):
    """
    Component for background music and long-form audio.
    
    Features:
    - Music playlist management
    - Smooth transitions between tracks
    - Looping and queueing
    - Volume fading effects
    - Music mood/intensity system
    """
    
    def __init__(self,
                 music_files: Optional[Dict[str, str]] = None,
                 volume: float = 0.7,
                 loop_current: bool = True,
                 auto_play: bool = False,
                 fade_duration: float = 2.0):
        """
        Initialize MusicComponent.
        
        Args:
            music_files: Dictionary mapping music names to file paths
            volume: Base volume for music (0.0 to 1.0)
            loop_current: Whether current track should loop
            auto_play: Whether to start playing immediately
            fade_duration: Default duration for fade transitions
        """
        self.music_files = music_files or {}
        self.volume = max(0.0, min(1.0, volume))
        self.loop_current = loop_current
        self.auto_play = auto_play
        self.fade_duration = fade_duration
        
        # Playback state
        self.current_track = None
        self.music_state = MusicState.STOPPED
        self.current_volume = 0.0
        self.target_volume = self.volume
        
        # Playlist management
        self.playlist = []
        self.playlist_index = 0
        self.shuffle_enabled = False
        self.repeat_playlist = True
        
        # Transition system
        self.transition_type = MusicTransition.CROSSFADE
        self.fade_timer = 0.0
        self.is_transitioning = False
        self.next_track = None
        
        # Mood system for dynamic music
        self.music_moods = {}  # mood_name -> list of track names
        self.current_mood = None
        self.mood_transition_probability = 0.1  # Chance to switch tracks within mood
        
        # Runtime state
        self.loaded_music = {}  # Track name -> Panda3D AudioSound object
        self.is_muted = False
        
    def add_music(self, name: str, file_path: str, mood: Optional[str] = None):
        """
        Add a music track.
        
        Args:
            name: Track identifier
            file_path: Path to music file
            mood: Optional mood category for dynamic music
        """
        self.music_files[name] = file_path
        
        if mood:
            if mood not in self.music_moods:
                self.music_moods[mood] = []
            self.music_moods[mood].append(name)
    
    def create_playlist(self, track_names: List[str], shuffle: bool = False):
        """Create a playlist from track names."""
        self.playlist = track_names.copy()
        self.shuffle_enabled = shuffle
        self.playlist_index = 0
        
        if shuffle:
            import random
            random.shuffle(self.playlist)
    
    def add_to_playlist(self, track_name: str):
        """Add a track to the current playlist."""
        if track_name in self.music_files:
            self.playlist.append(track_name)
    
    def set_mood(self, mood: str):
        """
        Set the current music mood for dynamic music selection.
        
        Args:
            mood: Mood name (must exist in music_moods)
        """
        if mood in self.music_moods:
            self.current_mood = mood
    
    def get_available_moods(self) -> List[str]:
        """Get list of available music moods."""
        return list(self.music_moods.keys())
    
    def get_tracks_in_mood(self, mood: str) -> List[str]:
        """Get list of tracks in a specific mood."""
        return self.music_moods.get(mood, [])
    
    def set_volume(self, volume: float, fade: bool = True):
        """
        Set music volume.
        
        Args:
            volume: Target volume (0.0 to 1.0)
            fade: Whether to fade to the new volume
        """
        self.volume = max(0.0, min(1.0, volume))
        self.target_volume = self.volume
        
        if not fade:
            self.current_volume = self.volume
    
    def mute(self):
        """Mute the music."""
        self.is_muted = True
        self.target_volume = 0.0
    
    def unmute(self):
        """Unmute the music."""
        self.is_muted = False
        self.target_volume = self.volume
    
    def set_transition_type(self, transition: MusicTransition):
        """Set the type of transition between tracks."""
        self.transition_type = transition
    
    def next_track_in_playlist(self) -> Optional[str]:
        """Get the next track in the playlist."""
        if not self.playlist:
            return None
            
        if self.shuffle_enabled:
            import random
            return random.choice(self.playlist)
        else:
            self.playlist_index = (self.playlist_index + 1) % len(self.playlist)
            return self.playlist[self.playlist_index]
    
    def should_transition_mood(self) -> bool:
        """Check if music should transition within current mood."""
        if not self.current_mood or not self.music_moods.get(self.current_mood):
            return False
            
        import random
        return random.random() < self.mood_transition_probability
    
    def get_mood_track(self) -> Optional[str]:
        """Get a random track from the current mood."""
        if not self.current_mood:
            return None
            
        mood_tracks = self.music_moods.get(self.current_mood, [])
        if not mood_tracks:
            return None
            
        import random
        return random.choice(mood_tracks)
