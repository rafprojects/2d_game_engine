# Sprite Animation Implementation Plan

This document outlines the step-by-step process for implementing sprite animations in the 2D game engine.

## Phase 1: Basic Setup

1. **Create the SpriteSheet Module**
   - Implement the `SpriteFrame` class
   - Implement the `Animation` class
   - Implement the `SpriteSheet` class with frame management

2. **Enhance SpriteComponent**
   - Add sprite sheet reference
   - Add animation state properties 
   - Add animation control methods

3. **Update RenderSystem**
   - Add support for sprite sheet textures
   - Add UV coordinate manipulation for animations
   - Implement animation frame application

## Phase 2: Animation Control

4. **Implement Animation Control Methods**
   - Play/pause/stop/resume controls
   - Animation transitions
   - Frame event callbacks

5. **Create Animation Testing Tools**
   - Debug visualization for frame boundaries
   - Animation timeline viewer
   - Frame-by-frame stepping

## Phase 3: Advanced Features

6. **Implement Animation State Machine**
   - Define state transitions
   - Automatic animation switching based on conditions
   - Blending between animations

7. **Sprite Batching**
   - Group similar sprites for efficient rendering
   - Instance-based rendering
   - Automatic batching system

8. **Animation Events**
   - Event triggers at specific frames
   - Callback system for animation events
   - Integration with game audio/effects

## Implementation Details

### SpriteSheet Class

```python
class SpriteSheet:
    def __init__(self, texture):
        self.texture = texture
        self.animations = {}
        self.width = texture.getXSize()
        self.height = texture.getYSize()
    
    # Methods for creating animations from different sprite sheet formats
    def create_grid_animation(self, name, rows, cols, row_start, col_start, frame_count, 
                             frame_duration=0.1, loop=True):
        """Create an animation from a uniform grid layout"""
        pass
    
    def create_animation_from_regions(self, name, regions, frame_durations=None, loop=True):
        """Create an animation from specific regions of the sprite sheet"""
        pass
```

### Enhanced SpriteComponent

```python
class SpriteComponent(Component):
    def __init__(self, image_path=None, sprite_sheet=None):
        self.image_path = image_path
        self.sprite_sheet = sprite_sheet
        self.current_animation = None
        self.current_frame_index = 0
        self.animation_time = 0.0
        self.is_playing = True
        self.panda_node = None
    
    def play_animation(self, animation_name, reset=True):
        """Play an animation by name"""
        pass
    
    def update_animation(self, dt):
        """Update animation state based on elapsed time"""
        pass
```

### RenderSystem Animation Support

```python
def _apply_animation_frame(self, node, frame):
    """Apply animation frame UV coordinates to a sprite node"""
    ts = TextureStage.getDefault()
    node.setTexOffset(ts, frame.u_offset, frame.v_offset)
    node.setTexScale(ts, frame.u_size, frame.v_size)
```

## Integration with Input System

To make sprites respond to input:

```python
def update_game(self, task):
    entities = self.world.get_entities_with_components(InputComponent, SpriteComponent)
    
    for entity in entities:
        input_comp = self.world.get_component(entity.id, InputComponent)
        sprite_comp = self.world.get_component(entity.id, SpriteComponent)
        
        # Switch animations based on input
        if input_comp.action_active.get("move_left") or input_comp.action_active.get("move_right"):
            sprite_comp.play_animation("walk")
            sprite_comp.flip_x = input_comp.action_active.get("move_left", False)
        else:
            sprite_comp.play_animation("idle")
```

## Timeline

- Week 1: Basic implementation of SpriteSheet and animation support
- Week 2: Enhance SpriteComponent and update RenderSystem
- Week 3: Testing and debugging
- Week 4: Performance optimization and advanced features

By following this plan, you'll have a fully functional sprite animation system integrated into your game engine.
