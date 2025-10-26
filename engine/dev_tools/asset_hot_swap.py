"""
Asset Hot Swap Manager - Live asset replacement without restart.

This module provides the ability to replace assets (textures, audio, etc.) at runtime,
allowing artists and designers to see changes immediately without restarting the game.
"""

import os
import time
import hashlib
import threading
from typing import Dict, Callable, Optional, Any, List

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler as WatchdogHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    print("⚠️ Watchdog not available. Asset hot swap will not work.")
    WATCHDOG_AVAILABLE = False
    Observer = None
    WatchdogHandler = None

try:
    from panda3d.core import Loader
    PANDA3D_AVAILABLE = True
except ImportError:
    print("⚠️ Panda3D not available. Asset hot swap will be limited.")
    PANDA3D_AVAILABLE = False
    Loader = None


class AssetChangeHandler:
    """File system event handler that triggers asset reloads."""
    
    def __init__(self, asset_hot_swap_manager):
        if not WATCHDOG_AVAILABLE:
            raise RuntimeError("Watchdog is required for AssetChangeHandler")
        self.asset_hot_swap_manager = asset_hot_swap_manager
        self.last_reload_time = {}
        self.reload_delay = 0.2  # Prevent multiple rapid reloads for assets
    
    def on_modified(self, event):
        if event.is_directory:
            return
            
        # Check if it's a supported asset type
        supported_extensions = {'.png', '.jpg', '.jpeg', '.tga', '.bmp', 
                              '.wav', '.ogg', '.mp3', '.flac'}
        
        file_path = event.src_path
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext not in supported_extensions:
            return
            
        # Debounce rapid file changes
        current_time = time.time()
        if file_path in self.last_reload_time:
            if current_time - self.last_reload_time[file_path] < self.reload_delay:
                return
        
        self.last_reload_time[file_path] = current_time
        
        # Queue the asset reload
        self.asset_hot_swap_manager._queue_asset_reload(file_path)


# Create proper handler class if watchdog is available
if WATCHDOG_AVAILABLE:
    class FileSystemEventHandler(WatchdogHandler):
        """Wrapper to properly inherit from watchdog handler."""
        def __init__(self, asset_hot_swap_manager):
            super().__init__()
            self.asset_hot_swap_manager = asset_hot_swap_manager
            self.last_reload_time = {}
            self.reload_delay = 0.2
        
        def on_modified(self, event):
            if event.is_directory:
                return
                
            # Check if it's a supported asset type
            supported_extensions = {'.png', '.jpg', '.jpeg', '.tga', '.bmp', 
                                  '.wav', '.ogg', '.mp3', '.flac'}
            
            file_path = event.src_path
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext not in supported_extensions:
                return
                
            # Debounce rapid file changes
            current_time = time.time()
            if file_path in self.last_reload_time:
                if current_time - self.last_reload_time[file_path] < self.reload_delay:
                    return
            
            self.last_reload_time[file_path] = current_time
            
            # Queue the asset reload
            self.asset_hot_swap_manager._queue_asset_reload(file_path)


