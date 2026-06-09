from .animation import Tween, TweenManager, MovementTweenComponent, EasingType, EasingFunctions
from .assets import ResourceManager, AssetStreamingSystem, AssetInfo, StreamingRequest, TextureAtlas, AtlasRegion, AssetType, AssetState, TexturePackingStrategy, StreamingPriority
from .audio import AudioSystem, SoundComponent, MusicComponent, AudioListenerComponent, AudioManager, MusicSystem, MusicState, MusicTransition, SoundType

from .core.system import World, System
from .core.events import EventManager, Event, EntityCreatedEvent, EntityDestroyedEvent, ComponentAddedEvent, ComponentRemovedEvent
from .core.entity import Entity
from .core.component import Component

from .dev_tools import HotReloadManager, AssetHotSwapManager, ComponentInspector
from .graphics import TransformComponent, SpriteComponent, RenderSystem, SpriteSheet
from .input import InputSystem, InputComponent, InputBinding

from .physics import CollisionSystem, PandaCollisionSystem, ColliderComponent, RigidBodyComponent, PandaCollisionNode, ColliderType, CollisionEvent, TriggerEnterEvent, TriggerExitEvent
from .scene import SceneState, SceneManager, TransitionType, SceneComponent, ScenePersistenceComponent, SceneTransitionComponent, SceneTransitionSystem, ScenePersistenceSystem

from .game_object import GameObject

__all__ = [
    # Types and States
    'EasingType',
    'AssetType', 'AssetState', 'TexturePackingStrategy', 'StreamingPriority', # Assets
    'MusicState', 'SoundType', # Audio
    'ColliderType', # Physics
    'SceneState', 'TransitionType', # Scene
    
    # Base Classes
    'Tween',
    'AssetInfo', 'StreamingRequest', 'TextureAtlas', 'AtlasRegion', # Assets
    'World', 'Entity', 'System', 'Event', 'Component', # CORE
    'GameObject', # Game Objects
    
    # Events
    'EntityCreatedEvent', 'EntityDestroyedEvent', 'ComponentAddedEvent', 'ComponentRemovedEvent', # CORE
    'CollisionEvent', 'TriggerEnterEvent', 'TriggerExitEvent', # Physics
    
    # Components
    'MovementTweenComponent', # Animation
    'SoundComponent', 'MusicComponent', 'AudioListenerComponent', # Audio
    'TransformComponent', 'SpriteComponent', # Graphics
    'InputComponent', # Input
    'ColliderComponent', 'RigidBodyComponent', 'PandaCollisionNode', # Physics
    'SceneComponent', 'SceneTransitionComponent', 'ScenePersistenceComponent', # Scene
    
    # Libraries and Functions
    'EasingFunctions', # Animation
    
    # Managers and Systems
    'RenderSystem', 'InputSystem',
    'TweenManager', # Animation
    'ResourceManager', 'AssetStreamingSystem', # Assets
    'AudioManager', 'AudioSystem', 'MusicSystem', # Audio
    'EventManager', # CORE
    'CollisionSystem', 'PandaCollisionSystem', # Physics
    'SceneManager', 'SceneTransitionSystem', 'ScenePersistenceSystem', # Scene
    
    # Miscellaneous
    'MusicTransition', # Audio
    'HotReloadManager', 'AssetHotSwapManager', 'ComponentInspector', # Dev Tools
    'SpriteSheet', # Graphics
    'InputBinding', # Input
    '__version__',
]

# Engine version for cartridge manifest "requires.engine" checks (P1-F).
# Primary runtime source: importlib.metadata.version("py2d-game-engine")
# (falls back to this value for editable/dev installs without metadata).
__version__ = "0.1.0"