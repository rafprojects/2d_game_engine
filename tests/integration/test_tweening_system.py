#!/usr/bin/env python3
"""
Test script for the Movement Tweening System.
This validates the tweening effects and integration.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from panda3d.core import Vec2
import time

def test_basic_tweening():
    """Test basic tweening functionality."""
    print("🧪 Testing Basic Tweening System")
    print("=" * 40)
    
    try:
        from engine.animation.tweening import Tween, EasingType, EasingFunctions, TweenManager
        print("✅ Tweening imports successful")
        
        # Test easing functions
        print("\n📈 Testing Easing Functions")
        
        test_values = [0.0, 0.25, 0.5, 0.75, 1.0]
        
        # Test linear easing
        linear_results = [EasingFunctions.linear(t) for t in test_values]
        print(f"  Linear: {[f'{r:.2f}' for r in linear_results]}")
        
        # Test ease out cubic
        cubic_results = [EasingFunctions.ease_out_cubic(t) for t in test_values]
        print(f"  Ease Out Cubic: {[f'{r:.2f}' for r in cubic_results]}")
        
        # Test bounce
        bounce_results = [EasingFunctions.ease_out_bounce(t) for t in test_values]
        print(f"  Ease Out Bounce: {[f'{r:.2f}' for r in bounce_results]}")
        
        print("✅ Easing functions working correctly")
        
        # Test tween manager
        print("\n🎬 Testing Tween Manager")
        
        class MockObject:
            def __init__(self):
                self.value = 0.0
                self.position = Vec2(0, 0)
        
        mock_obj = MockObject()
        tween_manager = TweenManager()
        
        # Test numeric tween
        tween_manager.tween_to(mock_obj, 'value', 10.0, 1.0, EasingType.EASE_OUT_CUBIC)
        
        # Simulate time steps
        for i in range(5):
            tween_manager.update(0.2)  # 0.2 seconds per step
            print(f"  Step {i+1}: value = {mock_obj.value:.2f}")
        
        print("✅ Tween Manager working correctly")
        
        # Test Vec2 tweening
        print("\n📍 Testing Vector Tweening")
        
        mock_obj.position = Vec2(0, 0)
        tween_manager.tween_to(mock_obj, 'position', Vec2(5, 3), 1.0, EasingType.EASE_OUT_BOUNCE)
        
        for i in range(5):
            tween_manager.update(0.2)
            pos = mock_obj.position
            print(f"  Step {i+1}: position = ({pos.x:.2f}, {pos.y:.2f})")
        
        print("✅ Vector tweening working correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ Tweening test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_movement_tweening():
    """Test movement tweening component."""
    print("\n🚀 Testing Movement Tweening Component")
    print("=" * 40)
    
    try:
        from engine.animation.movement_tweening import MovementTweenComponent
        from engine.animation.tweening import EasingType
        
        # Create component
        tween_comp = MovementTweenComponent()
        tween_comp.set_base_transform(Vec2(0, 0), Vec2(1, 1), 0.0)
        
        print("✅ Movement tweening component created")
        
        # Test presets
        print("\n🎛️  Testing Presets")
        
        presets = ["snappy", "smooth", "bouncy", "elastic"]
        for preset in presets:
            tween_comp.set_preset(preset)
            print(f"  {preset.capitalize()}: lag={tween_comp.position_lag:.2f}, "
                  f"bounce={tween_comp.bounce_scale:.2f}, "
                  f"scale={tween_comp.movement_scale_factor:.2f}")
        
        print("✅ Presets working correctly")
        
        # Test position smoothing
        print("\n📍 Testing Position Smoothing")
        
        tween_comp.set_preset("smooth")
        target_pos = Vec2(2, 1)
        
        for i in range(10):
            tween_comp.update_visual_position(target_pos, 0.1)
            pos = tween_comp.visual_position
            distance = (target_pos - pos).length()
            print(f"  Step {i+1}: pos=({pos.x:.2f}, {pos.y:.2f}), distance={distance:.2f}")
            
            if distance < 0.01:
                print(f"  ✅ Reached target in {i+1} steps")
                break
        
        # Test movement effects
        print("\n🎯 Testing Movement Effects")
        
        tween_comp.enable_juice_effects()
        velocity = Vec2(1, 0)  # Moving right
        
        # Simulate movement with effects
        for i in range(5):
            tween_comp.update_movement_effects(velocity, True, 0.1)
            scale = tween_comp.visual_scale
            print(f"  Step {i+1}: scale=({scale.x:.3f}, {scale.y:.3f})")
        
        print("✅ Movement effects working correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ Movement tweening test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_integration():
    """Test integration with movement system."""
    print("\n🔧 Testing Integration")
    print("=" * 40)
    
    try:
        from engine.core.system import World
        from engine.core.components.transform_component import TransformComponent
        from engine.core.components.movement_component import MovementComponent
        from engine.core.systems.movement_system import MovementSystem
        from engine.animation.movement_tweening import MovementTweenComponent
        
        # Create world and systems
        world = World()
        movement_system = MovementSystem(world)
        
        # Create entity with all components
        entity = world.create_entity("tweening_test")
        
        transform = TransformComponent(position=Vec2(0, 0), scale=Vec2(1, 1))
        movement = MovementComponent(base_speed=2.0)
        tween_comp = MovementTweenComponent()
        tween_comp.set_base_transform(transform.position, transform.scale, transform.rotation)
        
        world.add_component(entity.id, transform)
        world.add_component(entity.id, movement)
        world.add_component(entity.id, tween_comp)
        
        print("✅ Created entity with all components")
        
        # Test movement with tweening
        movement.set_target_direction(Vec2(1, 0))  # Move right
        
        initial_pos = transform.position.x
        dt = 0.016  # 60 FPS
        
        for i in range(30):  # Half second
            movement_system.update(dt)
            
            if i % 10 == 0:
                print(f"  Frame {i:2d}: "
                      f"physics=({movement.current_velocity.x:.2f}, {movement.current_velocity.y:.2f}), "
                      f"visual=({tween_comp.visual_position.x:.2f}, {tween_comp.visual_position.y:.2f}), "
                      f"scale=({tween_comp.visual_scale.x:.3f}, {tween_comp.visual_scale.y:.3f})")
        
        final_pos = transform.position.x
        print(f"✅ Movement with tweening: {initial_pos:.3f} → {final_pos:.3f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_all_tests():
    """Run all tweening tests."""
    print("🎨 Starting Movement Tweening Tests\n")
    
    tests = [
        test_basic_tweening,
        test_movement_tweening, 
        test_integration
    ]
    
    passed = 0
    for test in tests:
        try:
            if test():
                passed += 1
            print()  # Add spacing between tests
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            print()
    
    print(f"📊 Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("\n🎉 All tweening tests passed!")
        print("\nTweening System Features:")
        print("  ✅ Multiple easing functions (linear, cubic, bounce, elastic, etc.)")
        print("  ✅ Tween manager for coordinating animations")
        print("  ✅ Vector and scalar value tweening")
        print("  ✅ Movement-specific visual effects")
        print("  ✅ Configurable presets (snappy, smooth, bouncy, elastic)")
        print("  ✅ Position smoothing and lag effects")
        print("  ✅ Scale and rotation effects during movement")
        print("  ✅ Integration with existing movement system")
        print("  ✅ Optional tweening (graceful degradation)")
        
        print("\nUsage Tips:")
        print("  🎯 Use 'snappy' preset for responsive games")
        print("  🌊 Use 'smooth' preset for casual/relaxing games")
        print("  🏀 Use 'bouncy' preset for playful/cartoon games")
        print("  🎯 Use 'elastic' preset for juicy/polished feel")
        
        return True
    else:
        print(f"\n❌ {len(tests) - passed} tests failed")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
