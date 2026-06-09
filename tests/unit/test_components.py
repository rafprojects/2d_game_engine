"""
Unit tests for core components
"""

import pytest
from panda3d.core import Vec2

def test_transform_component_initialization():
    """Test TransformComponent initialization."""
    from engine.graphics.components.transform_component import TransformComponent

    # Test default initialization
    transform = TransformComponent()
    assert (transform.x, transform.y) == (0.0, 0.0)
    assert transform.rotation == 0.0
    assert (transform.scale_x, transform.scale_y) == (1.0, 1.0)

    # Test custom initialization
    transform = TransformComponent(x=10, y=20, rotation=45.0, scale_x=2, scale_y=3)
    assert (transform.x, transform.y) == (10, 20)
    assert transform.rotation == 45.0
    assert (transform.scale_x, transform.scale_y) == (2, 3)

def test_movement_component_initialization():
    """Test MovementComponent initialization."""
    from engine.core.components.movement_component import MovementComponent

    movement = MovementComponent(
        base_speed=2.0,
        acceleration=5.0,
        deceleration=8.0
    )

    assert movement.base_speed == 2.0
    assert movement.acceleration == 5.0
    assert movement.deceleration == 8.0
    assert movement.current_velocity == Vec2(0, 0)
    assert movement.target_velocity == Vec2(0, 0)
    assert movement.can_move == True
    assert len(movement.speed_modifiers) == 0

def test_movement_component_speed_modifiers():
    """Test speed modifier functionality."""
    from engine.core.components.movement_component import MovementComponent

    movement = MovementComponent(base_speed=1.0)

    # Test adding speed modifier
    movement.add_speed_modifier("test_effect", 0.5, 2.0)
    assert "test_effect" in movement.speed_modifiers
    assert movement.speed_modifiers["test_effect"] == (0.5, 2.0)

    # Test effective speed calculation
    effective_speed = movement.get_effective_speed()
    assert effective_speed == 0.5  # base_speed * modifier

    # Test multiple modifiers (boost lasts long enough to survive the update below)
    movement.add_speed_modifier("boost", 2.0, 3.0)
    effective_speed = movement.get_effective_speed()
    assert effective_speed == 1.0  # 1.0 * 0.5 * 2.0

    # Test modifier expiration: only test_effect (2.0s) expires after 2.5s
    movement.update_modifiers(2.5)
    assert "test_effect" not in movement.speed_modifiers
    assert "boost" in movement.speed_modifiers

def test_sprite_component_validation():
    """Test SpriteComponent validation."""
    from engine.graphics.components.sprite_component import SpriteComponent

    # Test valid creation
    sprite = SpriteComponent(image_path="test.png")
    assert sprite.image_path == "test.png"
    assert sprite.layer == 0
    assert sprite.opacity == 1.0

    # Test invalid layer type
    with pytest.raises(TypeError):
        SpriteComponent(image_path="test.png", layer="invalid")

    # Test invalid opacity range
    with pytest.raises(ValueError):
        SpriteComponent(image_path="test.png", opacity=1.5)

    with pytest.raises(ValueError):
        SpriteComponent(image_path="test.png", opacity=-0.1)

def test_input_component_initialization():
    """Test InputComponent initialization."""
    from engine.input.components.input_component import InputComponent
    from engine.input.input_bindings import InputBinding

    bindings = {
        "move_left": [InputBinding(input_type="key", event_name="a")],
        "jump": [InputBinding(input_type="key", event_name="space")]
    }

    input_comp = InputComponent(action_bindings=bindings)

    # Check that action states are initialized
    assert "move_left" in input_comp.action_active
    assert "jump" in input_comp.action_active
    assert input_comp.action_active["move_left"] == False
    assert input_comp.action_just_pressed["move_left"] == False
    assert input_comp.action_just_released["move_left"] == False
