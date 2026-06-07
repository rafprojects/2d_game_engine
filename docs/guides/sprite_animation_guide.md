# Sprite Animation Guide

This guide explains how to implement and use sprite animations in the 2D game engine.

## Basic Static Sprites

The engine supports basic static sprites through the `SpriteComponent` class. You can create a sprite by:

1. Creating an entity
2. Adding a `TransformComponent` to position and scale it
3. Adding a `SpriteComponent` with a path to your image

```python
player_entity = self.world.create_entity("player")
self.world.add_component(player_entity.id, 
    TransformComponent(position=Vec2(0, 0), scale=Vec2(1, 1)))
self.world.add_component(player_entity.id, 
    SpriteComponent(image_path="path/to/sprite.png"))
```

## Important Rendering Changes

The engine now uses `aspect2d` instead of `render2d` for rendering sprites. This provides more reliable positioning and scaling across different window sizes and aspect ratios. Key improvements include:

1. Using `aspect2d` for more reliable sprite positioning
2. Improved scaling that works better for common sprite sizes
3. Automatic transparency handling for sprites with alpha channels
4. Better debugging support for sprite visibility issues

## Implementing Sprite Animations

To implement sprite animations, you'll need to extend the current system with the following components:

### 1. SpriteSheet Class

Create a `SpriteSheet` class that manages multiple frames from a single texture:

```python
# engine/graphics/sprite_sheet.py
class SpriteFrame:
    """Represents a single frame in a sprite animation"""
    def __init__(self, texture, u_offset, v_offset, u_size, v_size, duration=0.1):
        self.texture = texture        # The full sprite sheet texture
        self.u_offset = u_offset      # UV coordinates (left)
        self.v_offset = v_offset      # UV coordinates (top)
        self.u_size = u_size          # UV width
        self.v_size = v_size          # UV height
        self.duration = duration      # How long to display (seconds)

class Animation:
    """A sequence of sprite frames"""
    def __init__(self, name, frames, loop=True):
        self.name = name
        self.frames = frames
        self.loop = loop
        self.total_duration = sum(frame.duration for frame in frames)

class SpriteSheet:
    """Handles sprite sheets and animations"""
    def __init__(self, texture=None):
        self.texture = texture
        self.animations = {}
        self.width = texture.getXSize() if texture else 0
        self.height = texture.getYSize() if texture else 0
    
    def create_grid_animation(self, name, rows, cols, 
                              row_start, col_start, frame_count,
                              frame_duration=0.1, loop=True):
        """Create an animation from a grid-based sprite sheet"""
        frames = []
        frame_width = 1.0 / cols
        frame_height = 1.0 / rows
        
        for i in range(frame_count):
            grid_x = (col_start + i) % cols
            grid_y = row_start + ((col_start + i) // cols)
            
            u = grid_x * frame_width
            v = 1.0 - ((grid_y + 1) * frame_height)
            
            frames.append(SpriteFrame(
                self.texture, u, v, frame_width, frame_height, frame_duration
            ))
            
        animation = Animation(name, frames, loop)
        self.animations[name] = animation
        return animation
```

### 2. Enhanced SpriteComponent

Extend the `SpriteComponent` to support animations:

