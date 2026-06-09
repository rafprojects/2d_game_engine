"""
Live Development Tools Integration Example

This example shows how to integrate the live development tools
into a real game application for maximum development productivity.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from engine.dev_tools import HotReloadManager, ComponentInspector


class GameApplication:
    """Example game application with integrated live development tools."""
    
    def __init__(self, enable_dev_tools=True):
        self.running = True
        self.entities = {}
        self.systems = []
        
        # Live development tools (only in development mode)
        if enable_dev_tools:
            self.setup_dev_tools()
        else:
            self.hot_reload_manager = None
            self.component_inspector = None
    
    def setup_dev_tools(self):
        """Initialize live development tools."""
        print("🔧 Setting up live development tools...")
        
        # Hot reload manager
        self.hot_reload_manager = HotReloadManager(self)
        self.hot_reload_manager.add_watch_directory(str(project_root / "engine"))
        self.hot_reload_manager.add_watch_directory(str(project_root / "game"))  # Your game code
        
        # Register important modules for hot reload
        self.hot_reload_manager.register_module("engine.graphics.components.sprite_component")
        self.hot_reload_manager.register_module("engine.graphics.components.transform_component")
        self.hot_reload_manager.register_module("engine.graphics.systems.sprite_render_system")
        
        # Component inspector
        self.component_inspector = ComponentInspector(self)
        
        # Start watching for changes
        self.hot_reload_manager.start_watching()
        
        print("✅ Live development tools ready!")
        print("📝 Edit any .py file in engine/ or game/ directories to see hot reload in action")
        print("🔍 Use component_inspector to edit component properties at runtime")
    
    def update(self, dt):
        """Main game update loop."""
        # Process live development tools (if enabled)
        if self.hot_reload_manager:
            self.hot_reload_manager.process_reload_queue()
        
        # Update game systems
        for system in self.systems:
            try:
                system.update(dt)
            except Exception as e:
                print(f"❌ Error in system {type(system).__name__}: {e}")
    
    def shutdown(self):
        """Clean shutdown of the application."""
        print("🔽 Shutting down game application...")
        
        # Stop live development tools
        if self.hot_reload_manager:
            self.hot_reload_manager.stop_watching()
            print("⏹️ Live development tools stopped")
        
        self.running = False
        print("✅ Game application shut down")


def main():
    """Example of running a game with live development tools."""
    print("🚀 Starting game with live development tools...")
    
    # Create game application with dev tools enabled
    game = GameApplication(enable_dev_tools=True)
    
    # Example: Access development tools from outside
    print("\n🔧 Development tools available:")
    print(f"  - Hot Reload Manager: {game.hot_reload_manager}")
    print(f"  - Component Inspector: {game.component_inspector}")
    
    # Simulate game loop for a few seconds
    import time
    frame_time = 1.0 / 60.0  # 60 FPS
    
    print(f"\n⏱️ Running game loop (60 FPS) for 3 seconds...")
    print("   (In real game, this would run until user quits)")
    
    start_time = time.time()
    while time.time() - start_time < 3.0:
        game.update(frame_time)
        time.sleep(frame_time)
    
    # Clean shutdown
    game.shutdown()
    
    print("\n🎉 Example completed!")
    print("\nIntegration tips:")
    print("1. Only enable dev tools in development builds")
    print("2. Call hot_reload.process_reload_queue() in your main update loop")
    print("3. Use component_inspector for runtime debugging and tweaking")
    print("4. Add reload callbacks for systems that need to refresh after code changes")


if __name__ == "__main__":
    main()
