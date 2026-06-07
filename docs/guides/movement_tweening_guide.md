# Movement Tweening System Documentation

The Movement Tweening System adds optional visual polish and "juice" to the movement in your 2D game engine. It provides smooth visual effects that enhance the feel of movement without affecting the core movement logic.

## Key Features

### 🎯 Visual Effects
- **Position Smoothing**: Visual position lags slightly behind physics position for smooth motion
- **Bounce Effects**: Visual bounce when changing direction quickly
- **Scale Effects**: Slight scaling during movement for added dynamism
- **Rotation Effects**: Optional rotation based on movement direction

### 🎨 Easing Functions
The system includes many easing types:
- Linear, Quad, Cubic, Quart, Sine
- Exponential, Bounce, Elastic
- Each with In, Out, and In-Out variants

### 🎛️ Presets
Pre-configured effect combinations:
- **Snappy**: Quick, responsive (game feels tight)
- **Smooth**: Gentle, flowing (relaxing games)
- **Bouncy**: Exaggerated bounce (cartoon/playful)
- **Elastic**: Spring-like effects (polished/juicy)

## Quick Start

### 1. Add MovementTweenComponent to Entity

```python
from engine.animation.movement_tweening import MovementTweenComponent

# Create player entity with existing components
player_entity = world.create_entity("player")
world.add_component(player_entity.id, TransformComponent(position=Vec2(0, 0), scale=Vec2(1, 1)))
world.add_component(player_entity.id, MovementComponent(base_speed=1.0))

# Add tweening component
tween_comp = MovementTweenComponent()
tween_comp.set_base_transform(Vec2(0, 0), Vec2(1, 1), 0.0)
tween_comp.enable_juice_effects()  # Enable all effects
world.add_component(player_entity.id, tween_comp)
```

### 2. MovementSystem Auto-Integration

The MovementSystem automatically detects and uses MovementTweenComponent when present:

```python
# No code changes needed - MovementSystem handles it automatically!
movement_system = MovementSystem(world)
world.add_system(movement_system)
```

### 3. Configure Effects

```python
# Use presets for quick setup
tween_comp.set_preset("bouncy")   # Fun, exaggerated
tween_comp.set_preset("smooth")   # Gentle, flowing
tween_comp.set_preset("snappy")   # Responsive, tight
tween_comp.set_preset("elastic")  # Spring-like

# Or configure manually
tween_comp.position_lag = 0.15          # How much visual lags behind physics
tween_comp.bounce_scale = 0.2           # Scale increase during bounce
tween_comp.movement_scale_factor = 0.1  # Scale increase while moving
tween_comp.position_easing = EasingType.EASE_OUT_CUBIC
```

## Advanced Usage

### Custom Tween Effects

```python
# Create custom tween on any property
tween_comp.create_custom_effect(
    property_name="visual_scale",
    end_value=Vec2(1.5, 1.5),
    duration=0.3,
    easing=EasingType.EASE_OUT_BOUNCE,
    on_complete=lambda: print("Scale effect complete!")
)
```

### Global Tween Manager

```python
from engine.animation.tweening import global_tween_manager

# Update in your game loop
def update_game(self, task):
    dt = globalClock.getDt()
    
    # Update world (includes movement system with tweening)
    self.world.update(dt)
    
    # Update global tweens (for custom effects)
    global_tween_manager.update(dt)
    
    return task.cont
```

### Runtime Effect Control

```python
# Enable/disable effects dynamically
if game_state == "paused":
    tween_comp.disable_all_effects()
elif game_state == "turbo_mode":
    tween_comp.set_preset("snappy")
    tween_comp.position_lag = 0.05  # More responsive

# Toggle specific effects
tween_comp.bounce_on_direction_change = player.has_ability("bounce")
tween_comp.rotate_on_movement = player.is_spinning
```

## Integration with Existing Code

### Minimal Integration
If you already have MovementComponent and MovementSystem working:

1. **Add the tweening component** to entities that need visual effects
2. **MovementSystem automatically detects and uses it** - no code changes needed
3. **Configure presets** for the desired feel

### Graceful Degradation
The system is designed to be completely optional:

```python
# This code works whether tweening is available or not
try:
    from engine.animation.movement_tweening import MovementTweenComponent
    TWEENING_AVAILABLE = True
except ImportError:
    TWEENING_AVAILABLE = False

if TWEENING_AVAILABLE:
    # Add visual effects
    tween_comp = MovementTweenComponent()
    # ... configure effects
else:
    # Game still works without visual effects
    print("Running without visual effects")
```

## Demo Controls

Run `examples/movement_tweening_demo.py` to see the system in action:

- **WASD**: Move player
- **Q**: Apply slowdown effect
- **E**: Apply speed boost effect  
- **1-4**: Switch between presets (Snappy, Smooth, Bouncy, Elastic)
- **R**: Toggle rotation on movement
- **T**: Toggle all tweening effects

## Performance Notes

- **Lightweight**: Tweening adds minimal overhead
- **Optional**: Can be disabled entirely with no impact
- **Efficient**: Uses object pooling and optimized math
- **Smooth**: 60+ FPS with dozens of tweened entities

## Effect Descriptions

### Position Smoothing
Visual position smoothly follows the physics position with configurable lag. Creates the feeling of weight and momentum.

### Bounce Effects  
When direction changes rapidly, the entity briefly scales up then back down, creating a satisfying "bounce" feeling.

### Movement Scaling
Entity slightly grows when moving, shrinks when stopping. Adds life and energy to movement.

### Rotation Effects
Entity can rotate to face movement direction, with smooth interpolation back to base rotation when stopping.

## Best Practices

1. **Start with presets** - they're balanced for different game feels
2. **Test with your game's camera** - effects may need adjustment based on zoom
3. **Consider your game's theme** - bouncy effects suit cartoon games, smooth suits zen games
4. **Adjust for gameplay** - competitive games might want minimal effects, casual games can use more
5. **Provide player options** - let players adjust or disable effects for accessibility

## Technical Details

- **Separation of Concerns**: Visual effects don't affect physics/collision
- **ECS Compatible**: Integrates cleanly with existing component system  
- **Configurable**: Every aspect can be tweaked
- **Extensible**: Easy to add new easing functions or effect types
- **Performance**: Minimal allocation, efficient updates

The tweening system transforms basic movement into polished, juicy game feel that players will notice and appreciate!
