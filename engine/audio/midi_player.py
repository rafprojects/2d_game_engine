"""
MIDI Player with Soundfont Support for 2D Game Engine

This module provides MIDI playback with soundfont support for the existing audio system.
This allows for high-quality instrument synthesis and flexible music composition.

Real implementation would use libraries like:
- python-rtmidi (real-time MIDI I/O)
- mido (MIDI file parsing)
- fluidsynth-python (soundfont synthesis)
- pygame.midi (alternative MIDI support)

For now, this is a well-structured mock that demonstrates the API.
"""

from typing import Dict, Optional, List, Any, Callable
import os
import time
from dataclasses import dataclass
from enum import Enum

from ..core.component import Component
from ..core.system import System


class MIDIEventType(Enum):
    """MIDI event types."""
    NOTE_ON = "note_on"
    NOTE_OFF = "note_off" 
    CONTROL_CHANGE = "control_change"
    PROGRAM_CHANGE = "program_change"
    PITCH_BEND = "pitch_bend"


@dataclass
class MIDINote:
    """Represents an active MIDI note."""
    channel: int
    note: int
    velocity: int
    start_time: float
    duration: Optional[float] = None


@dataclass 
class SoundfontInfo:
    """Information about a loaded soundfont."""
    path: str
    name: str
    preset_count: int
    instruments: Dict[int, str]  # program_number -> instrument_name


class MockFluidSynth:
    """
    Mock FluidSynth for demonstration purposes.
    
    In a real implementation, this would interface with:
    - FluidSynth library via python bindings
    - Real-time audio synthesis
    - Multiple soundfont loading and layering
    """
    
    def __init__(self):
        self.soundfonts: Dict[int, SoundfontInfo] = {}
        self.channels = [0] * 16  # 16 MIDI channels
        self.current_program = [0] * 16  # Current instrument per channel
        self.active_notes: Dict[int, List[MIDINote]] = {i: [] for i in range(16)}
        self.channel_volumes = [1.0] * 16
        self.master_volume = 1.0
        
    def load_soundfont(self, sf_path: str) -> int:
        """Load a soundfont file."""
        if not os.path.exists(sf_path):
            print(f"🎹 Mock FluidSynth: Soundfont not found: {sf_path}")
            return -1
            
        sf_id = len(self.soundfonts)
        
        # Mock instruments for demonstration
        mock_instruments = {
            0: "Piano", 1: "Bright Piano", 2: "Electric Piano", 3: "Honky-tonk",
            8: "Celesta", 9: "Glockenspiel", 10: "Music Box", 11: "Vibraphone",
            16: "Drawbar Organ", 17: "Percussive Organ", 18: "Rock Organ",
            24: "Acoustic Guitar", 25: "Electric Guitar", 26: "Jazz Guitar",
            32: "Acoustic Bass", 33: "Electric Bass", 34: "Pick Bass",
            40: "Violin", 41: "Viola", 42: "Cello", 43: "Contrabass",
            48: "String Ensemble", 49: "Slow Strings", 50: "Synth Strings",
            56: "Trumpet", 57: "Trombone", 58: "Tuba", 59: "Muted Trumpet",
            64: "Soprano Sax", 65: "Alto Sax", 66: "Tenor Sax", 67: "Baritone Sax",
            72: "Piccolo", 73: "Flute", 74: "Recorder", 75: "Pan Flute",
            128: "Drum Kit"  # Channel 9 (percussion)
        }
        
        soundfont_info = SoundfontInfo(
            path=sf_path,
            name=os.path.basename(sf_path),
            preset_count=len(mock_instruments),
            instruments=mock_instruments
        )
        
        self.soundfonts[sf_id] = soundfont_info
        print(f"🎹 Mock FluidSynth: Loaded soundfont: {soundfont_info.name} ({soundfont_info.preset_count} instruments)")
        return sf_id
        
    def program_change(self, channel: int, program: int):
        """Change instrument on a channel."""
        if 0 <= channel < 16:
            self.current_program[channel] = program
            # Find instrument name
            instrument_name = "Unknown"
            for sf_info in self.soundfonts.values():
                if program in sf_info.instruments:
                    instrument_name = sf_info.instruments[program]
                    break
            print(f"🎹 Mock FluidSynth: Channel {channel} -> {instrument_name} (#{program})")
        
    def note_on(self, channel: int, note: int, velocity: int):
        """Play a note."""
        if 0 <= channel < 16:
            midi_note = MIDINote(
                channel=channel,
                note=note,
                velocity=velocity,
                start_time=time.time()
            )
            self.active_notes[channel].append(midi_note)
            # print(f"🎹 Note ON: Ch{channel} Note{note} Vel{velocity}")
        
    def note_off(self, channel: int, note: int):
        """Stop a note."""
        if 0 <= channel < 16:
            # Find and remove the note
            for i, midi_note in enumerate(self.active_notes[channel]):
                if midi_note.note == note:
                    midi_note.duration = time.time() - midi_note.start_time
                    self.active_notes[channel].pop(i)
                    break
            # print(f"🎹 Note OFF: Ch{channel} Note{note}")
        
    def control_change(self, channel: int, control: int, value: int):
        """Send control change message."""
        if control == 7:  # Volume
            self.channel_volumes[channel] = value / 127.0
            print(f"🎹 Mock FluidSynth: Channel {channel} volume -> {value}/127")
        elif control == 64:  # Sustain pedal
            state = "ON" if value >= 64 else "OFF"
            print(f"🎹 Mock FluidSynth: Channel {channel} sustain -> {state}")
            
    def set_master_volume(self, volume: float):
        """Set master volume."""
        self.master_volume = max(0.0, min(1.0, volume))
        print(f"🎹 Mock FluidSynth: Master volume -> {self.master_volume:.2f}")
        
    def get_active_notes(self) -> Dict[int, List[MIDINote]]:
        """Get currently active notes for visualization."""
        return {ch: notes[:] for ch, notes in self.active_notes.items() if notes}


