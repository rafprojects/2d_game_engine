"""Scrolling two-layer starfield background."""
from __future__ import annotations

import random

from panda3d.core import CardMaker, Vec4

from engine.core.system import System


class StarfieldSystem(System):
    """Two-layer parallax starfield using CardMaker quads."""

    def __init__(self, world, base, cfg: dict):
        super().__init__(world)
        self._base = base
        self._stars = []

        if not cfg.get("enabled", True):
            return

        self._create_layer(cfg.get("layer_1_count", 60), cfg.get("layer_1_speed", 0.08), 0.005, 0.5)
        self._create_layer(cfg.get("layer_2_count", 35), cfg.get("layer_2_speed", 0.22), 0.008, 1.0)

    def _create_layer(self, count: int, speed: float, size: float, alpha: float):
        for _ in range(count):
            x = random.uniform(-1.4, 1.4)
            y = random.uniform(-1.1, 1.1)
            cm = CardMaker(f"star_{len(self._stars)}")
            cm.setFrame(-size / 2, size / 2, -size / 2, size / 2)
            star_np = self._base.aspect2d.attachNewNode(cm.generate())
            star_np.setPos(x, 0, y)
            star_np.setColor(Vec4(1, 1, 1, alpha))
            star_np.setBin("background", 1)
            self._stars.append((star_np, x, y, speed))

    def update(self, dt: float):
        for i, (star_np, x, y, speed) in enumerate(self._stars):
            y -= speed * dt
            if y < -1.2:
                y = 1.2
            star_np.setPos(x, 0, y)
            self._stars[i] = (star_np, x, y, speed)

    def destroy(self):
        for star_np, _, _, _ in self._stars:
            star_np.removeNode()
        self._stars.clear()