class AssetHotSwapManager:
    """
    Manages hot swapping of game assets during development.
    
    Features:
    - Watch filesystem for asset file changes
    - Reload textures, audio files, and other assets
    - Update all references to the asset automatically
    - Preserve asset state and properties where possible
    - Handle asset reload errors gracefully
    - Notify systems of asset changes
    """
    
    def __init__(self, world, showbase_instance=None, watch_directories: Optional[List[str]] = None):
        self.world = world
        self.showbase = showbase_instance  # Don't create default ShowBase instance
        self.watch_directories = watch_directories or []
        self.observer = None
        self.is_watching = False
        
        # Track loaded assets and their references
        self.tracked_assets: Dict[str, Dict] = {}
        self.asset_references: Dict[str, List] = {}
        self.reload_queue = []
        self.reload_lock = threading.Lock()
        
        # Asset reload callbacks
        self.asset_callbacks: Dict[str, List[Callable]] = {}
        
        # Create loaders for different asset types
        if PANDA3D_AVAILABLE and Loader:
            self.loader = Loader.getGlobalPtr()
        else:
            self.loader = None
        
        print("🔥 Asset Hot Swap Manager initialized")
    
    def add_watch_directory(self, directory: str):
        """Add a directory to watch for asset changes."""
        abs_path = os.path.abspath(directory)
        if abs_path not in self.watch_directories:
            self.watch_directories.append(abs_path)
            print(f"📁 Added asset watch directory: {abs_path}")
    
    def track_asset(self, asset_path: str, asset_object: Any, asset_type: str = "texture"):
        """
        Track an asset for hot swapping.
        
        Args:
            asset_path: Path to the asset file
            asset_object: The loaded asset object (Texture, AudioSound, etc.)
            asset_type: Type of asset ('texture', 'audio', 'model', etc.)
        """
        abs_path = os.path.abspath(asset_path)
        
        # Calculate file hash for change detection
        file_hash = self._calculate_file_hash(abs_path)
        
        self.tracked_assets[abs_path] = {
            'object': asset_object,
            'type': asset_type,
            'hash': file_hash,
            'references': []
        }
        
        print(f"📝 Tracking asset: {asset_path} ({asset_type})")
    
    def add_asset_reference(self, asset_path: str, reference_object: Any, 
                          update_callback: Optional[Callable] = None):
        """
        Add a reference to an asset that should be updated when the asset changes.
        
        Args:
            asset_path: Path to the asset file
            reference_object: Object that uses this asset
            update_callback: Function to call to update the reference
        """
        abs_path = os.path.abspath(asset_path)
        
        if abs_path not in self.tracked_assets:
            print(f"⚠️ Asset not tracked: {asset_path}")
            return
        
        reference_info = {
            'object': reference_object,
            'callback': update_callback
        }
        
        self.tracked_assets[abs_path]['references'].append(reference_info)
        print(f"🔗 Added reference for asset: {asset_path}")
    
    def register_asset_callback(self, asset_path: str, callback: Callable):
        """Register a callback to be called when an asset is reloaded."""
        abs_path = os.path.abspath(asset_path)
        
        if abs_path not in self.asset_callbacks:
            self.asset_callbacks[abs_path] = []
        
        self.asset_callbacks[abs_path].append(callback)
        print(f"📞 Registered callback for asset: {asset_path}")
    
    def start_watching(self):
        """Start watching for asset file changes."""
        if self.is_watching:
            return
            
        if not WATCHDOG_AVAILABLE:
            print("❌ Watchdog not available, cannot start asset watching")
            return
            
        if not self.watch_directories:
            print("⚠️ No watch directories specified for asset hot swap")
            return
        
        self.observer = Observer()
        event_handler = AssetChangeHandler(self)
        
        for directory in self.watch_directories:
            if os.path.exists(directory):
                self.observer.schedule(event_handler, directory, recursive=True)
                print(f"👀 Watching assets in: {directory}")
            else:
                print(f"⚠️ Asset watch directory does not exist: {directory}")
        
        self.observer.start()
        self.is_watching = True
        print("🔥 Asset hot swap watching started")
    
    def stop_watching(self):
        """Stop watching for asset file changes."""
        if self.observer and self.is_watching:
            self.observer.stop()
            self.observer.join()
            self.is_watching = False
            print("⏹️ Asset hot swap watching stopped")
    
    def _queue_asset_reload(self, file_path: str):
        """Queue an asset for reloading (thread-safe)."""
        with self.reload_lock:
            if file_path not in self.reload_queue:
                self.reload_queue.append(file_path)
    
    def process_reload_queue(self):
        """Process any queued asset reloads. Call this from the main thread."""
        if not self.reload_queue:
            return
            
        with self.reload_lock:
            files_to_reload = self.reload_queue.copy()
            self.reload_queue.clear()
        
        for file_path in files_to_reload:
            self._handle_asset_changed(file_path)
    
    def _handle_asset_changed(self, file_path: str):
        """Handle an asset file change."""
        try:
            abs_path = os.path.abspath(file_path)
            
            if abs_path not in self.tracked_assets:
                print(f"🤷 Asset not tracked, skipping: {file_path}")
                return
            
            # Check if file actually changed (hash comparison)
            new_hash = self._calculate_file_hash(abs_path)
            old_hash = self.tracked_assets[abs_path]['hash']
            
            if new_hash == old_hash:
                return  # No actual change
            
            print(f"🔄 Asset changed: {file_path}")
            
            # Reload the asset based on its type
            asset_info = self.tracked_assets[abs_path]
            asset_type = asset_info['type']
            
            if asset_type == 'texture':
                self._reload_texture(abs_path)
            elif asset_type == 'audio':
                self._reload_audio(abs_path)
            elif asset_type == 'model':
                self._reload_model(abs_path)
            else:
                print(f"⚠️ Unsupported asset type: {asset_type}")
                
        except Exception as e:
            print(f"❌ Error handling asset change for {file_path}: {e}")
    
    def _reload_texture(self, asset_path: str):
        """Reload a texture asset."""
        try:
            asset_info = self.tracked_assets[asset_path]
            old_texture = asset_info['object']
            
            # Load the new texture
            print(f"🖼️ Reloading texture: {asset_path}")
            new_texture = self.loader.loadTexture(asset_path)
            
            if not new_texture:
                print(f"❌ Failed to load new texture: {asset_path}")
                return
            
            # Copy important properties from old texture if they were set
            if old_texture:
                # Preserve filtering, wrapping, etc.
                new_texture.setMinfilter(old_texture.getMinfilter())
                new_texture.setMagfilter(old_texture.getMagfilter())
                new_texture.setWrapU(old_texture.getWrapU())
                new_texture.setWrapV(old_texture.getWrapV())
            
            # Update the tracked asset
            asset_info['object'] = new_texture
            asset_info['hash'] = self._calculate_file_hash(asset_path)
            
            # Update all references
            for ref_info in asset_info['references']:
                if ref_info['callback']:
                    try:
                        ref_info['callback'](ref_info['object'], new_texture)
                    except Exception as e:
                        print(f"❌ Error updating texture reference: {e}")
                else:
                    # Default texture update for NodePath objects
                    if hasattr(ref_info['object'], 'setTexture'):
                        ref_info['object'].setTexture(new_texture)
            
            # Call any registered callbacks
            if asset_path in self.asset_callbacks:
                for callback in self.asset_callbacks[asset_path]:
                    try:
                        callback(asset_path, old_texture, new_texture)
                    except Exception as e:
                        print(f"❌ Error in asset callback: {e}")
            
            print(f"✅ Successfully reloaded texture: {asset_path}")
            
        except Exception as e:
            print(f"❌ Error reloading texture {asset_path}: {e}")
    
    def _reload_audio(self, asset_path: str):
        """Reload an audio asset."""
        try:
            asset_info = self.tracked_assets[asset_path]
            old_audio = asset_info['object']
            
            print(f"🔊 Reloading audio: {asset_path}")
            
            # For audio, we need to notify audio systems to reload
            new_audio = self.showbase.loader.loadSfx(asset_path)
            
            if not new_audio:
                print(f"❌ Failed to load new audio: {asset_path}")
                return
            
            # Update the tracked asset
            asset_info['object'] = new_audio
            asset_info['hash'] = self._calculate_file_hash(asset_path)
            
            # Update references (audio components, etc.)
            for ref_info in asset_info['references']:
                if ref_info['callback']:
                    try:
                        ref_info['callback'](ref_info['object'], new_audio)
                    except Exception as e:
                        print(f"❌ Error updating audio reference: {e}")
            
            # Call any registered callbacks
            if asset_path in self.asset_callbacks:
                for callback in self.asset_callbacks[asset_path]:
                    try:
                        callback(asset_path, old_audio, new_audio)
                    except Exception as e:
                        print(f"❌ Error in audio callback: {e}")
            
            print(f"✅ Successfully reloaded audio: {asset_path}")
            
        except Exception as e:
            print(f"❌ Error reloading audio {asset_path}: {e}")
    
    def _reload_model(self, asset_path: str):
        """Reload a model asset."""
        print(f"🎭 Model reloading not yet implemented: {asset_path}")
        # TODO: Implement model reloading
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate MD5 hash of a file for change detection."""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            print(f"Error calculating hash for {file_path}: {e}")
            return ""
    
    def reload_asset_manually(self, asset_path: str):
        """Manually reload a specific asset."""
        print(f"🔄 Manual asset reload requested for: {asset_path}")
        abs_path = os.path.abspath(asset_path)
        self._handle_asset_changed(abs_path)
    
    def list_tracked_assets(self):
        """List all currently tracked assets."""
        print("📋 Tracked assets:")
        for asset_path, asset_info in self.tracked_assets.items():
            print(f"  - {asset_path} ({asset_info['type']}) - {len(asset_info['references'])} references")
    
    def __del__(self):
        """Cleanup when manager is destroyed."""
        self.stop_watching()
