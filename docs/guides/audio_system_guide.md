# Audio System Integration Guide

*Complete guide to the 2D Game Engine's audio system*

## 📋 **Overview**

The audio system provides comprehensive sound and music management with:
- **Sound Effects** - Short audio clips with 3D positioning
- **Background Music** - Long-form audio with smooth transitions  
- **Audio Listener** - 3D audio positioning and volume control
- **Dynamic Music** - Mood-based music selection
- **Performance Optimization** - Sound pooling and streaming

## 🏗️ **Architecture**

### **Components**
- **`SoundComponent`** - Sound effects and short audio clips
- **`MusicComponent`** - Background music and playlists
- **`AudioListenerComponent`** - 3D audio positioning and settings

### **Systems**
- **`AudioSystem`** - Handles sound effects and 3D audio
- **`MusicSystem`** - Manages background music and transitions
- **`AudioManager`** - High-level API for common operations

## 🚀 **Quick Start**

### **1. Basic Setup**

```python
from engine.audio.audio_manager import AudioManager
from engine.audio.systems.audio_system import AudioSystem
from engine.audio.systems.music_system import MusicSystem

# Initialize audio systems
audio_system = AudioSystem(world)
music_system = MusicSystem(world)
audio_manager = AudioManager(world, audio_system, music_system)

# Add systems to world
world.add_system(audio_system)
world.add_system(music_system)
```

### **2. Adding Sound Effects**

```python
from engine.audio.components.sound_component import SoundComponent, SoundType

# Create entity with sound effects
player = world.create_entity("player")

# Add sound component
sound_comp = SoundComponent(
    sound_files={
        "jump": "assets/audio/jump.wav",
        "hurt": "assets/audio/hurt.wav",
        "pickup": "assets/audio/pickup.wav"
    },
    sound_type=SoundType.EFFECT,
    volume=0.8,
    is_3d=False
)
world.add_component(player.id, sound_comp)

# Play sounds
audio_system.play_sound(player.id, "jump")
```

### **3. Adding Background Music**

```python
from engine.audio.components.music_component import MusicComponent

# Create music entity
music_entity = world.create_entity("background_music")

# Add music component
music_comp = MusicComponent(
    music_files={
        "menu": "assets/music/menu.ogg",
        "level1": "assets/music/level1.ogg",
        "boss": "assets/music/boss.ogg"
    },
    volume=0.6,
    auto_play=True,
    fade_duration=2.0
)
world.add_component(music_entity.id, music_comp)

# Play music
music_system.play_music(music_entity.id, "menu")
```

### **4. 3D Audio Setup**

```python
from engine.audio.components.audio_listener_component import AudioListenerComponent

# Add audio listener to player/camera
listener_comp = AudioListenerComponent(
    is_active=True,
    forward_vector=Vec3(0, 1, 0),
    up_vector=Vec3(0, 0, 1)
)
world.add_component(player.id, listener_comp)

# Create 3D sound source
ambient_entity = world.create_entity("water_source")
world.add_component(ambient_entity.id, TransformComponent(position=Vec2(100, 200)))

sound_comp = SoundComponent(
    sound_files={"water": "assets/audio/water.wav"},
    sound_type=SoundType.AMBIENT,
    volume=0.5,
    is_3d=True,
    max_distance=200.0,
    loop=True,
    auto_play=True
)
world.add_component(ambient_entity.id, sound_comp)
```

## 🎵 **Advanced Features**

### **Dynamic Music Moods**

```python
# Set up music moods
music_comp.music_moods = {
    "calm": ["peaceful1.ogg", "peaceful2.ogg"],
    "action": ["intense1.ogg", "intense2.ogg"],
    "mystery": ["dark1.ogg", "dark2.ogg"]
}

# Switch mood
music_comp.set_mood("action")
action_tracks = music_comp.get_tracks_in_mood("action")
music_comp.create_playlist(action_tracks, shuffle=True)
```

### **Sound Categories and Volume Control**

```python
# Different sound types for volume management
SoundType.EFFECT    # UI sounds, player actions
SoundType.AMBIENT   # Environmental sounds
SoundType.VOICE     # Character speech
SoundType.UI        # Interface sounds

# Global volume controls
audio_manager.set_master_volume(0.8)
audio_manager.set_music_volume(0.6)
audio_manager.set_sfx_volume(0.9)

# Per-component volume
sound_comp.set_volume(0.5)
music_comp.volume = 0.7
```

### **Music Transitions**

```python
from engine.audio.components.music_component import MusicTransition

# Set transition type
music_comp.transition_type = MusicTransition.CROSSFADE
music_comp.fade_duration = 3.0

# Smooth transition between tracks
music_system.transition_to_track(music_comp, "new_track")
```

### **3D Audio Positioning**

```python
# Update listener position (usually attached to player/camera)
listener_comp.set_orientation(
    forward=Vec3(0, 1, 0),
    up=Vec3(0, 0, 1)
)
listener_comp.set_velocity(Vec3(10, 0, 0))  # For Doppler effects

# 3D sound properties
sound_comp.is_3d = True
sound_comp.max_distance = 500.0

# Position is automatically taken from entity's TransformComponent
```

## 🎯 **Common Patterns**

### **One-Shot Sound Effects**

```python
# Quick sound effect without persistent entity
audio_manager.play_sound(
    "assets/audio/explosion.wav",
    sound_type=SoundType.EFFECT,
    volume=1.0,
    pitch=1.0,
    loop=False
)
```

### **Looping Ambient Sounds**

