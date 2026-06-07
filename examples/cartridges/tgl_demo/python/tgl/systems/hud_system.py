from __future__ import annotations

from direct.gui.OnscreenText import OnscreenText
from panda3d.core import TextNode

from engine.core.system import System
from tgl.components.player_component import PlayerComponent


class HUDSystem(System):
    """Renders score and lives as OnscreenText overlays."""

    def __init__(self, world, base):
        super().__init__(world)
        self._base = base
        self._score_text = OnscreenText(
            text="SCORE: 0",
            pos=(-1.25, 0.92),
            scale=0.06,
            align=TextNode.ALeft,
            fg=(1, 1, 1, 1),
            shadow=(0, 0, 0, 0.8),
        )
        self._lives_text = OnscreenText(
            text="LIVES: 3",
            pos=(1.25, 0.92),
            scale=0.06,
            align=TextNode.ARight,
            fg=(1, 1, 1, 1),
            shadow=(0, 0, 0, 0.8),
        )
        self._gameover_text: OnscreenText | None = None

    def update(self, dt: float):
        for entity in self.world.get_entities_with_components(PlayerComponent):
            pc = self.world.get_component(entity.id, PlayerComponent)
            if pc is None:
                continue
            self._score_text.setText(f"SCORE: {pc.score}")
            self._lives_text.setText(f"LIVES: {pc.lives}")
            if pc.game_over and self._gameover_text is None:
                self._gameover_text = OnscreenText(
                    text="GAME OVER",
                    pos=(0, 0),
                    scale=0.15,
                    fg=(1, 0.2, 0.2, 1),
                    shadow=(0, 0, 0, 0.9),
                )
            break

    def destroy(self):
        self._score_text.destroy()
        self._lives_text.destroy()
        if self._gameover_text:
            self._gameover_text.destroy()