class MockMIDIFile:
    """Mock MIDI file parser for demonstration."""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.loaded = False
        self.tracks = []
        self.tempo = 120  # BPM
        self.time_division = 480  # Ticks per quarter note
        self.total_time = 0.0
        
    def load(self) -> bool:
        """Load and parse MIDI file."""
        if not os.path.exists(self.filepath):
            print(f"🎹 Mock MIDI: File not found: {self.filepath}")
            return False
            
        # Mock MIDI data for demonstration
        self.tracks = [
            {"name": "Piano", "channel": 0, "events": 150},
            {"name": "Bass", "channel": 1, "events": 75},
            {"name": "Strings", "channel": 2, "events": 120},
            {"name": "Drums", "channel": 9, "events": 200}
        ]
        self.total_time = 180.0  # 3 minutes
        self.loaded = True
        
        print(f"🎹 Mock MIDI: Loaded {os.path.basename(self.filepath)} ({len(self.tracks)} tracks)")
        return True
        
    def get_info(self) -> Dict[str, Any]:
        """Get MIDI file information."""
        return {
            "filename": os.path.basename(self.filepath),
            "tracks": len(self.tracks),
            "tempo": self.tempo,
            "duration": self.total_time,
            "time_division": self.time_division
        }

class MIDIPlayerComponent(Component):
    """Component for MIDI playback with soundfont support."""
    
    def __init__(self, midi_file_path: str, soundfont_path: Optional[str] = None):
        """
        Initialize MIDI player component.
        
        Args:
            midi_file_path: Path to the MIDI file
            soundfont_path: Optional path to default soundfont
        """
        super().__init__()
        self.midi_file_path = midi_file_path
        self.midi_file = MockMIDIFile(midi_file_path)
        self.fluidsynth = MockFluidSynth()
        
        # Playback state
        self.is_loaded = False
        self.is_playing = False
        self.current_position = 0.0
        self.loop_enabled = True
        self.playback_speed = 1.0
        
        # Soundfont management
        self.loaded_soundfonts: Dict[str, int] = {}  # path -> sf_id
        self.default_soundfont_id: Optional[int] = None
        
        # Channel configuration
        self.channel_instruments: Dict[int, int] = {}  # channel -> program
        self.channel_volumes: Dict[int, float] = {}   # channel -> volume
        self.channel_muted: Dict[int, bool] = {}      # channel -> muted
        
        # Callbacks for events
        self.note_callbacks: List[Callable] = []
        self.instrument_callbacks: List[Callable] = []
        
        # Load components
        self.load()
        if soundfont_path:
            self.load_soundfont(soundfont_path)
        
    def load(self) -> bool:
        """Load the MIDI file."""
        self.is_loaded = self.midi_file.load()
        if self.is_loaded:
            # Initialize default channel settings
            for channel in range(16):
                self.channel_instruments[channel] = 0 if channel != 9 else 128  # Channel 9 = drums
                self.channel_volumes[channel] = 1.0
                self.channel_muted[channel] = False
        return self.is_loaded
        
    def load_soundfont(self, soundfont_path: str) -> bool:
        """Load a soundfont file."""
        if soundfont_path in self.loaded_soundfonts:
            print(f"🎹 Soundfont already loaded: {os.path.basename(soundfont_path)}")
            return True
            
        sf_id = self.fluidsynth.load_soundfont(soundfont_path)
        if sf_id >= 0:
            self.loaded_soundfonts[soundfont_path] = sf_id
            if self.default_soundfont_id is None:
                self.default_soundfont_id = sf_id
            return True
        return False
        
    def play(self) -> bool:
        """Start MIDI playback."""
        if not self.is_loaded:
            return False
            
        self.is_playing = True
        print(f"🎹 Playing MIDI: {os.path.basename(self.midi_file_path)}")
        
        # Apply current channel settings
        for channel, program in self.channel_instruments.items():
            self.fluidsynth.program_change(channel, program)
            
        return True
        
    def stop(self):
        """Stop MIDI playback."""
        self.is_playing = False
        self.current_position = 0.0
        
        # Stop all notes
        for channel in range(16):
            # In real implementation, send note_off for all active notes
            pass
            
        print(f"🎹 Stopped MIDI: {os.path.basename(self.midi_file_path)}")
        
    def pause(self):
        """Pause MIDI playback."""
        self.is_playing = False
        print("🎹 Paused MIDI playback")
        
    def resume(self):
        """Resume MIDI playback."""
        if self.is_loaded:
            self.is_playing = True
            print("🎹 Resumed MIDI playback")
        
    def set_channel_instrument(self, channel: int, program: int):
        """Set instrument for a specific channel."""
        if 0 <= channel < 16:
            self.channel_instruments[channel] = program
            self.fluidsynth.program_change(channel, program)
            
            # Trigger callbacks
            for callback in self.instrument_callbacks:
                callback(channel, program)
                
    def set_channel_volume(self, channel: int, volume: float):
        """Set volume for a specific channel."""
        if 0 <= channel < 16:
            volume = max(0.0, min(1.0, volume))
            self.channel_volumes[channel] = volume
            self.fluidsynth.control_change(channel, 7, int(volume * 127))
            
    def mute_channel(self, channel: int, muted: bool = True):
        """Mute/unmute a specific channel."""
        if 0 <= channel < 16:
            self.channel_muted[channel] = muted
            volume = 0.0 if muted else self.channel_volumes.get(channel, 1.0)
            self.fluidsynth.control_change(channel, 7, int(volume * 127))
            
    def set_master_volume(self, volume: float):
        """Set master volume for MIDI playback."""
        self.fluidsynth.set_master_volume(volume)
        
    def get_active_notes(self) -> Dict[int, List[MIDINote]]:
        """Get currently active notes for visualization."""
        return self.fluidsynth.get_active_notes()
        
    def get_midi_info(self) -> Dict[str, Any]:
        """Get information about the loaded MIDI file."""
        info = self.midi_file.get_info()
        info.update({
            "is_playing": self.is_playing,
            "current_position": self.current_position,
            "loop_enabled": self.loop_enabled,
            "loaded_soundfonts": len(self.loaded_soundfonts)
        })
        return info
        
    def get_soundfont_info(self) -> Dict[str, SoundfontInfo]:
        """Get information about loaded soundfonts."""
        info = {}
        for path, sf_id in self.loaded_soundfonts.items():
            if sf_id in self.fluidsynth.soundfonts:
                info[path] = self.fluidsynth.soundfonts[sf_id]
        return info
        
    def add_note_callback(self, callback: Callable):
        """Add callback for note events."""
        self.note_callbacks.append(callback)
        
    def add_instrument_callback(self, callback: Callable):
        """Add callback for instrument change events."""
        self.instrument_callbacks.append(callback)


