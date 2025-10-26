import time
from typing import Dict, List, Optional, Set, Callable, Any, TYPE_CHECKING
from collections import deque
from dataclasses import dataclass

from engine.core.system import System
from engine.assets.typesg.asset_types import StreamingPriority

if TYPE_CHECKING:
    from .resource_manager import ResourceManager, AssetInfo, AssetState


@dataclass
class StreamingRequest:
    """Request for asset streaming."""
    asset_path: str
    priority: StreamingPriority
    distance: float = 0.0  # Distance from player/camera
    required_by: float = 0.0  # Time when asset is needed
    callback: Optional[Callable] = None
    
class AssetStreamingSystem(System):
    """
    System for dynamic asset loading and unloading based on proximity and need.
    
    Features:
    - Distance-based asset streaming
    - Priority-based loading queues
    - Predictive asset loading
    - Memory pressure management
    - Level-of-detail (LOD) asset management
    """
    
    def __init__(self, world, resource_manager: Any):
        super().__init__(world)
        self.resource_manager = resource_manager
        
        # Streaming configuration
        self.streaming_enabled = True
        self.max_concurrent_loads = 3
        self.stream_distance = 200.0  # Units
        self.unload_distance = 400.0  # Units
        self.prediction_time = 2.0  # Seconds ahead to predict
        
        # Streaming queues by priority
        self.streaming_queues: Dict[StreamingPriority, deque] = {
            priority: deque() for priority in StreamingPriority
        }
        
        # Current streaming operations
        self.active_streams: Dict[str, StreamingRequest] = {}
        self.stream_positions: Dict[str, tuple] = {}  # asset_path -> (x, y)
        
        # Player/camera tracking
        self.player_position = (0.0, 0.0)
        self.player_velocity = (0.0, 0.0)
        self.camera_position = (0.0, 0.0)
        self.camera_bounds = (-100, -100, 100, 100)  # left, bottom, right, top
        
        # Performance tracking
        self.streams_completed = 0
        self.streams_failed = 0
        self.total_stream_time = 0.0
        self.memory_pressure = 0.0  # 0.0 to 1.0
        
        # Asset zones and regions
        self.asset_zones: Dict[str, Set[str]] = {}  # zone_name -> asset_paths
        self.active_zones: Set[str] = set()
        
        # Threading for background operations
        self.streaming_thread = None
        self.thread_running = False
    
    def update(self, dt: float):
        """Update streaming system."""
        if not self.streaming_enabled:
            return
        
        # Update memory pressure
        self._update_memory_pressure()
        
        # Process streaming requests
        self._process_streaming_queues()
        
        # Check distance-based streaming
        self._update_distance_streaming()
        
        # Predictive streaming
        self._update_predictive_streaming()
        
        # Zone-based streaming
        self._update_zone_streaming()
        
        # Clean up completed streams
        self._cleanup_completed_streams()
    
    def register_asset_position(self, asset_path: str, x: float, y: float):
        """Register the world position of an asset for distance-based streaming."""
        self.stream_positions[asset_path] = (x, y)
    
    def register_asset_zone(self, zone_name: str, asset_paths: List[str]):
        """Register a zone with associated assets."""
        if zone_name not in self.asset_zones:
            self.asset_zones[zone_name] = set()
        
        self.asset_zones[zone_name].update(asset_paths)
        
        # Register positions for zone assets if not already registered
        for asset_path in asset_paths:
            if asset_path not in self.stream_positions:
                # Default to zone center (can be overridden)
                self.stream_positions[asset_path] = (0.0, 0.0)
    
    def activate_zone(self, zone_name: str):
        """Activate streaming for a specific zone."""
        if zone_name in self.asset_zones:
            self.active_zones.add(zone_name)
            
            # Queue assets in this zone for loading
            for asset_path in self.asset_zones[zone_name]:
                self.request_stream(asset_path, StreamingPriority.NORMAL)
            
            print(f"📍 Activated streaming zone: {zone_name}")
    
    def deactivate_zone(self, zone_name: str):
        """Deactivate streaming for a specific zone."""
        if zone_name in self.active_zones:
            self.active_zones.remove(zone_name)
            
            # Queue assets in this zone for unloading
            for asset_path in self.asset_zones[zone_name]:
                self.request_unload(asset_path)
            
            print(f"📍 Deactivated streaming zone: {zone_name}")
    
    def update_player_position(self, x: float, y: float, vx: float = 0.0, vy: float = 0.0):
        """Update player position and velocity for streaming calculations."""
        self.player_position = (x, y)
        self.player_velocity = (vx, vy)
    
    def update_camera_bounds(self, left: float, bottom: float, right: float, top: float):
        """Update camera viewing bounds for streaming calculations."""
        self.camera_bounds = (left, bottom, right, top)
        self.camera_position = ((left + right) / 2, (bottom + top) / 2)
    
    def request_stream(self, asset_path: str, priority: StreamingPriority = StreamingPriority.NORMAL,
                      distance: float = 0.0, required_by: float = 0.0,
                      callback: Optional[Callable] = None):
        """Request an asset to be streamed in."""
        # Check if already loaded or being loaded
        if self.resource_manager.is_loaded(asset_path):
            if callback:
                callback(asset_path, True)
            return
        
        if asset_path in self.active_streams:
            # Update priority if higher
            existing_request = self.active_streams[asset_path]
            if priority.value > existing_request.priority.value:
                existing_request.priority = priority
            return
        
        # Create streaming request
        request = StreamingRequest(
            asset_path=asset_path,
            priority=priority,
            distance=distance,
            required_by=required_by or (time.time() + 10.0),  # Default 10 seconds
            callback=callback
        )
        
        # Add to appropriate queue
        self.streaming_queues[priority].append(request)
        self.active_streams[asset_path] = request
    
    def request_unload(self, asset_path: str):
        """Request an asset to be unloaded."""
        # Remove from active streams if pending
        if asset_path in self.active_streams:
            del self.active_streams[asset_path]
        
        # Remove from all queues
        for queue in self.streaming_queues.values():
            queue = deque([req for req in queue if req.asset_path != asset_path])
        
        # Unload from resource manager
        self.resource_manager.unload_asset(asset_path)
    
    def preload_for_level(self, level_assets: List[str], priority: StreamingPriority = StreamingPriority.HIGH):
        """Preload assets for an upcoming level."""
        print(f"📦 Preloading {len(level_assets)} assets for level")
        
        for asset_path in level_assets:
            self.request_stream(asset_path, priority, required_by=time.time() + 1.0)
    
    def get_streaming_statistics(self) -> Dict[str, Any]:
        """Get streaming system statistics."""
        total_queued = sum(len(queue) for queue in self.streaming_queues.values())
        
        return {
            'streaming_enabled': self.streaming_enabled,
            'active_streams': len(self.active_streams),
            'total_queued': total_queued,
            'queues': {priority.name: len(queue) for priority, queue in self.streaming_queues.items()},
            'streams_completed': self.streams_completed,
            'streams_failed': self.streams_failed,
            'avg_stream_time': (self.total_stream_time / max(1, self.streams_completed)),
            'memory_pressure': self.memory_pressure,
            'active_zones': len(self.active_zones),
            'registered_positions': len(self.stream_positions)
        }
    
    def enable_streaming(self, enabled: bool = True):
        """Enable or disable asset streaming."""
        self.streaming_enabled = enabled
        
        if enabled:
            print("🌊 Asset streaming enabled")
        else:
            print("🛑 Asset streaming disabled")
    
    def set_streaming_distances(self, stream_distance: float, unload_distance: float):
        """Set distances for streaming and unloading assets."""
        self.stream_distance = stream_distance
        self.unload_distance = unload_distance
        
        print(f"📏 Updated streaming distances: {stream_distance:.1f} / {unload_distance:.1f}")
    
    def _update_memory_pressure(self):
        """Update memory pressure based on resource manager stats."""
        memory_stats = self.resource_manager.get_memory_usage()
        self.memory_pressure = memory_stats['utilization_percent'] / 100.0
        
        # Adjust streaming behavior based on pressure
        if self.memory_pressure > 0.8:
            # High memory pressure - be more aggressive about unloading
            self.max_concurrent_loads = 1
            self._emergency_unload()
        elif self.memory_pressure > 0.6:
            # Medium memory pressure - reduce concurrent loads
            self.max_concurrent_loads = 2
        else:
            # Low memory pressure - normal operation
            self.max_concurrent_loads = 3
    
    def _process_streaming_queues(self):
        """Process streaming requests by priority."""
        active_loads = len([req for req in self.active_streams.values() 
                           if self.resource_manager.get_asset_info(req.asset_path) and 
                           self.resource_manager.get_asset_info(req.asset_path).state == "loading"])
        
        if active_loads >= self.max_concurrent_loads:
            return
        
        # Process highest priority queues first
        for priority in reversed(list(StreamingPriority)):
            queue = self.streaming_queues[priority]
            
            while queue and active_loads < self.max_concurrent_loads:
                request = queue.popleft()
                
                # Check if still needed
                if request.required_by < time.time():
                    # Request expired
                    if request.asset_path in self.active_streams:
                        del self.active_streams[request.asset_path]
                    continue
                
                # Start loading
                start_time = time.time()
                success = self._start_asset_load(request)
                
                if success:
                    active_loads += 1
                    load_time = time.time() - start_time
                    self.total_stream_time += load_time
                    self.streams_completed += 1
                else:
                    self.streams_failed += 1
                    if request.asset_path in self.active_streams:
                        del self.active_streams[request.asset_path]
    
    def _start_asset_load(self, request: StreamingRequest) -> bool:
        """Start loading an asset."""
        def load_callback(path: str, data: Any):
            if request.callback:
                request.callback(path, data is not None)
        
        return self.resource_manager.load_asset_async(request.asset_path, load_callback)
    
    def _update_distance_streaming(self):
        """Update streaming based on distance from player."""
        player_x, player_y = self.player_position
        
        for asset_path, (asset_x, asset_y) in self.stream_positions.items():
            distance = ((asset_x - player_x) ** 2 + (asset_y - player_y) ** 2) ** 0.5
            
            if distance <= self.stream_distance:
                # Within streaming distance - load if not already loaded/loading
                if not self.resource_manager.is_loaded(asset_path) and asset_path not in self.active_streams:
                    priority = StreamingPriority.HIGH if distance <= self.stream_distance * 0.5 else StreamingPriority.NORMAL
                    self.request_stream(asset_path, priority, distance=distance)
            
            elif distance >= self.unload_distance:
                # Outside unload distance - unload if loaded
                if self.resource_manager.is_loaded(asset_path):
                    self.request_unload(asset_path)
    
    def _update_predictive_streaming(self):
        """Predictively stream assets based on player movement."""
        if self.player_velocity == (0.0, 0.0):
            return
        
        # Predict future player position
        vx, vy = self.player_velocity
        future_x = self.player_position[0] + vx * self.prediction_time
        future_y = self.player_position[1] + vy * self.prediction_time
        
        # Check assets near predicted position
        for asset_path, (asset_x, asset_y) in self.stream_positions.items():
            distance = ((asset_x - future_x) ** 2 + (asset_y - future_y) ** 2) ** 0.5
            
            if distance <= self.stream_distance * 1.2:  # Slightly larger radius for prediction
                if not self.resource_manager.is_loaded(asset_path) and asset_path not in self.active_streams:
                    self.request_stream(asset_path, StreamingPriority.LOW, distance=distance,
                                      required_by=time.time() + self.prediction_time)
    
    def _update_zone_streaming(self):
        """Update streaming for active zones."""
        # This is handled by activate_zone/deactivate_zone methods
        # Could be extended with dynamic zone activation based on player position
        pass
    
    def _cleanup_completed_streams(self):
        """Clean up completed streaming requests."""
        completed = []
        
        for asset_path, request in self.active_streams.items():
            asset_info = self.resource_manager.get_asset_info(asset_path)
            
            if asset_info and asset_info.state in ["loaded", "error"]:
                completed.append(asset_path)
        
        for asset_path in completed:
            del self.active_streams[asset_path]
    
    def _emergency_unload(self):
        """Emergency unloading when memory pressure is high."""
        # Find least recently used assets to unload
        asset_infos = []
        
        for path, info in self.resource_manager.assets.items():
            if self.resource_manager.is_loaded(path) and info.ref_count == 0:
                asset_infos.append((path, info.last_access))
        
        # Sort by last access (oldest first)
        asset_infos.sort(key=lambda x: x[1])
        
        # Unload up to 25% of loaded assets
        unload_count = max(1, len(asset_infos) // 4)
        
        for i in range(min(unload_count, len(asset_infos))):
            asset_path = asset_infos[i][0]
            self.resource_manager.unload_asset(asset_path)
            print(f"🚨 Emergency unloaded: {asset_path}")
