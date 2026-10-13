from __future__ import annotations

import uuid

from panda3d.core import CardMaker, NodePath, TransparencyAttrib, Texture, TextureStage

from engine.core.system import System
from engine.graphics.components.transform_component import TransformComponent
from engine.graphics.components.sprite_component import SpriteComponent
from engine.core.events import ComponentRemovedEvent, EntityDestroyedEvent
from engine.graphics.sprite_sheet import SpriteFrame

class RenderSystem(System):
    def __init__(self, world, base, resource_manager=None): 
        super().__init__(world)
        self.base = base 
        self.aspect2d = base.aspect2d  # Use aspect2d instead of render2d for more reliable positioning
        self.loader = base.loader 
        self.resource_manager = resource_manager  # Optional; when present, used for cartridge asset precedence via mount roots
        self.textures = {} 
        self.world.event_manager.subscribe(ComponentRemovedEvent, self.handle_sprite_component_removed)
        self.world.event_manager.subscribe(EntityDestroyedEvent, self.handle_entity_destroyed)

    def handle_sprite_component_removed(self, event: ComponentRemovedEvent):
        """Handles cleanup when a SpriteComponent is removed from an entity."""
        if event.component_type == SpriteComponent:
            # The component's panda_node should ideally be cleaned by World.remove_component.
            # This handler acts as a fallback or for logging.
            # It attempts to find the node by its conventional name if it's still in the scene graph.
            node_name_pattern = f'{event.entity_id}_sprite_card'
            potential_node = self.aspect2d.find(f"**/{node_name_pattern}")
            if not potential_node.isEmpty():
                # print(f"RenderSystem (event): Found and removing lingering node {potential_node.getName()} for entity {event.entity_id} after SpriteComponent removal.")
                potential_node.removeNode()

    def handle_entity_destroyed(self, event: EntityDestroyedEvent):
        """Handles cleanup when an entity is destroyed."""
        # This also acts as a fallback. The SpriteComponent's removal (triggered by entity removal)
        # should lead to its node being cleaned up by handle_sprite_component_removed or World.remove_component.
        node_name_pattern = f'{event.entity_id}_sprite_card'
        potential_node = self.aspect2d.find(f"**/{node_name_pattern}")
        if not potential_node.isEmpty():
            potential_node.removeNode()

    def _load_texture(self, image_path: str) -> Texture | None:
        """Load and cache a texture with proper error handling.

        When a ResourceManager with mounted cartridge asset roots is present,
        the declared relative path is resolved against the layered roots first
        (cartridge mounts win). The cache is keyed by the *actual loaded path*
        (the resolved file) so that after unmount/switching cartridges the
        same declared image_path can correctly load a different (or updated)
        asset without returning a stale cached Texture from a previous mount.
        """
        load_path = image_path
        if self.resource_manager is not None:
            try:
                resolved = self.resource_manager.resolve_asset_path(image_path)
                if resolved:
                    load_path = resolved
            except Exception:
                # Fall back to raw path on any resolution hiccup (keeps legacy demos working)
                pass

        if load_path not in self.textures:
            try:
                tex = self.loader.loadTexture(load_path)
                if tex:
                    tex.setMagfilter(Texture.FTNearest)
                    tex.setMinfilter(Texture.FTNearest)
                    self.textures[load_path] = tex
                    print(f"Successfully loaded texture: {image_path} (resolved to {load_path})")
                else:
                    print(f"Error: Could not load texture: {image_path}")
                    return None
            except Exception as e:
                print(f"Error loading texture {image_path}: {e}")
                return None
        return self.textures[load_path]

    def _create_sprite_node(self, entity_id: uuid.UUID, image_path: str,
                            sprite: SpriteComponent | None = None) -> NodePath | None:
        """Create a sprite node. Delegates to .egg loader when path ends in .egg."""
        if image_path and image_path.lower().endswith('.egg'):
            return self._create_egg_sprite_node(entity_id, image_path, sprite)

        if not image_path:
            cm = CardMaker(f'{entity_id}_sprite_card')
            cm.setFrame(-0.5, 0.5, -0.5, 0.5)
            node = NodePath(cm.generate())
            node.setTransparency(TransparencyAttrib.MAlpha)
            node.setColor(1, 1, 1, 1)
            node.reparentTo(self.aspect2d)
            print(f"Created colored rectangle sprite node for entity {entity_id}")
            return node

        texture = self._load_texture(image_path)
        if texture:
            cm = CardMaker(f'{entity_id}_sprite_card')
            cm.setFrame(-0.5, 0.5, -0.5, 0.5)
            node = NodePath(cm.generate())
            node.setTexture(texture)
            node.setTransparency(TransparencyAttrib.MAlpha)
            node.setColor(1, 1, 1, 1)
            node.reparentTo(self.aspect2d)
            print(f"Created sprite node for entity {entity_id}: texture {texture.getXSize()}x{texture.getYSize()}")
            return node
        else:
            print(f"Error: Failed to create sprite node for entity {entity_id} - texture loading failed")
            return None

    def _create_egg_sprite_node(self, entity_id: uuid.UUID, image_path: str,
                                sprite: SpriteComponent | None) -> NodePath | None:
        """Load a Panda3D .egg model as a sprite and wire up its SequenceNode.

        Respects ResourceManager mounted roots (cartridge assets first) when available,
        using the same resolve logic as texture loads for consistency.
        """
        load_path = image_path
        if self.resource_manager is not None:
            try:
                resolved = self.resource_manager.resolve_asset_path(image_path)
                if resolved:
                    load_path = resolved
            except Exception:
                pass
        try:
            model = self.loader.loadModel(load_path)
        except Exception as e:
            print(f"Error loading .egg model {image_path}: {e}")
            return None

        if model is None or model.isEmpty():
            print(f"Error: Could not load .egg model: {image_path}")
            return None

        # Set nearest-neighbour filtering on all embedded textures for pixel-art look
        for tex in model.findAllTextures():
            tex.setMagfilter(Texture.FTNearest)
            tex.setMinfilter(Texture.FTNearest)

        # Normalise the model to a 1×1 unit card so _update_node_transform
        # applies the same base_scale as CardMaker-based sprites.
        bounds = model.getTightBounds()
        if bounds:
            min_pt, max_pt = bounds
            extent_x = max_pt.x - min_pt.x
            extent_z = max_pt.z - min_pt.z
            max_extent = max(extent_x, extent_z)
            if max_extent > 0:
                model.setScale(1.0 / max_extent)

        # Create a named parent so cleanup logic (which searches for _sprite_card) works.
        parent = self.aspect2d.attachNewNode(f'{entity_id}_sprite_card')
        parent.setTransparency(TransparencyAttrib.MAlpha)
        model.reparentTo(parent)

        # Find the SequenceNode and store it on the SpriteComponent.
        if sprite is not None:
            seq_path = model.find('**/+SequenceNode')
            if not seq_path.isEmpty():
                sprite._egg_sequence_node = seq_path.node()
                print(f"Found SequenceNode in {image_path} ({seq_path.node().getNumFrames()} frames)")

        print(f"Created .egg sprite node for entity {entity_id}: {image_path}")
        return parent
        
    def _apply_animation_frame(self, node: NodePath, frame: 'SpriteFrame', flip_x: bool = False, flip_y: bool = False):
        """Apply a sprite animation frame's UV coordinates to the given node."""
        if not node or not frame:
            return False
        
        # Get the texture stage
        ts = TextureStage.getDefault()
        
        # Apply UV transformations for the current frame
        node.setTexOffset(ts, frame.u_offset, frame.v_offset)
        node.setTexScale(ts, frame.u_size, frame.v_size)
        
        # Handle flipping if requested
        if flip_x:
            node.setTexScale(ts, -frame.u_size, frame.v_size)
            node.setTexOffset(ts, frame.u_offset + frame.u_size, frame.v_offset)
        
        if flip_y:
            node.setTexScale(ts, frame.u_size, -frame.v_size)
            node.setTexOffset(ts, frame.u_offset, frame.v_offset + frame.v_size)
        
        if flip_x and flip_y:
            node.setTexScale(ts, -frame.u_size, -frame.v_size)
            node.setTexOffset(ts, frame.u_offset + frame.u_size, frame.v_offset + frame.v_size)
            
        return True

    def _update_node_transform(self, node: NodePath, transform: TransformComponent, sprite: SpriteComponent):
        # Position the sprite in aspect2d coordinates
        node.setPos(transform.x, 0, transform.y)
        node.setR(transform.rotation)
        
        # CRITICAL FIX: Use scaling approach that matches minimal.py
        # Transform.scale is now a direct multiplier where 1.0 = reasonable default size
        # This gives sprites that are actually visible, similar to minimal.py's setScale(0.5)
        base_scale = 0.5  # This matches what works in minimal.py
        
        # Apply transform scale as a direct multiplier
        final_scale_x = base_scale * transform.scale_x
        final_scale_z = base_scale * transform.scale_y
        
        node.setScale(final_scale_x, 1, final_scale_z)
        
        # Debug logging for troubleshooting (commented out to reduce noise)
        # print(f"Sprite scale debug - Transform: {transform.scale}, Final: {final_scale_x}x{final_scale_z}")
            
        # Ensure proper color and transparency
        node.setColor(sprite.color)
        # Make sure transparency is properly applied every update
        node.setTransparency(TransparencyAttrib.MAlpha)

    def _get_sorted_renderable_entities(self) -> list:
        entities_to_render = self.world.get_entities_with_components(TransformComponent, SpriteComponent)
        
        sorted_entities_data = []
        for entity in entities_to_render:
            transform = self.world.get_component(entity.id, TransformComponent)
            sprite = self.world.get_component(entity.id, SpriteComponent)
            if transform and sprite: # Ensure components are still there
                sorted_entities_data.append({'entity': entity, 'transform': transform, 'sprite': sprite, 'layer': sprite.layer, 'y_pos': transform.y})

        sorted_entities_data.sort(key=lambda e: (e['layer'], -e['y_pos']))
        return sorted_entities_data

    def _cleanup_stale_nodes(self, current_sprite_entity_ids: set):
        nodes_to_remove = []
        for node in list(self.aspect2d.getChildren()):
            if "_sprite_card" in node.getName():
                try:
                    entity_id_str = node.getName().split('_sprite_card')[0]
                    entity_uuid = uuid.UUID(entity_id_str)

                    should_remove = False
                    if entity_uuid not in current_sprite_entity_ids:
                        should_remove = True
                    else:
                        entity_in_world = self.world.entities.get(entity_uuid)
                        sprite_comp = self.world.get_component(entity_uuid, SpriteComponent) if entity_in_world else None
                        
                        if not entity_in_world or not sprite_comp:
                            should_remove = True
                        # If sprite_comp exists, its panda_node should be this node.
                        # If sprite_comp.panda_node is None (cleaned by World.remove_component) or different, this node is stale.
                        elif sprite_comp and (sprite_comp.panda_node is None or sprite_comp.panda_node != node): # Node is stale if component has a new/different node
                            should_remove = True
                    
                    if should_remove:
                        nodes_to_remove.append(node)

                except ValueError: 
                    print(f"Warning: Could not parse entity ID from node name: {node.getName()} during cleanup.")
                except Exception as e: # More general catch for unexpected issues during cleanup
                    print(f"Error during cleanup check for node {node.getName()}: {e}")
        
        for node in nodes_to_remove:
            node.removeNode()

    def update(self, dt):
        sorted_entities_data = self._get_sorted_renderable_entities()
        current_sprite_entity_ids = set()

        for item_data in sorted_entities_data:
            entity = item_data['entity']
            transform = item_data['transform']
            sprite = item_data['sprite']
            
            current_sprite_entity_ids.add(entity.id)
            
            # Debug output for projectiles
            if hasattr(entity, 'id') and str(entity.id).startswith('projectile'):
                print(f"🚀 Processing projectile entity {entity.id} at ({transform.x:.2f}, {transform.y:.2f})")
                
            # Create node if it doesn't exist yet
            if sprite.panda_node is None:
                if sprite.image_path or (sprite.image_path is None and sprite.sprite_sheet is None):
                    sprite.panda_node = self._create_sprite_node(entity.id, sprite.image_path, sprite)
                    if sprite.panda_node:
                        print(f"✅ Created sprite node for entity {entity.id}")
                    else:
                        print(f"❌ Failed to create sprite node for entity {entity.id}")

            # Update transform and appearance
            if sprite.panda_node:
                self._update_node_transform(sprite.panda_node, transform, sprite)

                # UV sprite-sheet animation (skip for .egg — SequenceNode manages its own timing)
                if sprite._egg_sequence_node is None and sprite.sprite_sheet and sprite.is_playing:
                    sprite.update_animation(dt)
                    current_frame = sprite.get_current_frame()
                    if current_frame:
                        self._apply_animation_frame(sprite.panda_node, current_frame)
            else:
                sprite.panda_node = None

        self._cleanup_stale_nodes(current_sprite_entity_ids)
