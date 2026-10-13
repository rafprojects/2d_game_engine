from engine.core.component import Component
from engine.patterns.shmup import PatternState


class EnemyComponent(Component):
    def __init__(self, point_value: int = 100, speed: float = 0.4,
                 pattern: str = "straight",
                 pattern_state: PatternState | None = None):
        self.point_value = point_value
        self.speed = speed
        self.pattern = pattern
        self.pattern_state = pattern_state
        self.pattern_time: float = 0.0
