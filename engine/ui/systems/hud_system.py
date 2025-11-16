"""
HUD System (Framework)

Subscribes to HealthChangedEvent and EntityDiedEvent to provide hooks for drawing HUD elements.
This is a minimal scaffold; actual rendering can be added later (e.g., using OnscreenText).
"""
from engine.core.system import System
from engine.core.events import HealthChangedEvent, EntityDiedEvent


class HUDSystem(System):
    def __init__(self, world, base=None):
        super().__init__(world)
        self.base = base
        self.world.event_manager.subscribe(HealthChangedEvent, self._on_health_changed)
        self.world.event_manager.subscribe(EntityDiedEvent, self._on_entity_died)
        # Placeholder storage for per-entity HUD widgets if needed
        self._widgets = {}

    def update(self, dt: float):
        # No-op for now
        pass

    def _on_health_changed(self, event: HealthChangedEvent):
        # Hook point: update a health bar for event.entity_id
        # print(f"HUD: {event.entity_id} health {event.old_health}->{event.new_health}/{event.max_health}")
        return

    def _on_entity_died(self, event: EntityDiedEvent):
        # Hook point: show death indicator or remove HUD widget
        # print(f"HUD: {event.entity_id} died")
        return
