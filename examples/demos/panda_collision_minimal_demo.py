"""
Minimal Panda3D Collision Demo

Spawns a player and an enemy with Panda collision, fires a projectile,
and enables collision-node visualization.
"""
import os
import sys

from direct.showbase.ShowBase import ShowBase
from direct.showbase.ShowBaseGlobal import globalClock
from panda3d.core import Vec2, Vec4

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from engine.core.system import World
from engine.graphics.components.transform_component import TransformComponent
from engine.graphics.components.sprite_component import SpriteComponent
from engine.graphics.systems.render_system import RenderSystem
from engine.physics.components.collider_component import ColliderComponent
from engine.physics.typesg.collider_type import ColliderType
from engine.physics.systems.panda_collision_system import PandaCollisionSystem, PandaCollisionEvent
from engine.physics.systems.collision_system import CollisionEvent, TriggerEnterEvent, TriggerExitEvent
from engine.physics.systems.projectile_system import ProjectileSystem
from engine.physics.typesg import CollisionLayer, mask_of


class Demo(ShowBase):
    def __init__(self):
        super().__init__()
        self.world = World()
        self._viz_toggle_cooldown = 0.0

        # Systems
        self.render_system = RenderSystem(self.world, self)
        self.world.add_system(self.render_system)

        self.panda_col = PandaCollisionSystem(self.world, base=self)
        self.world.add_system(self.panda_col)

        self.projectiles = ProjectileSystem(self.world)
        self.world.add_system(self.projectiles)

        # Subscribe to events
        self.world.event_manager.subscribe(PandaCollisionEvent, self.on_panda_collision)
        self.world.event_manager.subscribe(CollisionEvent, self.on_collision)
        self.world.event_manager.subscribe(TriggerEnterEvent, self.on_trigger_enter)
        self.world.event_manager.subscribe(TriggerExitEvent, self.on_trigger_exit)

        # Define simple playfield bounds in aspect2d units and create boundary colliders
        # Visible X ~ [-1, 1], Z(Y in 2D) ~ [-0.75, 0.75] approximately
        self.panda_col.set_playfield_bounds(min_x=-1.1, min_y=-0.8, max_x=1.1, max_y=0.8)

        # Player (green rectangle)
        player = self.world.create_entity("player")
        self.player_id = str(player.id)
        # Place inside aspect2d visible range (-1..1 on X), with a comfortable size
        self.world.add_component(player.id, TransformComponent(x=-0.6, y=0.0, scale_x=0.6, scale_y=0.6))
        self.world.add_component(player.id, SpriteComponent(image_path=None, layer=1, color=Vec4(0, 1, 0, 1)))
        self.world.add_component(player.id, ColliderComponent(
            collider_type=ColliderType.RECTANGLE,
            size=Vec2(0.5, 0.5),
            collision_layer=int(CollisionLayer.PLAYER),
            collision_mask=mask_of(CollisionLayer.ENEMY, CollisionLayer.BOUNDARY)
        ))

        # Enemy (red rectangle)
        enemy = self.world.create_entity("enemy")
        self.world.add_component(enemy.id, TransformComponent(x=0.6, y=0.0, scale_x=0.7, scale_y=0.7))
        self.world.add_component(enemy.id, SpriteComponent(image_path=None, layer=1, color=Vec4(1, 0, 0, 1)))
        self.world.add_component(enemy.id, ColliderComponent(
            collider_type=ColliderType.RECTANGLE,
            size=Vec2(0.6, 0.6),
            collision_layer=int(CollisionLayer.ENEMY),
            collision_mask=mask_of(CollisionLayer.PLAYER, CollisionLayer.PLAYER_BULLET, CollisionLayer.BOUNDARY)
        ))

        # Show collision visualization
        self.panda_col.show_collision_nodes(True)

        # Fire a short burst of player bullets toward the enemy, repeating every 0.6s
        self._shots_remaining = 6

        def fire_burst(task):
            if self._shots_remaining <= 0:
                return task.done
            # Start bullet near player so everything is visible and in-range
            start = Vec2(-0.5, 0.0)
            direction = Vec2(1.0, 0.0)
            bullet_id = self.projectiles.create_projectile(
                position=start,
                direction=direction,
                speed=2.5,
                lifetime=5.0,
                damage=1.0,
                owner_entity_id=str(player.id),
                projectile_type="player_bullet",
            )
            # Configure collision for player bullet
            col = self.world.get_component(bullet_id, ColliderComponent)
            if col:
                col.collision_layer = int(CollisionLayer.PLAYER_BULLET)
                col.collision_mask = mask_of(CollisionLayer.ENEMY, CollisionLayer.BOUNDARY)
            self._shots_remaining -= 1
            task.delayTime = 0.6
            return task.again if self._shots_remaining > 0 else task.done

        self.taskMgr.doMethodLater(0.5, fire_burst, "fire_burst")

        # Optional: hold Space to continuously fire
        self._fire_cooldown = 0.0

        # Update loop
        self.taskMgr.add(self.update, "update")

    # Event handlers
    def on_panda_collision(self, e: PandaCollisionEvent):
        print(f"🐼 PandaCollision: {e.entity_a_id} ↔ {e.entity_b_id} @ {e.collision_point}")
        # Briefly highlight
        self.panda_col.highlight_collision(str(e.entity_a_id))
        self.panda_col.highlight_collision(str(e.entity_b_id))

    def on_collision(self, e: CollisionEvent):
        print(f"💥 Collision: {e.entity_a_id} ↔ {e.entity_b_id} n={e.collision_normal}")

    def on_trigger_enter(self, e: TriggerEnterEvent):
        print(f"🚪 TriggerEnter: {e.trigger_entity_id} -> {e.other_entity_id}")

    def on_trigger_exit(self, e: TriggerExitEvent):
        print(f"🚪 TriggerExit: {e.trigger_entity_id} x {e.other_entity_id}")

    def update(self, task):
        dt = globalClock.getDt()
        self.world.update(dt)
        # Toggle collision viz with "v"
        if self.mouseWatcherNode and self.mouseWatcherNode.is_button_down("v"):
            if self._viz_toggle_cooldown <= 0.0:
                current = self.panda_col.is_collision_nodes_visible()
                self.panda_col.show_collision_nodes(not current)
                self._viz_toggle_cooldown = 0.3
        if self._viz_toggle_cooldown > 0.0:
            self._viz_toggle_cooldown -= dt

        # Hold-to-fire (Space)
        if self.mouseWatcherNode and self.mouseWatcherNode.is_button_down("space"):
            if self._fire_cooldown <= 0.0:
                start = Vec2(-0.5, 0.0)
                direction = Vec2(1.0, 0.0)
                bullet_id = self.projectiles.create_projectile(
                    position=start,
                    direction=direction,
                    speed=2.5,
                    lifetime=5.0,
                    damage=1.0,
                    owner_entity_id=self.player_id,
                    projectile_type="player_bullet",
                )
                col = self.world.get_component(bullet_id, ColliderComponent)
                if col:
                    col.collision_layer = int(CollisionLayer.PLAYER_BULLET)
                    col.collision_mask = mask_of(CollisionLayer.ENEMY, CollisionLayer.BOUNDARY)
                self._fire_cooldown = 0.2
        if self._fire_cooldown > 0.0:
            self._fire_cooldown -= dt
        return task.cont


if __name__ == "__main__":
    app = Demo()
    app.run()
