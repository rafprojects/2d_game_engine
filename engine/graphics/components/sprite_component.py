from panda3d.core import Vec4
from engine.core.component import Component

class SpriteComponent(Component):
    def __init__(self, image_path: str | None = None, sprite_sheet = None, layer: int = 0, 
                 color: Vec4 = Vec4(1, 1, 1, 1), opacity: float = 1.0):
        self.image_path = image_path
        self.layer = layer  # For sorting render order
        self.color = color
        self.opacity = opacity
        self.panda_node = None  # To store the Panda3D NodePath once loaded
        
        # Animation properties
        self.sprite_sheet = sprite_sheet
        self.current_animation = None
        self.current_frame_index = 0
        self.animation_time = 0.0
        self.is_playing = False
    
    def play_animation(self, animation_name: str, reset: bool = True):
        """Play the specified animation"""
        if not self.sprite_sheet:
            return False
            
        animation = self.sprite_sheet.get_animation(animation_name)
        if animation:
            self.current_animation = animation_name
            if reset:
                self.current_frame_index = 0
                self.animation_time = 0.0
            self.is_playing = True
            return True
        return False
    
    def stop_animation(self):
        """Stop the current animation"""
        self.is_playing = False
    
    def resume_animation(self):
        """Resume the current animation if it was stopped"""
        self.is_playing = True
    
    def reset_animation(self):
        """Reset the current animation to the first frame"""
        self.current_frame_index = 0
        self.animation_time = 0.0
    
    def update_animation(self, dt: float):
        """Update the animation state based on elapsed time"""
        if not self.sprite_sheet or not self.current_animation or not self.is_playing:
            return False
            
        animation = self.sprite_sheet.get_animation(self.current_animation)
        if not animation or not animation.frames:
            return False
            
        self.animation_time += dt
        
        # Calculate the current frame based on time
        if animation.total_duration > 0:
            if self.animation_time >= animation.total_duration:
                if animation.loop:
                    # Loop the animation
                    self.animation_time %= animation.total_duration
                else:
                    # Stop at the last frame
                    self.animation_time = animation.total_duration
                    self.is_playing = False
        
        # Find the correct frame based on the elapsed time
        elapsed = self.animation_time
        for i, frame in enumerate(animation.frames):
            if elapsed <= frame.duration:
                self.current_frame_index = i
                break
            elapsed -= frame.duration
            if i == len(animation.frames) - 1 and not animation.loop:
                self.current_frame_index = i  # Stay on last frame
                
        return True
    
    def get_current_frame(self):
        """Get the current animation frame"""
        if not self.sprite_sheet or not self.current_animation:
            return None
            
        animation = self.sprite_sheet.get_animation(self.current_animation)
        if not animation or not animation.frames:
            return None
            
        if 0 <= self.current_frame_index < len(animation.frames):
            return animation.frames[self.current_frame_index]
        return None
