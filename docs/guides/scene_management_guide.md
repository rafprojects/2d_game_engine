# Scene Management System Guide

*Complete guide to the 2D Game Engine's scene management system*

## 📋 **Overview**

The scene management system provides comprehensive multi-scene support with:
- **Scene Lifecycle** - Complete scene state management and coordination
- **Visual Transitions** - Smooth transitions with multiple effect types
- **Scene Persistence** - Save/load scene state with multiple formats
- **Asset Management** - Dynamic loading and unloading per scene
- **Multi-Scene Coordination** - Scene stacking, overlays, and priorities

## 🏗️ **Architecture**

### **Components**
- **`SceneComponent`** - Core scene data and state management
- **`SceneTransitionComponent`** - Visual transition effects and timing
- **`ScenePersistenceComponent`** - Save/load functionality and persistence

### **Systems**
- **`SceneManager`** - Core scene lifecycle management and coordination
- **`SceneTransitionSystem`** - Transition effect processing and rendering
- **`ScenePersistenceSystem`** - Save/load operations and file management

## 🚀 **Quick Start**

### **1. Basic Setup**

```python
from engine.scene.systems.scene_manager import SceneManager
from engine.scene.systems.scene_transition_system import SceneTransitionSystem
from engine.scene.systems.scene_persistence_system import ScenePersistenceSystem

# Initialize scene management systems
scene_manager = SceneManager(world)
transition_system = SceneTransitionSystem(world, base)
persistence_system = ScenePersistenceSystem(world)

# Add systems to world
world.add_system(scene_manager)
world.add_system(transition_system)
world.add_system(persistence_system)
```

### **2. Creating Scenes**

```python
from engine.scene.components.scene_component import SceneComponent

# Create a new scene entity
menu_scene_entity = world.create_entity("menu_scene")

# Add scene component
scene_comp = SceneComponent(
    scene_name="Main Menu",
    scene_id="main_menu",
    is_persistent=True,
    priority=0
)
world.add_component(menu_scene_entity.id, scene_comp)

# Register scene with manager
scene_manager.register_scene_template("main_menu", create_main_menu_scene)
```

### **3. Scene Transitions**

```python
from engine.scene.components.scene_transition_component import SceneTransitionComponent, TransitionType

# Add transition component
transition_comp = SceneTransitionComponent(
    transition_type=TransitionType.FADE,
    duration=1.0,
    easing="ease_in_out"
)
world.add_component(menu_scene_entity.id, transition_comp)

# Start transition
transition_system.start_transition("main_menu", menu_scene_entity.id, "in")
```

### **4. Scene Persistence**

```python
from engine.scene.components.scene_persistence_component import ScenePersistenceComponent

# Add persistence component
persistence_comp = ScenePersistenceComponent(
    auto_save=True,
    auto_save_interval=30.0,
    save_format="json",
    max_save_slots=5
)
world.add_component(menu_scene_entity.id, persistence_comp)

# Save scene manually
persistence_system.save_scene("main_menu", slot=0)

# Load scene
persistence_system.load_scene("main_menu", slot=0)
```

## 🎬 **Scene Lifecycle Management**

### **Scene States**

Scenes progress through well-defined states:

```python
from engine.scene.components.scene_component import SceneState

# Available scene states
SceneState.INACTIVE          # Scene not loaded or visible
SceneState.LOADING           # Scene is being loaded
SceneState.ACTIVE            # Scene is active and running
SceneState.PAUSED            # Scene is paused (background scene)
SceneState.TRANSITIONING_IN  # Scene is transitioning in
SceneState.TRANSITIONING_OUT # Scene is transitioning out
SceneState.UNLOADING         # Scene is being unloaded
```

### **Scene Operations**

```python
# Create scene
scene_id = scene_manager.create_scene("main_menu", scene_id="unique_id")

# Load scene (without activating)
scene_manager.load_scene(scene_id, activate=False)

# Activate scene
scene_manager.activate_scene(scene_id, push_to_stack=True)

# Deactivate scene
scene_manager.deactivate_scene(scene_id, remove_from_stack=False)

# Unload scene
scene_manager.unload_scene(scene_id)

# Destroy scene completely
scene_manager.destroy_scene(scene_id)
```

### **Multi-Scene Coordination**

