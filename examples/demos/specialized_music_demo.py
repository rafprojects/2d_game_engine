"""
Specialized Music Formats Demo

This demo showcases the NSF (Nintendo Sound Format) and MIDI with soundfont
capabilities of the 2D Game Engine. It demonstrates:

- NSF chiptune music playback with per-channel control
- MIDI music with soundfont synthesis
- Real-time instrument and channel manipulation
- Audio visualization and channel meters
- Integration with the existing ECS audio system
"""

import sys
import os
import time

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from engine.audio.nsf_player import NSFPlayerComponent, demo_nsf_integration
from engine.audio.midi_player import MIDIPlayerComponent, demo_midi_integration


def demo_specialized_music_formats():
    """Main demonstration of specialized music format capabilities."""
    print("🎵 Specialized Music Formats Demo")
    print("=" * 50)
    print("This demo showcases NSF and MIDI capabilities")
    print("=" * 50)
    
    # Demo NSF functionality
    print("\n" + "🎮" * 20)
    print("NSF (Nintendo Sound Format) Demo")
    print("🎮" * 20)
    demo_nsf_integration()
    
    # Demo MIDI functionality  
    print("\n" + "🎹" * 20)
    print("MIDI with Soundfont Demo")
    print("🎹" * 20)
    demo_midi_integration()
    
    # Demo comparative features
    print("\n" + "🔄" * 20)
    print("Format Comparison Demo")
    print("🔄" * 20)
    demo_format_comparison()
    
    # Demo real-time control
    print("\n" + "🎛️" * 20)
    print("Real-time Control Demo")  
    print("🎛️" * 20)
    demo_realtime_control()


def demo_format_comparison():
    """Compare NSF vs MIDI capabilities side by side."""
    print("\n📊 NSF vs MIDI Comparison")
    print("-" * 30)
    
    # Create both components
    nsf_comp = NSFPlayerComponent("assets/music/Guardian_Legendnsf")
    midi_comp = MIDIPlayerComponent("assets/music/orchestral_theme.mid")
    midi_comp.load_soundfont("assets/soundfonts/OPL-3_FM_128M.sf2")
    
    print("\n🎵 NSF Characteristics:")
    print("  ✓ Authentic chiptune sound")
    print("  ✓ Low CPU usage")
    print("  ✓ 6 hardware channels (Pulse1, Pulse2, Triangle, Noise, DMC, Expansion)")
    print("  ✓ Per-channel muting and volume control")
    print("  ✓ Hardware-accurate sound reproduction")
    print("  ✓ Multiple tracks per file")
    
    if nsf_comp.is_loaded:
        info = nsf_comp.get_track_info()
        print(f"  📝 Loaded: {info['title']} ({info['total_tracks']} tracks)")
    
    print("\n🎹 MIDI Characteristics:")
    print("  ✓ High-quality instrument samples")
    print("  ✓ 16 channels with full instrument range")
    print("  ✓ Real-time instrument switching")
    print("  ✓ Multiple soundfont support")
    print("  ✓ Professional music production quality")
    print("  ✓ Complex orchestration support")
    
    if midi_comp.is_loaded:
        info = midi_comp.get_midi_info()
        print(f"  📝 Loaded: {info['filename']} ({info['tracks']} tracks)")
        sf_info = midi_comp.get_soundfont_info()
        for path, sf_data in sf_info.items():
            print(f"  🎼 Soundfont: {sf_data.name} ({sf_data.preset_count} instruments)")


