import uuid
from typing import Dict, List, Optional, Any, Callable

from panda3d.core import Vec2, Vec4

from engine.core.system import System
from engine.scene.components.scene_component import SceneComponent
from engine.scene.components.scene_transition_component import SceneTransitionComponent
from engine.scene.components.scene_persistence_component import ScenePersistenceComponent
from engine.scene.typeg.scene_types import SceneState

class SceneManager(System):
    """
    Core system for scene management and coordination.
    
    Features:
    - Scene lifecycle management
    - Multi-scene coordination
    - Scene loading and unloading
    - Scene state management
    - Scene entity management
    """
    
    def __init__(self, world):
        super().__init__(world)
        
        # Scene management
        self.active_scenes: Dict[str, uuid.UUID] = {}  # scene_id -> entity_id
        self.scene_stack: List[str] = []  # Stack of active scene IDs
        self.current_scene_id: Optional[str] = None
        self.loading_scenes: Dict[str, uuid.UUID] = {}
        
        # Scene coordination
        self.scene_priority_order: List[str] = []  # Scene IDs by priority
        self.overlay_scenes: List[str] = []  # Overlay scene IDs
        self.persistent_scenes: List[str] = []  # Persistent scene IDs
        
        # Scene loading
        self.scene_templates: Dict[str, Callable] = {}  # scene_name -> creation function
        self.scene_cache: Dict[str, Dict[str, Any]] = {}  # Cached scene data
        self.preloaded_assets: Dict[str, Any] = {}  # Asset cache
        
        # Performance tracking
        self.scene_update_times: Dict[str, float] = {}
        self.total_entities_managed = 0
        self.memory_usage_mb = 0.0
        
        # Events and callbacks
        self.on_scene_changed: Optional[Callable] = None
        self.on_scene_loaded: Optional[Callable] = None
        self.on_scene_unloaded: Optional[Callable] = None
        self.on_loading_progress: Optional[Callable] = None
    
    def update(self, dt: float):
        """Update scene management."""
        # Update active scenes
        self._update_active_scenes(dt)
        
        # Handle loading scenes
        self._update_loading_scenes(dt)
        
        # Update scene priorities
        self._update_scene_priorities()
        
        # Clean up inactive scenes
        self._cleanup_inactive_scenes()
    
    def register_scene_template(self, scene_name: str, creation_func: Callable):
        """Register a scene template function."""
        self.scene_templates[scene_name] = creation_func
    
    def create_scene(self, scene_name: str, scene_id: Optional[str] = None, **kwargs) -> Optional[str]:
        """Create a new scene."""
        # Generate scene ID if not provided
        if scene_id is None:
            scene_id = f"{scene_name}_{uuid.uuid4().hex[:8]}"
        
        # Check if scene already exists
        if scene_id in self.active_scenes:
            print(f"Warning: Scene {scene_id} already exists")
            return scene_id
        
        # Create scene entity
        scene_entity = self.world.create_entity(f"scene_{scene_name}")
        
        # Create scene component
        scene_comp = SceneComponent(
            scene_name=scene_name,
            scene_id=scene_id,
            **kwargs
        )
        self.world.add_component(scene_entity.id, scene_comp)
        
        # Register scene
        self.active_scenes[scene_id] = scene_entity.id
        
        # Call template function if available
        if scene_name in self.scene_templates:
            try:
                self.scene_templates[scene_name](scene_comp, self.world)
            except Exception as e:
                print(f"Error creating scene {scene_name}: {e}")
                self.destroy_scene(scene_id)
                return None
        
        print(f"✅ Created scene: {scene_name} ({scene_id})")
        return scene_id
    
    def load_scene(self, scene_id: str, activate: bool = True) -> bool:
        """Load and optionally activate a scene."""
        if scene_id not in self.active_scenes:
            print(f"Error: Scene {scene_id} not found")
            return False
        
        entity_id = self.active_scenes[scene_id]
        scene_comp = self.world.get_component(entity_id, SceneComponent)
        
        if not scene_comp:
            return False
        
        # Set loading state
        scene_comp.set_state(SceneState.LOADING)
        self.loading_scenes[scene_id] = entity_id
        
        # Start loading assets
        self._start_asset_loading(scene_comp)
        
        # Execute init functions
        for init_func in scene_comp.init_functions:
            try:
                init_func(scene_comp, self.world)
            except Exception as e:
                print(f"Error in scene init function: {e}")
        
        # Call loading callback
        if self.on_scene_loaded:
            self.on_scene_loaded(scene_id, scene_comp)
        
        # Activate if requested
        if activate:
            return self.activate_scene(scene_id)
        
        return True
    
    def activate_scene(self, scene_id: str, push_to_stack: bool = True) -> bool:
        """Activate a scene."""
        if scene_id not in self.active_scenes:
            return False
        
        entity_id = self.active_scenes[scene_id]
        scene_comp = self.world.get_component(entity_id, SceneComponent)
        
        if not scene_comp:
            return False
        
        # Deactivate current scene if not overlay
        if self.current_scene_id and not scene_comp.is_overlay:
            self.deactivate_scene(self.current_scene_id, remove_from_stack=False)
        
        # Activate new scene
        scene_comp.set_state(SceneState.ACTIVE)
        self.current_scene_id = scene_id
        
        # Add to scene stack
        if push_to_stack and scene_id not in self.scene_stack:
            self.scene_stack.append(scene_id)
        
        # Update priority order
        self._update_scene_priorities()
        
        print(f"✅ Activated scene: {scene_comp.scene_name} ({scene_id})")
        
        # Call change callback
        if self.on_scene_changed:
            self.on_scene_changed(scene_id, scene_comp)
        
        return True
    
    def deactivate_scene(self, scene_id: str, remove_from_stack: bool = True) -> bool:
        """Deactivate a scene."""
        if scene_id not in self.active_scenes:
            return False
        
        entity_id = self.active_scenes[scene_id]
        scene_comp = self.world.get_component(entity_id, SceneComponent)
        
        if not scene_comp:
            return False
        
        # Set appropriate state
        if scene_comp.auto_pause_background:
            scene_comp.set_state(SceneState.PAUSED)
        else:
            scene_comp.set_state(SceneState.INACTIVE)
        
        # Remove from stack
        if remove_from_stack and scene_id in self.scene_stack:
            self.scene_stack.remove(scene_id)
        
        # Update current scene
        if self.current_scene_id == scene_id:
            if self.scene_stack:
                # Activate previous scene from stack
                prev_scene_id = self.scene_stack[-1]
                self.current_scene_id = prev_scene_id
                prev_entity_id = self.active_scenes[prev_scene_id]
                prev_scene_comp = self.world.get_component(prev_entity_id, SceneComponent)
                if prev_scene_comp:
                    prev_scene_comp.set_state(SceneState.ACTIVE)
            else:
                self.current_scene_id = None
        
        print(f"⏸️ Deactivated scene: {scene_comp.scene_name} ({scene_id})")
        return True
    
    def unload_scene(self, scene_id: str) -> bool:
        """Unload a scene."""
        if scene_id not in self.active_scenes:
            return False
        
        entity_id = self.active_scenes[scene_id]
        scene_comp = self.world.get_component(entity_id, SceneComponent)
        
        if not scene_comp:
            return False
        
        # Set unloading state
        scene_comp.set_state(SceneState.UNLOADING)
        
        # Execute cleanup functions
        for cleanup_func in scene_comp.cleanup_functions:
            try:
                cleanup_func(scene_comp, self.world)
            except Exception as e:
                print(f"Error in scene cleanup function: {e}")
        
        # Remove from active scenes
        if scene_id in self.scene_stack:
            self.scene_stack.remove(scene_id)
        
        if self.current_scene_id == scene_id:
            self.current_scene_id = None
        
        # Clean up entities
        self._cleanup_scene_entities(scene_comp)
        
        # Clear loaded assets
        scene_comp.clear_loaded_assets()
        
        # Call unload callback
        if self.on_scene_unloaded:
            self.on_scene_unloaded(scene_id, scene_comp)
        
        print(f"📤 Unloaded scene: {scene_comp.scene_name} ({scene_id})")
        return True
    
    def destroy_scene(self, scene_id: str) -> bool:
        """Completely destroy a scene."""
        if not self.unload_scene(scene_id):
            return False
        
        if scene_id in self.active_scenes:
            entity_id = self.active_scenes[scene_id]
            del self.active_scenes[scene_id]
            
            # Remove entity
            self.world.remove_entity(entity_id)
        
        print(f"🗑️ Destroyed scene: {scene_id}")
        return True
    
    def get_scene_component(self, scene_id: str) -> Optional[SceneComponent]:
        """Get scene component by ID."""
        if scene_id not in self.active_scenes:
            return None
        
        entity_id = self.active_scenes[scene_id]
        return self.world.get_component(entity_id, SceneComponent)
    
    def get_active_scenes(self) -> List[str]:
        """Get list of active scene IDs."""
        active = []
        for scene_id, entity_id in self.active_scenes.items():
            scene_comp = self.world.get_component(entity_id, SceneComponent)
            if scene_comp and scene_comp.should_update():
                active.append(scene_id)
        return active
    
    def get_current_scene_id(self) -> Optional[str]:
        """Get current active scene ID."""
        return self.current_scene_id
    
    def get_scene_count(self) -> int:
        """Get total number of managed scenes."""
        return len(self.active_scenes)
    
    def pause_all_scenes(self):
        """Pause all active scenes."""
        for scene_id in self.active_scenes.keys():
            scene_comp = self.get_scene_component(scene_id)
            if scene_comp and scene_comp.is_active():
                scene_comp.set_state(SceneState.PAUSED)
    
    def resume_all_scenes(self):
        """Resume all paused scenes."""
        for scene_id in self.active_scenes.keys():
            scene_comp = self.get_scene_component(scene_id)
            if scene_comp and scene_comp.state == SceneState.PAUSED:
                scene_comp.set_state(SceneState.ACTIVE)
    
    def _update_active_scenes(self, dt: float):
        """Update all active scenes."""
        for scene_id in list(self.active_scenes.keys()):
            scene_comp = self.get_scene_component(scene_id)
            if scene_comp and scene_comp.should_update():
                # Update scene-specific logic here
                pass
    
    def _update_loading_scenes(self, dt: float):
        """Update scenes that are loading."""
        completed_scenes = []
        
        for scene_id in list(self.loading_scenes.keys()):
            scene_comp = self.get_scene_component(scene_id)
            if not scene_comp:
                completed_scenes.append(scene_id)
                continue
            
            # Check if loading is complete
            if scene_comp.is_fully_loaded():
                scene_comp.set_state(SceneState.INACTIVE)
                completed_scenes.append(scene_id)
                
                # Call progress callback
                if self.on_loading_progress:
                    self.on_loading_progress(scene_id, 1.0, True)
            else:
                # Update loading progress
                if self.on_loading_progress:
                    self.on_loading_progress(scene_id, scene_comp.loading_progress, False)
        
        # Remove completed scenes from loading list
        for scene_id in completed_scenes:
            if scene_id in self.loading_scenes:
                del self.loading_scenes[scene_id]
    
    def _update_scene_priorities(self):
        """Update scene rendering priority order."""
        scenes_with_priority = []
        
        for scene_id in self.active_scenes.keys():
            scene_comp = self.get_scene_component(scene_id)
            if scene_comp and scene_comp.should_render():
                scenes_with_priority.append((scene_id, scene_comp.priority))
        
        # Sort by priority (lower priority renders first)
        scenes_with_priority.sort(key=lambda x: x[1])
        self.scene_priority_order = [scene_id for scene_id, _ in scenes_with_priority]
    
    def _start_asset_loading(self, scene_comp: SceneComponent):
        """Start loading assets for a scene."""
        # This would integrate with an asset loading system
        # For now, just mark as loaded
        for asset_path in scene_comp.assets_to_load:
            scene_comp.set_asset_loaded(asset_path, f"loaded_{asset_path}")
    
    def _cleanup_scene_entities(self, scene_comp: SceneComponent):
        """Clean up entities belonging to a scene."""
        for entity_id in list(scene_comp.entities):
            try:
                self.world.remove_entity(entity_id)
            except Exception as e:
                print(f"Error removing entity {entity_id}: {e}")
        
        scene_comp.entities.clear()
        scene_comp.entity_cache.clear()
    
    def _cleanup_inactive_scenes(self):
        """Clean up scenes that should be removed."""
        # This could implement logic to automatically clean up
        # scenes that have been inactive for too long
        pass
    
    def get_scene_stats(self) -> Dict[str, Any]:
        """Get comprehensive scene management statistics."""
        total_entities = 0
        loading_count = 0
        active_count = 0
        
        for scene_id in self.active_scenes.keys():
            scene_comp = self.get_scene_component(scene_id)
            if scene_comp:
                total_entities += len(scene_comp.entities)
                if scene_comp.is_loading():
                    loading_count += 1
                if scene_comp.is_active():
                    active_count += 1
        
        return {
            'total_scenes': len(self.active_scenes),
            'active_scenes': active_count,
            'loading_scenes': loading_count,
            'current_scene': self.current_scene_id,
            'scene_stack_depth': len(self.scene_stack),
            'total_entities': total_entities,
            'overlay_scenes': len(self.overlay_scenes),
            'persistent_scenes': len(self.persistent_scenes),
            'registered_templates': len(self.scene_templates)
        }