```python
# Scene stacking for overlays
scene_manager.activate_scene("pause_menu", push_to_stack=True)  # Overlays current
scene_manager.activate_scene("game_level", push_to_stack=False)  # Replaces current

# Scene priorities (lower renders first)
scene_comp.priority = 0  # Background
overlay_comp.priority = 10  # Foreground

# Persistent scenes (stay loaded)
scene_comp.is_persistent = True

# Overlay scenes (render on top)
scene_comp.is_overlay = True
```

## ✨ **Transition Effects**

### **Built-in Transition Types**

```python
from engine.scene.components.scene_transition_component import TransitionType

# Available transition types
TransitionType.IMMEDIATE         # Instant switch
TransitionType.FADE             # Fade to black
TransitionType.FADE_THROUGH_COLOR # Fade to custom color
TransitionType.SLIDE_LEFT       # Slide scenes left
TransitionType.SLIDE_RIGHT      # Slide scenes right
TransitionType.SLIDE_UP         # Slide scenes up
TransitionType.SLIDE_DOWN       # Slide scenes down
TransitionType.PUSH_LEFT        # Push scenes left
TransitionType.PUSH_RIGHT       # Push scenes right
TransitionType.WIPE_LEFT        # Wipe transition left
TransitionType.WIPE_RIGHT       # Wipe transition right
TransitionType.CIRCLE_CLOSE     # Circular close transition
TransitionType.CIRCLE_OPEN      # Circular open transition
TransitionType.CUSTOM           # Custom transition function
```

### **Transition Configuration**

```python
# Fade transition
fade_transition = SceneTransitionComponent(
    transition_type=TransitionType.FADE,
    duration=1.5,
    fade_color=Vec4(0, 0, 0, 1),  # Black
    easing="ease_in_out"
)

# Slide transition
slide_transition = SceneTransitionComponent(
    transition_type=TransitionType.SLIDE_LEFT,
    duration=0.8,
    slide_distance=Vec2(800, 600),
    easing="ease_out"
)

# Circle transition
circle_transition = SceneTransitionComponent(
    transition_type=TransitionType.CIRCLE_CLOSE,
    duration=1.0,
    circle_center=Vec2(0.5, 0.5),  # Screen center
    circle_max_radius=1.0
)
```

### **Custom Transitions**

```python
def custom_spiral_transition(overlay_node, transition_comp, progress):
    """Custom spiral transition effect."""
    import math
    
    # Calculate spiral parameters
    angle = progress * math.pi * 4  # 2 full rotations
    scale = 1.0 - progress
    
    # Apply transformation
    overlay_node.setScale(scale)
    overlay_node.setR(angle * 180 / math.pi)
    overlay_node.setColorScale(1, 1, 1, 1 - progress)

# Apply custom transition
transition_comp = SceneTransitionComponent(
    transition_type=TransitionType.CUSTOM,
    duration=2.0,
    custom_transition_func=custom_spiral_transition
)
```

## 💾 **Scene Persistence**

### **Save Formats**

```python
# JSON format (human-readable)
persistence_comp = ScenePersistenceComponent(
    save_format="json",
    compress_saves=False
)

# Pickle format (fast, binary)
persistence_comp = ScenePersistenceComponent(
    save_format="pickle",
    compress_saves=True
)

# Binary format (compact)
persistence_comp = ScenePersistenceComponent(
    save_format="binary",
    compress_saves=True
)
```

### **Persistence Configuration**

```python
# Configure what to save
persistence_comp.add_persistent_component_type("TransformComponent")
persistence_comp.add_persistent_component_type("SpriteComponent")
persistence_comp.add_excluded_component_type("InputComponent")

# Entity filtering
persistence_comp.add_persistent_entity_tag("saveable")
persistence_comp.add_excluded_entity_tag("temporary")

# Save validation
persistence_comp.validate_saves = True
persistence_comp.backup_saves = True
```

### **Auto-Save Configuration**

```python
# Enable auto-save
persistence_comp = ScenePersistenceComponent(
    auto_save=True,
    auto_save_interval=30.0,  # Save every 30 seconds
    max_save_slots=10
)

# Register for auto-save
persistence_system.register_auto_save("main_menu")

# Custom save data
persistence_comp.add_persistent_data("player_level", 5)
persistence_comp.add_persistent_data("game_settings", settings_dict)
```

