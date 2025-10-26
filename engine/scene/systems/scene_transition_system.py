import uuid
from typing import Dict, Optional, List

from panda3d.core import NodePath, CardMaker, TransparencyAttrib, Vec4, Vec2

from engine.core.system import System
from engine.scene.components.scene_transition_component import SceneTransitionComponent
from engine.scene.components.scene_component import SceneComponent
from engine.scene.typeg.scene_transition_types import TransitionType


class SceneTransitionSystem(System):
    """
    System for managing scene transitions and visual effects.
    
    Features:
    - Multiple transition types (fade, slide, wipe, etc.)
    - Smooth transition animations
    - Transition state management
    - Visual overlay management
    - Custom transition effects
    """
    
    def __init__(self, world, base):
        super().__init__(world)
        self.base = base
        
        # Transition management
        self.active_transitions: Dict[str, uuid.UUID] = {}  # scene_id -> entity_id
        self.transition_overlays: Dict[str, NodePath] = {}  # scene_id -> overlay_node
        
        # Rendering setup
        self.aspect2d = base.aspect2d
        self.transition_root = self.aspect2d.attachNewNode("transition_root")
        self.transition_root.setRenderModeWireframe()
        self.transition_root.setBin("fixed", 100)  # Render on top
        
        # Default settings
        self.screen_width = 800  # Will be updated from base
        self.screen_height = 600
        self.default_fade_color = Vec4(0, 0, 0, 1)
        
        # Performance settings
        self.max_concurrent_transitions = 3
        self.use_render_to_texture = False  # For advanced effects
        
        # Update screen dimensions if available
        if hasattr(base, 'win') and base.win:
            props = base.win.getProperties()
            self.screen_width = props.getXSize()
            self.screen_height = props.getYSize()
    
    def update(self, dt: float):
        """Update all active transitions."""
        completed_transitions = []
        
        # Update each active transition
        for scene_id in list(self.active_transitions.keys()):
            entity_id = self.active_transitions[scene_id]
            transition_comp = self.world.get_component(entity_id, SceneTransitionComponent)
            
            if not transition_comp:
                completed_transitions.append(scene_id)
                continue
            
            # Update transition progress
            transition_comp.update_transition(dt)
            
            # Update visual effects
            self._update_transition_visual(scene_id, transition_comp)
            
            # Check if transition is complete
            if not transition_comp.is_transitioning:
                completed_transitions.append(scene_id)
        
        # Clean up completed transitions
        for scene_id in completed_transitions:
            self._cleanup_transition(scene_id)
    
    def start_transition(self, scene_id: str, entity_id: uuid.UUID, direction: str = "in") -> bool:
        """Start a scene transition."""
        transition_comp = self.world.get_component(entity_id, SceneTransitionComponent)
        if not transition_comp:
            return False
        
        # Check if already transitioning
        if scene_id in self.active_transitions:
            transition_comp.interrupt_transition()
            self._cleanup_transition(scene_id)
        
        # Register active transition
        self.active_transitions[scene_id] = entity_id
        
        # Create visual overlay
        self._create_transition_overlay(scene_id, transition_comp)
        
        # Start transition
        if direction == "in":
            transition_comp.start_transition_in()
        else:
            transition_comp.start_transition_out()
        
        print(f"🎬 Started {direction} transition for scene: {scene_id}")
        return True
    
    def interrupt_transition(self, scene_id: str) -> bool:
        """Interrupt an active transition."""
        if scene_id not in self.active_transitions:
            return False
        
        entity_id = self.active_transitions[scene_id]
        transition_comp = self.world.get_component(entity_id, SceneTransitionComponent)
        
        if transition_comp:
            transition_comp.interrupt_transition()
        
        self._cleanup_transition(scene_id)
        return True
    
    def is_transitioning(self, scene_id: str) -> bool:
        """Check if scene is currently transitioning."""
        return scene_id in self.active_transitions
    
    def get_transition_progress(self, scene_id: str) -> float:
        """Get transition progress (0.0 to 1.0)."""
        if scene_id not in self.active_transitions:
            return 0.0
        
        entity_id = self.active_transitions[scene_id]
        transition_comp = self.world.get_component(entity_id, SceneTransitionComponent)
        
        return transition_comp.progress if transition_comp else 0.0
    
    def _create_transition_overlay(self, scene_id: str, transition_comp: SceneTransitionComponent):
        """Create visual overlay for transition."""
        # Clean up existing overlay
        if scene_id in self.transition_overlays:
            self.transition_overlays[scene_id].removeNode()
        
        # Create overlay based on transition type
        overlay_node = self._create_overlay_node(transition_comp)
        
        if overlay_node:
            self.transition_overlays[scene_id] = overlay_node
            overlay_node.reparentTo(self.transition_root)
    
    def _create_overlay_node(self, transition_comp: SceneTransitionComponent) -> Optional[NodePath]:
        """Create overlay node based on transition type."""
        if transition_comp.transition_type in [TransitionType.FADE, TransitionType.FADE_THROUGH_COLOR]:
            return self._create_fade_overlay(transition_comp)
        elif transition_comp.transition_type in [
            TransitionType.SLIDE_LEFT, TransitionType.SLIDE_RIGHT,
            TransitionType.SLIDE_UP, TransitionType.SLIDE_DOWN
        ]:
            return self._create_slide_overlay(transition_comp)
        elif transition_comp.transition_type in [TransitionType.CIRCLE_CLOSE, TransitionType.CIRCLE_OPEN]:
            return self._create_circle_overlay(transition_comp)
        elif transition_comp.transition_type == TransitionType.CUSTOM:
            return self._create_custom_overlay(transition_comp)
        
        return None
    
    def _create_fade_overlay(self, transition_comp: SceneTransitionComponent) -> NodePath:
        """Create fade transition overlay."""
        # Create a full-screen card
        card_maker = CardMaker("fade_overlay")
        card_maker.setFrame(-1, 1, -1, 1)  # Full screen in normalized coordinates
        
        overlay_node = self.transition_root.attachNewNode(card_maker.generate())
        overlay_node.setColor(transition_comp.fade_color)
        overlay_node.setTransparency(TransparencyAttrib.MAlpha)
        overlay_node.setBin("fixed", 99)
        
        return overlay_node
    
    def _create_slide_overlay(self, transition_comp: SceneTransitionComponent) -> NodePath:
        """Create slide transition overlay."""
        # For slide transitions, we might create multiple overlays
        # or manipulate existing scene nodes. For now, create a simple overlay.
        card_maker = CardMaker("slide_overlay")
        card_maker.setFrame(-1, 1, -1, 1)
        
        overlay_node = self.transition_root.attachNewNode(card_maker.generate())
        overlay_node.setColor(Vec4(0, 0, 0, 1))
        overlay_node.setTransparency(TransparencyAttrib.MAlpha)
        overlay_node.setBin("fixed", 99)
        
        return overlay_node
    
    def _create_circle_overlay(self, transition_comp: SceneTransitionComponent) -> NodePath:
        """Create circle transition overlay."""
        # This would typically use a shader or complex geometry
        # For now, create a simple overlay
        card_maker = CardMaker("circle_overlay")
        card_maker.setFrame(-1, 1, -1, 1)
        
        overlay_node = self.transition_root.attachNewNode(card_maker.generate())
        overlay_node.setColor(Vec4(0, 0, 0, 1))
        overlay_node.setTransparency(TransparencyAttrib.MAlpha)
        overlay_node.setBin("fixed", 99)
        
        return overlay_node
    
    def _create_custom_overlay(self, transition_comp: SceneTransitionComponent) -> Optional[NodePath]:
        """Create custom transition overlay."""
        if transition_comp.custom_transition_func:
            try:
                return transition_comp.custom_transition_func(
                    transition_comp, 
                    self.transition_root,
                    transition_comp.custom_transition_data
                )
            except Exception as e:
                print(f"Error in custom transition function: {e}")
        
        return None
    
    def _update_transition_visual(self, scene_id: str, transition_comp: SceneTransitionComponent):
        """Update visual effects based on transition progress."""
        if scene_id not in self.transition_overlays:
            return
        
        overlay_node = self.transition_overlays[scene_id]
        
        if transition_comp.transition_type in [TransitionType.FADE, TransitionType.FADE_THROUGH_COLOR]:
            self._update_fade_visual(overlay_node, transition_comp)
        elif transition_comp.transition_type in [
            TransitionType.SLIDE_LEFT, TransitionType.SLIDE_RIGHT,
            TransitionType.SLIDE_UP, TransitionType.SLIDE_DOWN
        ]:
            self._update_slide_visual(overlay_node, transition_comp)
        elif transition_comp.transition_type in [TransitionType.CIRCLE_CLOSE, TransitionType.CIRCLE_OPEN]:
            self._update_circle_visual(overlay_node, transition_comp)
        elif transition_comp.transition_type == TransitionType.CUSTOM:
            self._update_custom_visual(overlay_node, transition_comp)
    
    def _update_fade_visual(self, overlay_node: NodePath, transition_comp: SceneTransitionComponent):
        """Update fade transition visual."""
        alpha = transition_comp.get_current_alpha()
        current_color = overlay_node.getColor()
        overlay_node.setColor(current_color.x, current_color.y, current_color.z, alpha)
    
    def _update_slide_visual(self, overlay_node: NodePath, transition_comp: SceneTransitionComponent):
        """Update slide transition visual."""
        offset = transition_comp.get_current_offset()
        
        # Convert screen offset to normalized coordinates
        normalized_x = offset.x / (self.screen_width / 2)
        normalized_y = offset.y / (self.screen_height / 2)
        
        overlay_node.setPos(normalized_x, 0, normalized_y)
    
    def _update_circle_visual(self, overlay_node: NodePath, transition_comp: SceneTransitionComponent):
        """Update circle transition visual."""
        radius = transition_comp.get_current_circle_radius()
        
        # This would typically use a shader to create circular masking
        # For now, just adjust scale as a simple approximation
        scale = max(0.01, radius)  # Prevent zero scale
        overlay_node.setScale(scale, 1, scale)
    
    def _update_custom_visual(self, overlay_node: NodePath, transition_comp: SceneTransitionComponent):
        """Update custom transition visual."""
        if transition_comp.custom_transition_func and transition_comp.on_transition_update:
            try:
                transition_comp.on_transition_update(transition_comp, transition_comp.progress)
            except Exception as e:
                print(f"Error in custom transition update: {e}")
    
    def _cleanup_transition(self, scene_id: str):
        """Clean up transition resources."""
        # Remove from active transitions
        if scene_id in self.active_transitions:
            del self.active_transitions[scene_id]
        
        # Clean up overlay
        if scene_id in self.transition_overlays:
            self.transition_overlays[scene_id].removeNode()
            del self.transition_overlays[scene_id]
        
        print(f"🧹 Cleaned up transition for scene: {scene_id}")
    
    def cleanup_all_transitions(self):
        """Clean up all active transitions."""
        for scene_id in list(self.active_transitions.keys()):
            self._cleanup_transition(scene_id)
        
        # Clear transition root
        for child in self.transition_root.getChildren():
            child.removeNode()
    
    def create_fade_transition(self, duration: float = 1.0, color: Vec4 = None) -> SceneTransitionComponent:
        """Create a fade transition component."""
        color = color or self.default_fade_color
        
        transition_comp = SceneTransitionComponent(
            transition_type=TransitionType.FADE,
            duration=duration,
            easing="ease_in_out"
        )
        transition_comp.set_fade_color(color)
        
        return transition_comp
    
    def create_slide_transition(self, direction: str, duration: float = 1.0) -> SceneTransitionComponent:
        """Create a slide transition component."""
        transition_type_map = {
            "left": TransitionType.SLIDE_LEFT,
            "right": TransitionType.SLIDE_RIGHT,
            "up": TransitionType.SLIDE_UP,
            "down": TransitionType.SLIDE_DOWN
        }
        
        transition_type = transition_type_map.get(direction, TransitionType.SLIDE_LEFT)
        
        transition_comp = SceneTransitionComponent(
            transition_type=transition_type,
            duration=duration,
            easing="ease_in_out"
        )
        transition_comp.set_slide_distance(Vec2(self.screen_width, self.screen_height))
        
        return transition_comp
    
    def get_transition_stats(self) -> Dict[str, any]:
        """Get transition system statistics."""
        return {
            'active_transitions': len(self.active_transitions),
            'overlay_count': len(self.transition_overlays),
            'max_concurrent': self.max_concurrent_transitions,
            'screen_size': (self.screen_width, self.screen_height),
            'use_render_to_texture': self.use_render_to_texture
        }