class MIDISystem(System):
    """System for managing MIDI playback across entities."""
    
    def __init__(self, world=None):
        super().__init__(world)
        self.active_midi_players: Dict[int, MIDIPlayerComponent] = {}
        
    def update(self, delta_time: float):
        """Update MIDI players."""
        # Find all entities with MIDI components
        for entity_id in self.world.get_entities_with_component(MIDIPlayerComponent):
            midi_component = self.world.get_component(entity_id, MIDIPlayerComponent)
            if midi_component and midi_component.is_loaded:
                self.active_midi_players[entity_id] = midi_component
                
        # Update active players
        for entity_id, midi_component in self.active_midi_players.items():
            self._update_midi_player(midi_component, delta_time)
            
    def _update_midi_player(self, midi_component: MIDIPlayerComponent, delta_time: float):
        """Update an individual MIDI player."""
        if midi_component.is_playing:
            # Update playback position
            midi_component.current_position += delta_time * midi_component.playback_speed
            
            # In a real implementation, this would:
            # - Process MIDI events at current position
            # - Send note on/off messages to FluidSynth
            # - Handle looping and track end
            # - Trigger callbacks for visualization
            pass
            
    def play_midi(self, entity_id: int) -> bool:
        """Start MIDI playback on a specific entity."""
        midi_component = self.world.get_component(entity_id, MIDIPlayerComponent)
        if midi_component:
            return midi_component.play()
        return False
        
    def stop_midi(self, entity_id: int):
        """Stop MIDI playback on a specific entity."""
        midi_component = self.world.get_component(entity_id, MIDIPlayerComponent)
        if midi_component:
            midi_component.stop()
            
    def set_global_midi_volume(self, volume: float):
        """Set volume for all active MIDI players."""
        for midi_component in self.active_midi_players.values():
            midi_component.set_master_volume(volume)
            
    def get_midi_visualization_data(self, entity_id: int) -> Optional[Dict[int, List[MIDINote]]]:
        """Get active notes for visualization."""
        midi_component = self.world.get_component(entity_id, MIDIPlayerComponent)
        if midi_component:
            return midi_component.get_active_notes()
        return None