```python
class SpriteComponent(Component):
    def __init__(self, image_path=None, layer=0, color=Vec4(1,1,1,1), 
                 sprite_sheet=None, flip_x=False, flip_y=False):
        self.image_path = image_path
        self.layer = layer
        self.color = color
        self.flip_x = flip_x
        self.flip_y = flip_y
        
        # Animation properties
        self.sprite_sheet = sprite_sheet
        self.current_animation = None
        self.current_frame_index = 0
        self.animation_time = 0.0
        self.is_playing = True
        
        self.panda_node = None
    
    def play_animation(self, animation_name, reset=True):
        """Play the specified animation"""
        if not self.sprite_sheet:
            return False
            
        animation = self.sprite_sheet.get_animation(animation_name)
        if animation:
            self.current_animation = animation_name
            if reset:
                self.current_frame_index = 0
                self.animation_time = 0.0
            self.is_playing = True
            return True
        return False
    
    def update_animation(self, dt):
        """Update animation based on elapsed time"""
        if not self.sprite_sheet or not self.current_animation or not self.is_playing:
            return
            
        animation = self.sprite_sheet.get_animation(self.current_animation)
        if not animation:
            return
            
        self.animation_time += dt
        
        # Handle looping/ending
        if self.animation_time >= animation.total_duration:
            if animation.loop:
                self.animation_time %= animation.total_duration
            else:
                self.animation_time = animation.total_duration
                self.is_playing = False
                self.current_frame_index = len(animation.frames) - 1
                return
        
        # Find the correct frame based on elapsed time
        elapsed = self.animation_time
        for i, frame in enumerate(animation.frames):
            if elapsed <= frame.duration:
                self.current_frame_index = i
                break
            elapsed -= frame.duration
```

### 3. Updated RenderSystem

Modify the `RenderSystem` to handle animated sprites:

```python
def _apply_animation_frame(self, node, frame, flip_x=False, flip_y=False):
    """Apply UV coordinates from an animation frame"""
    ts = TextureStage.getDefault()
    
    # Set the UV offsets/scale
    node.setTexOffset(ts, frame.u_offset, frame.v_offset)
    node.setTexScale(ts, frame.u_size, frame.v_size)
    
    # Handle flipping if needed
    if flip_x:
        node.setTexScale(ts, -frame.u_size, frame.v_size)
        node.setTexOffset(ts, frame.u_offset + frame.u_size, frame.v_offset)
    # ...similar for flip_y and both

def update(self, dt):
    # For each sprite entity...
    
    # Update animation if applicable
    if sprite.sprite_sheet and sprite.current_animation:
        sprite.update_animation(dt)
    
    # Apply animation frame if needed
    if sprite.sprite_sheet and sprite.current_animation:
        current_frame = sprite.get_current_frame()
        if current_frame:
            self._apply_animation_frame(sprite.panda_node, current_frame)
```

## Using Animated Sprites

Here's an example of how to use animated sprites:

```python
# Load a sprite sheet texture
texture = loader.loadTexture("assets/player_sheet.png")
sprite_sheet = SpriteSheet(texture)

# Create animations
sprite_sheet.create_grid_animation("idle", rows=4, cols=4, 
                                 row_start=0, col_start=0, 
                                 frame_count=4, frame_duration=0.15)
sprite_sheet.create_grid_animation("walk", rows=4, cols=4, 
                                 row_start=1, col_start=0, 
                                 frame_count=4, frame_duration=0.15)

# Create the sprite component with animations
sprite_comp = SpriteComponent(sprite_sheet=sprite_sheet)
sprite_comp.play_animation("idle")  # Start with idle animation

# Add to entity
self.world.add_component(player_entity.id, sprite_comp)
```

## Controlling Animations with Input

You can control animations based on player input:

```python
# In your update loop:
if input_comp.action_active.get("move_left") or input_comp.action_active.get("move_right"):
    if sprite_comp.current_animation != "walk":
        sprite_comp.play_animation("walk")
    
    # Also update sprite direction
    if input_comp.action_active.get("move_left"):
        sprite_comp.flip_x = True
    else:
        sprite_comp.flip_x = False
else:
    if sprite_comp.current_animation != "idle":
        sprite_comp.play_animation("idle")
```

## Further Enhancements

To make your animation system even more powerful, consider:

1. **Animation state machines**: Create a formal state machine for complex animation transitions
2. **Animation events**: Trigger events at specific frames (e.g., footstep sounds)
3. **Skeletal animations**: For more complex character movements
4. **Animation blending**: For smooth transitions between animations

The examples folder contains sample implementations to help you get started.
