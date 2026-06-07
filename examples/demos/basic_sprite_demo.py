from direct.showbase.ShowBase import ShowBase
from panda3d.core import Vec2, Filename, ClockObject
import os

from engine.core.system import World
from engine.core.components.transform_component import TransformComponent
from engine.graphics.components.sprite_component import SpriteComponent
from engine.graphics.systems.render_system import RenderSystem
from engine.input.components.input_component import InputComponent
from engine.input.systems.input_system import InputSystem
from engine.input.input_bindings import InputBinding

class BasicSpriteDemo(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        print("Basic Sprite Demo initialized")

        self.world = World()

        # Add systems
        self.render_system = RenderSystem(self.world, self)
        self.world.add_system(self.render_system)

        self.input_system = InputSystem(self.world, self)
        self.world.add_system(self.input_system)

        # Try to find an assets directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        assets_dir = os.path.join(os.path.dirname(script_dir), "assets")
        
        # Use the player sprite
        player_sprite_path = Filename.fromOsSpecific(os.path.join(assets_dir, "player.png")).getFullpath()
        if not os.path.exists(player_sprite_path):
            print(f"ERROR: No sprite found at {player_sprite_path}")
            return

        # Create a static player entity
        player_entity = self.world.create_entity("player_static")
        self.world.add_component(player_entity.id, 
            TransformComponent(position=Vec2(0, 0), scale=Vec2(2, 2)))  # Make it larger
        self.world.add_component(player_entity.id, 
            SpriteComponent(image_path=player_sprite_path, layer=1))
        
        # Add input component for movement
        input_bindings = {
            "move_left": [
                InputBinding(input_type="key", event_name="a"),
                InputBinding(input_type="key", event_name="arrow_left"),
            ],
            "move_right": [
                InputBinding(input_type="key", event_name="d"),
                InputBinding(input_type="key", event_name="arrow_right"),
            ],
            "move_up": [
                InputBinding(input_type="key", event_name="w"),
                InputBinding(input_type="key", event_name="arrow_up"),
            ],
            "move_down": [
                InputBinding(input_type="key", event_name="s"),
                InputBinding(input_type="key", event_name="arrow_down"),
            ]
        }
        self.world.add_component(player_entity.id, 
            InputComponent(action_bindings=input_bindings))

        # Game loop task
        self.taskMgr.add(self.update_game, "update_game_task")
    
    def update_game(self, task):
        dt = globalClock.getDt()
        self.world.update(dt)
        
        # Handle player movement based on input
        entities = self.world.get_entities_with_components(InputComponent, TransformComponent)
        for entity in entities:
            input_comp = self.world.get_component(entity.id, InputComponent)
            transform_comp = self.world.get_component(entity.id, TransformComponent)
            
            if input_comp and transform_comp:
                # Movement physics - adjusted for aspect2d coordinate system
                # In aspect2d, coordinates are normalized, so we need smaller movement values
                move_speed = 1.0 * dt  # 1 unit per second (appropriate for aspect2d)
                if input_comp.action_active.get("move_left", False):
                    transform_comp.position.x -= move_speed
                if input_comp.action_active.get("move_right", False):
                    transform_comp.position.x += move_speed
                if input_comp.action_active.get("move_up", False):
                    transform_comp.position.y += move_speed
                if input_comp.action_active.get("move_down", False):
                    transform_comp.position.y -= move_speed
        
        return task.cont

if __name__ == '__main__':
    app = BasicSpriteDemo()
    app.run()
