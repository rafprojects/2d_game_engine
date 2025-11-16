"""
Projectile System

System for managing projectile entities, their movement, lifetime, and cleanup.
"""
from typing import List, Optional
from panda3d.core import Vec2

from engine.core.system import System
from engine.graphics.components.transform_component import TransformComponent
from engine.physics.components.projectile_component import ProjectileComponent
from engine.physics.components.collider_component import ColliderComponent
from engine.physics.typesg.collider_type import ColliderType


class ProjectileSystem(System):
    """
    System for managing projectiles in the game world.

    Handles projectile movement, lifetime management, and cleanup.
    """

    def __init__(self, world):
        super().__init__(world)
        self.projectiles_to_remove: List[str] = []

    def update(self, dt: float):
        """Update all projectiles."""
        self.projectiles_to_remove.clear()

        # Update projectile positions and lifetimes
        for entity in self.world.get_entities_with_components(
            ProjectileComponent, TransformComponent
        ):
            projectile_comp = self.world.get_component(entity.id, ProjectileComponent)
            transform_comp = self.world.get_component(entity.id, TransformComponent)

            if not projectile_comp or not transform_comp:
                continue

            # Early removal if projectile is marked dead by other systems (e.g., DamageSystem)
            if not projectile_comp.is_alive:
                self.projectiles_to_remove.append(entity.id)
                continue

            # Update lifetime
            projectile_comp.time_alive += dt
            if projectile_comp.time_alive >= projectile_comp.lifetime:
                self.projectiles_to_remove.append(entity.id)
                continue

            # Update position based on velocity
            transform_comp.x += projectile_comp.velocity.x * projectile_comp.speed * dt
            transform_comp.y += projectile_comp.velocity.y * projectile_comp.speed * dt

            # Check if projectile is off-screen (simple bounds check)
            if (abs(transform_comp.x) > 5 or abs(transform_comp.y) > 4):
                self.projectiles_to_remove.append(entity.id)

        # Remove expired projectiles
        for entity_id in self.projectiles_to_remove:
            self.world.remove_entity(entity_id)

    def create_projectile(self,
                         position: Vec2,
                         direction: Vec2,
                         speed: float = 5.0,
                         lifetime: float = 3.0,
                         damage: float = 1.0,
                         owner_entity_id: Optional[str] = None,
                         projectile_type: str = "bullet") -> str:
        """
        Create a new projectile entity.

        Args:
            position: Starting position
            direction: Direction vector (will be normalized)
            speed: Projectile speed
            lifetime: How long projectile lives
            damage: Damage on collision
            owner_entity_id: Entity that fired the projectile
            projectile_type: Type of projectile

        Returns:
            Entity ID of the created projectile
        """
        # Normalize direction
        length = (direction.x ** 2 + direction.y ** 2) ** 0.5
        if length > 0:
            direction = Vec2(direction.x / length, direction.y / length)

        # Create projectile entity
        projectile_entity = self.world.create_entity(f"projectile_{projectile_type}")

        # Add components
        self.world.add_component(projectile_entity.id,
            TransformComponent(x=position.x, y=position.y, scale_x=0.2, scale_y=0.2))

        self.world.add_component(projectile_entity.id,
            ProjectileComponent(
                velocity=direction,
                speed=speed,
                lifetime=lifetime,
                damage=damage,
                owner_entity_id=owner_entity_id,
                projectile_type=projectile_type
            ))

        # Add collision component
        self.world.add_component(projectile_entity.id,
            ColliderComponent(
                collider_type=ColliderType.CIRCLE,
                radius=0.1,
                use_panda_collision=True
            ))

        # Add visual component (simple colored sprite for now)
        # We'll create a simple colored rectangle as projectile visual
        from engine.graphics.components.sprite_component import SpriteComponent
        
        # Choose color based on projectile type
        if projectile_type == "player_bullet":
            color = (0, 1, 0, 1)  # Green for player bullets
            print(f"🎯 Creating PLAYER projectile at ({position.x:.2f}, {position.y:.2f}) with GREEN color")
        elif projectile_type == "enemy_bullet":
            color = (1, 0, 0, 1)  # Red for enemy bullets
            print(f"🎯 Creating ENEMY projectile at ({position.x:.2f}, {position.y:.2f}) with RED color")
        else:
            color = (1, 1, 0, 1)  # Yellow for other projectiles
            print(f"🎯 Creating projectile at ({position.x:.2f}, {position.y:.2f}) with YELLOW color")
        
        self.world.add_component(projectile_entity.id,
            SpriteComponent(
                image_path=None,  # Will use colored rectangle
                layer=2,  # Above other sprites
                color=color
            ))

        print(f"✅ Projectile entity {projectile_entity.id} created successfully")
        return projectile_entity.id
