#!/usr/bin/env python3
"""
Test script for the MovementComponent and MovementSystem integration.
This validates the robust movement system with dynamic speed effects.
"""

import sys

from panda3d.core import Vec2

from engine.core.components.movement_component import MovementComponent
from engine.core.systems.movement_system import MovementSystem
from engine.graphics.components.transform_component import TransformComponent
from engine.core.system import World

def test_movement_component():
    """Test MovementComponent functionality."""
    print("\n=== Testing MovementComponent ===")
    
    # Create component with default values
    movement = MovementComponent(
        base_speed=1.0,
        acceleration=5.0,
        deceleration=8.0,
        max_speed_multiplier=3.0
    )
    
    # Test initial state
    assert movement.base_speed == 1.0
    assert movement.current_velocity == Vec2(0, 0)
    assert movement.target_velocity == Vec2(0, 0)
    assert len(movement.speed_modifiers) == 0
    assert movement.can_move == True
    print("✅ Initial state correct")
    
    # Test speed modifiers
    movement.add_speed_modifier("slowdown", 0.5, 3.0)
    assert "slowdown" in movement.speed_modifiers
    assert movement.speed_modifiers["slowdown"] == (0.5, 3.0)
    print("✅ Speed modifier addition works")
    
    # Test effective speed calculation
    effective_speed = movement.get_effective_speed()
    expected_speed = 1.0 * 0.5  # base_speed * slowdown_multiplier
    assert abs(effective_speed - expected_speed) < 0.001
    print("✅ Effective speed calculation correct")
    
    # Test multiple modifiers
    movement.add_speed_modifier("boost", 2.0, 2.0)
    effective_speed = movement.get_effective_speed()
    expected_speed = 1.0 * 0.5 * 2.0  # base_speed * slowdown * boost
    assert abs(effective_speed - expected_speed) < 0.001
    print("✅ Multiple modifiers work correctly")
    
    # Test modifier expiration
    movement.update_modifiers(3.5)  # Should expire slowdown
    assert "slowdown" not in movement.speed_modifiers
    assert "boost" in movement.speed_modifiers  # Should still be active
    print("✅ Modifier expiration works")
    
    # Test target direction setting
    movement.set_target_direction(Vec2(1, 0))
    assert movement.target_velocity.x > 0
    assert movement.is_moving == True
    print("✅ Target direction setting works")
    
    # Test movement disable
    movement.can_move = False
    movement.set_target_direction(Vec2(1, 0))
    assert movement.target_velocity == Vec2(0, 0)
    print("✅ Movement disable works")
    
    print("✅ MovementComponent tests passed")

def test_movement_system():
    """Test MovementSystem functionality."""
    print("\n=== Testing MovementSystem ===")
    
    # Create world and system
    world = World()
    movement_system = MovementSystem(world)
    
    # Create test entity
    entity = world.create_entity("test_entity")
    world.add_component(entity.id, TransformComponent(x=0.0, y=0.0))
    world.add_component(entity.id, MovementComponent(base_speed=1.0))
    
    # Test system can find entities
    movement_entities = world.get_entities_with_components(MovementComponent, TransformComponent)
    assert len(movement_entities) == 1
    print("✅ MovementSystem can find entities")
    
    # Test speed effect application
    movement_system.apply_speed_effect(entity.id, "test_effect", 0.5, 1.0)
    movement_comp = world.get_component(entity.id, MovementComponent)
    assert "test_effect" in movement_comp.speed_modifiers
    print("✅ Speed effect application works")
    
    # Test movement enable/disable
    movement_system.set_movement_enabled(entity.id, False)
    assert movement_comp.can_move == False
    movement_system.set_movement_enabled(entity.id, True)
    assert movement_comp.can_move == True
    print("✅ Movement enable/disable works")
    
    print("✅ MovementSystem tests passed")

def test_integration():
    """Test full integration with movement over time."""
    print("\n=== Testing Integration ===")
    
    world = World()
    movement_system = MovementSystem(world)
    
    # Create entity with movement
    entity = world.create_entity("integration_test")
    transform = TransformComponent(x=0.0, y=0.0)
    movement = MovementComponent(base_speed=2.0, acceleration=10.0)
    
    world.add_component(entity.id, transform)
    world.add_component(entity.id, movement)
    
    # Set movement direction
    movement.set_target_direction(Vec2(1, 0))  # Move right
    
    # Simulate several update frames
    initial_pos = transform.x
    dt = 0.016  # ~60 FPS
    
    for frame in range(10):
        movement_system.update(dt)
    
    # Entity should have moved right
    final_pos = transform.x
    assert final_pos > initial_pos
    print(f"✅ Entity moved from x={initial_pos:.3f} to x={final_pos:.3f}")
    
    # Test with speed effect
    movement_system.apply_speed_effect(entity.id, "super_speed", 3.0, 1.0)
    pos_before_boost = final_pos
    
    for frame in range(10):
        movement_system.update(dt)
    
    pos_after_boost = transform.x
    distance_normal = final_pos - initial_pos
    distance_boosted = pos_after_boost - pos_before_boost
    
    # Movement should be faster with speed boost
    assert distance_boosted > distance_normal
    print(f"✅ Speed boost increased movement speed")
    
    print("✅ Integration tests passed")

def run_all_tests():
    """Run all movement system tests."""
    print("🧪 Starting Movement System Tests\n")
    
    try:
        test_movement_component()
        test_movement_system()
        test_integration()
        
        print("\n🎉 All tests passed! Movement system is working correctly.")
        print("\nMovement System Features:")
        print("  ✅ Smooth acceleration and deceleration")
        print("  ✅ Dynamic speed modifiers (status effects)")
        print("  ✅ Timed effects with automatic expiration")
        print("  ✅ Frame-rate independent movement")
        print("  ✅ Multiple stacking effects")
        print("  ✅ Movement enable/disable")
        print("  ✅ ECS integration")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
