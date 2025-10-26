"""
Panda3D Collision System Integration

This module provides integration between the ECS collision system and Panda3D's
built-in collision detection system for improved performance and features.
"""

from typing import Dict, Optional

from panda3d.core import (
    CollisionTraverser, CollisionHandlerQueue, CollisionNode,
    NodePath, Vec3, BitMask32, CollisionSolid,
    CollisionSphere, CollisionBox, CollisionCapsule
)
from panda3d.bullet import BulletWorld

from engine.core.system import System
from engine.core.events import Event
from engine.graphics.components.transform_component import TransformComponent
from engine.physics.components.collider_component import ColliderComponent
from engine.physics.components.panda_collision_node import PandaCollisionNode
from engine.physics.typesg.collider_type import ColliderType


class PandaCollisionEvent(Event):
    """Event fired when Panda3D collision is detected."""
    def __init__(self, entity_a_id, entity_b_id, collision_point: Vec3, collision_normal: Vec3):
        self.entity_a_id = entity_a_id
        self.entity_b_id = entity_b_id
        self.collision_point = collision_point
        self.collision_normal = collision_normal


class PandaCollisionSystem(System):
    """
    Panda3D-based collision detection system.

    Provides hardware-accelerated collision detection with support for:
    - Multiple collision shapes (spheres, boxes, capsules, polygons)
    - Collision layers and masks
    - Trigger volumes
    - Physics integration
    - Performance optimization for large numbers of colliders
    """

    def __init__(self, world, base=None, use_bullet_physics: bool = False):
        """
        Initialize the Panda3D collision system.

        Args:
            world: ECS world instance
            base: Panda3D ShowBase instance (optional, for scene graph access)
            use_bullet_physics: Whether to use Bullet physics integration
        """
        super().__init__(world)
        self.base = base

        # Panda3D collision setup
        self.collision_traverser = CollisionTraverser("ecs_collision_traverser")
        self.collision_handler = CollisionHandlerQueue()

        # Collision node management
        self.collision_nodes: Dict[str, NodePath] = {}  # entity_id -> collision_node_path
        self.entity_to_node: Dict[str, str] = {}  # entity_id -> collision_node_name

        # Physics integration (optional)
        self.use_bullet_physics = use_bullet_physics
        self.bullet_world = None
        if use_bullet_physics:
            self.bullet_world = BulletWorld()
            self.bullet_world.set_gravity(Vec3(0, 0, -9.81))  # Default gravity

        # Performance tracking
        self.collision_checks_this_frame = 0
        self.collision_pairs_found = 0

        # Configuration
        self.max_collision_checks = 1000  # Safety limit
        self.collision_mask_size = 32  # Support 32 collision layers

        # Setup collision traverser
        # Note: We don't add the root node here. Instead, individual CollisionNodes
        # are added as entities are created. The traverser will find them automatically.

    @property
    def collision_root(self) -> NodePath:
        """Get or create the root node for collision detection."""
        if not hasattr(self, '_collision_root'):
            self._collision_root = NodePath("ecs_collision_root")
            if self.base:
                self._collision_root.reparentTo(self.base.render)
        return self._collision_root

    def update(self, dt: float):
        """Update collision detection for all entities."""
        # Reset performance counters
        self.collision_checks_this_frame = 0
        self.collision_pairs_found = 0

        # Get all entities with collision components
        collision_entities = self.world.get_entities_with_components(
            TransformComponent, ColliderComponent
        )

        # Update collision nodes for all entities
        for entity in collision_entities:
            self._update_entity_collision_node(entity.id)

        # Only traverse if we have collision nodes
        if self.collision_nodes:
            # Perform collision detection
            self.collision_traverser.traverse(self.collision_root)

            # Process collision results
            self._process_collision_results()

        # Update physics simulation if enabled
        if self.use_bullet_physics:
            self._update_physics_simulation(dt)

    def _update_entity_collision_node(self, entity_id: str):
        """Update or create collision node for an entity."""
        transform = self.world.get_component(entity_id, TransformComponent)
        collider = self.world.get_component(entity_id, ColliderComponent)

        if not transform or not collider:
            return

        # Check if entity should use Panda3D collision
        if not getattr(collider, 'use_panda_collision', True):
            return

        # Get or create collision node
        node_name = f"collision_{entity_id}"
        if node_name not in self.collision_nodes:
            # Create new collision node
            collision_node = CollisionNode(node_name)
            collision_node_path = NodePath(collision_node)
            collision_node_path.reparentTo(self.collision_root)

            # Set collision mask from ECS collision layer
            mask = BitMask32.bit(collider.collision_layer - 1)
            collision_node.set_into_collide_mask(mask)
            collision_node.set_from_collide_mask(BitMask32.allOn())

            self.collision_nodes[node_name] = collision_node_path
            self.entity_to_node[str(entity_id)] = node_name
            
            # Add the collision node to the traverser
            self.collision_traverser.add_collider(collision_node_path, self.collision_handler)
        else:
            collision_node_path = self.collision_nodes[node_name]

        # Update collision solid
        self._update_collision_solid(collision_node_path, collider, transform)

        # Update transform
        # Update transform - use 2D positioning for 2D game
        # Position in 3D space but keep Z at 0 for 2D gameplay
        pos_3d = Vec3(transform.x, transform.y, 0)
        collision_node_path.set_pos(pos_3d)
        collision_node_path.set_hpr(Vec3(0, 0, transform.rotation))
        
        # Update the PandaCollisionNode component if it exists
        panda_node_comp = self.world.get_component(entity_id, PandaCollisionNode)
        if panda_node_comp:
            panda_node_comp.update_transform(transform)

    def _update_collision_solid(self, node_path: NodePath, collider: ColliderComponent,
                               transform: TransformComponent):
        """Update the collision solid for a collision node."""
        collision_node = node_path.node()

        # Clear existing solids
        collision_node.clear_solids()

        # Create appropriate collision solid based on collider type
        solid = self._create_collision_solid(collider)
        if solid:
            collision_node.add_solid(solid)

    def _create_collision_solid(self, collider: ColliderComponent) -> Optional[CollisionSolid]:
        """Create a Panda3D collision solid from ECS collider component."""
        if collider.collider_type == ColliderType.RECTANGLE:
            # Create box collision
            half_width = collider.size.x / 2
            half_height = collider.size.y / 2
            return CollisionBox(
                Vec3(-half_width, -half_height, -0.1),  # min point
                Vec3(half_width, half_height, 0.1)      # max point
            )

        elif collider.collider_type == ColliderType.CIRCLE:
            # Create sphere collision (cylinder in 2D)
            return CollisionSphere(0, 0, 0, collider.radius)

        elif collider.collider_type == ColliderType.SPHERE:
            # 3D sphere
            return CollisionSphere(0, 0, 0, collider.radius)

        elif collider.collider_type == ColliderType.BOX:
            # 3D box
            half_width = collider.size.x / 2
            half_height = collider.size.y / 2
            half_depth = getattr(collider, 'depth', 1.0) / 2
            return CollisionBox(
                Vec3(-half_width, -half_height, -half_depth),
                Vec3(half_width, half_height, half_depth)
            )

        elif collider.collider_type == ColliderType.CAPSULE:
            # Capsule for character controllers
            height = getattr(collider, 'height', collider.size.y)
            return CollisionCapsule(0, 0, -height/2, 0, 0, height/2, collider.radius)

        # Add support for polygon shapes later
        return None

    def _process_collision_results(self):
        """Process collision results from Panda3D collision traverser."""
        # Only process if we have actual collision entries
        num_entries = self.collision_handler.get_num_entries()
        
        if num_entries == 0:
            return
            
        print(f"🐼 Processing {num_entries} collision entries")
        
        for i in range(num_entries):
            entry = self.collision_handler.get_entry(i)

            # Get colliding nodes
            from_node = entry.get_from_node()
            into_node = entry.get_into_node()

            # Extract entity IDs from node names
            from_entity_id = self._extract_entity_id(from_node.get_name())
            into_entity_id = self._extract_entity_id(into_node.get_name())

            if from_entity_id and into_entity_id and from_entity_id != into_entity_id:
                # Check if this is an actual collision (not just potential)
                if entry.has_surface_point():
                    # Get collision data
                    collision_point = entry.get_surface_point(self.collision_root)
                    collision_normal = entry.get_surface_normal(self.collision_root)

                    print(f"💥 REAL COLLISION: {from_entity_id} ↔ {into_entity_id}")

                    # Fire collision event
                    self.world.event_manager.publish(
                        PandaCollisionEvent(from_entity_id, into_entity_id,
                                          collision_point, collision_normal)
                    )

                    self.collision_pairs_found += 1
                else:
                    # This is just a potential collision, not actual contact
                    pass

            self.collision_checks_this_frame += 1

            # Safety check to prevent infinite loops
            if self.collision_checks_this_frame >= self.max_collision_checks:
                break

    def _extract_entity_id(self, node_name: str) -> Optional[str]:
        """Extract entity ID from collision node name."""
        if node_name.startswith("collision_"):
            return node_name[10:]  # Remove "collision_" prefix
        return None

    def _update_physics_simulation(self, dt: float):
        """Update Bullet physics simulation if enabled."""
        if self.bullet_world:
            self.bullet_world.do_physics(dt)

            # Sync physics results back to ECS
            self._sync_physics_to_ecs()

    def _sync_physics_to_ecs(self):
        """Sync Bullet physics results back to ECS components."""
        # This would sync rigidbody positions/velocities back to ECS
        # Implementation depends on how Bullet rigidbodies are created
        pass

    def remove_entity(self, entity_id: str):
        """Remove collision node for an entity."""
        if entity_id in self.entity_to_node:
            node_name = self.entity_to_node[entity_id]
            if node_name in self.collision_nodes:
                collision_node_path = self.collision_nodes[node_name]
                # Remove from collision traverser
                self.collision_traverser.remove_collider(collision_node_path)
                # Remove from scene graph
                collision_node_path.removeNode()
                del self.collision_nodes[node_name]
            del self.entity_to_node[entity_id]

    def get_collision_stats(self) -> Dict[str, int]:
        """Get collision detection performance statistics."""
        return {
            'collision_checks': self.collision_checks_this_frame,
            'collision_pairs_found': self.collision_pairs_found,
            'active_collision_nodes': len(self.collision_nodes)
        }

    def cleanup(self):
        """Clean up Panda3D collision resources."""
        # Remove all collision nodes
        for node_path in self.collision_nodes.values():
            node_path.removeNode()

        self.collision_nodes.clear()
        self.entity_to_node.clear()

        # Clean up physics world
        if self.bullet_world:
            # Bullet cleanup would go here
            pass

    def show_collision_nodes(self, show: bool = True):
        """Show or hide collision node visualizations."""
        print(f"🔍 Setting collision visualization to: {'ON' if show else 'OFF'}")
        
        for node_name, node_path in self.collision_nodes.items():
            if show:
                print(f"  📍 Showing collision node: {node_name}")
                node_path.show()
                # Also show bounds for better visualization
                collision_node = node_path.node()
                if hasattr(collision_node, 'showBounds'):
                    collision_node.showBounds()
                # Make sure it's visible
                node_path.setColor(1, 1, 0, 0.5)  # Semi-transparent yellow
            else:
                print(f"  📍 Hiding collision node: {node_name}")
                node_path.hide()
                # Hide bounds too
                collision_node = node_path.node()
                if hasattr(collision_node, 'hideBounds'):
                    collision_node.hideBounds()

    def highlight_collision(self, entity_id: str, duration: float = 0.2):
        """Temporarily highlight a collision node when collision occurs."""
        print(f"🎯 Attempting to highlight collision for entity {entity_id}")
        
        if entity_id in self.entity_to_node:
            node_name = self.entity_to_node[entity_id]
            print(f"  📍 Found collision node: {node_name}")
            
            if node_name in self.collision_nodes:
                node_path = self.collision_nodes[node_name]
                # Store original color
                original_color = node_path.getColor()
                # Set highlight color (red for collision)
                node_path.setColor(1, 0, 0, 1)  # Red highlight
                
                print(f"💥 Highlighting collision for entity {entity_id} - set to RED")
                
                # Schedule color reset
                def reset_color():
                    if node_path:
                        node_path.setColor(original_color)
                        print(f"🔄 Reset collision highlight for entity {entity_id}")
                
                # Use task manager to reset color after duration
                if hasattr(self, 'base') and self.base:
                    self.base.taskMgr.doMethodLater(duration, lambda task: reset_color(), f"reset_collision_color_{entity_id}")
            else:
                print(f"  ❌ Collision node {node_name} not found in collision_nodes dict")
        else:
            print(f"  ❌ Entity {entity_id} not found in entity_to_node mapping")
            print(f"    Available entities: {list(self.entity_to_node.keys())}")

    def is_collision_nodes_visible(self) -> bool:
        """Check if collision nodes are currently visible."""
        if not self.collision_nodes:
            return False
        # Check if the first node is visible (assuming all are in the same state)
        first_node = next(iter(self.collision_nodes.values()))
        return not first_node.is_hidden()
