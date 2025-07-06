from engine.core.system import System
from engine.audio.components.music_component import MusicComponent, MusicState, MusicTransition
from panda3d.core import AudioManager, AudioSound
from typing import Dict, Optional
import os
import random

class MusicSystem(System):
    """
    System for managing background music and long-form audio.
    
    Features:
    - Music playlist management
    - Smooth transitions between tracks
    - Dynamic music based on game state/mood
    - Volume fading and crossfading
    - Music streaming and memory management
    """
    
    def __init__(self, world, audio_manager: Optional[AudioManager] = None):
        super().__init__(world)
        self.audio_manager = audio_manager
        
        # Music cache
        self.loaded_music: Dict[str, AudioSound] = {}
        
        # Global music state
        self.current_music_entity = None
        self.global_music_volume = 1.0
        self.music_enabled = True
        
        # Fade system
        self.fade_timer = 0.0
        self.fade_duration = 2.0
        self.fade_start_volume = 0.0
        self.fade_target_volume = 1.0
        
        # Statistics
        self.tracks_loaded = 0
        self.transitions_performed = 0
    
    def update(self, dt: float):
        """Update the music system."""
        music_entities = self.world.get_entities_with_components(MusicComponent)
        
        for entity in music_entities:
            music_comp = self.world.get_component(entity.id, MusicComponent)
            if not music_comp:
                continue
            
            # Update music component state
            self._update_music_component(music_comp, dt)
            
            # Handle music transitions
            if music_comp.is_transitioning:
                self._update_transition(music_comp, dt)
            
            # Check for automatic track changes
            self._check_auto_progression(music_comp)
    
    def _update_music_component(self, music_comp: MusicComponent, dt: float):
        """Update a single music component."""
        # Update volume fading
        if music_comp.current_volume != music_comp.target_volume:
            fade_speed = 1.0 / music_comp.fade_duration if music_comp.fade_duration > 0 else float('inf')
            volume_diff = music_comp.target_volume - music_comp.current_volume
            
            if abs(volume_diff) < fade_speed * dt:
                music_comp.current_volume = music_comp.target_volume
            else:
                music_comp.current_volume += fade_speed * dt * (1 if volume_diff > 0 else -1)
            
            # Update actual audio volume
            if music_comp.current_track and music_comp.current_track in music_comp.loaded_music:
                audio_sound = music_comp.loaded_music[music_comp.current_track]
                final_volume = music_comp.current_volume * self.global_music_volume
                audio_sound.set_volume(final_volume)
        
        # Update music state based on playback
        if music_comp.current_track and music_comp.current_track in music_comp.loaded_music:
            audio_sound = music_comp.loaded_music[music_comp.current_track]
            
            if music_comp.music_state == MusicState.PLAYING:
                if audio_sound.status() != AudioSound.PLAYING:
                    # Track finished, handle progression
                    self._handle_track_finished(music_comp)
            elif music_comp.music_state == MusicState.FADING_OUT:
                if music_comp.current_volume <= 0.01:
                    music_comp.music_state = MusicState.STOPPED
                    audio_sound.stop()
    
    def _update_transition(self, music_comp: MusicComponent, dt: float):
        """Update music transition."""
        music_comp.fade_timer += dt
        
        if music_comp.fade_timer >= music_comp.fade_duration:
            # Transition complete
            self._complete_transition(music_comp)
    
    def _handle_track_finished(self, music_comp: MusicComponent):
        """Handle when a music track finishes playing."""
        if music_comp.loop_current:
            # Restart current track
            self._play_track(music_comp, music_comp.current_track)
        elif music_comp.playlist and music_comp.repeat_playlist:
            # Move to next track in playlist
            next_track = music_comp.next_track_in_playlist()
            if next_track:
                self.transition_to_track(music_comp, next_track)
        elif music_comp.current_mood:
            # Dynamic music: pick new track from current mood
            mood_track = music_comp.get_mood_track()
            if mood_track and mood_track != music_comp.current_track:
                self.transition_to_track(music_comp, mood_track)
        else:
            # No more music to play
            music_comp.music_state = MusicState.STOPPED
    
    def _check_auto_progression(self, music_comp: MusicComponent):
        """Check if music should automatically progress to next track."""
        if (music_comp.music_state == MusicState.PLAYING and 
            music_comp.current_mood and 
            music_comp.should_transition_mood()):
            
            mood_track = music_comp.get_mood_track()
            if mood_track and mood_track != music_comp.current_track:
                self.transition_to_track(music_comp, mood_track)
    
    def _complete_transition(self, music_comp: MusicComponent):
        """Complete a music transition."""
        if music_comp.next_track:
            # Stop current track
            if (music_comp.current_track and 
                music_comp.current_track in music_comp.loaded_music):
                music_comp.loaded_music[music_comp.current_track].stop()
            
            # Start next track
            self._play_track(music_comp, music_comp.next_track)
            music_comp.current_track = music_comp.next_track
            music_comp.next_track = None
        
        music_comp.is_transitioning = False
        music_comp.fade_timer = 0.0
        self.transitions_performed += 1
    
    def load_music(self, file_path: str) -> Optional[AudioSound]:
        """Load a music file."""
        if file_path in self.loaded_music:
            return self.loaded_music[file_path]
        
        if not self.audio_manager:
            print(f"Warning: No audio manager available to load {file_path}")
            return None
        
        if not os.path.exists(file_path):
            print(f"Warning: Music file not found: {file_path}")
            return None
        
        try:
            audio_sound = self.audio_manager.get_sound(file_path)
            if audio_sound:
                self.loaded_music[file_path] = audio_sound
                self.tracks_loaded += 1
                return audio_sound
            else:
                print(f"Warning: Failed to load music: {file_path}")
                return None
        except Exception as e:
            print(f"Error loading music {file_path}: {e}")
            return None
    
    def _play_track(self, music_comp: MusicComponent, track_name: str) -> bool:
        """Start playing a music track."""
        if track_name not in music_comp.music_files:
            print(f"Warning: Music track '{track_name}' not found")
            return False
        
        file_path = music_comp.music_files[track_name]
        audio_sound = self.load_music(file_path)
        
        if not audio_sound:
            return False
        
        # Store loaded music in component
        music_comp.loaded_music[track_name] = audio_sound
        
        # Set properties
        final_volume = music_comp.current_volume * self.global_music_volume
        audio_sound.set_volume(final_volume)
        audio_sound.set_loop(music_comp.loop_current)
        
        # Start playback
        audio_sound.play()
        music_comp.music_state = MusicState.PLAYING
        
        return True
    
    def play_music(self, entity_id, track_name: str) -> bool:
        """Start playing a music track immediately."""
        music_comp = self.world.get_component(entity_id, MusicComponent)
        if not music_comp:
            return False
        
        # Stop current music
        self.stop_music(entity_id)
        
        # Start new track
        if self._play_track(music_comp, track_name):
            music_comp.current_track = track_name
            music_comp.target_volume = music_comp.volume
            self.current_music_entity = entity_id
            return True
        
        return False
    
    def transition_to_track(self, music_comp: MusicComponent, track_name: str):
        """Transition to a new music track using the configured transition type."""
        if track_name not in music_comp.music_files:
            print(f"Warning: Cannot transition to unknown track: {track_name}")
            return
        
        if music_comp.transition_type == MusicTransition.IMMEDIATE:
            # Immediate switch
            if music_comp.current_track and music_comp.current_track in music_comp.loaded_music:
                music_comp.loaded_music[music_comp.current_track].stop()
            self._play_track(music_comp, track_name)
            music_comp.current_track = track_name
            
        elif music_comp.transition_type == MusicTransition.FADE_OUT_IN:
            # Fade out current, then fade in new
            music_comp.next_track = track_name
            music_comp.target_volume = 0.0
            music_comp.is_transitioning = True
            music_comp.fade_timer = 0.0
            
        elif music_comp.transition_type == MusicTransition.CROSSFADE:
            # Crossfade (simplified - could be enhanced)
            music_comp.next_track = track_name
            music_comp.target_volume = 0.0
            music_comp.is_transitioning = True
            music_comp.fade_timer = 0.0
    
    def stop_music(self, entity_id) -> bool:
        """Stop music playback."""
        music_comp = self.world.get_component(entity_id, MusicComponent)
        if not music_comp:
            return False
        
        if music_comp.current_track and music_comp.current_track in music_comp.loaded_music:
            music_comp.loaded_music[music_comp.current_track].stop()
        
        music_comp.music_state = MusicState.STOPPED
        music_comp.current_track = None
        music_comp.is_transitioning = False
        
        return True
    
    def pause_music(self, entity_id) -> bool:
        """Pause music playback."""
        music_comp = self.world.get_component(entity_id, MusicComponent)
        if not music_comp:
            return False
        
        if (music_comp.current_track and 
            music_comp.current_track in music_comp.loaded_music):
            audio_sound = music_comp.loaded_music[music_comp.current_track]
            if audio_sound.status() == AudioSound.PLAYING:
                # Panda3D doesn't have pause, so we'll stop and remember position
                music_comp.music_state = MusicState.PAUSED
                # Note: For full pause/resume, you'd need to track playback position
                return True
        
        return False
    
    def resume_music(self, entity_id) -> bool:
        """Resume paused music."""
        music_comp = self.world.get_component(entity_id, MusicComponent)
        if not music_comp or music_comp.music_state != MusicState.PAUSED:
            return False
        
        if music_comp.current_track:
            return self._play_track(music_comp, music_comp.current_track)
        
        return False
    
    def set_global_music_volume(self, volume: float):
        """Set global music volume."""
        self.global_music_volume = max(0.0, min(1.0, volume))
    
    def enable_music(self, enabled: bool):
        """Enable or disable music globally."""
        self.music_enabled = enabled
        if not enabled:
            # Stop all music
            music_entities = self.world.get_entities_with_components(MusicComponent)
            for entity in music_entities:
                self.stop_music(entity.id)
    
    def get_stats(self) -> Dict[str, int]:
        """Get music system statistics."""
        return {
            'tracks_loaded': self.tracks_loaded,
            'transitions_performed': self.transitions_performed,
            'music_enabled': self.music_enabled
        }