# Integration examples
def create_midi_music_entity(world, midi_file_path: str, soundfont_path: Optional[str] = None):
    """
    Example: Create an entity with MIDI music capabilities.
    
    Args:
        world: ECS World instance
        midi_file_path: Path to MIDI file
        soundfont_path: Optional path to soundfont
        
    Returns:
        Entity with MIDI component attached
    """
    entity = world.create_entity()
    midi_component = MIDIPlayerComponent(midi_file_path, soundfont_path)
    world.add_component(entity.id, midi_component)
    
    # Add some example callbacks
    def on_instrument_change(channel: int, program: int):
        print(f"🎹 Channel {channel} instrument changed to #{program}")
        
    midi_component.add_instrument_callback(on_instrument_change)
    
    return entity


def demo_midi_integration():
    """Demonstration of MIDI integration with the audio system."""
    print("🎹 MIDI Integration Demo")
    print("=" * 40)
    
    # Create MIDI component with soundfont
    midi_component = MIDIPlayerComponent(
        "assets/music/classical_theme.mid",
        "assets/soundfonts/orchestral.sf2"
    )
    
    if midi_component.is_loaded:
        print("✅ MIDI file and soundfont loaded successfully!")
        
        # Show MIDI info
        print("\n📝 MIDI Info:")
        info = midi_component.get_midi_info()
        for key, value in info.items():
            print(f"  {key}: {value}")
        
        # Show soundfont info
        print("\n🎼 Soundfont Info:")
        sf_info = midi_component.get_soundfont_info()
        for path, sf_data in sf_info.items():
            print(f"  {sf_data.name}: {sf_data.preset_count} instruments")
            
        # Start playback
        midi_component.play()
        
        # Demonstrate channel control
        print("\n🎛️ Channel Control Demo:")
        midi_component.set_channel_instrument(0, 0)   # Piano
        midi_component.set_channel_instrument(1, 40)  # Violin
        midi_component.set_channel_instrument(2, 48)  # String Ensemble
        midi_component.set_channel_instrument(9, 128) # Drum Kit
        
        # Adjust volumes
        midi_component.set_channel_volume(0, 0.8)
        midi_component.set_channel_volume(1, 0.6)
        midi_component.mute_channel(9)  # Mute drums
        
        # Load additional soundfont
        midi_component.load_soundfont("assets/soundfonts/vintage_synths.sf2")
        
        # Simulate some notes for visualization
        print("\n📊 Active Notes Demo:")
        midi_component.fluidsynth.note_on(0, 60, 80)  # Middle C
        midi_component.fluidsynth.note_on(1, 64, 70)  # E
        midi_component.fluidsynth.note_on(2, 67, 75)  # G
        
        time.sleep(0.1)  # Brief pause
        
        active_notes = midi_component.get_active_notes()
        for channel, notes in active_notes.items():
            for note in notes:
                print(f"  Ch{channel}: Note {note.note} (vel {note.velocity})")
                
        # Stop notes
        midi_component.fluidsynth.note_off(0, 60)
        midi_component.fluidsynth.note_off(1, 64)
        midi_component.fluidsynth.note_off(2, 67)
        
        # Stop playback
        midi_component.stop()
        print("\n⏹️ Stopped MIDI playback")
        
    else:
        print("❌ Failed to load MIDI file")