### **Save/Load Callbacks**

```python
def on_save_complete(scene_id, slot, filepath):
    print(f"Saved scene {scene_id} to slot {slot}")

def on_load_complete(scene_id, slot, filepath):
    print(f"Loaded scene {scene_id} from slot {slot}")

def on_save_error(scene_id, slot, error):
    print(f"Save failed for {scene_id}: {error}")

# Set callbacks
persistence_comp.on_save_complete = on_save_complete
persistence_comp.on_load_complete = on_load_complete
persistence_comp.on_save_error = on_save_error
```

## 🔧 **Advanced Features**

### **Asset Management**

```python
# Preload assets for scene
scene_comp.assets_to_load = [
    "assets/sprites/player.png",
    "assets/audio/background.ogg",
    "assets/data/level1.json"
]

# Check loading progress
if scene_comp.is_fully_loaded():
    print("All assets loaded!")

progress = scene_comp.loading_progress  # 0.0 to 1.0

# Access loaded assets
player_texture = scene_comp.get_loaded_asset("assets/sprites/player.png")
```

### **Scene Templates**

```python
def create_game_level(scene_name, **kwargs):
    """Template function for creating game levels."""
    # Create scene entity
    entity = world.create_entity(scene_name)
    
    # Create scene component
    scene_comp = SceneComponent(
        scene_name=scene_name,
        scene_id=kwargs.get('scene_id'),
        priority=1
    )
    
    # Add specific assets for this scene
    scene_comp.assets_to_load = [
        "assets/levels/" + kwargs.get('level_file', 'level1.json'),
        "assets/music/" + kwargs.get('music_file', 'level_music.ogg')
    ]
    
    world.add_component(entity.id, scene_comp)
    return entity.id

# Register template
scene_manager.register_scene_template("game_level", create_game_level)

# Create scene from template
level1_id = scene_manager.create_scene(
    "game_level", 
    scene_id="level_1",
    level_file="forest_level.json",
    music_file="forest_ambient.ogg"
)
```

### **Scene Events and Callbacks**

```python
def on_scene_changed(old_scene_id, new_scene_id):
    print(f"Scene changed from {old_scene_id} to {new_scene_id}")

def on_scene_loaded(scene_id, scene_comp):
    print(f"Scene {scene_id} finished loading")

def on_loading_progress(scene_id, progress, is_complete):
    print(f"Loading {scene_id}: {progress*100:.1f}%")

# Set callbacks
scene_manager.on_scene_changed = on_scene_changed
scene_manager.on_scene_loaded = on_scene_loaded
scene_manager.on_loading_progress = on_loading_progress
```

## 🎯 **Common Patterns**

### **Game Menu System**

```python
# Main menu scene
def create_main_menu():
    entity = world.create_entity("main_menu")
    scene_comp = SceneComponent(
        scene_name="Main Menu",
        scene_id="main_menu",
        is_persistent=True,
        priority=0
    )
    world.add_component(entity.id, scene_comp)
    return entity.id

# Pause menu overlay
def create_pause_menu():
    entity = world.create_entity("pause_menu")
    scene_comp = SceneComponent(
        scene_name="Pause Menu",
        scene_id="pause_menu",
        is_overlay=True,
        priority=100,
        auto_pause_background=True
    )
    world.add_component(entity.id, scene_comp)
    return entity.id
```

### **Level Progression**

```python
def load_next_level(current_level_id):
    # Transition out of current level
    transition_system.start_transition(current_level_id, entity_id, "out")
    
    # Create next level
    next_level_id = f"level_{current_level + 1}"
    scene_manager.create_scene("game_level", scene_id=next_level_id)
    
    # Load and transition in
    scene_manager.load_scene(next_level_id)
    transition_system.start_transition(next_level_id, entity_id, "in")
```

### **Save Game System**

```python
def save_game_state():
    """Save all persistent scenes."""
    persistent_scenes = ["main_menu", "player_progress", "game_settings"]
    
    for scene_id in persistent_scenes:
        success = persistence_system.save_scene(scene_id, slot=0)
        if not success:
            print(f"Failed to save {scene_id}")

def load_game_state():
    """Load all persistent scenes."""
    persistent_scenes = ["main_menu", "player_progress", "game_settings"]
    
    for scene_id in persistent_scenes:
        success = persistence_system.load_scene(scene_id, slot=0)
        if not success:
            print(f"Failed to load {scene_id}")
```

