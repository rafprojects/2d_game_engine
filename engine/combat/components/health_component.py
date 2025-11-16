"""
Health Component

Tracks an entity's current and maximum health along with optional invulnerability frames.
"""
from dataclasses import dataclass
from engine.core.component import Component


@dataclass
class HealthComponent(Component):
    max_health: float = 1.0
    current_health: float = 1.0
    invulnerable_time: float = 0.0  # seconds remaining of invulnerability
    team: str | None = None  # Optional team/faction tag for friendly-fire rules

    def apply_damage(self, amount: float) -> float:
        """Apply damage and return the new health value (clamped)."""
        self.current_health = max(0.0, self.current_health - max(0.0, amount))
        return self.current_health

    def heal(self, amount: float) -> float:
        """Heal and return the new health value (clamped)."""
        self.current_health = min(self.max_health, self.current_health + max(0.0, amount))
        return self.current_health
