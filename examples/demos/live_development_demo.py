"""
Live Development Tools Demo

This demo showcases the hot reload, asset hot swap, and component inspector
features working together for real-time development feedback.
"""

import sys
import time
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from engine.core.entity import Entity
from engine.core.component import Component
from engine.core.system import System
from engine.graphics.components.sprite_component import SpriteComponent
from engine.graphics.components.transform_component import TransformComponent
from engine.dev_tools.hot_reload import HotReloadManager
from engine.dev_tools.component_inspector import ComponentInspector

# Mock world class for demo
class DemoEntity:
    def __init__(self, entity_id):
        self.id = entity_id
        self.components = {}
    
    def add_component(self, component):
        self.components[type(component)] = component
    
    def get_component(self, component_type):
        return self.components.get(component_type)


class DemoWorld:
    def __init__(self):
        self.entities = {}
        self.systems = []
        self.next_entity_id = 1
        
        # Initialize live development tools
        self.hot_reload_manager = HotReloadManager(self)
        self.component_inspector = ComponentInspector(self)
        
        # Setup hot reload for engine modules
        self.hot_reload_manager.add_watch_directory(str(project_root / "engine"))
        self.hot_reload_manager.add_watch_directory(str(project_root / "examples"))
        
        # Register some modules for hot reload
        self.hot_reload_manager.register_module("engine.graphics.components.sprite_component")
        self.hot_reload_manager.register_module("engine.graphics.components.transform_component")
        
    def create_entity(self) -> int:
        """Create a new entity and return its ID."""
        entity_id = self.next_entity_id
        entity = DemoEntity(entity_id)
        self.entities[entity_id] = entity
        self.next_entity_id += 1
        return entity_id
    
    def add_component(self, entity_id: int, component: Component):
        """Add a component to an entity."""
        if entity_id in self.entities:
            self.entities[entity_id].add_component(component)
    
    def get_component(self, entity_id: int, component_type: type):
        """Get a component from an entity."""
        if entity_id in self.entities:
            return self.entities[entity_id].get_component(component_type)
        return None
    
    def add_system(self, system: System):
        """Add a system to the world."""
        system.world = self
        self.systems.append(system)
    
    def update(self, dt: float):
        """Update all systems."""
        # Process hot reload queue (must be done from main thread)
        self.hot_reload_manager.process_reload_queue()
        
        # Update all systems
        for system in self.systems:
            try:
                system.update(dt)
            except Exception as e:
                print(f"❌ Error in system {type(system).__name__}: {e}")


def demo_hot_reload():
    """Demonstrate hot reload functionality."""
    print("\n🔥 === HOT RELOAD DEMO ===")
    
    world = DemoWorld()
    
    # Start watching for changes
    world.hot_reload_manager.start_watching()
    
    print("✅ Hot reload is now active!")
    print("📝 Try editing files in the engine/ directory")
    print("🔄 Changes will be automatically reloaded")
    
    # Simulate some runtime
    for i in range(5):
        print(f"⏱️ Running... {i+1}/5")
        world.update(0.016)  # ~60 FPS
        time.sleep(1)
    
    world.hot_reload_manager.stop_watching()
    print("⏹️ Hot reload demo finished")


def demo_component_inspector():
    """Demonstrate component inspector functionality."""
    print("\n🔍 === COMPONENT INSPECTOR DEMO ===")
    
    world = DemoWorld()
    
    # Create some test entities with components
    entity1 = world.create_entity()
    transform1 = TransformComponent(x=100, y=200, rotation=45)
    sprite1 = SpriteComponent(image_path="assets/player.png")
    
    world.add_component(entity1, transform1)
    world.add_component(entity1, sprite1)
    
    entity2 = world.create_entity()
    transform2 = TransformComponent(x=300, y=150, rotation=0)
    sprite2 = SpriteComponent(image_path="assets/player_sheet.png")
    
    world.add_component(entity2, transform2)
    world.add_component(entity2, sprite2)
    
    inspector = world.component_inspector
    
    # List all entities
    print("📋 Entities in world:")
    for entity_id in inspector.list_entities():
        print(f"  - Entity {entity_id}")
        components = inspector.get_entity_components(entity_id)
        for comp_name, comp in components.items():
            print(f"    └─ {comp_name}: {inspector.get_component_info(comp)['properties']}")
    
    # Demonstrate property editing
    print("\n🔧 Editing component properties:")
    
    # Get current transform position
    old_x = inspector.get_component_property(entity1, TransformComponent, 'x')
    print(f"Entity {entity1} transform.x = {old_x}")
    
    # Change the position
    inspector.set_component_property(entity1, TransformComponent, 'x', 500)
    new_x = inspector.get_component_property(entity1, TransformComponent, 'x')
    print(f"Entity {entity1} transform.x = {new_x}")
    
    # Demonstrate undo
    print("\n↶ Testing undo functionality:")
    inspector.undo_last_change()
    undone_x = inspector.get_component_property(entity1, TransformComponent, 'x')
    print(f"After undo, Entity {entity1} transform.x = {undone_x}")
    
    # Demonstrate redo
    print("\n↷ Testing redo functionality:")
    inspector.redo_last_change()
    redone_x = inspector.get_component_property(entity1, TransformComponent, 'x')
    print(f"After redo, Entity {entity1} transform.x = {redone_x}")
    
    # Demonstrate preset saving and loading
    print("\n💾 Testing presets:")
    inspector.save_component_preset(entity1, TransformComponent, "player_start_position")
    
    # Change the position again
    inspector.set_component_property(entity1, TransformComponent, 'x', 1000)
    inspector.set_component_property(entity1, TransformComponent, 'y', 1000)
    changed_x = inspector.get_component_property(entity1, TransformComponent, 'x')
    changed_y = inspector.get_component_property(entity1, TransformComponent, 'y')
    print(f"Changed position to ({changed_x}, {changed_y})")
    
    # Load the preset
    inspector.load_component_preset(entity1, TransformComponent, "player_start_position")
    restored_x = inspector.get_component_property(entity1, TransformComponent, 'x')
    restored_y = inspector.get_component_property(entity1, TransformComponent, 'y')
    print(f"Restored position to ({restored_x}, {restored_y})")
    
    # List available presets
    print(f"\n📁 Available presets: {inspector.list_presets()}")
    
    print("✅ Component inspector demo finished")


