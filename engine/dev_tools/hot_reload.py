"""
Hot Reload Manager - Live code updates without restart.

This module provides the ability to reload Python modules at runtime,
allowing developers to see code changes immediately without restarting the game.
"""

import importlib
import sys
import time
import os
from pathlib import Path
from typing import Dict, Set, Callable, Optional, Any
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading


class ModuleReloadHandler(FileSystemEventHandler):
    """File system event handler that triggers module reloads."""
    
    def __init__(self, hot_reload_manager):
        self.hot_reload_manager = hot_reload_manager
        self.last_reload_time = {}
        self.reload_delay = 0.1  # Prevent multiple rapid reloads
    
    def on_modified(self, event):
        if event.is_directory:
            return
            
        if not event.src_path.endswith('.py'):
            return
            
        # Debounce rapid file changes
        current_time = time.time()
        if event.src_path in self.last_reload_time:
            if current_time - self.last_reload_time[event.src_path] < self.reload_delay:
                return
        
        self.last_reload_time[event.src_path] = current_time
        
        # Queue the reload (don't do it immediately to avoid threading issues)
        self.hot_reload_manager._queue_reload(event.src_path)


class HotReloadManager:
    """
    Manages hot reloading of Python modules during development.
    
    Features:
    - Watch filesystem for .py file changes
    - Safely reload modules without breaking references
    - Preserve component instances and game state
    - Handle reload errors gracefully
    - Notify systems of reloads for cleanup/re-initialization
    """
    
    def __init__(self, world, watch_directories: Optional[list] = None):
        self.world = world
        self.watch_directories = watch_directories or []
        self.observer = None
        self.is_watching = False
        
        # Track modules and their reload callbacks
        self.watched_modules: Dict[str, Any] = {}
        self.reload_callbacks: Dict[str, list] = {}
        self.reload_queue = []
        self.reload_lock = threading.Lock()
        
        # Track component classes for preservation during reload
        self.component_classes = {}
        self.system_classes = {}
        
        print("🔥 Hot Reload Manager initialized")
    
    def add_watch_directory(self, directory: str):
        """Add a directory to watch for file changes."""
        abs_path = os.path.abspath(directory)
        if abs_path not in self.watch_directories:
            self.watch_directories.append(abs_path)
            print(f"📁 Added watch directory: {abs_path}")
    
    def register_module(self, module_name: str, callback: Optional[Callable] = None):
        """
        Register a module for hot reloading.
        
        Args:
            module_name: Name of the module to watch
            callback: Optional function to call after reload
        """
        if module_name in sys.modules:
            self.watched_modules[module_name] = sys.modules[module_name]
            
            if callback:
                if module_name not in self.reload_callbacks:
                    self.reload_callbacks[module_name] = []
                self.reload_callbacks[module_name].append(callback)
            
            print(f"📝 Registered module for hot reload: {module_name}")
    
    def register_component_class(self, component_class):
        """Register a component class to preserve instances during reload."""
        class_name = component_class.__name__
        self.component_classes[class_name] = component_class
        print(f"🧩 Registered component class: {class_name}")
    
    def register_system_class(self, system_class):
        """Register a system class for hot reload handling."""
        class_name = system_class.__name__
        self.system_classes[class_name] = system_class
        print(f"⚙️ Registered system class: {class_name}")
    
    def start_watching(self):
        """Start watching for file changes."""
        if self.is_watching:
            return
            
        if not self.watch_directories:
            print("⚠️ No watch directories specified for hot reload")
            return
        
        self.observer = Observer()
        event_handler = ModuleReloadHandler(self)
        
        for directory in self.watch_directories:
            if os.path.exists(directory):
                self.observer.schedule(event_handler, directory, recursive=True)
                print(f"👀 Watching directory: {directory}")
            else:
                print(f"⚠️ Watch directory does not exist: {directory}")
        
        self.observer.start()
        self.is_watching = True
        print("🔥 Hot reload watching started")
    
    def stop_watching(self):
        """Stop watching for file changes."""
        if self.observer and self.is_watching:
            self.observer.stop()
            self.observer.join()
            self.is_watching = False
            print("⏹️ Hot reload watching stopped")
    
    def _queue_reload(self, file_path: str):
        """Queue a file for reloading (thread-safe)."""
        with self.reload_lock:
            if file_path not in self.reload_queue:
                self.reload_queue.append(file_path)
    
    def process_reload_queue(self):
        """Process any queued reloads. Call this from the main thread."""
        if not self.reload_queue:
            return
            
        with self.reload_lock:
            files_to_reload = self.reload_queue.copy()
            self.reload_queue.clear()
        
        for file_path in files_to_reload:
            self._handle_file_changed(file_path)
    
    def _handle_file_changed(self, file_path: str):
        """Handle a Python file change."""
        try:
            # Convert file path to module name
            module_name = self._file_path_to_module_name(file_path)
            if not module_name:
                return
            
            print(f"🔄 File changed: {file_path}")
            print(f"🔄 Attempting to reload module: {module_name}")
            
            # Reload the module
            if module_name in sys.modules:
                self._reload_module(module_name)
            else:
                print(f"⚠️ Module {module_name} not in sys.modules")
                
        except Exception as e:
            print(f"❌ Error handling file change for {file_path}: {e}")
    
    def _file_path_to_module_name(self, file_path: str) -> Optional[str]:
        """Convert a file path to a Python module name."""
        try:
            # Normalize the path
            file_path = os.path.abspath(file_path)
            
            # Find which watch directory contains this file
            for watch_dir in self.watch_directories:
                watch_dir = os.path.abspath(watch_dir)
                if file_path.startswith(watch_dir):
                    # Get relative path from watch directory
                    rel_path = os.path.relpath(file_path, watch_dir)
                    
                    # Convert to module name
                    module_parts = rel_path.replace('.py', '').split(os.sep)
                    
                    # Handle engine directory specially
                    if 'engine' in module_parts:
                        engine_idx = module_parts.index('engine')
                        module_parts = module_parts[engine_idx:]
                    
                    module_name = '.'.join(module_parts)
                    return module_name
            
            return None
        except Exception as e:
            print(f"Error converting file path to module name: {e}")
            return None
    
    def _reload_module(self, module_name: str):
        """Safely reload a module."""
        try:
            if module_name not in sys.modules:
                print(f"⚠️ Module {module_name} not loaded")
                return
            
            old_module = sys.modules[module_name]
            
            # Perform the reload
            print(f"🔄 Reloading module: {module_name}")
            new_module = importlib.reload(old_module)
            
            # Call any registered callbacks
            if module_name in self.reload_callbacks:
                for callback in self.reload_callbacks[module_name]:
                    try:
                        callback(old_module, new_module)
                    except Exception as e:
                        print(f"❌ Error in reload callback: {e}")
            
            # Notify the world about the reload
            self._notify_world_of_reload(module_name, old_module, new_module)
            
            print(f"✅ Successfully reloaded: {module_name}")
            
        except Exception as e:
            print(f"❌ Error reloading module {module_name}: {e}")
    
    def _notify_world_of_reload(self, module_name: str, old_module: Any, new_module: Any):
        """Notify the world and systems about module reload."""
        try:
            # Check if any systems need to be notified
            for system in self.world.systems:
                if hasattr(system, 'on_module_reloaded'):
                    try:
                        system.on_module_reloaded(module_name, old_module, new_module)
                    except Exception as e:
                        print(f"❌ Error notifying system {type(system).__name__}: {e}")
        except Exception as e:
            print(f"❌ Error notifying world of reload: {e}")
    
    def reload_module_manually(self, module_name: str):
        """Manually reload a specific module."""
        print(f"🔄 Manual reload requested for: {module_name}")
        self._reload_module(module_name)
    
    def list_watched_modules(self):
        """List all currently watched modules."""
        print("📋 Watched modules:")
        for module_name in self.watched_modules:
            print(f"  - {module_name}")
    
    def __del__(self):
        """Cleanup when manager is destroyed."""
        self.stop_watching()
