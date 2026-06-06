# engine/core/events.py

class Event:
    """Base class for all events."""
    pass

class EventManager:
    def __init__(self):
        self.listeners = {}

    def subscribe(self, event_type, listener_callback):
        """Subscribe a listener callback to a specific event type."""
        if event_type not in self.listeners:
            self.listeners[event_type] = []
        if listener_callback not in self.listeners[event_type]:
            self.listeners[event_type].append(listener_callback)

    def unsubscribe(self, event_type, listener_callback):
        """Unsubscribe a listener callback from an event type."""
        if event_type in self.listeners:
            if listener_callback in self.listeners[event_type]:
                self.listeners[event_type].remove(listener_callback)
            if not self.listeners[event_type]: # Remove event type if no listeners left
                del self.listeners[event_type]

    def publish(self, event_instance):
        """Publish an event to all subscribed listeners."""
        event_type = type(event_instance)
        if event_type in self.listeners:
            # Iterate over a copy in case listeners unsubscribe themselves during callback
            for listener in list(self.listeners[event_type]):
                listener(event_instance)

# --- Example Specific Event Types (can be moved to more specific modules later) ---

class EntityCreatedEvent(Event):
    def __init__(self, entity_id):
        self.entity_id = entity_id

class EntityDestroyedEvent(Event):
    def __init__(self, entity_id):
        self.entity_id = entity_id

# --- Combat/Health Events ---

class DamageAppliedEvent(Event):
    """Published when damage is applied to a target."""
    def __init__(self, source_entity_id, target_entity_id, amount: float):
        self.source_entity_id = source_entity_id
        self.target_entity_id = target_entity_id
        self.amount = amount

class HealthChangedEvent(Event):
    """Published when an entity's health value changes."""
    def __init__(self, entity_id, old_health: float, new_health: float, max_health: float):
        self.entity_id = entity_id
        self.old_health = old_health
        self.new_health = new_health
        self.max_health = max_health

class EntityDiedEvent(Event):
    """Published when an entity's health reaches zero or below."""
    def __init__(self, entity_id):
        self.entity_id = entity_id

class ComponentAddedEvent(Event):
    def __init__(self, entity_id, component_type, component_instance):
        self.entity_id = entity_id
        self.component_type = component_type
        self.component = component_instance

class ComponentRemovedEvent(Event):
    def __init__(self, entity_id, component_type, component_instance):
        self.entity_id = entity_id
        self.component_type = component_type
        self.component = component_instance
