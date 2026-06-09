"""
Unit tests for core systems
"""

def test_world_entity_creation():
    """Test World entity creation and management."""
    from engine.core.system import World

    world = World()

    # Test entity creation
    entity = world.create_entity("test_entity")
    assert entity.name == "test_entity"
    assert entity.id in world.entities
    assert entity.id in world.components

    # Test entity retrieval by name
    retrieved = world.get_entity_by_name("test_entity")
    assert retrieved is not None
    assert retrieved.id == entity.id

def test_world_component_management():
    """Test World component addition and retrieval."""
    from engine.core.system import World
    from engine.graphics.components.transform_component import TransformComponent

    world = World()
    entity = world.create_entity()

    # Test component addition
    transform = TransformComponent(x=5, y=10)
    world.add_component(entity.id, transform)

    # Test component retrieval
    retrieved_transform = world.get_component(entity.id, TransformComponent)
    assert retrieved_transform is not None
    assert (retrieved_transform.x, retrieved_transform.y) == (5, 10)

    # Test entities with component query
    entities_with_transform = world.get_entities_with_component(TransformComponent)
    assert len(entities_with_transform) == 1
    assert entities_with_transform[0].id == entity.id

def test_world_component_removal():
    """Test World component removal."""
    from engine.core.system import World
    from engine.graphics.components.transform_component import TransformComponent

    world = World()
    entity = world.create_entity()
    transform = TransformComponent()

    world.add_component(entity.id, transform)
    assert world.get_component(entity.id, TransformComponent) is not None

    # Test component removal
    world.remove_component(entity.id, TransformComponent)
    assert world.get_component(entity.id, TransformComponent) is None

def test_world_entity_removal():
    """Test World entity removal."""
    from engine.core.system import World
    from engine.graphics.components.transform_component import TransformComponent

    world = World()
    entity = world.create_entity("test_entity")
    world.add_component(entity.id, TransformComponent())

    # Verify entity exists
    assert entity.id in world.entities
    assert entity.id in world.components

    # Remove entity
    world.remove_entity(entity.id)

    # Verify entity is removed
    assert entity.id not in world.entities
    assert entity.id not in world.components
    assert world.get_entity_by_name("test_entity") is None

def test_world_multiple_component_query():
    """Test querying entities with multiple components."""
    from engine.core.system import World
    from engine.graphics.components.transform_component import TransformComponent
    from engine.core.components.movement_component import MovementComponent

    world = World()

    # Create entity with just transform
    entity1 = world.create_entity("entity1")
    world.add_component(entity1.id, TransformComponent())

    # Create entity with both components
    entity2 = world.create_entity("entity2")
    world.add_component(entity2.id, TransformComponent())
    world.add_component(entity2.id, MovementComponent())

    # Query for entities with both components
    entities_with_both = world.get_entities_with_components(
        TransformComponent, MovementComponent
    )

    assert len(entities_with_both) == 1
    assert entities_with_both[0].id == entity2.id

def test_event_manager():
    """Test EventManager functionality."""
    from engine.core.events import EventManager, Event

    class TestEvent(Event):
        def __init__(self, data):
            self.data = data

    event_manager = EventManager()
    received_events = []

    def event_handler(event):
        received_events.append(event)

    # Test subscription
    event_manager.subscribe(TestEvent, event_handler)

    # Test event publishing
    test_event = TestEvent("test_data")
    event_manager.publish(test_event)

    assert len(received_events) == 1
    assert received_events[0].data == "test_data"

    # Test unsubscription
    event_manager.unsubscribe(TestEvent, event_handler)
    event_manager.publish(TestEvent("should_not_receive"))

    # Should still only have one event
    assert len(received_events) == 1
