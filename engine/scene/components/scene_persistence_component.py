import json
import pickle
import os
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List, Callable


from engine.core.component import Component


class ScenePersistenceComponent(Component):
    """
    Component for scene state saving and loading.
    
    Features:
    - Scene state serialization
    - Save/load scene data
    - Entity persistence
    - Asset tracking
    - Version management
    - Compression and validation
    """
    
    def __init__(self,
                 auto_save: bool = False,
                 auto_save_interval: float = 30.0,
                 max_save_slots: int = 10,
                 save_format: str = "json",
                 compress_saves: bool = True):
        """
        Initialize ScenePersistenceComponent.
        
        Args:
            auto_save: Whether to automatically save scene state
            auto_save_interval: Seconds between auto-saves
            max_save_slots: Maximum number of save slots to keep
            save_format: Save format ("json", "pickle", "binary")
            compress_saves: Whether to compress save data
        """
        super().__init__()
        
        self.auto_save = auto_save
        self.auto_save_interval = auto_save_interval
        self.max_save_slots = max_save_slots
        self.save_format = save_format
        self.compress_saves = compress_saves
        
        # Persistence state
        self.last_save_time = 0.0
        self.save_count = 0
        self.is_dirty = False  # Has unsaved changes
        
        # Save data
        self.persistent_data: Dict[str, Any] = {}
        self.entity_states: Dict[str, Dict[str, Any]] = {}  # entity_id -> component data
        self.scene_metadata: Dict[str, Any] = {}
        
        # Save configuration
        self.save_directory = "saves"
        self.save_filename_prefix = "scene"
        self.backup_saves = True
        self.validate_saves = True
        
        # Persistence filters
        self.persistent_component_types: List[str] = []  # Component types to save
        self.excluded_component_types: List[str] = []    # Component types to skip
        self.persistent_entity_tags: List[str] = []      # Entity tags to save
        self.excluded_entity_tags: List[str] = []        # Entity tags to skip
        
        # Callbacks
        self.on_save_start: Optional[Callable] = None
        self.on_save_complete: Optional[Callable] = None
        self.on_save_error: Optional[Callable] = None
        self.on_load_start: Optional[Callable] = None
        self.on_load_complete: Optional[Callable] = None
        self.on_load_error: Optional[Callable] = None
        
        # Save validation
        self.last_save_hash: Optional[str] = None
        self.save_version: str = "1.0"
        self.engine_version: str = "1.0"
        
        # Performance settings
        self.async_saves = False  # Save asynchronously
        self.incremental_saves = False  # Only save changed data
        self.memory_efficient = True  # Optimize memory usage
    
    def mark_dirty(self):
        """Mark scene as having unsaved changes."""
        self.is_dirty = True
    
    def mark_clean(self):
        """Mark scene as having no unsaved changes."""
        self.is_dirty = False
    
    def should_auto_save(self, current_time: float) -> bool:
        """Check if scene should be auto-saved."""
        if not self.auto_save or not self.is_dirty:
            return False
        
        return (current_time - self.last_save_time) >= self.auto_save_interval
    
    def add_persistent_data(self, key: str, data: Any):
        """Add data to persist across saves/loads."""
        self.persistent_data[key] = data
        self.mark_dirty()
    
    def get_persistent_data(self, key: str, default: Any = None) -> Any:
        """Get persistent data."""
        return self.persistent_data.get(key, default)
    
    def remove_persistent_data(self, key: str):
        """Remove persistent data."""
        if key in self.persistent_data:
            del self.persistent_data[key]
            self.mark_dirty()
    
    def add_entity_state(self, entity_id: str, component_data: Dict[str, Any]):
        """Add entity state for persistence."""
        self.entity_states[entity_id] = component_data
        self.mark_dirty()
    
    def get_entity_state(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get saved entity state."""
        return self.entity_states.get(entity_id)
    
    def remove_entity_state(self, entity_id: str):
        """Remove entity state."""
        if entity_id in self.entity_states:
            del self.entity_states[entity_id]
            self.mark_dirty()
    
    def set_scene_metadata(self, metadata: Dict[str, Any]):
        """Set scene metadata."""
        self.scene_metadata = metadata
        self.mark_dirty()
    
    def update_metadata(self, key: str, value: Any):
        """Update specific metadata value."""
        self.scene_metadata[key] = value
        self.mark_dirty()
    
    def add_persistent_component_type(self, component_type: str):
        """Add component type to persist."""
        if component_type not in self.persistent_component_types:
            self.persistent_component_types.append(component_type)
    
    def add_excluded_component_type(self, component_type: str):
        """Add component type to exclude from persistence."""
        if component_type not in self.excluded_component_types:
            self.excluded_component_types.append(component_type)
    
    def should_persist_component(self, component_type: str) -> bool:
        """Check if component type should be persisted."""
        # If excluded, don't persist
        if component_type in self.excluded_component_types:
            return False
        
        # If persistent list is empty, persist all (except excluded)
        if not self.persistent_component_types:
            return True
        
        # Only persist if in persistent list
        return component_type in self.persistent_component_types
    
    def add_persistent_entity_tag(self, tag: str):
        """Add entity tag to persist."""
        if tag not in self.persistent_entity_tags:
            self.persistent_entity_tags.append(tag)
    
    def add_excluded_entity_tag(self, tag: str):
        """Add entity tag to exclude from persistence."""
        if tag not in self.excluded_entity_tags:
            self.excluded_entity_tags.append(tag)
    
    def should_persist_entity(self, entity_tags: List[str]) -> bool:
        """Check if entity should be persisted based on tags."""
        # If entity has excluded tag, don't persist
        for tag in entity_tags:
            if tag in self.excluded_entity_tags:
                return False
        
        # If persistent list is empty, persist all (except excluded)
        if not self.persistent_entity_tags:
            return True
        
        # Only persist if entity has a persistent tag
        for tag in entity_tags:
            if tag in self.persistent_entity_tags:
                return True
        
        return False
    
    def get_save_filename(self, slot: int = 0) -> str:
        """Get save filename for slot."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{self.save_filename_prefix}_{slot}_{timestamp}.{self.save_format}"
    
    def get_save_filepath(self, filename: str) -> str:
        """Get full save file path."""
        os.makedirs(self.save_directory, exist_ok=True)
        return os.path.join(self.save_directory, filename)
    
    def create_save_data(self) -> Dict[str, Any]:
        """Create complete save data structure."""
        return {
            'version': self.save_version,
            'engine_version': self.engine_version,
            'timestamp': datetime.now().isoformat(),
            'save_id': str(uuid.uuid4()),
            'scene_metadata': self.scene_metadata,
            'persistent_data': self.persistent_data,
            'entity_states': self.entity_states,
            'save_count': self.save_count,
            'config': {
                'save_format': self.save_format,
                'compress_saves': self.compress_saves,
                'persistent_component_types': self.persistent_component_types,
                'excluded_component_types': self.excluded_component_types,
                'persistent_entity_tags': self.persistent_entity_tags,
                'excluded_entity_tags': self.excluded_entity_tags
            }
        }
    
    def validate_save_data(self, save_data: Dict[str, Any]) -> bool:
        """Validate save data structure."""
        required_keys = ['version', 'timestamp', 'scene_metadata', 'persistent_data', 'entity_states']
        
        for key in required_keys:
            if key not in save_data:
                return False
        
        # Version compatibility check
        if 'engine_version' in save_data:
            # Add version compatibility logic here
            pass
        
        return True
    
    def cleanup_old_saves(self):
        """Remove old save files beyond max_save_slots."""
        if not os.path.exists(self.save_directory):
            return
        
        # Get all save files for this scene
        save_files = []
        for filename in os.listdir(self.save_directory):
            if filename.startswith(self.save_filename_prefix) and filename.endswith(f".{self.save_format}"):
                filepath = os.path.join(self.save_directory, filename)
                save_files.append((filepath, os.path.getmtime(filepath)))
        
        # Sort by modification time (newest first)
        save_files.sort(key=lambda x: x[1], reverse=True)
        
        # Remove old files
        for filepath, _ in save_files[self.max_save_slots:]:
            try:
                os.remove(filepath)
            except OSError:
                pass  # Ignore errors
    
    def get_save_info(self) -> Dict[str, Any]:
        """Get save system information."""
        save_dir_size = 0
        save_file_count = 0
        
        if os.path.exists(self.save_directory):
            for filename in os.listdir(self.save_directory):
                if filename.startswith(self.save_filename_prefix):
                    filepath = os.path.join(self.save_directory, filename)
                    if os.path.isfile(filepath):
                        save_file_count += 1
                        save_dir_size += os.path.getsize(filepath)
        
        return {
            'auto_save': self.auto_save,
            'auto_save_interval': self.auto_save_interval,
            'is_dirty': self.is_dirty,
            'save_count': self.save_count,
            'last_save_time': self.last_save_time,
            'save_directory': self.save_directory,
            'save_format': self.save_format,
            'compress_saves': self.compress_saves,
            'save_file_count': save_file_count,
            'save_dir_size_bytes': save_dir_size,
            'max_save_slots': self.max_save_slots,
            'persistent_data_keys': len(self.persistent_data),
            'entity_states_count': len(self.entity_states)
        }
