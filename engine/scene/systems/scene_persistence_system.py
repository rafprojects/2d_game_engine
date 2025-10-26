import json
import pickle
import os
import time
import hashlib
import uuid
from typing import Dict, Any, Optional, List

from engine.core.system import System
from engine.scene.components.scene_persistence_component import ScenePersistenceComponent
from engine.scene.components.scene_component import SceneComponent

class ScenePersistenceSystem(System):
    """
    System for scene state persistence, saving, and loading.
    
    Features:
    - Automatic and manual scene saving
    - Multiple save formats (JSON, pickle, binary)
    - Save slot management
    - Data validation and integrity checking
    - Incremental and full saves
    - Asset tracking and caching
    """
    
    def __init__(self, world):
        super().__init__(world)
        
        # Persistence management
        self.auto_save_entities: Dict[str, uuid.UUID] = {}  # scene_id -> entity_id
        self.save_operations: List[Dict[str, Any]] = []  # Queue of save operations
        self.load_operations: List[Dict[str, Any]] = []  # Queue of load operations
        
        # Global settings
        self.global_save_directory = "saves"
        self.backup_directory = "saves/backups"
        self.temp_directory = "saves/temp"
        
        # Performance tracking
        self.save_times: List[float] = []
        self.load_times: List[float] = []
        self.total_saves_performed = 0
        self.total_loads_performed = 0
        
        # Create directories
        os.makedirs(self.global_save_directory, exist_ok=True)
        os.makedirs(self.backup_directory, exist_ok=True)
        os.makedirs(self.temp_directory, exist_ok=True)
    
    def update(self, dt: float):
        """Update persistence system."""
        current_time = time.time()
        
        # Check for auto-saves
        self._check_auto_saves(current_time)
        
        # Process save operations
        self._process_save_operations()
        
        # Process load operations
        self._process_load_operations()
    
    def save_scene(self, scene_id: str, slot: int = 0, save_name: Optional[str] = None) -> bool:
        """Save a scene to disk."""
        # Find scene entity
        scene_entities = self.world.get_entities_with_components(SceneComponent)
        scene_entity = None
        scene_comp = None
        
        for entity in scene_entities:
            comp = self.world.get_component(entity.id, SceneComponent)
            if comp and comp.scene_id == scene_id:
                scene_entity = entity
                scene_comp = comp
                break
        
        if not scene_comp:
            print(f"Error: Scene {scene_id} not found")
            return False
        
        # Get persistence component
        persistence_comp = self.world.get_component(scene_entity.id, ScenePersistenceComponent)
        if not persistence_comp:
            print(f"Warning: Scene {scene_id} has no persistence component")
            return False
        
        try:
            start_time = time.time()
            
            # Call save start callback
            if persistence_comp.on_save_start:
                persistence_comp.on_save_start(scene_id, slot)
            
            # Collect scene data
            save_data = self._collect_scene_data(scene_comp, persistence_comp)
            
            # Generate filename
            if save_name:
                filename = f"{save_name}.{persistence_comp.save_format}"
            else:
                filename = persistence_comp.get_save_filename(slot)
            
            filepath = persistence_comp.get_save_filepath(filename)
            
            # Create backup if exists
            if os.path.exists(filepath) and persistence_comp.backup_saves:
                self._create_backup(filepath)
            
            # Save data
            success = self._write_save_data(filepath, save_data, persistence_comp)
            
            if success:
                # Update persistence component
                persistence_comp.save_count += 1
                persistence_comp.last_save_time = time.time()
                persistence_comp.mark_clean()
                
                # Track performance
                save_time = time.time() - start_time
                self.save_times.append(save_time)
                self.total_saves_performed += 1
                
                # Call save complete callback
                if persistence_comp.on_save_complete:
                    persistence_comp.on_save_complete(scene_id, slot, filepath)
                
                # Cleanup old saves
                persistence_comp.cleanup_old_saves()
                
                print(f"💾 Saved scene: {scene_comp.scene_name} to {filename} ({save_time:.3f}s)")
                return True
            else:
                if persistence_comp.on_save_error:
                    persistence_comp.on_save_error(scene_id, slot, "Write failed")
                return False
        
        except Exception as e:
            print(f"Error saving scene {scene_id}: {e}")
            if persistence_comp.on_save_error:
                persistence_comp.on_save_error(scene_id, slot, str(e))
            return False
    
    def load_scene(self, scene_id: str, slot: int = 0, load_name: Optional[str] = None) -> bool:
        """Load a scene from disk."""
        # Find scene entity
        scene_entities = self.world.get_entities_with_components(SceneComponent)
        scene_entity = None
        scene_comp = None
        
        for entity in scene_entities:
            comp = self.world.get_component(entity.id, SceneComponent)
            if comp and comp.scene_id == scene_id:
                scene_entity = entity
                scene_comp = comp
                break
        
        if not scene_comp:
            print(f"Error: Scene {scene_id} not found")
            return False
        
        # Get persistence component
        persistence_comp = self.world.get_component(scene_entity.id, ScenePersistenceComponent)
        if not persistence_comp:
            print(f"Warning: Scene {scene_id} has no persistence component")
            return False
        
        try:
            start_time = time.time()
            
            # Call load start callback
            if persistence_comp.on_load_start:
                persistence_comp.on_load_start(scene_id, slot)
            
            # Generate filename
            if load_name:
                filename = f"{load_name}.{persistence_comp.save_format}"
            else:
                filename = persistence_comp.get_save_filename(slot)
            
            filepath = persistence_comp.get_save_filepath(filename)
            
            if not os.path.exists(filepath):
                print(f"Error: Save file not found: {filepath}")
                if persistence_comp.on_load_error:
                    persistence_comp.on_load_error(scene_id, slot, "File not found")
                return False
            
            # Load data
            save_data = self._read_save_data(filepath, persistence_comp)
            
            if not save_data:
                if persistence_comp.on_load_error:
                    persistence_comp.on_load_error(scene_id, slot, "Failed to read save data")
                return False
            
            # Validate data
            if persistence_comp.validate_saves and not persistence_comp.validate_save_data(save_data):
                print(f"Error: Invalid save data in {filepath}")
                if persistence_comp.on_load_error:
                    persistence_comp.on_load_error(scene_id, slot, "Invalid save data")
                return False
            
            # Apply loaded data
            success = self._apply_save_data(scene_comp, persistence_comp, save_data)
            
            if success:
                # Track performance
                load_time = time.time() - start_time
                self.load_times.append(load_time)
                self.total_loads_performed += 1
                
                # Call load complete callback
                if persistence_comp.on_load_complete:
                    persistence_comp.on_load_complete(scene_id, slot, filepath)
                
                print(f"📂 Loaded scene: {scene_comp.scene_name} from {filename} ({load_time:.3f}s)")
                return True
            else:
                if persistence_comp.on_load_error:
                    persistence_comp.on_load_error(scene_id, slot, "Failed to apply save data")
                return False
        
        except Exception as e:
            print(f"Error loading scene {scene_id}: {e}")
            if persistence_comp.on_load_error:
                persistence_comp.on_load_error(scene_id, slot, str(e))
            return False
    
    def register_auto_save(self, scene_id: str):
        """Register scene for auto-saving."""
        scene_entities = self.world.get_entities_with_components(SceneComponent)
        
        for entity in scene_entities:
            comp = self.world.get_component(entity.id, SceneComponent)
            if comp and comp.scene_id == scene_id:
                self.auto_save_entities[scene_id] = entity.id
                print(f"🔄 Registered auto-save for scene: {comp.scene_name}")
                return True
        
        return False
    
    def unregister_auto_save(self, scene_id: str):
        """Unregister scene from auto-saving."""
        if scene_id in self.auto_save_entities:
            del self.auto_save_entities[scene_id]
            print(f"❌ Unregistered auto-save for scene: {scene_id}")
    
    def get_save_files(self, scene_prefix: str = "") -> List[Dict[str, Any]]:
        """Get list of available save files."""
        save_files = []
        
        if not os.path.exists(self.global_save_directory):
            return save_files
        
        for filename in os.listdir(self.global_save_directory):
            if scene_prefix and not filename.startswith(scene_prefix):
                continue
            
            filepath = os.path.join(self.global_save_directory, filename)
            if os.path.isfile(filepath):
                stat = os.stat(filepath)
                save_files.append({
                    'filename': filename,
                    'filepath': filepath,
                    'size_bytes': stat.st_size,
                    'modified_time': stat.st_mtime,
                    'created_time': stat.st_ctime
                })
        
        # Sort by modification time (newest first)
        save_files.sort(key=lambda x: x['modified_time'], reverse=True)
        return save_files
    
    def delete_save_file(self, filename: str) -> bool:
        """Delete a save file."""
        filepath = os.path.join(self.global_save_directory, filename)
        
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                print(f"🗑️ Deleted save file: {filename}")
                return True
            else:
                print(f"Warning: Save file not found: {filename}")
                return False
        except Exception as e:
            print(f"Error deleting save file {filename}: {e}")
            return False
    
    def _check_auto_saves(self, current_time: float):
        """Check if any scenes need auto-saving."""
        for scene_id, entity_id in self.auto_save_entities.items():
            persistence_comp = self.world.get_component(entity_id, ScenePersistenceComponent)
            
            if persistence_comp and persistence_comp.should_auto_save(current_time):
                # Queue auto-save operation
                self.save_operations.append({
                    'type': 'auto_save',
                    'scene_id': scene_id,
                    'slot': 0,
                    'timestamp': current_time
                })
    
    def _process_save_operations(self):
        """Process queued save operations."""
        completed_operations = []
        
        for i, operation in enumerate(self.save_operations):
            if operation['type'] == 'auto_save':
                success = self.save_scene(operation['scene_id'], operation['slot'])
                if success:
                    completed_operations.append(i)
        
        # Remove completed operations
        for i in reversed(completed_operations):
            del self.save_operations[i]
    
    def _process_load_operations(self):
        """Process queued load operations."""
        completed_operations = []
        
        for i, operation in enumerate(self.load_operations):
            if operation['type'] == 'load':
                success = self.load_scene(operation['scene_id'], operation['slot'])
                if success:
                    completed_operations.append(i)
        
        # Remove completed operations
        for i in reversed(completed_operations):
            del self.load_operations[i]
    
    def _collect_scene_data(self, scene_comp: SceneComponent, persistence_comp: ScenePersistenceComponent) -> Dict[str, Any]:
        """Collect all data for scene saving."""
        # Start with base save data
        save_data = persistence_comp.create_save_data()
        
        # Add scene-specific data
        save_data['scene_info'] = {
            'scene_name': scene_comp.scene_name,
            'scene_id': scene_comp.scene_id,
            'entity_count': len(scene_comp.entities),
            'priority': scene_comp.priority,
            'is_persistent': scene_comp.is_persistent,
            'is_overlay': scene_comp.is_overlay
        }
        
        # Collect entity component data
        entity_data = {}
        for entity_id in scene_comp.entities:
            if self._should_persist_entity(entity_id, persistence_comp):
                components = self._collect_entity_components(entity_id, persistence_comp)
                if components:
                    entity_data[str(entity_id)] = components
        
        save_data['entities'] = entity_data
        
        return save_data
    
    def _should_persist_entity(self, entity_id: uuid.UUID, persistence_comp: ScenePersistenceComponent) -> bool:
        """Check if entity should be persisted."""
        # For now, persist all entities in scene
        # Could be enhanced with entity tag checking
        return True
    
    def _collect_entity_components(self, entity_id: uuid.UUID, persistence_comp: ScenePersistenceComponent) -> Dict[str, Any]:
        """Collect component data for an entity."""
        entity_components = {}
        
        # Get all components for entity
        if entity_id in self.world.components:
            for component_type, component in self.world.components[entity_id].items():
                component_type_name = component_type.__name__
                
                if persistence_comp.should_persist_component(component_type_name):
                    # Serialize component data
                    component_data = self._serialize_component(component)
                    if component_data:
                        entity_components[component_type_name] = component_data
        
        return entity_components
    
    def _serialize_component(self, component) -> Optional[Dict[str, Any]]:
        """Serialize a component to dictionary."""
        try:
            # Simple serialization - could be enhanced
            component_data = {}
            
            for attr_name in dir(component):
                if not attr_name.startswith('_'):
                    attr_value = getattr(component, attr_name)
                    
                    # Only serialize basic types for now
                    if isinstance(attr_value, (str, int, float, bool, list, dict)):
                        component_data[attr_name] = attr_value
            
            return component_data
        
        except Exception as e:
            print(f"Error serializing component: {e}")
            return None
    
    def _write_save_data(self, filepath: str, save_data: Dict[str, Any], persistence_comp: ScenePersistenceComponent) -> bool:
        """Write save data to file."""
        try:
            temp_filepath = filepath + ".tmp"
            
            if persistence_comp.save_format == "json":
                with open(temp_filepath, 'w') as f:
                    json.dump(save_data, f, indent=2, default=str)
            elif persistence_comp.save_format == "pickle":
                with open(temp_filepath, 'wb') as f:
                    pickle.dump(save_data, f)
            else:
                print(f"Unsupported save format: {persistence_comp.save_format}")
                return False
            
            # Atomic move
            os.rename(temp_filepath, filepath)
            return True
        
        except Exception as e:
            print(f"Error writing save data: {e}")
            # Clean up temp file
            if os.path.exists(temp_filepath):
                os.remove(temp_filepath)
            return False
    
    def _read_save_data(self, filepath: str, persistence_comp: ScenePersistenceComponent) -> Optional[Dict[str, Any]]:
        """Read save data from file."""
        try:
            if persistence_comp.save_format == "json":
                with open(filepath, 'r') as f:
                    return json.load(f)
            elif persistence_comp.save_format == "pickle":
                with open(filepath, 'rb') as f:
                    return pickle.load(f)
            else:
                print(f"Unsupported save format: {persistence_comp.save_format}")
                return None
        
        except Exception as e:
            print(f"Error reading save data: {e}")
            return None
    
    def _apply_save_data(self, scene_comp: SceneComponent, persistence_comp: ScenePersistenceComponent, save_data: Dict[str, Any]) -> bool:
        """Apply loaded save data to scene."""
        try:
            # Apply persistent data
            if 'persistent_data' in save_data:
                persistence_comp.persistent_data = save_data['persistent_data']
            
            # Apply entity states
            if 'entity_states' in save_data:
                persistence_comp.entity_states = save_data['entity_states']
            
            # Apply scene metadata
            if 'scene_metadata' in save_data:
                persistence_comp.scene_metadata = save_data['scene_metadata']
            
            return True
        
        except Exception as e:
            print(f"Error applying save data: {e}")
            return False
    
    def _create_backup(self, filepath: str):
        """Create backup of existing save file."""
        try:
            backup_filename = os.path.basename(filepath) + ".backup"
            backup_filepath = os.path.join(self.backup_directory, backup_filename)
            
            import shutil
            shutil.copy2(filepath, backup_filepath)
        
        except Exception as e:
            print(f"Warning: Failed to create backup: {e}")
    
    def get_persistence_stats(self) -> Dict[str, Any]:
        """Get persistence system statistics."""
        avg_save_time = sum(self.save_times) / len(self.save_times) if self.save_times else 0.0
        avg_load_time = sum(self.load_times) / len(self.load_times) if self.load_times else 0.0
        
        save_files = self.get_save_files()
        total_save_size = sum(f['size_bytes'] for f in save_files)
        
        return {
            'auto_save_scenes': len(self.auto_save_entities),
            'save_operations_queued': len(self.save_operations),
            'load_operations_queued': len(self.load_operations),
            'total_saves_performed': self.total_saves_performed,
            'total_loads_performed': self.total_loads_performed,
            'avg_save_time_seconds': avg_save_time,
            'avg_load_time_seconds': avg_load_time,
            'total_save_files': len(save_files),
            'total_save_size_bytes': total_save_size,
            'save_directory': self.global_save_directory
        }