def demo_adaptive_music():
    """Demo of adaptive music using MIDI and soundfonts."""
    print("\n🎮 Adaptive Music Demo")
    print("=" * 30)
    
    midi_component = MIDIPlayerComponent("assets/music/game_theme.mid")
    midi_component.load_soundfont("assets/soundfonts/orchestral.sf2")
    midi_component.load_soundfont("assets/soundfonts/8bit_sounds.sf2")
    
    # Normal gameplay - orchestral instruments
    print("🏰 Normal gameplay - Orchestral")
    midi_component.set_channel_instrument(0, 0)   # Piano
    midi_component.set_channel_instrument(1, 40)  # Violin
    midi_component.set_channel_instrument(2, 48)  # String Ensemble
    
    # Combat mode - more aggressive instruments
    print("⚔️ Combat mode - Aggressive")
    midi_component.set_channel_instrument(0, 25)  # Electric Guitar
    midi_component.set_channel_instrument(1, 56)  # Trumpet
    midi_component.set_channel_instrument(2, 58)  # Tuba
    
    # Retro area - chiptune style
    print("👾 Retro area - Chiptune")
    midi_component.set_channel_instrument(0, 80)  # Square Wave
    midi_component.set_channel_instrument(1, 81)  # Sawtooth Wave
    midi_component.set_channel_instrument(2, 82)  # Triangle Wave


if __name__ == "__main__":
    demo_midi_integration()
    demo_adaptive_music()