def demo_realtime_control():
    """Demonstrate real-time control capabilities."""
    print("\n🎛️ Real-time Audio Control")
    print("-" * 25)
    
    # NSF real-time control
    print("\n🎮 NSF Real-time Control:")
    nsf_comp = NSFPlayerComponent("assets/music/action_game.nsf")
    
    if nsf_comp.is_loaded:
        nsf_comp.play_track(0)
        
        print("  🔊 Playing track 0 - Full mix")
        show_channel_visualization(nsf_comp)
        
        time.sleep(1)
        
        print("  🔇 Muting percussion (noise channel)")
        nsf_comp.mute_channel(3)  # Mute noise channel
        show_channel_visualization(nsf_comp)
        
        time.sleep(1)
        
        print("  🔉 Reducing melody volume")
        nsf_comp.set_channel_volume(0, 0.3)  # Reduce pulse 1
        show_channel_visualization(nsf_comp)
        
        nsf_comp.stop()
    
    # MIDI real-time control
    print("\n🎹 MIDI Real-time Control:")
    midi_comp = MIDIPlayerComponent("assets/music/adaptive_theme.mid")
    midi_comp.load_soundfont("assets/soundfonts/orchestral.sf2")
    
    if midi_comp.is_loaded:
        midi_comp.play()
        
        print("  🎼 Playing with orchestral instruments")
        print("    Ch0: Piano, Ch1: Violin, Ch2: Cello")
        midi_comp.set_channel_instrument(0, 0)   # Piano
        midi_comp.set_channel_instrument(1, 40)  # Violin  
        midi_comp.set_channel_instrument(2, 42)  # Cello
        
        time.sleep(1)
        
        print("  🎸 Switching to rock instruments")
        print("    Ch0: Electric Guitar, Ch1: Electric Bass, Ch2: Synth Lead")
        midi_comp.set_channel_instrument(0, 25)  # Electric Guitar
        midi_comp.set_channel_instrument(1, 33)  # Electric Bass
        midi_comp.set_channel_instrument(2, 80)  # Synth Lead
        
        time.sleep(1)
        
        print("  🎺 Switching to brass section")
        print("    Ch0: Trumpet, Ch1: Trombone, Ch2: French Horn")
        midi_comp.set_channel_instrument(0, 56)  # Trumpet
        midi_comp.set_channel_instrument(1, 57)  # Trombone
        midi_comp.set_channel_instrument(2, 60)  # French Horn
        
        midi_comp.stop()


def show_channel_visualization(nsf_component):
    """Show a simple visualization of NSF channel activity."""
    levels = nsf_component.get_channel_levels()
    channel_names = ["Pulse1", "Pulse2", "Triangle", "Noise", "DMC", "Expansion"]
    
    print("    📊 Channel Activity:")
    for i, (name, level) in enumerate(zip(channel_names, levels)):
        if level > 0:
            bar = "█" * int(level * 8)
            print(f"      {name:>8}: {bar:<8} {level:.2f}")
        else:
            print(f"      {name:>8}: -------- 0.00")


def demo_game_integration_scenarios():
    """Demonstrate how these formats could be used in actual games."""
    print("\n🎮 Game Integration Scenarios")
    print("=" * 30)
    
    print("\n🏰 Scenario 1: Retro Platformer")
    print("  🎵 NSF for authentic chiptune soundtrack")
    print("  🎛️ Per-channel control for dynamic effects")
    print("  📢 Example: Mute melody during dialogue")
    
    nsf_game = NSFPlayerComponent("assets/music/platformer_level1.nsf")
    if nsf_game.is_loaded:
        print("  ▶️ Playing level music...")
        nsf_game.play_track(0)
        
        print("  💬 Dialogue starts - reducing melody")
        nsf_game.set_channel_volume(0, 0.2)  # Reduce pulse 1 (melody)
        nsf_game.set_channel_volume(1, 0.2)  # Reduce pulse 2 (harmony)
        
        time.sleep(1)
        
        print("  💬 Dialogue ends - restoring music")
        nsf_game.set_channel_volume(0, 1.0)
        nsf_game.set_channel_volume(1, 1.0)
        
        nsf_game.stop()
    
    print("\n🏛️ Scenario 2: Epic RPG")
    print("  🎼 MIDI + orchestral soundfonts for rich music")
    print("  🎭 Dynamic instrument changes for mood")
    print("  🌍 Adaptive music based on location/situation")
    
    rpg_music = MIDIPlayerComponent("assets/music/rpg_overworld.mid")
    rpg_music.load_soundfont("assets/soundfonts/orchestral.sf2")
    rpg_music.load_soundfont("assets/soundfonts/ethnic_instruments.sf2")
    
    if rpg_music.is_loaded:
        print("  🌲 Forest area - Celtic instruments")
        rpg_music.set_channel_instrument(0, 73)  # Flute
        rpg_music.set_channel_instrument(1, 105) # Celtic harp
        rpg_music.play()
        
        time.sleep(1)
        
        print("  ⚔️ Battle starts - dramatic orchestral")
        rpg_music.set_channel_instrument(0, 56)  # Trumpet
        rpg_music.set_channel_instrument(1, 48)  # String ensemble
        rpg_music.set_channel_instrument(2, 58)  # Tuba
        
        time.sleep(1)
        
        print("  🏰 Town area - peaceful chamber music")
        rpg_music.set_channel_instrument(0, 0)   # Piano
        rpg_music.set_channel_instrument(1, 40)  # Violin
        rpg_music.set_channel_instrument(2, 42)  # Cello
        
        rpg_music.stop()
    
    print("\n🤖 Scenario 3: Hybrid Approach")
    print("  🔄 Combining NSF and MIDI for unique soundscape")
    print("  🎵 NSF for retro elements, MIDI for modern orchestration")
    
    hybrid_nsf = NSFPlayerComponent("assets/music/hybrid_chiptune.nsf")
    hybrid_midi = MIDIPlayerComponent("assets/music/hybrid_orchestral.mid")
    hybrid_midi.load_soundfont("assets/soundfonts/cinematic.sf2")
    
    print("  📻 Playing layered hybrid music...")
    if hybrid_nsf.is_loaded:
        hybrid_nsf.play_track(0)
        print("    🎮 NSF layer: Retro lead melody and rhythm")
    
    if hybrid_midi.is_loaded:
        hybrid_midi.play()
        print("    🎼 MIDI layer: Orchestral backing and atmosphere")
    
    time.sleep(2)
    
    print("  🎭 Dynamic crossfade: NSF dominant -> MIDI dominant")
    if hybrid_nsf.is_loaded:
        hybrid_nsf.set_master_volume(0.3)
    if hybrid_midi.is_loaded:
        hybrid_midi.set_master_volume(1.0)
    
    time.sleep(1)
    
    # Stop both
    if hybrid_nsf.is_loaded:
        hybrid_nsf.stop()
    if hybrid_midi.is_loaded:
        hybrid_midi.stop()