## 🛠️ **Integration with Main Game**

### **In main.py**

```python
# Scene management imports
SCENE_MANAGEMENT_AVAILABLE = True
try:
    from engine.scene.systems.scene_manager import SceneManager
    from engine.scene.systems.scene_transition_system import SceneTransitionSystem
    from engine.scene.systems.scene_persistence_system import ScenePersistenceSystem
    from engine.scene.components.scene_component import SceneComponent
    from engine.scene.components.scene_transition_component import SceneTransitionComponent
    from engine.scene.components.scene_persistence_component import ScenePersistenceComponent
except ImportError as e:
    print(f"⚠️  Scene management not available: {e}")
    SCENE_MANAGEMENT_AVAILABLE = False

class Game(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        
        # Initialize scene management if available
        if SCENE_MANAGEMENT_AVAILABLE:
            self.scene_manager = SceneManager(self.world)
            self.transition_system = SceneTransitionSystem(self.world, self)
            self.persistence_system = ScenePersistenceSystem(self.world)
            
            self.world.add_system(self.scene_manager)
            self.world.add_system(self.transition_system)
            self.world.add_system(self.persistence_system)
            
            print("🎬 Scene management initialized")
        else:
            self.scene_manager = None
```

## 📁 **File Organization**

### **Recommended Save Structure**

```
saves/
├── scenes/              # Scene-specific saves
│   ├── main_menu/       # Main menu saves
│   ├── level_1/         # Level 1 saves
│   └── settings/        # Settings saves
├── backups/             # Automatic backups
├── temp/                # Temporary files
└── global/              # Global save data
```

### **Asset Organization**

```
assets/
├── scenes/              # Scene-specific assets
│   ├── menu/            # Menu scene assets
│   ├── levels/          # Level data files
│   └── ui/              # UI assets
├── audio/               # Audio per scene
└── textures/            # Textures per scene
```

## 📊 **Performance Optimization**

### **Memory Management**

```python
# Unload non-persistent scenes
scene_manager.unload_scene("heavy_cutscene")

# Clear asset cache for unused scenes
scene_comp.clear_loaded_assets()

# Set memory-efficient persistence
persistence_comp.memory_efficient = True
persistence_comp.incremental_saves = True
```

### **Transition Performance**

```python
# Use shader effects for better performance
transition_comp.use_shader_effects = True

# Skip intermediate frames for performance
transition_comp.skip_frames = True

# Limit concurrent transitions
transition_system.max_concurrent_transitions = 3
```

## 🐛 **Troubleshooting**

### **Common Issues**

1. **Scene Not Loading**
   - Check if scene template is registered
   - Verify scene ID is unique
   - Ensure required assets exist

2. **Transitions Not Working**
   - Verify SceneTransitionSystem is added to world
   - Check if transition component is added to scene entity
   - Ensure base parameter is passed to transition system

3. **Save/Load Failures**
   - Check file permissions in save directory
   - Verify save format is supported
   - Ensure persistent components are properly configured

### **Debug Information**

```python
# Get scene management statistics
stats = scene_manager.get_scene_stats()
print(f"Active scenes: {stats['active_scenes']}")
print(f"Loading scenes: {stats['loading_scenes']}")

# Check transition status
is_transitioning = transition_system.is_transitioning("scene_id")
progress = transition_system.get_transition_progress("scene_id")

# Get persistence statistics
persistence_stats = persistence_system.get_persistence_stats()
print(f"Auto-save scenes: {persistence_stats['auto_save_scenes']}")
print(f"Total saves: {persistence_stats['total_saves_performed']}")
```

## 📚 **Examples and Tutorials**

### **Demo Files**
- `examples/demos/scene_management_demo.py` - Complete scene management demonstration
- `examples/tutorials/scene_integration.py` - Step-by-step integration tutorial

### **Example Games**
- `examples/games/` - Complete games using the scene management system

## 🔗 **Related Systems**

- **Audio System** - Per-scene audio management
- **Input System** - Scene-specific input handling
- **Render System** - Scene layer rendering
- **Asset Pipeline** - Scene asset loading and caching

---

*For more information, see the complete [API Documentation](../api/) and [Integration Examples](../../examples/).*
