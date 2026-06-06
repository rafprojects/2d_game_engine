"""
Panda3D Collision System Integration

This module provides integration between the ECS collision system and Panda3D's
built-in collision detection system for improved performance and features.
"""

from typing import Dict, Optional, Set, Tuple
import uuid

from panda3d.core import (
    CollisionTraverser, CollisionHandlerQueue, CollisionNode,
    NodePath, Vec3, Vec2, BitMask32, CollisionSolid,
    CollisionSphere, CollisionBox, CollisionCapsule,
    CardMaker, TransparencyAttrib, LineSegs
)
import math
from panda3d.bullet import BulletWorld

from engine.core.system import System
from engine.core.events import Event
from engine.graphics.components.transform_component import TransformComponent
from engine.physics.components.collider_component import ColliderComponent
from engine.physics.components.panda_collision_node import PandaCollisionNode
from engine.physics.typesg.collider_type import ColliderType
from engine.physics.systems.collision_system import (
    CollisionEvent,
    TriggerEnterEvent,
    TriggerExitEvent,
)


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
        self.boundary_nodes: Dict[str, NodePath] = {}
        self._viz_enabled = False
        self._debug_overlays = {}

        # Setup collision traverser
        # Note: We don't add the root node here. Instead, individual CollisionNodes
        # are added as entities are created. The traverser will find them automatically.

    @property
    def collision_root(self) -> NodePath:
        """Get or create the root node for collision detection."""
        if not hasattr(self, '_collision_root'):
            self._collision_root = NodePath("ecs_collision_root")
            if self.base:
                # Align with 2D scene graph for visibility and consistent transforms
                parent_np = getattr(self.base, 'aspect2d', None) or self.base.render
                self._collision_root.reparentTo(parent_np)
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

        # Reset collider state for trigger enter/exit calculations
        for entity in collision_entities:
            collider = self.world.get_component(entity.id, ColliderComponent)
            if collider:
                collider.was_colliding_entities = collider.colliding_entities.copy()
                collider.colliding_entities.clear()

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

            # Initial collision masks
            into_mask = BitMask32.bit(max(0, collider.collision_layer - 1))
            from_mask = self._int_to_bitmask32(collider.collision_mask)
            collision_node.set_into_collide_mask(into_mask)
            collision_node.set_from_collide_mask(from_mask)

            self.collision_nodes[node_name] = collision_node_path
            self.entity_to_node[str(entity_id)] = node_name
            
            # Add the collision node to the traverser
            self.collision_traverser.add_collider(collision_node_path, self.collision_handler)

            # Attach PandaCollisionNode component for lifecycle/inspection
            try:
                self.world.add_component(entity_id, PandaCollisionNode(collision_node_path, collision_node))
            except Exception as e:
                # Non-fatal: continue without the helper component
                print(f"[PandaCollisionSystem] Warning: failed to attach PandaCollisionNode: {e}")
            # If visualization is enabled, immediately show this new node as well
            if self._viz_enabled:
                try:
                    collision_node_path.show()
                    if hasattr(collision_node, 'show'):
                        collision_node.show()
                    if hasattr(collision_node, 'showBounds'):
                        collision_node.showBounds()
                    collision_node_path.setTransparency(True)
                    collision_node_path.setColor(1, 1, 0, 0.5)
                except Exception:
                    pass
        else:
            collision_node_path = self.collision_nodes[node_name]

        # Update collision solid
        self._update_collision_solid(collision_node_path, collider, transform)

        # Keep masks in sync with component each frame (cheap and robust)
        collision_node = collision_node_path.node()
        into_mask = BitMask32.bit(max(0, collider.collision_layer - 1))
        from_mask = self._int_to_bitmask32(collider.collision_mask)
        collision_node.set_into_collide_mask(into_mask)
        collision_node.set_from_collide_mask(from_mask)

        # Update transform - map 2D (x, y) to Panda 3D (x, 0, z)
        # aspect2d uses X/Z for 2D; keep Y at 0 for a flat plane
        pos_3d = Vec3(transform.x, 0, transform.y)
        collision_node_path.set_pos(pos_3d)
        collision_node_path.set_hpr(Vec3(0, 0, transform.rotation))
        
        # Update the PandaCollisionNode component if it exists
        panda_node_comp = self.world.get_component(entity_id, PandaCollisionNode)
        if panda_node_comp:
            panda_node_comp.update_transform(transform)

        # Ensure and update debug overlay for reliable coloring
        ent_id_str = str(entity_id)
        self._ensure_debug_overlay(ent_id_str, collider)
        self._update_debug_overlay(ent_id_str, collider, transform)

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
            # Map 2D (width, height) to Panda3D X and Z extents;
            # keep Y (depth) very thin so it lies on the X/Z plane
            depth = 0.05
            return CollisionBox(
                Vec3(-half_width, -depth, -half_height),  # min point (x, y, z)
                Vec3(half_width, depth, half_height)      # max point
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
        
        processed_pairs: Set[Tuple[uuid.UUID, uuid.UUID]] = set()

        for i in range(num_entries):
            entry = self.collision_handler.get_entry(i)

            # Get colliding nodes
            from_node = entry.get_from_node()
            into_node = entry.get_into_node()

            # Extract entity IDs from node names
            from_entity_id_str = self._extract_entity_id(from_node.get_name())
            into_entity_id_str = self._extract_entity_id(into_node.get_name())

            if from_entity_id_str and into_entity_id_str and from_entity_id_str != into_entity_id_str:
                # Check if this is an actual collision (not just potential)
                if entry.has_surface_point():
                    # Get collision data
                    collision_point = entry.get_surface_point(self.collision_root)
                    collision_normal = entry.get_surface_normal(self.collision_root)

                    # Convert IDs back to UUIDs used by ECS
                    try:
                        from_uuid = uuid.UUID(from_entity_id_str)
                        into_uuid = uuid.UUID(into_entity_id_str)
                    except Exception:
                        # Fallback: skip if IDs can't be parsed
                        continue

                    # De-dup pairs (treat A-B same as B-A)
                    sorted_pair = sorted((from_uuid, into_uuid), key=lambda u: str(u))
                    pair_key: Tuple[uuid.UUID, uuid.UUID] = (sorted_pair[0], sorted_pair[1])
                    if pair_key in processed_pairs:
                        continue
                    processed_pairs.add(pair_key)

                    print(f"💥 REAL COLLISION: {from_uuid} ↔ {into_uuid}")

                    # Fire collision event
                    self.world.event_manager.publish(
                        PandaCollisionEvent(str(from_uuid), str(into_uuid),
                                          collision_point, collision_normal)
                    )

                    # Update collider runtime sets
                    collider_a = self.world.get_component(from_uuid, ColliderComponent)
                    collider_b = self.world.get_component(into_uuid, ColliderComponent)
                    if collider_a:
                        collider_a.colliding_entities.add(into_uuid)
                    if collider_b:
                        collider_b.colliding_entities.add(from_uuid)

                    # Publish generic 2D CollisionEvent for non-triggers
                    if collider_a and collider_b and (not collider_a.is_trigger and not collider_b.is_trigger):
                        # Convert normal to 2D
                        normal_2d = Vec2(collision_normal.x, collision_normal.y)
                        self.world.event_manager.publish(
                            CollisionEvent(from_uuid, into_uuid, normal_2d)
                        )

                    self.collision_pairs_found += 1
                else:
                    # This is just a potential collision, not actual contact
                    pass

            self.collision_checks_this_frame += 1

            # Safety check to prevent infinite loops
            if self.collision_checks_this_frame >= self.max_collision_checks:
                break

        # After processing all collisions, fire trigger enter/exit events
        self._fire_trigger_events()

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
        # Remove debug overlay if present
        overlay_np = self._debug_overlays.pop(entity_id, None)
        if overlay_np:
            try:
                overlay_np.removeNode()
            except Exception:
                pass

    # --- World lifecycle hooks ---
    def on_entity_removed(self, entity_id, components):
        """World hook: cleanup collision data when entity is destroyed."""
        self.remove_entity(str(entity_id))

    def on_component_removed(self, entity_id, component):
        """World hook: cleanup when collider component is removed."""
        if isinstance(component, ColliderComponent) or isinstance(component, PandaCollisionNode):
            self.remove_entity(str(entity_id))

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
        # Remove overlays
        for np in self._debug_overlays.values():
            try:
                np.removeNode()
            except Exception:
                pass
        self._debug_overlays.clear()

        # Clean up physics world
        if self.bullet_world:
            # Bullet cleanup would go here
            pass

    def show_collision_nodes(self, show: bool = True):
        """Show or hide collision node visualizations."""
        print(f"🔍 Setting collision visualization to: {'ON' if show else 'OFF'}")
        self._viz_enabled = bool(show)

        for node_name, node_path in self.collision_nodes.items():
            if show:
                print(f"  📍 Showing collision node: {node_name}")
                node_path.show()
                collision_node = node_path.node()
                # Show the actual collision solids and bounds
                if hasattr(collision_node, 'show'):
                    collision_node.show()
                if hasattr(collision_node, 'showBounds'):
                    collision_node.showBounds()
                # Make semi-transparent for visibility
                node_path.setTransparency(True)
                node_path.setColor(1, 1, 0, 0.5)
            else:
                print(f"  📍 Hiding collision node: {node_name}")
                node_path.hide()
                collision_node = node_path.node()
                if hasattr(collision_node, 'hide'):
                    collision_node.hide()
                if hasattr(collision_node, 'hideBounds'):
                    collision_node.hideBounds()

        # Also toggle visualization for boundary nodes
        for name, node_path in self.boundary_nodes.items():
            if show:
                print(f"  📍 Showing boundary node: {name}")
                node_path.show()
                node_path.setTransparency(True)
                node_path.setColor(1, 1, 0, 0.35)
                node = node_path.node()
                if hasattr(node, 'showBounds'):
                    node.showBounds()
            else:
                print(f"  📍 Hiding boundary node: {name}")
                node_path.hide()
                node = node_path.node()
                if hasattr(node, 'hideBounds'):
                    node.hideBounds()

        # Toggle debug overlays visibility to match
        for ent_id, overlay_np in self._debug_overlays.items():
            if show:
                overlay_np.show()
                overlay_np.setTransparency(TransparencyAttrib.M_alpha)
                overlay_np.setColor(1, 1, 0, 0.5)
            else:
                overlay_np.hide()

    def highlight_collision(self, entity_id: str, duration: float = 0.2):
        """Temporarily highlight a collision node when collision occurs."""
        print(f"🎯 Attempting to highlight collision for entity {entity_id}")
        
        # Prefer the debug overlay for coloring
        overlay_np = self._debug_overlays.get(entity_id)
        if overlay_np is None:
            # Fallback to collision node path
            if entity_id in self.entity_to_node:
                node_name = self.entity_to_node[entity_id]
                overlay_np = self.collision_nodes.get(node_name)
        if overlay_np is None:
            print(f"  ❌ No overlay or node found to highlight for {entity_id}")
            return

        # Set to red, then schedule reset back to yellow
        overlay_np.setTransparency(TransparencyAttrib.M_alpha)
        overlay_np.setColor(1, 0, 0, 1)
        print(f"💥 Highlighting collision for entity {entity_id} - overlay RED")

        if hasattr(self, 'base') and self.base:
            def _reset_task(task):
                try:
                    overlay_np.setColor(1, 1, 0, 0.5)
                    overlay_np.setTransparency(TransparencyAttrib.M_alpha)
                except Exception:
                    pass
                return task.done
            self.base.taskMgr.doMethodLater(duration, _reset_task, f"reset_collision_color_{entity_id}")

    # --- Debug overlay helpers ---
    def _ensure_debug_overlay(self, entity_id: str, collider: ColliderComponent):
        if entity_id in self._debug_overlays:
            return
        np = None
        if collider.collider_type in (ColliderType.RECTANGLE, ColliderType.BOX):
            cm = CardMaker(f"viz_{entity_id}")
            cm.set_frame(-0.5, 0.5, -0.5, 0.5)
            np = NodePath(cm.generate())
            # Rotate from XY to XZ plane
            np.set_hpr(0, -90, 0)
        elif collider.collider_type in (ColliderType.CIRCLE, ColliderType.SPHERE):
            ls = LineSegs()
            ls.set_thickness(2.0)
            segs = 48
            for i in range(segs + 1):
                t = (i / segs) * (2 * math.pi)
                x = math.cos(t)
                z = math.sin(t)
                if i == 0:
                    ls.move_to(x, 0, z)
                else:
                    ls.draw_to(x, 0, z)
            np = NodePath(ls.create())
        else:
            cm = CardMaker(f"viz_{entity_id}")
            cm.set_frame(-0.5, 0.5, -0.5, 0.5)
            np = NodePath(cm.generate())
            np.set_hpr(0, -90, 0)
        np.reparentTo(self.collision_root)
        np.setTransparency(TransparencyAttrib.M_alpha)
        np.setColor(1, 1, 0, 0.5)
        if not self._viz_enabled:
            np.hide()
        self._debug_overlays[entity_id] = np

    def _update_debug_overlay(self, entity_id: str, collider: ColliderComponent, transform: TransformComponent):
        np = self._debug_overlays.get(entity_id)
        if not np:
            return
        # Match position and rotation
        np.set_pos(transform.x, 0, transform.y)
        np.set_hpr(0, 0, transform.rotation)
        # Match size
        if collider.collider_type in (ColliderType.RECTANGLE, ColliderType.BOX):
            # Scale the card to collider size (x,z)
            sx = max(0.001, collider.size.x)
            sz = max(0.001, collider.size.y)
            np.set_scale(sx, 1.0, sz)
        elif collider.collider_type in (ColliderType.CIRCLE, ColliderType.SPHERE):
            r = max(0.001, collider.radius)
            np.set_scale(r, 1.0, r)

    def is_collision_nodes_visible(self) -> bool:
        """Check if collision nodes are currently visible."""
        return self._viz_enabled

    # --- Helpers and optional API ---
    def _int_to_bitmask32(self, mask_value: int) -> BitMask32:
        """Convert an integer bitfield to Panda3D BitMask32."""
        bm = BitMask32.allOff()
        # Support up to 32 layers
        for i in range(32):
            if mask_value & (1 << i):
                bm.set_bit(i)
        return bm

    def _fire_trigger_events(self):
        """Compute trigger enter/exit based on colliding sets and publish events."""
        entities = self.world.get_entities_with_components(TransformComponent, ColliderComponent)
        for entity in entities:
            collider = self.world.get_component(entity.id, ColliderComponent)
            if not collider or not collider.is_trigger:
                continue

            new_collisions = collider.colliding_entities - collider.was_colliding_entities
            for other_id in new_collisions:
                self.world.event_manager.publish(TriggerEnterEvent(entity.id, other_id))

            ended_collisions = collider.was_colliding_entities - collider.colliding_entities
            for other_id in ended_collisions:
                self.world.event_manager.publish(TriggerExitEvent(entity.id, other_id))

    def set_playfield_bounds(self, min_x: float, min_y: float, max_x: float, max_y: float):
        """Create static into-only boundary colliders around the playfield.

        The boundaries are implemented as thin CollisionBox solids on the X/Z plane
        and reparented under the collision_root. They use into-masks only so they
        don't need to be added to the traverser.
        """
        # Remove existing boundaries first
        self.remove_playfield_bounds()

        thickness = 0.05
        width = max_x - min_x
        height = max_y - min_y
        # Use a fixed layer for boundaries (layer 5 by default)
        BOUNDARY_LAYER = 5
        boundary_mask = BitMask32.bit(max(0, BOUNDARY_LAYER - 1))

        def make_wall(name: str, center_x: float, center_z: float, half_x: float, half_z: float):
            node = CollisionNode(name)
            # Use very thin Y thickness (depth) since our 2D lies on X/Z
            box = CollisionBox(Vec3(-half_x, -thickness, -half_z), Vec3(half_x, thickness, half_z))
            node.add_solid(box)
            node.set_from_collide_mask(BitMask32.allOff())  # into-only
            node.set_into_collide_mask(boundary_mask)
            np = NodePath(node)
            np.reparentTo(self.collision_root)
            np.set_pos(center_x, 0, center_z)
            self.boundary_nodes[name] = np

        # Left wall
        make_wall("boundary_left", min_x - thickness, 0.0, thickness, height / 2)
        # Right wall
        make_wall("boundary_right", max_x + thickness, 0.0, thickness, height / 2)
        # Bottom wall
        make_wall("boundary_bottom", 0.0, min_y - thickness, width / 2, thickness)
        # Top wall
        make_wall("boundary_top", 0.0, max_y + thickness, width / 2, thickness)

        self.playfield_bounds = (min_x, min_y, max_x, max_y)

    def remove_playfield_bounds(self):
        """Remove any existing boundary collider nodes."""
        for np in self.boundary_nodes.values():
            try:
                np.removeNode()
            except Exception:
                pass
        self.boundary_nodes.clear()