```python
# Environmental sounds that loop
ambient_comp = SoundComponent(
    sound_files={"wind": "assets/audio/wind.wav"},
    sound_type=SoundType.AMBIENT,
    volume=0.4,
    is_3d=True,
    loop=True,
    auto_play=True
)
```

### **UI Sound Feedback**

```python
# UI button sounds
ui_comp = SoundComponent(
    sound_files={
        "click": "assets/audio/ui_click.wav",
        "hover": "assets/audio/ui_hover.wav",
        "error": "assets/audio/ui_error.wav"
    },
    sound_type=SoundType.UI,
    volume=0.6,
    is_3d=False
)
```

### **Dynamic Music Playlists**

```python
# Create adaptive music system
def update_music_based_on_game_state(game_state):
    if game_state == "combat":
        music_comp.set_mood("action")
    elif game_state == "exploration":
        music_comp.set_mood("calm")
    elif game_state == "stealth":
        music_comp.set_mood("mystery")
        
    # Auto-transition to appropriate track
    current_mood_tracks = music_comp.get_tracks_in_mood(music_comp.current_mood)
    if current_mood_tracks:
        music_comp.create_playlist(current_mood_tracks, shuffle=True)
```

## 🛠️ **Integration with Main Game**

### **In main.py**

```python
# Audio system imports
AUDIO_AVAILABLE = True
try:
    from engine.audio.audio_manager import AudioManager
    from engine.audio.systems.audio_system import AudioSystem
    from engine.audio.systems.music_system import MusicSystem
    from engine.audio.components.audio_listener_component import AudioListenerComponent
except ImportError as e:
    print(f"⚠️  Audio system not available: {e}")
    AUDIO_AVAILABLE = False

class Game(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        
        # Initialize audio if available
        if AUDIO_AVAILABLE:
            self.audio_system = AudioSystem(self.world)
            self.music_system = MusicSystem(self.world)
            self.audio_manager = AudioManager(
                self.world, 
                self.audio_system, 
                self.music_system
            )
            
            self.world.add_system(self.audio_system)
            self.world.add_system(self.music_system)
            
            print("🎵 Audio system initialized")
        else:
            self.audio_manager = None
```

### **Error Handling**

```python
# Graceful degradation when audio files are missing
def play_sound_safe(audio_system, entity_id, sound_name):
    try:
        return audio_system.play_sound(entity_id, sound_name)
    except Exception as e:
        print(f"Warning: Could not play sound '{sound_name}': {e}")
        return False

# Check if audio is available before using
if AUDIO_AVAILABLE and self.audio_manager:
    self.audio_manager.play_sound("assets/audio/jump.wav")
```

## 📁 **Asset Organization**

### **Recommended Directory Structure**

```
assets/
├── audio/
│   ├── sfx/                 # Sound effects
│   │   ├── player/          # Player sounds
│   │   ├── enemies/         # Enemy sounds
│   │   ├── environment/     # Environmental sounds
│   │   └── ui/              # Interface sounds
│   ├── music/               # Background music
│   │   ├── menu/            # Menu music
│   │   ├── gameplay/        # Level music
│   │   └── ambient/         # Ambient tracks
│   └── voice/               # Voice acting
│       ├── narrator/        # Narrator lines
│       └── characters/      # Character speech
```

### **Supported Audio Formats**

- **WAV** - Uncompressed, best for short sound effects
- **OGG** - Compressed, good for music and longer sounds
- **MP3** - Widely supported, good compression
- **FLAC** - Lossless compression for high-quality audio

## 🔧 **Performance Tips**

### **Sound Pooling**

```python
# Use sound pools for frequently played sounds
sound_comp.sound_pool_size = 5  # Multiple instances can play simultaneously
```

### **3D Audio Optimization**

```python
# Set reasonable distance limits
sound_comp.max_distance = 200.0
audio_system.sound_distance_cutoff = 500.0
```

### **Memory Management**

```python
# Preload important sounds
sound_comp.preload_sounds = True

# Clean up finished sounds automatically
audio_system.max_simultaneous_sounds = 32
```

## 🐛 **Troubleshooting**

### **Common Issues**

1. **No Sound Playing**
   - Check if audio files exist
   - Verify volume levels (master, category, component)
   - Ensure AudioSystem is added to world

2. **3D Audio Not Working**
   - Add AudioListenerComponent to player/camera
   - Set `is_3d=True` on SoundComponent
   - Check distance between listener and sound source

3. **Music Not Transitioning**
   - Verify music files exist and are valid
   - Check MusicComponent fade_duration
   - Ensure MusicSystem is running

### **Debug Information**

```python
# Get audio system statistics
stats = audio_manager.get_audio_stats()
print(f"Sounds playing: {stats['audio_system']['sounds_playing']}")
print(f"Music volume: {stats['music_volume']}")

# Check component state
print(f"Sound component playing: {sound_comp.is_playing()}")
print(f"Music state: {music_comp.music_state}")
```

## 📚 **Examples**

See the complete examples in:
- `examples/demos/audio_system_demo.py` - Comprehensive feature demonstration
- `examples/tutorials/audio_integration.py` - Step-by-step integration guide
- `examples/games/` - Complete games using the audio system

## 🔗 **Related Documentation**

- [Component Design Patterns](component_patterns.md)
- [Performance Optimization](performance_guide.md)
- [Asset Pipeline](asset_pipeline.md)
- [Event System Integration](event_system.md)

---

*For advanced audio features and custom audio processing, see the API reference documentation.*
