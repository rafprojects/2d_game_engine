from engine.core.system import System
from engine.core.components.transform_component import TransformComponent
from engine.graphics.components.sprite_component import SpriteComponent
from engine.core.events import ComponentRemovedEvent, EntityDestroyedEvent
from engine.graphics.sprite_sheet import SpriteFrame
# Import Panda3D components the same way as in minimal.py
from panda3d.core import CardMaker, NodePath, TransparencyAttrib, Texture, TextureStage
import uuid

class RenderSystem(System):
    def __init__(self, world, base): 
        super().__init__(world)
        self.base = base 
        self.aspect2d = base.aspect2d  # Use aspect2d instead of render2d for more reliable positioning
        self.loader = base.loader 
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
        if image_path not in self.textures:
            tex = self.loader.loadTexture(image_path)
            if tex:
                tex.setMagfilter(Texture.FTNearest)
                tex.setMinfilter(Texture.FTNearest)
                self.textures[image_path] = tex
            else:
                print(f"Warning: Could not load texture: {image_path}")
                return None
        return self.textures[image_path]

    def _create_sprite_node(self, entity_id: uuid.UUID, image_path: str) -> NodePath | None:
        texture = self._load_texture(image_path)
        if texture:
            cm = CardMaker(f'{entity_id}_sprite_card')
            cm.setFrame(-0.5, 0.5, -0.5, 0.5)  # Centered at origin
            node = NodePath(cm.generate())
            node.setTexture(texture)
            node.setTransparency(TransparencyAttrib.MAlpha)
            node.setColor(1, 1, 1, 1)  # Ensure full opacity and color by default
            node.reparentTo(self.aspect2d)
            return node
        return None
        
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
        node.setPos(transform.position.x, 0, transform.position.y)
        node.setR(transform.rotation)
        
        # Apply scaling based on texture size with more appropriate scale values
        # This approach avoids extreme scaling values that can cause rendering issues
        if node.getTexture():
            # Use a more moderate scale factor similar to what worked in the minimal demo
            # We'll use a base scale of 0.1 per pixel which gives good results for typical 64px sprites
            base_scale = 0.1
            # Adjust scale based on texture size
            texture = node.getTexture()
            tex_width = texture.getXSize()
            tex_height = texture.getYSize()
            # Scale proportionally to texture size
            scale_x = transform.scale.x * base_scale * (tex_width / 64.0)
            scale_z = transform.scale.y * base_scale * (tex_height / 64.0)
            node.setScale(scale_x, 1, scale_z)
        else:
            # Fallback scaling if no texture is available
            node.setScale(transform.scale.x * 0.5, 1, transform.scale.y * 0.5)
            
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
                sorted_entities_data.append({'entity': entity, 'transform': transform, 'sprite': sprite, 'layer': sprite.layer, 'y_pos': transform.position.y})

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
                
            # Create node if it doesn't exist yet
            if sprite.panda_node is None and sprite.image_path:
                sprite.panda_node = self._create_sprite_node(entity.id, sprite.image_path)
            
            # Update transform and appearance
            if sprite.panda_node:
                self._update_node_transform(sprite.panda_node, transform, sprite)
                
                # Handle animation if sprite has a sprite sheet and animation
                if sprite.sprite_sheet and sprite.is_playing:
                    sprite.update_animation(dt)
                    current_frame = sprite.get_current_frame()
                    if current_frame:
                        self._apply_animation_frame(sprite.panda_node, current_frame)
            else:
                # If node creation failed or image_path is None, ensure panda_node is None
                sprite.panda_node = None

        self._cleanup_stale_nodes(current_sprite_entity_ids)
