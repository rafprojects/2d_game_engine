from direct.showbase.ShowBase import ShowBase
from direct.showbase.ShowBaseGlobal import globalClock
from panda3d.core import Vec2, Filename, ClockObject, Vec4
import os
import sys

# Add parent directory to path for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.append(parent_dir)

from engine.core.system import World
from engine.core.components.transform_component import TransformComponent
from engine.graphics.components.sprite_component import SpriteComponent
from engine.graphics.systems.render_system import RenderSystem
from engine.input.components.input_component import InputComponent
from engine.input.systems.input_system import InputSystem
from engine.input.input_bindings import InputBinding
from engine.graphics.sprite_sheet import SpriteSheet

class AnimatedSpriteDemo(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        print("Animated Sprite Demo initialized")

        self.world = World()

        # Add systems
        self.render_system = RenderSystem(self.world, self)
        self.world.add_system(self.render_system)

        self.input_system = InputSystem(self.world, self)
        self.world.add_system(self.input_system)

        # Try to find an assets directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        assets_dir = os.path.join(os.path.dirname(script_dir), "assets")
        if not os.path.exists(assets_dir):
            os.makedirs(assets_dir)
            print(f"Created assets directory at: {assets_dir}")

        # Check for a sprite sheet
        sprite_sheet_path = os.path.join(assets_dir, "player_sheet.png")
        if not os.path.exists(sprite_sheet_path):
            print(f"WARNING: Sprite sheet not found at {sprite_sheet_path}")
            print("Please add a sprite sheet named 'player_sheet.png' to the assets directory.")
            print("The demo will use a static sprite instead.")
            
            # Fall back to static sprite
            player_sprite_path = Filename.fromOsSpecific(os.path.join(assets_dir, "player.png")).getFullpath()
            if not os.path.exists(player_sprite_path):
                print(f"ERROR: No sprite found at {player_sprite_path}")
                print("Please add a sprite named 'player.png' to the assets directory.")
                return

            # Create a static player entity
            player_entity = self.world.create_entity("player_static")
            self.world.add_component(player_entity.id, 
                TransformComponent(position=Vec2(0, 0), scale=Vec2(100, 100)))
            self.world.add_component(player_entity.id, 
                SpriteComponent(image_path=player_sprite_path, layer=1))
            
        else:
            # Create a sprite sheet for animations
            sprite_sheet_path = Filename.fromOsSpecific(sprite_sheet_path).getFullpath()
            texture = self.loader.loadTexture(sprite_sheet_path)
            
            sprite_sheet = SpriteSheet(texture)
            
            # Create animations (assuming a standard arrangement)
            # Idle animation (first row)
            sprite_sheet.create_grid_animation("idle", rows=4, cols=4, 
                                              row_start=0, col_start=0, 
                                              frame_count=4, frame_duration=0.15)
            
            # Walk animation (second row)
            sprite_sheet.create_grid_animation("walk", rows=4, cols=4, 
                                              row_start=1, col_start=0, 
                                              frame_count=4, frame_duration=0.15)
            
            # Jump animation (third row)
            sprite_sheet.create_grid_animation("jump", rows=4, cols=4, 
                                              row_start=2, col_start=0, 
                                              frame_count=4, frame_duration=0.1, 
                                              loop=False)
            
            # Attack animation (fourth row)
            sprite_sheet.create_grid_animation("attack", rows=4, cols=4, 
                                              row_start=3, col_start=0, 
                                              frame_count=4, frame_duration=0.1, 
                                              loop=False)

            # Create an animated player entity
            player_entity = self.world.create_entity("player_animated")
            self.world.add_component(player_entity.id, 
                TransformComponent(position=Vec2(0, 0), scale=Vec2(100, 100)))
            
            # Create the sprite component with the sprite sheet
            # We need to provide both the image_path and sprite_sheet
            sprite_comp = SpriteComponent(image_path=sprite_sheet_path, sprite_sheet=sprite_sheet, layer=1)
            sprite_comp.play_animation("idle")  # Start with idle animation
            
            self.world.add_component(player_entity.id, sprite_comp)
            
            # Add input component to control animations
            input_bindings = {
                "move_left": [
                    InputBinding(input_type="key", event_name="a"),
                    InputBinding(input_type="key", event_name="arrow_left"),
                ],
                "move_right": [
                    InputBinding(input_type="key", event_name="d"),
                    InputBinding(input_type="key", event_name="arrow_right"),
                ],
                "jump": [
                    InputBinding(input_type="key", event_name="space"),
                ],
                "attack": [
                    InputBinding(input_type="mouse_button", event_name="mouse1"),
                ]
            }
            self.world.add_component(player_entity.id, 
                InputComponent(action_bindings=input_bindings))

        # Game loop task
        self.taskMgr.add(self.update_game, "update_game_task")
    
    def update_game(self, task):
        dt = globalClock.getDt()
        self.world.update(dt)
        
        # Handle player animations based on input
        entities = self.world.get_entities_with_components(InputComponent, SpriteComponent)
        for entity in entities:
            input_comp = self.world.get_component(entity.id, InputComponent)
            sprite_comp = self.world.get_component(entity.id, SpriteComponent)
            transform_comp = self.world.get_component(entity.id, TransformComponent)
            
            if input_comp and sprite_comp and transform_comp:
                if sprite_comp.sprite_sheet:  # Only for sprite sheet-based sprites
                    # Movement and animation logic
                    moving_left = input_comp.action_active.get("move_left", False)
                    moving_right = input_comp.action_active.get("move_right", False)
                    jumping = input_comp.action_just_pressed.get("jump", False)
                    attacking = input_comp.action_just_pressed.get("attack", False)
                    
                    # Set sprite flipping based on direction
                    if moving_left:
                        sprite_comp.flip_x = True
                    elif moving_right:
                        sprite_comp.flip_x = False
                    
                    # Movement physics - adjusted for aspect2d coordinate system
                    # In aspect2d, coordinates are normalized, so we need smaller movement values
                    move_speed = 1.0 * dt  # 1 unit per second (appropriate for aspect2d)
                    if moving_left:
                        transform_comp.position.x -= move_speed
                    if moving_right:
                        transform_comp.position.x += move_speed
                    
                    # Animation state machine
                    current_anim = sprite_comp.current_animation
                    
                    # Attack takes priority
                    if attacking:
                        sprite_comp.play_animation("attack")
                        print("Attack animation")
                    # Then jumping
                    elif jumping:
                        sprite_comp.play_animation("jump")
                        print("Jump animation")
                    # Then walking
                    elif moving_left or moving_right:
                        if current_anim != "walk":
                            sprite_comp.play_animation("walk")
                    # Then idle
                    else:
                        if current_anim != "idle" and current_anim != "jump" and current_anim != "attack":
                            sprite_comp.play_animation("idle")
                
                    # Print current state for debugging
                    if input_comp.action_just_pressed.get("jump", False):
                        print("Jump button pressed!")
                    if input_comp.action_just_pressed.get("attack", False):
                        print("Attack button pressed!")
        
        return task.cont

if __name__ == '__main__':
    app = AnimatedSpriteDemo()
    app.run()
