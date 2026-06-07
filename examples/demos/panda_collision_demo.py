"""
Panda3D Collision System Demo

This demo showcases the new Panda3D collision system integration
with the existing ECS architecture.
"""
import os
import sys
from direct.showbase.ShowBase import ShowBase
from direct.showbase.ShowBaseGlobal import globalClock
from panda3d.core import Vec2

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from engine.core.system import World
from engine.graphics.components.transform_component import TransformComponent
from engine.graphics.components.sprite_component import SpriteComponent
from engine.graphics.systems.render_system import RenderSystem
from engine.physics.systems.collision_system import CollisionSystem
from engine.physics.systems.panda_collision_system import PandaCollisionSystem, PandaCollisionEvent
from engine.physics.systems.projectile_system import ProjectileSystem
from engine.physics.systems.enemy_ai_system import EnemyAISystem
from engine.physics.components.collider_component import ColliderComponent
from engine.physics.components.projectile_component import ProjectileComponent
from engine.physics.components.enemy_ai_component import EnemyAIComponent
from engine.physics.typesg.collider_type import ColliderType
from engine.input.components.input_component import InputComponent
from engine.input.systems.input_system import InputSystem
from engine.input.input_bindings import InputBinding


class PandaCollisionDemo(ShowBase):
    def __init__(self):
        # Configure for headless operation if needed
        import os
        if os.environ.get('DISPLAY', '') == '' and not os.environ.get('WAYLAND_DISPLAY', ''):
            os.environ['DISPLAY'] = ':0'  # Try to set display
        
        ShowBase.__init__(self)
        
        # Disable window if in headless environment
        if not self.win:
            print("⚠️  No display available, running in headless mode")
            self.graphicsEngine = None
        else:
            print("✅ Display available, running with graphics")
        
        print("🐼 Panda3D Collision System Demo initialized")

        self.world = World()

        # Add systems
        self.render_system = RenderSystem(self.world, self)
        self.world.add_system(self.render_system)

        self.collision_system = CollisionSystem(self.world)
        self.world.add_system(self.collision_system)

        # Add the new Panda3D collision system
        self.panda_collision_system = PandaCollisionSystem(self.world, self)
        self.world.add_system(self.panda_collision_system)

        # Add projectile system
        self.projectile_system = ProjectileSystem(self.world)
        self.world.add_system(self.projectile_system)

        # Add enemy AI system
        self.enemy_ai_system = EnemyAISystem(self.world, self.projectile_system)
        self.world.add_system(self.enemy_ai_system)

        self.input_system = InputSystem(self.world, self)
        self.world.add_system(self.input_system)

        # Try to find assets directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Look for assets in the project root, not examples
        project_root = os.path.dirname(os.path.dirname(script_dir))
        assets_dir = os.path.join(project_root, "assets")

        # Create test entities
        self.create_test_entities(assets_dir)

        # Subscribe to collision events for visual feedback
        self.world.event_manager.subscribe(PandaCollisionEvent, self.handle_collision_event)

        # Enable collision visualization by default
        self.panda_collision_system.show_collision_nodes(True)
        
        print("🐼 Collision visualization enabled - press 'V' to toggle")
        print("🎯 Demo setup complete! Use WASD to move, SPACE to shoot, V to toggle collision visualization")
        print("💡 The enemy will patrol and shoot at you when you're nearby")

        # Game loop
        self.taskMgr.add(self.update_game, "update_game_task")
        
    def create_test_entities(self, assets_dir):
        """Create test entities to demonstrate collision detection."""

        # Player entity (circle collider)
        player_sprite = os.path.join(assets_dir, "player.png")
        if os.path.exists(player_sprite):
            player_entity = self.world.create_entity("player")
            self.world.add_component(player_entity.id,
                TransformComponent(x=0, y=0, scale_x=1, scale_y=1))
            self.world.add_component(player_entity.id,
                SpriteComponent(image_path=player_sprite, layer=1))
            self.world.add_component(player_entity.id,
                ColliderComponent(
                    collider_type=ColliderType.CIRCLE,
                    radius=0.5,
                    use_panda_collision=True
                ))

            # Add input for player movement and shooting
            input_bindings = {
                "move_left": [InputBinding(input_type="key", event_name="a")],
                "move_right": [InputBinding(input_type="key", event_name="d")],
                "move_up": [InputBinding(input_type="key", event_name="w")],
                "move_down": [InputBinding(input_type="key", event_name="s")],
                "shoot": [InputBinding(input_type="key", event_name=" ")],  # Try space character
                "toggle_collision_viz": [InputBinding(input_type="key", event_name="v")],
            }
            self.world.add_component(player_entity.id,
                InputComponent(action_bindings=input_bindings))

        # Static obstacle (rectangle collider)
        obstacle_entity = self.world.create_entity("obstacle")
        self.world.add_component(obstacle_entity.id,
            TransformComponent(x=2, y=0, scale_x=1, scale_y=1))
        self.world.add_component(obstacle_entity.id,
            SpriteComponent(image_path=player_sprite, layer=1))  # Reuse player sprite
        self.world.add_component(obstacle_entity.id,
            ColliderComponent(
                collider_type=ColliderType.RECTANGLE,
                size=Vec2(1, 1),
                use_panda_collision=True
            ))

        # Moving enemy with AI (sphere collider for 3D collision)
        enemy_entity = self.world.create_entity("enemy")
        self.world.add_component(enemy_entity.id,
            TransformComponent(x=-2, y=1, scale_x=0.8, scale_y=0.8))
        self.world.add_component(enemy_entity.id,
            SpriteComponent(image_path=player_sprite, layer=1))
        self.world.add_component(enemy_entity.id,
            ColliderComponent(
                collider_type=ColliderType.SPHERE,  # 3D sphere
                radius=0.4,
                use_panda_collision=True
            ))
        # Add AI behavior
        self.world.add_component(enemy_entity.id,
            EnemyAIComponent(
                movement_speed=1.2,
                shoot_cooldown=1.5,
                patrol_radius=2.5,
                aggression_range=3.0
            ))

        print("✅ Created test entities with Panda3D collision components")

    def update_game(self, task):
        dt = globalClock.getDt()

        # Debug output to show the demo is running
        if not hasattr(self, '_frame_count'):
            self._frame_count = 0
        self._frame_count += 1
        
        if self._frame_count % 60 == 0:  # Every ~1 second at 60 FPS
            print(f"🎮 Frame {self._frame_count}: Demo is running (dt={dt:.3f})")

        # Update ECS world
        self.world.update(dt)

        # Handle player movement and shooting
        self.handle_player_movement(dt)
        self.handle_player_shooting(dt)
        self.handle_collision_visualization_toggle(dt)

        # Handle projectile collisions
        self.handle_projectile_collisions()

        # Print collision stats occasionally
        if hasattr(self, '_stats_timer'):
            self._stats_timer += dt
            if self._stats_timer > 2.0:  # Every 2 seconds
                stats = self.panda_collision_system.get_collision_stats()
                print(f"🐼 Collision Stats: {stats}")
                self._stats_timer = 0
        else:
            self._stats_timer = 0

        return task.cont

    def handle_player_movement(self, dt):
        """Handle player movement based on input."""
        move_speed = 2.0

        # Find player entity
        for entity in self.world.get_entities_with_components(
            InputComponent, TransformComponent, ColliderComponent
        ):
            input_comp = self.world.get_component(entity.id, InputComponent)
            transform_comp = self.world.get_component(entity.id, TransformComponent)

            if input_comp and transform_comp:
                direction = Vec2(0, 0)

                if input_comp.action_active.get("move_left", False):
                    direction.x -= 1
                if input_comp.action_active.get("move_right", False):
                    direction.x += 1
                if input_comp.action_active.get("move_up", False):
                    direction.y += 1
                if input_comp.action_active.get("move_down", False):
                    direction.y -= 1

                # Normalize direction
                length = (direction.x ** 2 + direction.y ** 2) ** 0.5
                if length > 0:
                    direction.x /= length
                    direction.y /= length

                # Apply movement
                transform_comp.x += direction.x * move_speed * dt
                transform_comp.y += direction.y * move_speed * dt

                # Keep player on screen
                transform_comp.x = max(-3, min(3, transform_comp.x))
                transform_comp.y = max(-2, min(2, transform_comp.y))

    def handle_player_shooting(self, dt):
        """Handle player shooting input."""
        for entity in self.world.get_entities_with_components(
            InputComponent, TransformComponent, ColliderComponent
        ):
            input_comp = self.world.get_component(entity.id, InputComponent)
            transform_comp = self.world.get_component(entity.id, TransformComponent)

            if input_comp and transform_comp:
                # Check for shoot input
                if input_comp.action_active.get("shoot", False):
                    # Only shoot if not already shooting (simple cooldown)
                    if not hasattr(self, '_player_shoot_cooldown') or self._player_shoot_cooldown <= 0:
                        self._shoot_player_projectile(transform_comp)
                        self._player_shoot_cooldown = 0.5  # 0.5 second cooldown

        # Update shoot cooldown
        if hasattr(self, '_player_shoot_cooldown'):
            self._player_shoot_cooldown -= dt
            if self._player_shoot_cooldown < 0:
                self._player_shoot_cooldown = 0

    def _shoot_player_projectile(self, transform_comp):
        """Create a projectile from the player's position."""
        # Shoot towards the center (or could be based on mouse position)
        direction = Vec2(1, 0)  # Shoot to the right for now
        position = Vec2(transform_comp.x + 0.5, transform_comp.y)  # Offset from player center

        self.projectile_system.create_projectile(
            position=position,
            direction=direction,
            speed=6.0,
            lifetime=2.0,
            damage=1.0,
            owner_entity_id=None,  # Player projectiles don't have an owner entity ID
            projectile_type="player_bullet"
        )

    def handle_projectile_collisions(self):
        """Handle collisions between projectiles and other entities."""
        projectiles = []
        other_entities = []

        # Separate projectiles from other entities
        for entity in self.world.get_entities_with_components(TransformComponent, ColliderComponent):
            projectile_comp = self.world.get_component(entity.id, ProjectileComponent)
            if projectile_comp is not None:
                projectiles.append(entity)
            else:
                other_entities.append(entity)

        # Check collisions between projectiles and other entities
        for projectile in projectiles:
            projectile_comp = self.world.get_component(projectile.id, ProjectileComponent)
            projectile_transform = self.world.get_component(projectile.id, TransformComponent)

            if not projectile_comp or not projectile_transform:
                continue

            for other in other_entities:
                # Skip if projectile belongs to this entity
                if projectile_comp.owner_entity_id == other.id:
                    continue

                other_transform = self.world.get_component(other.id, TransformComponent)
                if not other_transform:
                    continue

                # Simple distance-based collision check
                dx = projectile_transform.x - other_transform.x
                dy = projectile_transform.y - other_transform.y
                distance = (dx * dx + dy * dy) ** 0.5

                # Check collision based on collider types
                projectile_collider = self.world.get_component(projectile.id, ColliderComponent)
                other_collider = self.world.get_component(other.id, ColliderComponent)

                if projectile_collider and other_collider:
                    min_distance = projectile_collider.radius + other_collider.radius
                    if distance < min_distance:
                        # Collision detected!
                        print(f"💥 Projectile hit! Projectile: {projectile.id}, Target: {other.id}")
                        # Remove the projectile
                        self.world.remove_entity(projectile.id)
                        break  # Projectile can only hit one target

    def handle_collision_visualization_toggle(self, dt):
        """Handle toggling collision visualization."""
        for entity in self.world.get_entities_with_components(InputComponent):
            input_comp = self.world.get_component(entity.id, InputComponent)
            
            if input_comp and input_comp.action_active.get("toggle_collision_viz", False):
                # Only toggle if not already toggling (simple cooldown)
                if not hasattr(self, '_collision_viz_cooldown') or self._collision_viz_cooldown <= 0:
                    current_state = self.panda_collision_system.is_collision_nodes_visible()
                    self.panda_collision_system.show_collision_nodes(not current_state)
                    print(f"🔍 Collision visualization: {'ON' if not current_state else 'OFF'}")
                    self._collision_viz_cooldown = 0.3  # 0.3 second cooldown

        # Update cooldown
        if hasattr(self, '_collision_viz_cooldown'):
            self._collision_viz_cooldown -= dt
            if self._collision_viz_cooldown < 0:
                self._collision_viz_cooldown = 0

    def handle_collision_event(self, event: PandaCollisionEvent):
        """Handle collision events for visual feedback."""
        # Only print collision info occasionally to avoid spam
        if not hasattr(self, '_collision_count'):
            self._collision_count = 0
        self._collision_count += 1
        
        if self._collision_count % 50 == 0:  # Print every 50th collision
            print(f"💥 Collision detected! Total collisions: {self._collision_count}")
        
        # Highlight both colliding entities
        self.panda_collision_system.highlight_collision(event.entity_a_id)
        self.panda_collision_system.highlight_collision(event.entity_b_id)
        
        # Add screen flash effect
        # Quick screen flash
        original_clear_color = self.getBackgroundColor()
        self.setBackgroundColor(1, 1, 1, 0.3)  # White flash
        
        def reset_background():
            self.setBackgroundColor(original_clear_color)
        
        self.taskMgr.doMethodLater(0.1, lambda task: reset_background(), "reset_background_flash")


if __name__ == '__main__':
    app = PandaCollisionDemo()
    app.run()
