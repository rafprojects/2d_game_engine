from engine.core.component import Component


class PlayerComponent(Component):
    def __init__(self, health: int = 3, lives: int = 3, score: int = 0):
        self.health = health
        self.lives = lives
        self.score = score
        self.invulnerable_timer: float = 0.0   # seconds remaining of invulnerability
        self.game_over: bool = False
        self.fire_cooldown: float = 0.0         # seconds until next shot allowed
