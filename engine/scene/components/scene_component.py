import uuid
from typing import Dict, List, Optional, Any, Callable

from engine.core.component import Component
from engine.scene.typeg.scene_types import SceneState

class SceneComponent(Component):
    """
    Component for scene management and multi-scene support.
    
    Features:
    - Scene lifecycle management
    - Entity organization by scene
    - Scene metadata and configuration
    - Scene loading/unloading
    - Multi-scene coordination
    """
    
    def __init__(self,
                 scene_name: str,
                 scene_id: Optional[str] = None,
                 is_persistent: bool = False,
                 is_overlay: bool = False,
                 priority: int = 0,
                 auto_pause_background: bool = True):
        """
        Initialize SceneComponent.
        
        Args:
            scene_name: Human-readable name for the scene
            scene_id: Unique identifier (auto-generated if None)
            is_persistent: Whether scene survives scene changes
            is_overlay: Whether scene renders over other scenes
            priority: Rendering/update priority (higher = later)
            auto_pause_background: Whether to pause when not active
        """
        super().__init__()
        
        self.scene_name = scene_name
        self.scene_id = scene_id or str(uuid.uuid4())
        self.is_persistent = is_persistent
        self.is_overlay = is_overlay
        self.priority = priority
        self.auto_pause_background = auto_pause_background
        
        # Scene state
        self.state = SceneState.INACTIVE
        self.previous_state = SceneState.INACTIVE
        
        # Entity management
        self.entities: List[uuid.UUID] = []  # Entities belonging to this scene
        self.entity_cache: Dict[str, uuid.UUID] = {}  # Name -> entity_id mapping
        
        # Scene data and configuration
        self.scene_data: Dict[str, Any] = {}  # Custom scene data
        self.init_functions: List[Callable] = []  # Functions to call on scene start
        self.cleanup_functions: List[Callable] = []  # Functions to call on scene end
        
        # Loading and resources
        self.assets_to_load: List[str] = []  # Asset paths to preload
        self.loaded_assets: Dict[str, Any] = {}  # Loaded asset cache
        self.loading_progress: float = 0.0  # 0.0 to 1.0
        
        # Scene configuration
        self.background_color: Optional[tuple] = None  # RGB background color
        self.camera_settings: Dict[str, Any] = {}  # Camera configuration
        self.physics_settings: Dict[str, Any] = {}  # Physics world settings
        
        # Performance settings
        self.max_entities: Optional[int] = None  # Entity limit
        self.update_frequency: float = 60.0  # Target FPS for this scene
        self.memory_budget: Optional[int] = None  # Memory limit in MB
        
        # Events and callbacks
        self.on_enter_callbacks: List[Callable] = []
        self.on_exit_callbacks: List[Callable] = []
        self.on_pause_callbacks: List[Callable] = []
        self.on_resume_callbacks: List[Callable] = []
    
    def add_entity(self, entity_id: uuid.UUID, name: Optional[str] = None):
        """Add an entity to this scene."""
        if entity_id not in self.entities:
            self.entities.append(entity_id)
            if name:
                self.entity_cache[name] = entity_id
    
    def remove_entity(self, entity_id: uuid.UUID):
        """Remove an entity from this scene."""
        if entity_id in self.entities:
            self.entities.remove(entity_id)
            # Remove from cache if present
            for name, cached_id in list(self.entity_cache.items()):
                if cached_id == entity_id:
                    del self.entity_cache[name]
    
    def get_entity_by_name(self, name: str) -> Optional[uuid.UUID]:
        """Get entity ID by name."""
        return self.entity_cache.get(name)
    
    def set_state(self, new_state: SceneState):
        """Change scene state."""
        self.previous_state = self.state
        self.state = new_state
    
    def is_active(self) -> bool:
        """Check if scene is currently active."""
        return self.state == SceneState.ACTIVE
    
    def is_loading(self) -> bool:
        """Check if scene is currently loading."""
        return self.state == SceneState.LOADING
    
    def is_transitioning(self) -> bool:
        """Check if scene is transitioning."""
        return self.state in [SceneState.TRANSITIONING_IN, SceneState.TRANSITIONING_OUT]
    
    def can_receive_input(self) -> bool:
        """Check if scene should receive input."""
        return self.state in [SceneState.ACTIVE, SceneState.TRANSITIONING_IN]
    
    def should_update(self) -> bool:
        """Check if scene should update its systems."""
        if not self.auto_pause_background:
            return self.state != SceneState.INACTIVE
        return self.state in [SceneState.ACTIVE, SceneState.TRANSITIONING_IN, SceneState.TRANSITIONING_OUT]
    
    def should_render(self) -> bool:
        """Check if scene should render."""
        return self.state in [
            SceneState.ACTIVE, 
            SceneState.PAUSED, 
            SceneState.TRANSITIONING_IN, 
            SceneState.TRANSITIONING_OUT
        ]
    
    def add_init_function(self, func: Callable):
        """Add function to call when scene starts."""
        self.init_functions.append(func)
    
    def add_cleanup_function(self, func: Callable):
        """Add function to call when scene ends."""
        self.cleanup_functions.append(func)
    
    def add_asset_to_load(self, asset_path: str):
        """Add asset to preload list."""
        if asset_path not in self.assets_to_load:
            self.assets_to_load.append(asset_path)
    
    def set_asset_loaded(self, asset_path: str, asset_data: Any):
        """Mark asset as loaded and cache it."""
        self.loaded_assets[asset_path] = asset_data
        
        # Update loading progress
        if self.assets_to_load:
            loaded_count = len(self.loaded_assets)
            total_count = len(self.assets_to_load)
            self.loading_progress = loaded_count / total_count
    
    def get_loaded_asset(self, asset_path: str) -> Optional[Any]:
        """Get a loaded asset."""
        return self.loaded_assets.get(asset_path)
    
    def is_fully_loaded(self) -> bool:
        """Check if all assets are loaded."""
        return len(self.loaded_assets) >= len(self.assets_to_load)
    
    def clear_loaded_assets(self):
        """Clear loaded asset cache."""
        self.loaded_assets.clear()
        self.loading_progress = 0.0
    
    def get_entity_count(self) -> int:
        """Get number of entities in this scene."""
        return len(self.entities)
    
    def is_at_entity_limit(self) -> bool:
        """Check if scene is at entity limit."""
        if self.max_entities is None:
            return False
        return len(self.entities) >= self.max_entities
    
    def get_scene_info(self) -> Dict[str, Any]:
        """Get comprehensive scene information."""
        return {
            'scene_name': self.scene_name,
            'scene_id': self.scene_id,
            'state': self.state.value,
            'entity_count': len(self.entities),
            'is_persistent': self.is_persistent,
            'is_overlay': self.is_overlay,
            'priority': self.priority,
            'loading_progress': self.loading_progress,
            'assets_loaded': len(self.loaded_assets),
            'assets_total': len(self.assets_to_load)
        }
