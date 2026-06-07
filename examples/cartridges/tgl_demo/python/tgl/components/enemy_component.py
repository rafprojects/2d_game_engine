from engine.core.component import Component


class EnemyComponent(Component):
    def __init__(self, point_value: int = 100, speed: float = 0.4,
                 pattern: str = "straight"):
        self.point_value = point_value
        self.speed = speed
        # Movement patterns: "straight", "sinusoidal", "diagonal_left", "diagonal_right"
        self.pattern = pattern
        self.pattern_time: float = 0.0   # elapsed time used by wave patterns
