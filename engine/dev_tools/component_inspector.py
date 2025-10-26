"""
Component Inspector - Runtime component editing and visualization.

This module provides runtime inspection and editing of ECS components,
allowing developers to tweak component properties while the game is running.
"""

import json
import copy
import time
from typing import Dict, Any, List, Callable, Type
from dataclasses import fields, is_dataclass


class ComponentInspector:
    """
    Provides runtime inspection and editing of ECS components.
    
    Features:
    - List all entities and their components
    - View component properties in real-time
    - Edit component values with validation
    - Undo/redo functionality for changes
    - Save/load component presets
    - Hook into component change events
    """
    
    def __init__(self, world):
        self.world = world
        self.change_history = []
        self.history_index = -1
        self.max_history = 50
        
        # Component change callbacks
        self.change_callbacks: Dict[type, List[Callable]] = {}
        
        # Property validators
        self.validators: Dict[type, Dict[str, Callable]] = {}
        
        # Presets for components
        self.presets: Dict[str, Dict] = {}
        
        print("🔍 Component Inspector initialized")
    
    def list_entities(self) -> List[int]:
        """Get a list of all entity IDs."""
        return list(self.world.entities.keys())
    
    def get_entity_components(self, entity_id: int) -> Dict[str, Any]:
        """Get all components for an entity."""
        if entity_id not in self.world.entities:
            return {}
        
        entity = self.world.entities[entity_id]
        components = {}
        
        for component_type, component in entity.components.items():
            component_name = component_type.__name__
            components[component_name] = component
        
        return components
    
    def get_component_info(self, component: Any) -> Dict[str, Any]:
        """Get detailed information about a component."""
        info = {
            'type': type(component).__name__,
            'module': type(component).__module__,
            'properties': {}
        }
        
        # Handle dataclass components
        if is_dataclass(component):
            for field in fields(component):
                value = getattr(component, field.name)
                info['properties'][field.name] = {
                    'value': value,
                    'type': str(field.type),
                    'editable': True
                }
        else:
            # Handle regular class components
            for attr_name in dir(component):
                if not attr_name.startswith('_'):
                    try:
                        value = getattr(component, attr_name)
                        if not callable(value):
                            info['properties'][attr_name] = {
                                'value': value,
                                'type': type(value).__name__,
                                'editable': True
                            }
                    except Exception:
                        pass
        
        return info
    
    def set_component_property(self, entity_id: int, component_type: Type, 
                             property_name: str, new_value: Any) -> bool:
        """
        Set a property value on a component.
        
        Returns True if successful, False otherwise.
        """
        try:
            if entity_id not in self.world.entities:
                print(f"❌ Entity {entity_id} not found")
                return False
            
            entity = self.world.entities[entity_id]
            
            if component_type not in entity.components:
                print(f"❌ Component {component_type.__name__} not found on entity {entity_id}")
                return False
            
            component = entity.components[component_type]
            
            # Validate the new value if a validator exists
            if self._validate_property(component_type, property_name, new_value):
                old_value = getattr(component, property_name)
                
                # Record change for undo functionality
                self._record_change(entity_id, component_type, property_name, old_value, new_value)
                
                # Apply the change
                setattr(component, property_name, new_value)
                
                # Notify callbacks
                self._notify_component_changed(entity_id, component_type, property_name, old_value, new_value)
                
                print(f"✅ Set {component_type.__name__}.{property_name} = {new_value}")
                return True
            else:
                print(f"❌ Invalid value for {component_type.__name__}.{property_name}: {new_value}")
                return False
                
        except Exception as e:
            print(f"❌ Error setting component property: {e}")
            return False
    
    def get_component_property(self, entity_id: int, component_type: Type, property_name: str) -> Any:
        """Get a property value from a component."""
        try:
            if entity_id not in self.world.entities:
                return None
            
            entity = self.world.entities[entity_id]
            
            if component_type not in entity.components:
                return None
            
            component = entity.components[component_type]
            return getattr(component, property_name, None)
            
        except Exception as e:
            print(f"❌ Error getting component property: {e}")
            return None
    
    def add_component_validator(self, component_type: Type, property_name: str, validator: Callable):
        """Add a validator function for a component property."""
        if component_type not in self.validators:
            self.validators[component_type] = {}
        
        self.validators[component_type][property_name] = validator
        print(f"📋 Added validator for {component_type.__name__}.{property_name}")
    
    def add_change_callback(self, component_type: Type, callback: Callable):
        """Add a callback to be called when a component changes."""
        if component_type not in self.change_callbacks:
            self.change_callbacks[component_type] = []
        
        self.change_callbacks[component_type].append(callback)
        print(f"📞 Added change callback for {component_type.__name__}")
    
    def undo_last_change(self) -> bool:
        """Undo the last component change."""
        if self.history_index < 0 or not self.change_history:
            print("⚠️ No changes to undo")
            return False
        
        change = self.change_history[self.history_index]
        entity_id = change['entity_id']
        component_type = change['component_type']
        property_name = change['property_name']
        old_value = change['old_value']
        
        # Apply the old value
        try:
            entity = self.world.entities[entity_id]
            component = entity.components[component_type]
            setattr(component, property_name, old_value)
            
            self.history_index -= 1
            print(f"↶ Undid change to {component_type.__name__}.{property_name}")
            return True
        except Exception as e:
            print(f"❌ Error undoing change: {e}")
            return False
    
    def redo_last_change(self) -> bool:
        """Redo the last undone change."""
        if self.history_index >= len(self.change_history) - 1:
            print("⚠️ No changes to redo")
            return False
        
        self.history_index += 1
        change = self.change_history[self.history_index]
        entity_id = change['entity_id']
        component_type = change['component_type']
        property_name = change['property_name']
        new_value = change['new_value']
        
        # Apply the new value
        try:
            entity = self.world.entities[entity_id]
            component = entity.components[component_type]
            setattr(component, property_name, new_value)
            
            print(f"↷ Redid change to {component_type.__name__}.{property_name}")
            return True
        except Exception as e:
            print(f"❌ Error redoing change: {e}")
            return False
    
    def save_component_preset(self, entity_id: int, component_type: Type, preset_name: str):
        """Save a component's current state as a preset."""
        try:
            if entity_id not in self.world.entities:
                return False
            
            entity = self.world.entities[entity_id]
            
            if component_type not in entity.components:
                return False
            
            component = entity.components[component_type]
            
            # Create a serializable representation of the component
            preset_data = {
                'component_type': component_type.__name__,
                'properties': {}
            }
            
            if is_dataclass(component):
                for field in fields(component):
                    value = getattr(component, field.name)
                    if self._is_serializable(value):
                        preset_data['properties'][field.name] = value
            else:
                for attr_name in dir(component):
                    if not attr_name.startswith('_'):
                        try:
                            value = getattr(component, attr_name)
                            if not callable(value) and self._is_serializable(value):
                                preset_data['properties'][attr_name] = value
                        except Exception:
                            pass
            
            self.presets[preset_name] = preset_data
            print(f"💾 Saved preset '{preset_name}' for {component_type.__name__}")
            return True
            
        except Exception as e:
            print(f"❌ Error saving preset: {e}")
            return False
    
    def load_component_preset(self, entity_id: int, component_type: Type, preset_name: str) -> bool:
        """Load a preset into a component."""
        try:
            if preset_name not in self.presets:
                print(f"❌ Preset '{preset_name}' not found")
                return False
            
            preset_data = self.presets[preset_name]
            
            if preset_data['component_type'] != component_type.__name__:
                print(f"❌ Preset type mismatch: expected {component_type.__name__}, got {preset_data['component_type']}")
                return False
            
            # Apply each property from the preset
            for property_name, value in preset_data['properties'].items():
                success = self.set_component_property(entity_id, component_type, property_name, value)
                if not success:
                    print(f"⚠️ Failed to set property {property_name} from preset")
            
            print(f"📁 Loaded preset '{preset_name}' into {component_type.__name__}")
            return True
            
        except Exception as e:
            print(f"❌ Error loading preset: {e}")
            return False
    
    def list_presets(self) -> List[str]:
        """List all available presets."""
        return list(self.presets.keys())
    
    def export_presets(self, filename: str):
        """Export all presets to a JSON file."""
        try:
            with open(filename, 'w') as f:
                json.dump(self.presets, f, indent=2)
            print(f"📤 Exported presets to {filename}")
        except Exception as e:
            print(f"❌ Error exporting presets: {e}")
    
    def import_presets(self, filename: str):
        """Import presets from a JSON file."""
        try:
            with open(filename, 'r') as f:
                imported_presets = json.load(f)
            
            self.presets.update(imported_presets)
            print(f"📥 Imported presets from {filename}")
        except Exception as e:
            print(f"❌ Error importing presets: {e}")
    
    def get_change_history(self) -> List[Dict]:
        """Get the change history."""
        return self.change_history[:self.history_index + 1]
    
    def clear_change_history(self):
        """Clear the change history."""
        self.change_history.clear()
        self.history_index = -1
        print("🗑️ Cleared change history")
    
    def _validate_property(self, component_type: Type, property_name: str, value: Any) -> bool:
        """Validate a property value using registered validators."""
        if component_type in self.validators:
            if property_name in self.validators[component_type]:
                validator = self.validators[component_type][property_name]
                try:
                    return validator(value)
                except Exception as e:
                    print(f"❌ Validation error: {e}")
                    return False
        return True
    
    def _record_change(self, entity_id: int, component_type: Type, property_name: str, 
                      old_value: Any, new_value: Any):
        """Record a change for undo functionality."""
        change = {
            'entity_id': entity_id,
            'component_type': component_type,
            'property_name': property_name,
            'old_value': copy.deepcopy(old_value),
            'new_value': copy.deepcopy(new_value),
            'timestamp': time.time()
        }
        
        # Remove any changes after the current index (for redo consistency)
        self.change_history = self.change_history[:self.history_index + 1]
        
        # Add the new change
        self.change_history.append(change)
        self.history_index += 1
        
        # Limit history size
        if len(self.change_history) > self.max_history:
            self.change_history.pop(0)
            self.history_index -= 1
    
    def _notify_component_changed(self, entity_id: int, component_type: Type, 
                                property_name: str, old_value: Any, new_value: Any):
        """Notify registered callbacks of component changes."""
        if component_type in self.change_callbacks:
            for callback in self.change_callbacks[component_type]:
                try:
                    callback(entity_id, component_type, property_name, old_value, new_value)
                except Exception as e:
                    print(f"❌ Error in change callback: {e}")
    
    def _is_serializable(self, value: Any) -> bool:
        """Check if a value can be serialized to JSON."""
        try:
            json.dumps(value)
            return True
        except (TypeError, ValueError):
            return False
