"""
Damage System

Listens for collision events and applies damage based on projectile and health components.
Keeps engine-level logic separate from demos.
"""
from typing import Optional

from engine.core.system import System
from engine.core.events import DamageAppliedEvent, HealthChangedEvent, EntityDiedEvent
from engine.physics.components.projectile_component import ProjectileComponent
from ..components.health_component import HealthComponent
from engine.physics.systems.collision_system import CollisionEvent


class DamageSystem(System):
    """
    Applies damage on collisions when one side is a projectile and the other has health.

    Behavior:
    - If a ProjectileComponent collides with an entity with HealthComponent, apply projectile.damage
    - Respect simple team rules: projectile.owner's team vs target team (no friendly fire when equal)
    - Publish DamageAppliedEvent, HealthChangedEvent, and EntityDiedEvent
    - Handle projectile despawn policy: pierce count, despawn_on_hit
    """

    def __init__(self, world):
        super().__init__(world)
        # subscribe to generic collision events (Panda bridge publishes these for non-triggers)
        self.world.event_manager.subscribe(CollisionEvent, self._on_collision)

    def update(self, dt: float):
        # Decrement invulnerability timers if any
        for entity in self.world.get_entities_with_components(HealthComponent):
            hc = self.world.get_component(entity.id, HealthComponent)
            if hc and hc.invulnerable_time > 0.0:
                hc.invulnerable_time = max(0.0, hc.invulnerable_time - dt)

    def _on_collision(self, event: CollisionEvent):
        a = event.entity_a_id
        b = event.entity_b_id

        proj_a = self.world.get_component(a, ProjectileComponent)
        proj_b = self.world.get_component(b, ProjectileComponent)
        health_a = self.world.get_component(a, HealthComponent)
        health_b = self.world.get_component(b, HealthComponent)

        # Determine damage application direction(s)
        if proj_a and health_b:
            self._apply_projectile_hit(proj_a, a, b)
        if proj_b and health_a:
            self._apply_projectile_hit(proj_b, b, a)

    def _get_team(self, entity_id) -> Optional[str]:
        hc = self.world.get_component(entity_id, HealthComponent)
        return hc.team if hc else None

    def _apply_projectile_hit(self, projectile: ProjectileComponent, projectile_entity_id, target_entity_id):
        # Skip if projectile already dead
        if not projectile.is_alive:
            return

        target_health = self.world.get_component(target_entity_id, HealthComponent)
        if not target_health:
            return

        # Friendly fire check if both have teams
        owner_team = self._get_team(projectile.owner_entity_id) if projectile.owner_entity_id else None
        if owner_team is not None and target_health.team is not None and owner_team == target_health.team:
            return

        # Apply damage respecting i-frames
        if target_health.invulnerable_time > 0.0:
            return

        old = target_health.current_health
        new = target_health.apply_damage(projectile.damage)

        # Publish events
        self.world.event_manager.publish(DamageAppliedEvent(projectile.owner_entity_id, target_entity_id, projectile.damage))
        self.world.event_manager.publish(HealthChangedEvent(target_entity_id, old, new, target_health.max_health))

        # Handle death
        if new <= 0.0:
            self.world.event_manager.publish(EntityDiedEvent(target_entity_id))
            # World will actually remove the entity elsewhere if desired

        # Handle projectile policy
        projectile.pierced_count += 1
        if projectile.despawn_on_hit and projectile.pierced_count >= projectile.max_pierce_count:
            projectile.is_alive = False