def show_implementation_roadmap():
    """Show the roadmap for implementing these features."""
    print("\n🗺️ Implementation Roadmap")
    print("=" * 25)
    
    print("\n✅ Phase 1: Foundation (COMPLETED)")
    print("  ✓ Mock NSF and MIDI player components")
    print("  ✓ ECS integration architecture")
    print("  ✓ Channel control and visualization APIs")
    print("  ✓ Callback system for real-time events")
    
    print("\n🔧 Phase 2: Real Implementation (NEXT STEPS)")
    print("  🔲 Integrate real NSF library (pynsf or custom)")
    print("  🔲 Integrate FluidSynth for MIDI synthesis")
    print("  🔲 Add MIDI file parsing (mido library)")
    print("  🔲 Implement real-time audio threading")
    print("  🔲 Add soundfont management system")
    
    print("\n🎨 Phase 3: Advanced Features")
    print("  🔲 Real-time audio effects (reverb, delay, etc.)")
    print("  🔲 Audio visualization widgets")
    print("  🔲 Dynamic soundfont switching")
    print("  🔲 Cross-format synchronization")
    print("  🔲 Procedural music generation")
    
    print("\n🎮 Phase 4: Game Integration")
    print("  🔲 Game event -> music mapping system")
    print("  🔲 Adaptive music AI")
    print("  🔲 Player-controlled music elements")
    print("  🔲 Music editor/sequencer tools")


def show_required_dependencies():
    """Show what dependencies would be needed for real implementation."""
    print("\n📦 Required Dependencies for Real Implementation")
    print("=" * 45)
    
    print("\n🎵 NSF Support:")
    print("  pip install pynsf  # If available")
    print("  # Alternative: Custom C library bindings")
    print("  # Alternative: Subprocess-based NSF player")
    
    print("\n🎹 MIDI Support:")
    print("  pip install python-rtmidi  # Real-time MIDI I/O")
    print("  pip install mido           # MIDI file parsing")
    print("  pip install pyfluidsynth   # FluidSynth Python bindings")
    
    print("\n🔊 Audio Processing:")
    print("  pip install numpy          # Audio buffer processing")
    print("  pip install scipy          # Audio effects and filtering")
    
    print("\n📂 Asset Management:")
    print("  # Soundfont libraries (100MB+ each):")
    print("  # - GeneralUser GS (free, good quality)")
    print("  # - FluidR3 GM (free, decent quality)")
    print("  # - Commercial orchestral libraries")


if __name__ == "__main__":
    demo_specialized_music_formats()
    demo_game_integration_scenarios()
    show_implementation_roadmap()
    show_required_dependencies()
