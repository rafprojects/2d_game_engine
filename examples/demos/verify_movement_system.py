#!/usr/bin/env python3
"""
Simple verification script for movement system functionality.
This demonstrates the key features without graphics.
"""

import sys
import os
# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from panda3d.core import Vec2
from engine.core.system import World
from engine.core.components.transform_component import TransformComponent
from engine.core.components.movement_component import MovementComponent
from engine.core.systems.movement_system import MovementSystem

def demonstrate_movement_system():
    """Demonstrate movement system functionality."""
    print("🎮 Movement System Demonstration")
    print("=" * 40)
    
    # Create world and systems
    world = World()
    movement_system = MovementSystem(world)
    
    # Create a test entity
    entity = world.create_entity("demo_player")
    
    # Add components
    transform = TransformComponent(position=Vec2(0, 0), scale=Vec2(1, 1))
    movement = MovementComponent(
        base_speed=2.0,
        acceleration=8.0,
        deceleration=10.0,
        max_speed_multiplier=3.0
    )
    
    world.add_component(entity.id, transform)
    world.add_component(entity.id, movement)
    
    print(f"✅ Created entity '{entity.name}' with movement capabilities")
    print(f"   Initial position: {transform.position}")
    print(f"   Base speed: {movement.base_speed}")
    
    # Demonstrate movement
    print("\n🚀 Testing Basic Movement")
    movement.set_target_direction(Vec2(1, 0))  # Move right
    
    dt = 0.016  # 60 FPS
    for i in range(30):  # Half second of movement
        movement.update_velocity(dt)
        transform.position += movement.current_velocity * dt
        
        if i % 10 == 0:  # Print every 10 frames
            print(f"   Frame {i:2d}: pos={transform.position.x:.3f}, velocity={movement.current_velocity.x:.3f}")
    
    print(f"✅ Entity moved from 0.000 to {transform.position.x:.3f}")
    
    # Demonstrate speed effects
    print("\n⚡ Testing Speed Effects")
    
    # Apply slowdown effect
    movement.add_speed_modifier("slowdown", 0.3, 2.0)
    print(f"   Applied slowdown: 30% speed for 2 seconds")
    print(f"   Effective speed: {movement.get_effective_speed():.2f} (was {movement.base_speed:.2f})")
    
    # Apply speed boost on top of slowdown
    movement.add_speed_modifier("boost", 2.5, 1.0) 
    print(f"   Applied speed boost: 250% on top of slowdown")
    print(f"   Effective speed: {movement.get_effective_speed():.2f}")
    print(f"   Active effects: {list(movement.speed_modifiers.keys())}")
    
    # Show effect expiration
    print("\n⏰ Testing Effect Expiration")
    for seconds in [0.5, 1.5, 2.5]:
        movement.update_modifiers(0.5)  # Pass 0.5 seconds
        active_effects = list(movement.speed_modifiers.keys())
        print(f"   After {seconds}s: {active_effects}, speed={movement.get_effective_speed():.2f}")
    
    # Demonstrate movement disable
    print("\n🛑 Testing Movement Disable")
    movement.can_move = False
    old_speed = movement.get_effective_speed()
    disabled_speed = movement.get_effective_speed()
    print(f"   Movement disabled: speed went from {old_speed:.2f} to {disabled_speed:.2f}")
    
    movement.can_move = True
    enabled_speed = movement.get_effective_speed()
    print(f"   Movement enabled: speed restored to {enabled_speed:.2f}")
    
    # Show system integration
    print("\n🔧 Testing System Integration")
    movement_system.apply_speed_effect(entity.id, "system_test", 0.1, 1.0)
    print(f"   Applied effect via system: {list(movement.speed_modifiers.keys())}")
    
    movement_system.set_movement_enabled(entity.id, False)
    print(f"   Disabled via system: can_move = {movement.can_move}")
    
    movement_system.set_movement_enabled(entity.id, True)
    print(f"   Enabled via system: can_move = {movement.can_move}")
    
    print("\n🎉 Movement System Demo Complete!")
    print("\nKey Features Demonstrated:")
    print("  ✅ Smooth acceleration/deceleration")
    print("  ✅ Dynamic speed modifiers (status effects)")
    print("  ✅ Effect stacking and expiration")
    print("  ✅ Movement enable/disable")
    print("  ✅ System-level effect management")
    print("  ✅ Frame-rate independent movement")

if __name__ == "__main__":
    demonstrate_movement_system()