def demo_validators():
    """Demonstrate component property validators."""
    print("\n📋 === VALIDATOR DEMO ===")
    
    world = DemoWorld()
    inspector = world.component_inspector
    
    # Create test entity
    entity = world.create_entity()
    transform = TransformComponent(x=100, y=100, rotation=0)
    world.add_component(entity, transform)
    
    # Add a validator for position values
    def position_validator(value):
        """Ensure position values are within screen bounds."""
        return isinstance(value, (int, float)) and 0 <= value <= 1920
    
    def rotation_validator(value):
        """Ensure rotation is between 0 and 360 degrees."""
        return isinstance(value, (int, float)) and 0 <= value <= 360
    
    inspector.add_component_validator(TransformComponent, 'x', position_validator)
    inspector.add_component_validator(TransformComponent, 'y', position_validator)
    inspector.add_component_validator(TransformComponent, 'rotation', rotation_validator)
    
    # Test valid values
    print("🟢 Testing valid values:")
    success = inspector.set_component_property(entity, TransformComponent, 'x', 500)
    print(f"Set x=500: {'✅' if success else '❌'}")
    
    success = inspector.set_component_property(entity, TransformComponent, 'rotation', 180)
    print(f"Set rotation=180: {'✅' if success else '❌'}")
    
    # Test invalid values
    print("\n🔴 Testing invalid values:")
    success = inspector.set_component_property(entity, TransformComponent, 'x', -100)
    print(f"Set x=-100: {'✅' if success else '❌'}")
    
    success = inspector.set_component_property(entity, TransformComponent, 'rotation', 400)
    print(f"Set rotation=400: {'✅' if success else '❌'}")
    
    print("✅ Validator demo finished")


def demo_change_callbacks():
    """Demonstrate change callback functionality."""
    print("\n📞 === CHANGE CALLBACK DEMO ===")
    
    world = DemoWorld()
    inspector = world.component_inspector
    
    # Create test entity
    entity = world.create_entity()
    transform = TransformComponent(x=100, y=100, rotation=0)
    world.add_component(entity, transform)
    
    # Add change callbacks
    def transform_changed(entity_id, component_type, property_name, old_value, new_value):
        print(f"🔔 Transform callback: Entity {entity_id} {property_name} changed from {old_value} to {new_value}")
    
    def position_changed(entity_id, component_type, property_name, old_value, new_value):
        if property_name in ['x', 'y']:
            print(f"📍 Position update detected for entity {entity_id}")
    
    inspector.add_change_callback(TransformComponent, transform_changed)
    inspector.add_change_callback(TransformComponent, position_changed)
    
    # Make some changes to trigger callbacks
    print("Making changes to trigger callbacks:")
    inspector.set_component_property(entity, TransformComponent, 'x', 200)
    inspector.set_component_property(entity, TransformComponent, 'y', 300)
    inspector.set_component_property(entity, TransformComponent, 'rotation', 90)
    
    print("✅ Change callback demo finished")


def main():
    """Run all live development tool demos."""
    print("🚀 Live Development Tools Demo")
    print("=" * 50)
    
    # Note: Hot reload demo is commented out as it requires file changes
    # demo_hot_reload()
    
    demo_component_inspector()
    demo_validators()
    demo_change_callbacks()
    
    print("\n🎉 All demos completed!")
    print("\nTo test hot reload:")
    print("1. Run this demo in a separate terminal")
    print("2. Edit any .py file in the engine/ directory")
    print("3. Watch the console for reload messages")


if __name__ == "__main__":
    main()
