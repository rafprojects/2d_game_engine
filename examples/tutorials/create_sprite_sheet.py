#!/usr/bin/env python3
# Create a simple sprite sheet for the demo
from PIL import Image, ImageDraw
import os

def create_simple_sprite_sheet(output_path):
    # Create a 4x4 sprite sheet (4 animations with 4 frames each)
    width, height = 256, 256  # Total size
    sprite_width, sprite_height = 64, 64  # Each sprite size
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Colors for different animation rows
    colors = [
        (200, 200, 255, 255),  # Idle - Light blue
        (255, 200, 200, 255),  # Walk - Light red
        (200, 255, 200, 255),  # Jump - Light green
        (255, 255, 200, 255)   # Attack - Light yellow
    ]
    
    # Draw a sprite sheet with simple shapes
    for row in range(4):  # 4 animations
        color = colors[row]
        for col in range(4):  # 4 frames per animation
            x = col * sprite_width
            y = row * sprite_height
            
            # Draw frame background
            draw.rectangle([(x, y), (x + sprite_width - 1, y + sprite_height - 1)], 
                           fill=(0, 0, 0, 0))
            
            # Draw character body (circle)
            center_x = x + sprite_width // 2
            center_y = y + sprite_height // 2
            radius = sprite_width // 3
            draw.ellipse((center_x - radius, center_y - radius, 
                         center_x + radius, center_y + radius), 
                         fill=color)
            
            # Add animation-specific details
            if row == 0:  # Idle
                # Pulsate size based on frame
                pulse = 2 + col * 2
                draw.ellipse((center_x - pulse, center_y - pulse, 
                             center_x + pulse, center_y + pulse),
                             outline=(0, 0, 200, 255), width=2)
            
            elif row == 1:  # Walk
                # Moving legs
                leg_offset = [-6, -2, 2, 6][col]
                draw.rectangle([center_x - 5, center_y + radius, 
                               center_x - 2, center_y + radius + 15 + leg_offset], 
                               fill=(160, 100, 100, 255))
                draw.rectangle([center_x + 2, center_y + radius, 
                               center_x + 5, center_y + radius + 15 - leg_offset], 
                               fill=(160, 100, 100, 255))
            
            elif row == 2:  # Jump
                # Character moving up
                jump_offset = [0, -10, -15, -5][col]
                draw.ellipse((center_x - radius, center_y - radius + jump_offset, 
                             center_x + radius, center_y + radius + jump_offset), 
                             fill=color)
                # Original circle with lowered opacity
                if col > 0:
                    original_color = (color[0], color[1], color[2], 100)
                    draw.ellipse((center_x - radius, center_y - radius, 
                                 center_x + radius, center_y + radius), 
                                 fill=original_color)
            
            elif row == 3:  # Attack
                # Attacking arm
                attack_length = [10, 20, 25, 15][col]
                draw.line([center_x, center_y, center_x + attack_length, center_y],
                          fill=(255, 0, 0, 255), width=5)
                draw.ellipse((center_x + attack_length - 3, center_y - 3,
                             center_x + attack_length + 3, center_y + 3),
                             fill=(255, 0, 0, 255))
            
            # Add frame number for reference
            draw.text((x + 5, y + 5), f"{row},{col}", fill=(0, 0, 0, 255))
    
    # Save the sprite sheet
    img.save(output_path)
    print(f"Created sprite sheet at {output_path}")

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    assets_dir = os.path.join(os.path.dirname(script_dir), "assets")
    
    if not os.path.exists(assets_dir):
        os.makedirs(assets_dir)
    
    output_path = os.path.join(assets_dir, "player_sheet.png")
    create_simple_sprite_sheet(output_path)
