"""
NSF (Nintendo Sound Format) Player Integration for 2D Game Engine

This module provides NSF file support for the existing audio system.
NSF files contain the actual sound code from Nintendo games and can play authentic
chiptune music with multiple channels and per-channel control.
"""

from typing import Dict, Optional, List, Any, Callable
from enum import Enum
import threading
import time
import os
from dataclasses import dataclass

from ..core.component import Component
from ..core.system import System


class NSFChannelType(Enum):
    """NSF sound channels available on NES/Famicom."""
    PULSE_1 = 0      # Square wave with duty cycle control
    PULSE_2 = 1      # Square wave with duty cycle control  
    TRIANGLE = 2     # Triangle wave (no volume control on hardware)
    NOISE = 3        # Noise/percussion channel
    DMC = 4          # Delta Modulation Channel (samples)
    EXPANSION = 5    # Additional channels (VRC6, MMC5, etc.)


@dataclass
class NSFChannelState:
    """State of an individual NSF channel."""
    volume: float = 1.0
    muted: bool = False
    frequency: float = 440.0
    duty_cycle: float = 0.5  # For pulse channels
    envelope: float = 1.0
    is_active: bool = False


class MockNSFLibrary:
    """Mock NSF library for demonstration purposes."""
    
    def __init__(self):
        self.loaded = False
        self.current_track = 0
        self.total_tracks = 1
        self.is_playing = False
        self.channels = [NSFChannelState() for _ in range(6)]
        self.playback_thread: Optional[threading.Thread] = None
        self._stop_playback = False
        
    def load_nsf(self, filepath: str) -> bool:
        """Load an NSF file."""
        if not os.path.exists(filepath):
            print(f"🎵 Mock NSF: File not found: {filepath}")
            return False
            
        self.loaded = True
        self.total_tracks = 10  # Most NSF files have multiple tracks
        print(f"🎵 Mock NSF: Loaded {os.path.basename(filepath)} ({self.total_tracks} tracks)")
        return True
        
    def play_track(self, track_number: int) -> bool:
        """Play a specific track."""
        if not self.loaded or track_number >= self.total_tracks:
            return False
            
        self.current_track = track_number
        self.is_playing = True
        self._stop_playback = False
        
        # Simulate channel activity
        self.channels[0].is_active = True  # Pulse 1 - melody
        self.channels[1].is_active = True  # Pulse 2 - harmony
        self.channels[2].is_active = True  # Triangle - bass
        self.channels[3].is_active = track_number % 2 == 0  # Noise - percussion
        self.channels[4].is_active = False  # DMC - rarely used
        self.channels[5].is_active = False  # Expansion - rare
        
        print(f"🎵 Mock NSF: Playing track {track_number}")
        return True
        
    def stop(self):
        """Stop playback."""
        self.is_playing = False
        self._stop_playback = True
        for channel in self.channels:
            channel.is_active = False
        print("🎵 Mock NSF: Stopped")
        
    def set_master_volume(self, volume: float):
        """Set master playback volume."""
        volume = max(0.0, min(1.0, volume))
        print(f"🎵 Mock NSF: Master volume set to {volume:.2f}")
        
    def set_channel_volume(self, channel: int, volume: float):
        """Set volume for a specific channel."""
        if 0 <= channel < len(self.channels):
            self.channels[channel].volume = max(0.0, min(1.0, volume))
            print(f"🎵 Mock NSF: Channel {channel} volume set to {volume:.2f}")
            
    def mute_channel(self, channel: int, muted: bool = True):
        """Mute/unmute a specific channel."""
        if 0 <= channel < len(self.channels):
            self.channels[channel].muted = muted
            state = "muted" if muted else "unmuted"
            print(f"🎵 Mock NSF: Channel {channel} {state}")
            
    def get_channel_levels(self) -> List[float]:
        """Get current activity levels for visualization."""
        levels = []
        for i, channel in enumerate(self.channels):
            if channel.is_active and not channel.muted:
                # Simulate varying levels
                level = channel.volume * (0.5 + 0.5 * ((time.time() * 2 + i) % 1))
            else:
                level = 0.0
            levels.append(level)
        return levels
        
    def get_track_info(self) -> Dict[str, Any]:
        """Get information about the current track."""
        return {
            "current_track": self.current_track,
            "total_tracks": self.total_tracks,
            "is_playing": self.is_playing,
            "title": f"Mock Track {self.current_track + 1}",
            "length": 120.0,  # 2 minutes
            "composer": "Mock Composer"
        }


