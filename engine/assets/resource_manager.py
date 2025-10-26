import os
import json
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable, Set

from engine.core.system import System
from engine.assets.typesg.asset_types import AssetType, AssetState

@dataclass
class AssetInfo:
    """Information about an asset."""
    path: str
    asset_type: AssetType
    state: AssetState
    data: Optional[Any] = None
    size_bytes: int = 0
    load_time: float = 0.0
    last_access: float = 0.0
    ref_count: int = 0
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

class ResourceManager(System):
    """
    Centralized resource management system for the 2D Game Engine.
    
    Features:
    - Centralized asset loading and caching
    - Automatic asset type detection
    - Reference counting and memory management
    - Asset streaming and preloading
    - Asset validation and integrity checking
    - Hot reload support for development
    - Asset dependency tracking
    """
    
    def __init__(self, world, base):
        super().__init__(world)
        self.base = base
        self.loader = base.loader
        
        # Asset storage
        self.assets: Dict[str, AssetInfo] = {}  # path -> AssetInfo
        self.asset_cache: Dict[str, Any] = {}  # path -> loaded data
        self.loading_queue: List[str] = []  # Assets queued for loading
        
        # Asset groups and collections
        self.asset_groups: Dict[str, Set[str]] = {}  # group_name -> asset_paths
        self.asset_tags: Dict[str, Set[str]] = {}  # tag -> asset_paths
        
        # Configuration
        self.asset_root = "assets"
        self.cache_size_limit = 100 * 1024 * 1024  # 100MB default
        self.auto_unload_unused = True
        self.preload_common_assets = True
        
        # Performance tracking
        self.total_memory_usage = 0
        self.assets_loaded = 0
        self.assets_failed = 0
        self.load_times: List[float] = []
        
        # Hot reload support
        self.hot_reload_enabled = False
        self.file_watchers: Dict[str, float] = {}  # path -> last_modified
        
        # Asset type mappings
        self.asset_type_extensions = {
            AssetType.TEXTURE: {'.png', '.jpg', '.jpeg', '.bmp', '.tga', '.dds'},
            AssetType.AUDIO: {'.wav', '.ogg', '.mp3', '.flac'},
            AssetType.DATA: {'.json', '.xml', '.txt', '.yaml', '.yml'},
            AssetType.FONT: {'.ttf', '.otf', '.fnt'},
            AssetType.SPRITE_SHEET: {'.png', '.jpg'},  # Special handling needed
            AssetType.SHADER: {'.glsl', '.vert', '.frag', '.geom'},
            AssetType.MODEL: {'.egg', '.bam', '.obj', '.gltf', '.fbx'}
        }
        
        # Callbacks
        self.on_asset_loaded: Optional[Callable] = None
        self.on_asset_failed: Optional[Callable] = None
        self.on_cache_full: Optional[Callable] = None
        
        # Initialize common asset groups
        self._setup_default_groups()
        
    def _setup_default_groups(self):
        """Set up default asset groups."""
        self.asset_groups.update({
            'ui': set(),
            'gameplay': set(),
            'audio': set(),
            'level': set(),
            'character': set(),
            'effect': set()
        })
    
    def update(self, dt: float):
        """Update resource manager."""
        # Process loading queue
        self._process_loading_queue()
        
        # Check for hot reload
        if self.hot_reload_enabled:
            self._check_file_changes()
        
        # Clean up unused assets
        if self.auto_unload_unused:
            self._cleanup_unused_assets()
    def register_asset(self, path: str, asset_type: Optional[AssetType] = None,
                      group: Optional[str] = None, tags: Optional[List[str]] = None,
                      metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Register an asset for management."""
        if not os.path.exists(os.path.join(self.asset_root, path)):
            print(f"Warning: Asset not found: {path}")
            return False
        
        # Auto-detect asset type if not provided
        if asset_type is None:
            asset_type = self._detect_asset_type(path)
        
        # Create asset info
        full_path = os.path.join(self.asset_root, path)
        asset_info = AssetInfo(
            path=path,
            asset_type=asset_type,
            state=AssetState.UNLOADED,
            size_bytes=os.path.getsize(full_path),
            metadata=metadata or {}
        )
        
        self.assets[path] = asset_info
        
        # Add to groups and tags
        if group and group in self.asset_groups:
            self.asset_groups[group].add(path)
        
        if tags:
            for tag in tags:
                if tag not in self.asset_tags:
                    self.asset_tags[tag] = set()
                self.asset_tags[tag].add(path)
        
        return True
    
    def load_asset(self, path: str, force_reload: bool = False) -> Optional[Any]:
        """Load an asset synchronously."""
        # Check if already loaded
        if not force_reload and path in self.asset_cache:
            asset_info = self.assets.get(path)
            if asset_info:
                asset_info.last_access = time.time()
                asset_info.ref_count += 1
            return self.asset_cache[path]
        
        # Register asset if not already registered
        if path not in self.assets:
            if not self.register_asset(path):
                return None
        
        asset_info = self.assets[path]
        asset_info.state = AssetState.LOADING
        
        start_time = time.time()
        
        try:
            # Load based on asset type
            loaded_data = self._load_asset_data(path, asset_info.asset_type)
            
            if loaded_data is not None:
                # Store in cache
                self.asset_cache[path] = loaded_data
                asset_info.data = loaded_data
                asset_info.state = AssetState.LOADED
                asset_info.load_time = time.time() - start_time
                asset_info.last_access = time.time()
                asset_info.ref_count += 1
                
                # Update stats
                self.assets_loaded += 1
                self.load_times.append(asset_info.load_time)
                self.total_memory_usage += asset_info.size_bytes
                
                # Callback
                if self.on_asset_loaded:
                    self.on_asset_loaded(path, loaded_data)
                
                print(f"✅ Loaded asset: {path} ({asset_info.load_time:.3f}s)")
                return loaded_data
            else:
                asset_info.state = AssetState.ERROR
                self.assets_failed += 1
                
                if self.on_asset_failed:
                    self.on_asset_failed(path, "Failed to load asset data")
                
                print(f"❌ Failed to load asset: {path}")
                return None
                
        except Exception as e:
            asset_info.state = AssetState.ERROR
            self.assets_failed += 1
            
            if self.on_asset_failed:
                self.on_asset_failed(path, str(e))
            
            print(f"❌ Error loading asset {path}: {e}")
            return None
    
    def load_asset_async(self, path: str, callback: Optional[Callable] = None) -> bool:
        """Queue an asset for asynchronous loading."""
        if path not in self.loading_queue:
            self.loading_queue.append(path)
            
            # Register asset if not already registered
            if path not in self.assets:
                self.register_asset(path)
            
            asset_info = self.assets.get(path)
            if asset_info:
                asset_info.state = AssetState.LOADING
                if callback:
                    asset_info.metadata['load_callback'] = callback
            
            return True
        return False
    
    def unload_asset(self, path: str) -> bool:
        """Unload an asset from memory."""
        if path not in self.asset_cache:
            return False
        
        asset_info = self.assets.get(path)
        if asset_info:
            asset_info.ref_count = max(0, asset_info.ref_count - 1)
            
            # Only unload if no references
            if asset_info.ref_count == 0:
                del self.asset_cache[path]
                asset_info.data = None
                asset_info.state = AssetState.UNLOADED
                self.total_memory_usage -= asset_info.size_bytes
                print(f"🗑️ Unloaded asset: {path}")
                return True
        
        return False
    
    def preload_group(self, group_name: str) -> bool:
        """Preload all assets in a group."""
        if group_name not in self.asset_groups:
            print(f"Warning: Asset group '{group_name}' not found")
            return False
        
        asset_paths = self.asset_groups[group_name]
        
        print(f"📦 Preloading group '{group_name}' ({len(asset_paths)} assets)")
        
        for asset_path in asset_paths:
            self.load_asset_async(asset_path)
        
        return True
    
    def preload_tagged(self, tag: str) -> bool:
        """Preload all assets with a specific tag."""
        if tag not in self.asset_tags:
            print(f"Warning: Asset tag '{tag}' not found")
            return False
        
        asset_paths = self.asset_tags[tag]
        
        print(f"🏷️ Preloading tagged assets '{tag}' ({len(asset_paths)} assets)")
        
        for asset_path in asset_paths:
            self.load_asset_async(asset_path)
        
        return True
    
    def get_asset(self, path: str) -> Optional[Any]:
        """Get a loaded asset from cache."""
        if path in self.asset_cache:
            asset_info = self.assets.get(path)
            if asset_info:
                asset_info.last_access = time.time()
                asset_info.ref_count += 1
            return self.asset_cache[path]
        return None
    
    def is_loaded(self, path: str) -> bool:
        """Check if an asset is loaded."""
        return path in self.asset_cache
    
    def get_asset_info(self, path: str) -> Optional[AssetInfo]:
        """Get asset information."""
        return self.assets.get(path)
    
    def validate_asset(self, path: str) -> bool:
        """Validate an asset file exists and is readable."""
        full_path = os.path.join(self.asset_root, path)
        
        if not os.path.exists(full_path):
            return False
        
        try:
            # Basic file accessibility check
            with open(full_path, 'rb') as f:
                f.read(1)
            return True
        except Exception:
            return False
    
    def validate_all_assets(self) -> Dict[str, bool]:
        """Validate all registered assets."""
        results = {}
        
        for path in self.assets.keys():
            results[path] = self.validate_asset(path)
        
        return results
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """Get memory usage statistics."""
        return {
            'total_bytes': self.total_memory_usage,
            'total_mb': self.total_memory_usage / (1024 * 1024),
            'cache_size_limit_mb': self.cache_size_limit / (1024 * 1024),
            'assets_in_cache': len(self.asset_cache),
            'total_registered': len(self.assets),
            'utilization_percent': (self.total_memory_usage / self.cache_size_limit) * 100
        }
    
    def get_load_statistics(self) -> Dict[str, Any]:
        """Get loading performance statistics."""
        avg_load_time = sum(self.load_times) / len(self.load_times) if self.load_times else 0.0
        
        return {
            'assets_loaded': self.assets_loaded,
            'assets_failed': self.assets_failed,
            'success_rate': (self.assets_loaded / max(1, self.assets_loaded + self.assets_failed)) * 100,
            'avg_load_time': avg_load_time,
            'total_load_time': sum(self.load_times),
            'loading_queue_size': len(self.loading_queue)
        }
    
    def enable_hot_reload(self, enabled: bool = True):
        """Enable or disable hot reload functionality."""
        self.hot_reload_enabled = enabled
        
        if enabled:
            # Initialize file watchers for loaded assets
            for path in self.asset_cache.keys():
                full_path = os.path.join(self.asset_root, path)
                if os.path.exists(full_path):
                    self.file_watchers[path] = os.path.getmtime(full_path)
            
            print("🔥 Hot reload enabled")
        else:
            self.file_watchers.clear()
            print("❄️ Hot reload disabled")
    
    def create_asset_manifest(self, output_path: str = "asset_manifest.json") -> bool:
        """Create a manifest file of all registered assets."""
        manifest_data = {
            'generated': time.time(),
            'asset_root': self.asset_root,
            'total_assets': len(self.assets),
            'groups': {name: list(assets) for name, assets in self.asset_groups.items()},
            'assets': {}
        }
        
        for path, asset_info in self.assets.items():
            manifest_data['assets'][path] = {
                'type': asset_info.asset_type.value,
                'size_bytes': asset_info.size_bytes,
                'state': asset_info.state.value,
                'metadata': asset_info.metadata
            }
        
        try:
            with open(output_path, 'w') as f:
                json.dump(manifest_data, f, indent=2)
            
            print(f"📋 Asset manifest created: {output_path}")
            return True
        except Exception as e:
            print(f"❌ Failed to create manifest: {e}")
            return False
    
    def load_asset_manifest(self, manifest_path: str = "asset_manifest.json") -> bool:
        """Load assets from a manifest file."""
        try:
            with open(manifest_path, 'r') as f:
                manifest_data = json.load(f)
            
            # Register assets from manifest
            for path, asset_data in manifest_data.get('assets', {}).items():
                asset_type = AssetType(asset_data['type'])
                metadata = asset_data.get('metadata', {})
                self.register_asset(path, asset_type, metadata=metadata)
            
            # Restore groups
            for group_name, asset_paths in manifest_data.get('groups', {}).items():
                self.asset_groups[group_name] = set(asset_paths)
            
            print(f"📋 Loaded asset manifest: {manifest_path}")
            return True
        except Exception as e:
            print(f"❌ Failed to load manifest: {e}")
            return False
    
    def _detect_asset_type(self, path: str) -> AssetType:
        """Automatically detect asset type from file extension."""
        ext = os.path.splitext(path)[1].lower()
        
        for asset_type, extensions in self.asset_type_extensions.items():
            if ext in extensions:
                return asset_type
        
        return AssetType.DATA  # Default fallback
    
    def _load_asset_data(self, path: str, asset_type: AssetType) -> Optional[Any]:
        """Load asset data based on type."""
        full_path = os.path.join(self.asset_root, path)
        
        try:
            if asset_type == AssetType.TEXTURE:
                return self.loader.loadTexture(full_path)
            
            elif asset_type == AssetType.AUDIO:
                return self.loader.loadSfx(full_path)
            
            elif asset_type == AssetType.DATA:
                with open(full_path, 'r') as f:
                    if path.endswith('.json'):
                        return json.load(f)
                    else:
                        return f.read()
            
            elif asset_type == AssetType.FONT:
                return self.loader.loadFont(full_path)
            
            elif asset_type == AssetType.MODEL:
                return self.loader.loadModel(full_path)
            
            else:
                # Generic file loading
                with open(full_path, 'rb') as f:
                    return f.read()
                    
        except Exception as e:
            print(f"Error loading {asset_type.value} asset {path}: {e}")
            return None
    
    def _process_loading_queue(self):
        """Process assets in the loading queue."""
        if not self.loading_queue:
            return
        
        # Process one asset per frame to avoid blocking
        asset_path = self.loading_queue.pop(0)
        loaded_data = self.load_asset(asset_path)
        
        # Handle callback if specified
        asset_info = self.assets.get(asset_path)
        if asset_info and 'load_callback' in asset_info.metadata:
            callback = asset_info.metadata['load_callback']
            callback(asset_path, loaded_data)
            del asset_info.metadata['load_callback']
    
    def _check_file_changes(self):
        """Check for file changes for hot reload."""
        for path, last_modified in list(self.file_watchers.items()):
            full_path = os.path.join(self.asset_root, path)
            
            if os.path.exists(full_path):
                current_modified = os.path.getmtime(full_path)
                
                if current_modified > last_modified:
                    print(f"🔄 Hot reloading asset: {path}")
                    self.load_asset(path, force_reload=True)
                    self.file_watchers[path] = current_modified
    
    def _cleanup_unused_assets(self):
        """Clean up unused assets based on LRU and reference counting."""
        if self.total_memory_usage <= self.cache_size_limit:
            return
        
        # Find assets to unload (lowest reference count, oldest access)
        candidates = []
        
        for path, asset_info in self.assets.items():
            if path in self.asset_cache and asset_info.ref_count == 0:
                candidates.append((path, asset_info.last_access))
        
        # Sort by last access time (oldest first)
        candidates.sort(key=lambda x: x[1])
        
        # Unload assets until under limit
        for path, _ in candidates:
            if self.total_memory_usage <= self.cache_size_limit:
                break
            
            self.unload_asset(path)
            print(f"🧹 Auto-unloaded unused asset: {path}")
