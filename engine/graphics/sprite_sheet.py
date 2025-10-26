from typing import Dict, List, Tuple

from panda3d.core import Texture, PNMImage, LVecBase4f

class SpriteFrame:
    """Represents a single frame in a sprite animation"""
    def __init__(self, texture: Texture, u_offset: float, v_offset: float, 
                 u_size: float, v_size: float, duration: float = 0.1):
        self.texture = texture        # The full sprite sheet texture
        self.u_offset = u_offset      # UV coordinates (left)
        self.v_offset = v_offset      # UV coordinates (top)
        self.u_size = u_size          # UV width
        self.v_size = v_size          # UV height
        self.duration = duration      # How long this frame should display (in seconds)

class Animation:
    """Represents a sequence of sprite frames that make up an animation"""
    def __init__(self, name: str, frames: List[SpriteFrame], loop: bool = True):
        self.name = name
        self.frames = frames
        self.loop = loop
        self.total_duration = sum(frame.duration for frame in frames)
    
    @property
    def frame_count(self):
        return len(self.frames)

class SpriteSheet:
    """
    Handles sprite sheets and animations.
    Can load sprite sheets and create animations from them.
    """
    def __init__(self, texture: Texture = None):
        self.texture = texture
        self.animations: Dict[str, Animation] = {}
        self.width = 0
        self.height = 0
        if texture:
            self.width = texture.getXSize()
            self.height = texture.getYSize()
    
    def load_from_texture(self, texture: Texture):
        """Load spritesheet from a Panda3D texture"""
        self.texture = texture
        self.width = texture.getXSize()
        self.height = texture.getYSize()
    
    def create_grid_animation(self, name: str, rows: int, cols: int, 
                              row_start: int, col_start: int, frame_count: int,
                              frame_duration: float = 0.1, loop: bool = True) -> Animation:
        """
        Create an animation from a grid-based sprite sheet
        
        Args:
            name: Name of the animation
            rows: Total rows in the sprite sheet
            cols: Total columns in the sprite sheet
            row_start: Starting row (0-based)
            col_start: Starting column (0-based)
            frame_count: Number of frames in the animation
            frame_duration: Duration of each frame in seconds
            loop: Whether the animation should loop
        """
        if not self.texture:
            raise ValueError("Texture not loaded. Call load_from_texture first.")
            
        frames = []
        frame_width = 1.0 / cols
        frame_height = 1.0 / rows
        
        for i in range(frame_count):
            # Calculate grid position
            grid_x = (col_start + i) % cols
            grid_y = row_start + ((col_start + i) // cols)
            
            if grid_y >= rows:
                break  # Don't exceed grid bounds
                
            # Calculate UV coordinates
            u = grid_x * frame_width
            v = 1.0 - ((grid_y + 1) * frame_height)  # Panda3D's V is bottom-up
            
            frame = SpriteFrame(
                self.texture,
                u, v,
                frame_width, frame_height,
                frame_duration
            )
            frames.append(frame)
            
        animation = Animation(name, frames, loop)
        self.animations[name] = animation
        return animation
    
    def create_animation_from_frames(self, name: str, frame_coordinates: List[Tuple[int, int, int, int]], 
                                    frame_durations: List[float] = None, loop: bool = True) -> Animation:
        """
        Create an animation from specific frame coordinates
        
        Args:
            name: Name of the animation
            frame_coordinates: List of (x, y, width, height) tuples for each frame in pixels
            frame_durations: List of durations for each frame (or None to use a default)
            loop: Whether the animation should loop
        """
        if not self.texture:
            raise ValueError("Texture not loaded. Call load_from_texture first.")
            
        frames = []
        default_duration = 0.1
        
        for i, (x, y, width, height) in enumerate(frame_coordinates):
            # Convert pixel coordinates to UV coordinates
            u = x / self.width
            v = 1.0 - ((y + height) / self.height)  # Panda3D's V is bottom-up
            u_size = width / self.width
            v_size = height / self.height
            
            duration = default_duration
            if frame_durations and i < len(frame_durations):
                duration = frame_durations[i]
                
            frame = SpriteFrame(
                self.texture,
                u, v,
                u_size, v_size,
                duration
            )
            frames.append(frame)
            
        animation = Animation(name, frames, loop)
        self.animations[name] = animation
        return animation
    
    def get_animation(self, name: str) -> Animation:
        """Get an animation by name"""
        if name in self.animations:
            return self.animations[name]
        return None