class NSFPlayerComponent(Component):
    """Component for NSF music playback with per-channel control."""
    
    def __init__(self, nsf_file_path: str):
        """Initialize NSF player component."""
        super().__init__()
        self.nsf_file_path = nsf_file_path
        self.nsf_player = MockNSFLibrary()
        self.is_loaded = False
        self.current_track = 0
        self.loop_track = True
        self.fade_duration = 2.0
        
        # Channel effects and callbacks
        self.channel_callbacks: Dict[int, List[Callable]] = {}
        self.effect_callbacks: List[Callable] = []
        
        # Load the NSF file
        self.load()
        
    def load(self) -> bool:
        """Load the NSF file."""
        self.is_loaded = self.nsf_player.load_nsf(self.nsf_file_path)
        return self.is_loaded
        
    def play_track(self, track_number: int, loop: bool = True) -> bool:
        """Play a specific track from the NSF."""
        if not self.is_loaded:
            return False
            
        self.current_track = track_number
        self.loop_track = loop
        return self.nsf_player.play_track(track_number)
        
    def stop(self):
        """Stop NSF playback."""
        self.nsf_player.stop()
        
    def set_master_volume(self, volume: float):
        """Set master volume for NSF playback."""
        self.nsf_player.set_master_volume(volume)
        
    def set_channel_volume(self, channel: int, volume: float):
        """Set volume for a specific NSF channel."""
        self.nsf_player.set_channel_volume(channel, volume)
        
        # Trigger channel callbacks
        if channel in self.channel_callbacks:
            for callback in self.channel_callbacks[channel]:
                callback(channel, "volume", volume)
                
    def mute_channel(self, channel: int, muted: bool = True):
        """Mute/unmute a specific NSF channel."""
        self.nsf_player.mute_channel(channel, muted)
        
        # Trigger channel callbacks
        if channel in self.channel_callbacks:
            for callback in self.channel_callbacks[channel]:
                callback(channel, "mute", muted)
                
    def get_channel_levels(self) -> List[float]:
        """Get current channel activity levels for visualization."""
        return self.nsf_player.get_channel_levels()
        
    def get_track_info(self) -> Dict[str, Any]:
        """Get information about the currently loaded NSF."""
        return self.nsf_player.get_track_info()
        
    def add_channel_callback(self, channel: int, callback: Callable):
        """Add a callback for channel events."""
        if channel not in self.channel_callbacks:
            self.channel_callbacks[channel] = []
        self.channel_callbacks[channel].append(callback)
        
    def add_effect_callback(self, callback: Callable):
        """Add a callback for effect events."""
        self.effect_callbacks.append(callback)
        
    def apply_channel_effect(self, channel: int, effect_type: str, value: float):
        """Apply real-time effects to a channel."""
        print(f"🎵 NSF Effect: Channel {channel} {effect_type} = {value}")
        
        # Trigger effect callbacks
        for callback in self.effect_callbacks:
            callback(channel, effect_type, value)


class NSFSystem(System):
    """System for managing NSF playback across entities."""
    
    def __init__(self, world=None):
        super().__init__(world)
        self.active_nsf_players: Dict[int, NSFPlayerComponent] = {}
        
    def update(self, delta_time: float):
        """Update NSF players."""
        # Find all entities with NSF components
        for entity_id in self.world.get_entities_with_component(NSFPlayerComponent):
            nsf_component = self.world.get_component(entity_id, NSFPlayerComponent)
            if nsf_component and nsf_component.is_loaded:
                self.active_nsf_players[entity_id] = nsf_component
                
        # Update active players (check for track end, handle looping, etc.)
        for entity_id, nsf_component in self.active_nsf_players.items():
            self._update_nsf_player(nsf_component, delta_time)
            
    def _update_nsf_player(self, nsf_component: NSFPlayerComponent, delta_time: float):
        """Update an individual NSF player."""
        # In a real implementation, this would:
        # - Check if track has ended
        # - Handle looping
        # - Update channel states
        # - Process real-time effects
        pass
        
    def play_nsf(self, entity_id: int, track_number: int = 0) -> bool:
        """Play NSF on a specific entity."""
        nsf_component = self.world.get_component(entity_id, NSFPlayerComponent)
        if nsf_component:
            return nsf_component.play_track(track_number)
        return False
        
    def stop_nsf(self, entity_id: int):
        """Stop NSF playback on a specific entity."""
        nsf_component = self.world.get_component(entity_id, NSFPlayerComponent)
        if nsf_component:
            nsf_component.stop()
            
    def set_global_nsf_volume(self, volume: float):
        """Set volume for all active NSF players."""
        for nsf_component in self.active_nsf_players.values():
            nsf_component.set_master_volume(volume)
            
    def get_nsf_visualization_data(self, entity_id: int) -> Optional[List[float]]:
        """Get channel levels for visualization."""
        nsf_component = self.worl
        d.get_component(entity_id, NSFPlayerComponent)
        if nsf_component:06221758.
            return nsf_component.get_channel_levels()
        return None


# Integration example
def create_nsf_music_entity(world, nsf_file_path: str):
    """Create an entity with NSF music capabilities."""
    entity = world.create_entity()
    nsf_component = NSFPlayerComponent(nsf_file_path)
    world.add_component(entity.id, nsf_component)
    
    # Add some example channel callbacks
    def on_channel_change(channel: int, event_type: str, value: Any):
        print(f"🎵 Channel {channel} {event_type}: {value}")
        
    nsf_component.add_channel_callback(0, on_channel_change)  # Pulse 1
    nsf_component.add_channel_callback(1, on_channel_change)  # Pulse 2
    
    return entity


def demo_nsf_integration():
    """Demonstration of NSF integration with the audio system."""
    print("🎵 NSF Integration Demo")
    print("=" * 40)
    
    nsf_component = NSFPlayerComponent("assets/music/zelda_overworld.nsf")
    
    if nsf_component.is_loaded:
        print("✅ NSF file loaded successfully!")
        
        # Play the first track
        nsf_component.play_track(0)
        
        # Demonstrate channel control
        print("\n🎛️ Channel Control Demo:")
        nsf_component.set_channel_volume(0, 0.8)  # Reduce pulse 1
        nsf_component.mute_channel(3)             # Mute noise channel
        
        # Show channel levels
        print("\n📊 Channel Levels:")
        levels = nsf_component.get_channel_levels()
        channel_names = ["Pulse1", "Pulse2", "Triangle", "Noise", "DMC", "Expansion"]
        for i, (name, level) in enumerate(zip(channel_names, levels)):
            bar = "█" * int(level * 10)
            print(f"  {name:>8}: {bar:<10} {level:.2f}")
        
        # Show track info
        print("\n📝 Track Info:")
        info = nsf_component.get_track_info()
        for key, value in info.items():
            print(f"  {key}: {value}")
            
        # Stop playback
        nsf_component.stop()
        print("\n⏹️ Stopped playback")
        
    else:
        print("❌ Failed to load NSF file")


if __name__ == "__main__":
    demo_nsf_integration()
