# import uuid
from .events import EventManager, EntityCreatedEvent, EntityDestroyedEvent, ComponentAddedEvent, ComponentRemovedEvent
from .entity import Entity


class System:
    """
    Base class for all systems.
    Systems implement game logic and operate on entities with specific components.
    """
    def __init__(self, world):
        self.world = world

    def update(self, dt):
        """
        Update method called every frame.
        dt: delta time since last frame.
        """
        raise NotImplementedError

class World:
    """
    Manages entities, components, and systems.
    """
    def __init__(self):
        self.entities = {}  # entity_id -> Entity
        self.components = {}  # entity_id -> {component_type: component_instance}
        self.systems = []
        self.event_manager = EventManager()  # Initialize EventManager

        self.event_manager.subscribe(EntityCreatedEvent, self._on_entity_created_event)
        self.event_manager.subscribe(EntityDestroyedEvent, self._on_entity_destroyed_event)
        self.event_manager.subscribe(ComponentAddedEvent, self._on_component_added_event)
        self.event_manager.subscribe(ComponentRemovedEvent, self._on_component_removed_event)

    def create_entity(self, name=None):
        entity = Entity(name)
        self.entities[entity.id] = entity
        self.components[entity.id] = {}
        self.event_manager.publish(EntityCreatedEvent(entity.id))  # Publish event
        return entity

    def add_component(self, entity_id, component_instance):
        component_type = type(component_instance)
        if entity_id not in self.entities:
            print(f"Warning: Attempted to add component to non-existent entity {entity_id}")
            return
        self.components[entity_id][component_type] = component_instance
        self.event_manager.publish(ComponentAddedEvent(entity_id, component_type, component_instance))  # Publish event

    def get_component(self, entity_id, component_type):
        if entity_id not in self.components:
            return None
        return self.components[entity_id].get(component_type)

    def remove_component(self, entity_id, component_type):
        if entity_id in self.components and component_type in self.components[entity_id]:
            component_instance = self.components[entity_id][component_type]
            # Publish event BEFORE actual removal
            self.event_manager.publish(ComponentRemovedEvent(entity_id, component_type, component_instance))

            if hasattr(component_instance, 'panda_node') and component_instance.panda_node:
                component_instance.panda_node.removeNode()
                component_instance.panda_node = None
            del self.components[entity_id][component_type]

    def remove_entity(self, entity_id):
        if entity_id in self.entities:
            # Publish event BEFORE actual removal
            self.event_manager.publish(EntityDestroyedEvent(entity_id))

            # Remove all components, which should trigger their cleanup and events
            for component_type in list(self.components[entity_id].keys()):
                self.remove_component(entity_id, component_type)  # This will also publish ComponentRemovedEvent

            if entity_id in self.components:  # Check if components dict still has the entity_id key
                del self.components[entity_id]
            if entity_id in self.entities:  # Check if entities dict still has the entity_id key
                del self.entities[entity_id]

    def get_entities_with_component(self, component_type):
        entities = []
        for entity_id, components in self.components.items():
            if component_type in components:
                entities.append(self.entities[entity_id])
        return entities

    def get_entities_with_components(self, *component_types):
        entities = []
        for entity_id, components_map in self.components.items():
            if all(ct in components_map for ct in component_types):
                entities.append(self.entities[entity_id])
        return entities
        
    def get_entity_by_name(self, name):
        """
        Retrieve an entity by its name.
        Returns the first entity found with the specified name, or None if not found.
        """
        for entity in self.entities.values():
            if entity.name == name:
                return entity
        return None

    def add_system(self, system_instance):
        self.systems.append(system_instance)

        if hasattr(system_instance, "on_entity_added") and callable(system_instance.on_entity_added):
            for entity_id in self.entities:
                system_instance.on_entity_added(entity_id)

        if hasattr(system_instance, "on_component_added") and callable(system_instance.on_component_added):
            for entity_id in self.entities:
                for component_type, component_instance in self.components.get(entity_id, {}).items():
                    system_instance.on_component_added(entity_id, component_instance)

    def update(self, dt):
        for system in self.systems:
            system.update(dt)

    def _on_entity_created_event(self, event: EntityCreatedEvent):
        for system in self.systems:
            if hasattr(system, "on_entity_added") and callable(system.on_entity_added):
                system.on_entity_added(event.entity_id)

    def _on_entity_destroyed_event(self, event: EntityDestroyedEvent):
        # Pass all components of the removed entity to the system hook
        entity_components = self.components.get(event.entity_id, {}).copy()
        for system in self.systems:
            if hasattr(system, "on_entity_removed") and callable(system.on_entity_removed):
                system.on_entity_removed(event.entity_id, entity_components)

    def _on_component_added_event(self, event: ComponentAddedEvent):
        for system in self.systems:
            if hasattr(system, "on_component_added") and callable(system.on_component_added):
                system.on_component_added(event.entity_id, event.component)

    def _on_component_removed_event(self, event: ComponentRemovedEvent):
        for system in self.systems:
            if hasattr(system, "on_component_removed") and callable(system.on_component_removed):
                system.on_component_removed(event.entity_id, event.component)
