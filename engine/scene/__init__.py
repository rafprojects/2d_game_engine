"""
Scene Management Module for the 2D Game Engine

This module provides comprehensive scene management functionality including:
- Multi-scene support and coordination
- Scene transitions and visual effects
- Scene state persistence and saving
- Dynamic scene loading and unloading
- Asset management per scene

Main Components:
- SceneComponent: Core scene data and state management
- SceneTransitionComponent: Visual transition effects
- ScenePersistenceComponent: Save/load functionality

Main Systems:
- SceneManager: Core scene lifecycle management
- SceneTransitionSystem: Transition effect processing
- ScenePersistenceSystem: Save/load operations
"""

from .components.scene_component import SceneComponent
from .components.scene_transition_component import SceneTransitionComponent
from .components.scene_persistence_component import ScenePersistenceComponent
from .systems.scene_manager import SceneManager
from .systems.scene_transition_system import SceneTransitionSystem
from .systems.scene_persistence_system import ScenePersistenceSystem
from .typeg.scene_types import SceneState
from .typeg.scene_transition_types import TransitionType

__all__ = [
    # States & Types
    'SceneState',
    'TransitionType',
    
    # Components
    'SceneComponent',
    'SceneTransitionComponent', 
    'ScenePersistenceComponent',
    
    # Systems
    'SceneManager',
    'SceneTransitionSystem',
    'ScenePersistenceSystem'
]
