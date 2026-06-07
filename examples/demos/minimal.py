from direct.showbase.ShowBase import ShowBase
from panda3d.core import CardMaker, TransparencyAttrib, Vec4, Filename, loadPrcFileData
import os

# Set window properties before initialization
loadPrcFileData("", "win-size 800 600")
loadPrcFileData("", "window-title Minimal Sprite Demo")
loadPrcFileData("", "notify-level debug")  # Enable debug notifications

class MinimalDemo(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        print("Minimal demo initialized")
        
        # Set a background color other than the default blue to easily spot if content is rendering
        self.setBackgroundColor(0.2, 0.2, 0.2)  # Dark gray
        
        # Try to find an assets directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        assets_dir = os.path.join(script_dir, "assets")
        
        # Use the player sprite
        player_sprite_path = Filename.fromOsSpecific(os.path.join(assets_dir, "player.png")).getFullpath()
        if not os.path.exists(player_sprite_path):
            print(f"ERROR: No sprite found at {player_sprite_path}")
            return
        
        print(f"Loading texture from: {player_sprite_path}")
        texture = self.loader.loadTexture(player_sprite_path)
        
        if not texture:
            print("Failed to load texture!")
            return
            
        print(f"Texture loaded successfully: {texture}")
            
        # Create a card to display the sprite
        cm = CardMaker("player_sprite")
        cm.setFrame(-0.5, 0.5, -0.5, 0.5)  # Centered at origin
        
        # Use aspect2d instead of render2d for more reliable positioning
        node = self.aspect2d.attachNewNode(cm.generate())
        node.setTexture(texture)
        node.setTransparency(TransparencyAttrib.MAlpha)
        
        # Try a more moderate scale
        node.setScale(0.5)  # Adjust this value to change sprite size
        
        # Set color to ensure it's not transparent
        node.setColor(1, 1, 1, 1)
        
        # Position in the center of the screen
        node.setPos(0, 0, 0)
        
        # Print node information for debugging
        print(f"Node path: {node}")
        print(f"Node position: {node.getPos()}")
        print(f"Node scale: {node.getScale()}")
        print(f"Node has texture: {node.hasTexture()}")
        
        # Add a task to monitor the node
        self.taskMgr.add(self.monitor_node, "monitor_node", extraArgs=[node], appendTask=True)
        
        print("Sprite created successfully!")
        
    def monitor_node(self, node, task):
        """Monitor the node to ensure it remains visible"""
        if task.time < 5.0:  # Run for 5 seconds
            if task.time < 0.1 or int(task.time * 10) % 10 == 0:  # Report every second
                print(f"Time: {task.time:.1f} - Node visible: {not node.isHidden()}")
                print(f"Current position: {node.getPos()}")
                print(f"Current color: {node.getColor()}")
                print(f"Has texture: {node.hasTexture()}")
                if node.hasTexture():
                    tex = node.getTexture()
                    print(f"Texture size: {tex.getXSize()} x {tex.getYSize()}")
        else:
            return task.done
        return task.cont
        
    def check_render_tree(self):
        """Print the entire render tree for debugging"""
        print("\nRender tree (render):")
        self.render.ls()
        print("\nRender tree (render2d):")
        self.render2d.ls()
        print("\nRender tree (aspect2d):")
        self.aspect2d.ls()

if __name__ == '__main__':
    app = MinimalDemo()
    # Call after a short delay to see the scene graph
    from direct.task.TaskManagerGlobal import taskMgr
    taskMgr.doMethodLater(1.0, app.check_render_tree, "check_render_tree")
    app.run()
