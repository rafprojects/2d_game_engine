#!/usr/bin/env python3
# Create a simple player sprite
from PIL import Image, ImageDraw
import os

def create_simple_player_sprite(output_path):
    # Create a simple player sprite
    width, height = 64, 64
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw player body (circle)
    center_x, center_y = width // 2, height // 2
    radius = width // 3
    draw.ellipse((center_x - radius, center_y - radius, 
                 center_x + radius, center_y + radius), 
                 fill=(100, 100, 255, 255))
    
    # Draw eyes
    eye_radius = radius // 4
    draw.ellipse((center_x - radius//2 - eye_radius, center_y - eye_radius - 5, 
                 center_x - radius//2 + eye_radius, center_y + eye_radius - 5), 
                 fill=(255, 255, 255, 255))
    draw.ellipse((center_x + radius//2 - eye_radius, center_y - eye_radius - 5, 
                 center_x + radius//2 + eye_radius, center_y + eye_radius - 5), 
                 fill=(255, 255, 255, 255))
    
    # Draw pupils
    pupil_radius = eye_radius // 2
    draw.ellipse((center_x - radius//2 - pupil_radius, center_y - pupil_radius - 5, 
                 center_x - radius//2 + pupil_radius, center_y + pupil_radius - 5), 
                 fill=(0, 0, 0, 255))
    draw.ellipse((center_x + radius//2 - pupil_radius, center_y - pupil_radius - 5, 
                 center_x + radius//2 + pupil_radius, center_y + pupil_radius - 5), 
                 fill=(0, 0, 0, 255))
    
    # Draw mouth
    draw.arc((center_x - radius//2, center_y, center_x + radius//2, center_y + radius//2), 
             0, 180, fill=(0, 0, 0, 255), width=2)
    
    # Draw limbs
    # Arms
    draw.line([center_x - radius, center_y, center_x - radius - 10, center_y - 5], 
              fill=(100, 100, 255, 255), width=3)
    draw.line([center_x + radius, center_y, center_x + radius + 10, center_y - 5], 
              fill=(100, 100, 255, 255), width=3)
    
    # Legs
    draw.line([center_x - radius//2, center_y + radius, center_x - radius//2, center_y + radius + 15], 
              fill=(100, 100, 255, 255), width=3)
    draw.line([center_x + radius//2, center_y + radius, center_x + radius//2, center_y + radius + 15], 
              fill=(100, 100, 255, 255), width=3)
    
    # Save the sprite
    img.save(output_path)
    print(f"Created player sprite at {output_path}")

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    assets_dir = os.path.join(os.path.dirname(script_dir), "assets")
    
    if not os.path.exists(assets_dir):
        os.makedirs(assets_dir)
    
    output_path = os.path.join(assets_dir, "player.png")
    create_simple_player_sprite(output_path)
