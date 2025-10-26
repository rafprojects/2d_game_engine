"""
Panda3D Collision Node Management Component

This internal component manages the lifecycle of Panda3D collision nodes
for entities in the ECS system.
"""

from typing import Optional
from panda3d.core import NodePath, CollisionNode, BitMask32, Vec3

from engine.core.component import Component


class PandaCollisionNode(Component):
    """
    Internal component for managing Panda3D collision nodes.

    This component is automatically created and managed by the PandaCollisionSystem.
    It should not be created manually by users.
    """

    def __init__(self, collision_node_path: NodePath, collision_node: CollisionNode):
        """
        Initialize the Panda3D collision node component.

        Args:
            collision_node_path: Panda3D NodePath containing the collision node
            collision_node: The Panda3D CollisionNode itself
        """
        self.collision_node_path = collision_node_path
        self.collision_node = collision_node

        # State tracking
        self.is_active = True
        self.collision_mask = BitMask32.allOn()
        self.collide_mask = BitMask32.allOn()

        # Performance tracking
        self.collision_checks_this_frame = 0
        self.last_collision_time = 0.0

    def set_collision_masks(self, from_mask: BitMask32, into_mask: BitMask32):
        """Set collision masks for this collision node."""
        self.collision_node.set_from_collide_mask(from_mask)
        self.collision_node.set_into_collide_mask(into_mask)
        self.collision_mask = from_mask
        self.collide_mask = into_mask

    def set_active(self, active: bool):
        """Enable or disable collision detection for this node."""
        self.is_active = active
        if active:
            self.collision_node.set_into_collide_mask(self.collide_mask)
        else:
            self.collision_node.set_into_collide_mask(BitMask32.allOff())

    def get_node_path(self) -> NodePath:
        """Get the Panda3D NodePath for this collision node."""
        return self.collision_node_path

    def get_collision_node(self) -> CollisionNode:
        """Get the Panda3D CollisionNode."""
        return self.collision_node

    def update_transform(self, transform):
        """Update the transform of the collision node."""
        pos_3d = Vec3(transform.x, transform.y, 0)
        hpr = Vec3(0, 0, transform.rotation)
        scale_vec = Vec3(transform.scale_x, transform.scale_y, 1)

        if self.collision_node_path:
            self.collision_node_path.set_pos(pos_3d)
            self.collision_node_path.set_hpr(hpr)
            self.collision_node_path.set_scale(scale_vec)

    def cleanup(self):
        """Clean up the collision node resources."""
        if self.collision_node_path:
            self.collision_node_path.removeNode()
            self.collision_node_path = None
            self.collision_node = None
