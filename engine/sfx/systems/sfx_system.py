"""
SFX System (Framework)

Subscribes to common gameplay events and maps them to sound cues.
This is a scaffold; actual playback can be wired to the existing audio system later.
"""
from engine.core.system import System
from engine.core.events import DamageAppliedEvent, EntityDiedEvent


class SFXSystem(System):
    def __init__(self, world, audio_manager=None):
        super().__init__(world)
        self.audio_manager = audio_manager
        self.world.event_manager.subscribe(DamageAppliedEvent, self._on_damage)
        self.world.event_manager.subscribe(EntityDiedEvent, self._on_death)

    def update(self, dt: float):
        pass

    def _on_damage(self, event: DamageAppliedEvent):
        # Hook: play hit sound
        # if self.audio_manager:
        #     self.audio_manager.play_sfx('hit')
        return

    def _on_death(self, event: EntityDiedEvent):
        # Hook: play death sound
        # if self.audio_manager:
        #     self.audio_manager.play_sfx('death')
        return
