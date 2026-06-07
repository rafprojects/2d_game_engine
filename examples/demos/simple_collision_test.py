"""
Simple Collision Test

A text-based test of the collision systems without graphics.
"""
import os
import sys
import time
from panda3d.core import Vec2

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from engine.core.system import World
from engine.graphics.components.transform_component import TransformComponent
from engine.physics.systems.collision_system import CollisionSystem
from engine.physics.systems.projectile_system import ProjectileSystem
from engine.physics.systems.enemy_ai_system import EnemyAISystem
from engine.physics.components.collider_component import ColliderComponent
from engine.physics.components.projectile_component import ProjectileComponent
from engine.physics.components.enemy_ai_component import EnemyAIComponent
from engine.physics.typesg.collider_type import ColliderType


class SimpleCollisionTest:
    def __init__(self):
        print("🧪 Simple Collision Test Starting...")
        print("This test runs the collision systems without graphics")

        self.world = World()

        # Add systems (without graphics/rendering)
        self.collision_system = CollisionSystem(self.world)
        self.world.add_system(self.collision_system)

        # Note: PandaCollisionSystem requires ShowBase, so we'll skip it for this test
        print("⚠️  Skipping PandaCollisionSystem (requires graphics)")

        self.projectile_system = ProjectileSystem(self.world)
        self.world.add_system(self.projectile_system)

        self.enemy_ai_system = EnemyAISystem(self.world, self.projectile_system)
        self.world.add_system(self.enemy_ai_system)

        # Create test entities
        self.create_test_entities()

        print("✅ Test entities created")
        print("🎮 Starting simulation...")

        # Run simulation for a few seconds
        self.run_simulation()

    def create_test_entities(self):
        """Create test entities for collision testing."""

        # Player entity
        player_entity = self.world.create_entity("player")
        self.world.add_component(player_entity.id,
            TransformComponent(x=0, y=0, scale_x=1, scale_y=1))
        self.world.add_component(player_entity.id,
            ColliderComponent(
                collider_type=ColliderType.CIRCLE,
                radius=0.5,
                use_panda_collision=False  # Don't use Panda3D for this test
            ))
        print(f"🎯 Created player entity: {player_entity.id}")

        # Enemy entity with AI
        enemy_entity = self.world.create_entity("enemy")
        self.world.add_component(enemy_entity.id,
            TransformComponent(x=2, y=1, scale_x=0.8, scale_y=0.8))
        self.world.add_component(enemy_entity.id,
            ColliderComponent(
                collider_type=ColliderType.CIRCLE,  # Use CIRCLE instead of SPHERE for this test
                radius=0.4,
                use_panda_collision=False
            ))
        # Add AI behavior
        self.world.add_component(enemy_entity.id,
            EnemyAIComponent(
                movement_speed=1.0,
                shoot_cooldown=1.0,
                patrol_radius=3.0,
                aggression_range=2.0
            ))
        print(f"👾 Created enemy entity with AI: {enemy_entity.id}")

        # Static obstacle
        obstacle_entity = self.world.create_entity("obstacle")
        self.world.add_component(obstacle_entity.id,
            TransformComponent(x=1, y=-1, scale_x=1, scale_y=1))
        self.world.add_component(obstacle_entity.id,
            ColliderComponent(
                collider_type=ColliderType.RECTANGLE,
                size=Vec2(1, 1),
                use_panda_collision=False
            ))
        print(f"🧱 Created obstacle entity: {obstacle_entity.id}")

    def run_simulation(self):
        """Run the simulation loop."""
        dt = 0.1  # 10 FPS for testing
        max_frames = 50  # Run for about 5 seconds

        for frame in range(max_frames):
            print(f"\n--- Frame {frame + 1}/{max_frames} ---")

            # Update all systems
            self.world.update(dt)

            # Print entity positions
            self.print_entity_positions()

            # Count projectiles
            projectile_count = len(self.world.get_entities_with_components(ProjectileComponent))
            print(f"🚀 Active projectiles: {projectile_count}")

            # Simulate player movement (move right)
            self.simulate_player_movement(dt)

            time.sleep(0.1)  # Slow down output

        print("\n🎉 Simulation complete!")

    def print_entity_positions(self):
        """Print current positions of all entities."""
        for entity in self.world.get_entities_with_components(TransformComponent):
            transform = self.world.get_component(entity.id, TransformComponent)
            if transform:
                print(f"📍 {entity.name or 'Entity'}: ({transform.x:.2f}, {transform.y:.2f})")

    def simulate_player_movement(self, dt):
        """Simulate player movement for testing."""
        for entity in self.world.get_entities_with_components(TransformComponent):
            if entity.name == "player":
                transform = self.world.get_component(entity.id, TransformComponent)
                if transform:
                    # Move player slowly to the right
                    transform.x += 0.1 * dt * 10  # Scale up for visibility

                    # Simulate shooting occasionally
                    if hasattr(self, '_shoot_timer'):
                        self._shoot_timer += dt
                        if self._shoot_timer > 1.0:  # Shoot every second
                            self.simulate_player_shooting(transform)
                            self._shoot_timer = 0
                    else:
                        self._shoot_timer = 0

    def simulate_player_shooting(self, transform):
        """Simulate player shooting a projectile."""
        direction = Vec2(1, 0)  # Shoot to the right
        position = Vec2(transform.x + 0.5, transform.y)

        projectile_id = self.projectile_system.create_projectile(
            position=position,
            direction=direction,
            speed=3.0,
            lifetime=2.0,
            damage=1.0,
            owner_entity_id=None,
            projectile_type="player_bullet"
        )
        print(f"🔫 Player shot projectile: {projectile_id}")


if __name__ == '__main__':
    test = SimpleCollisionTest()
