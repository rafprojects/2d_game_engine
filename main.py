# Main entry point for the game engine
from direct.showbase.ShowBase import ShowBase
from panda3d.core import Vec2, Filename, ClockObject # Import ClockObject for globalClock
import os # Import os for path manipulation

from engine.core.system import World
from engine.core.components.transform_component import TransformComponent
from engine.graphics.components.sprite_component import SpriteComponent
from engine.graphics.systems.render_system import RenderSystem
from engine.input.components.input_component import InputComponent
from engine.input.systems.input_system import InputSystem
from engine.input.input_bindings import InputBinding

class Game(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        print("Game initialized")

        self.world = World()

        # Add systems
        self.render_system = RenderSystem(self.world, self) # Pass ShowBase instance
        self.world.add_system(self.render_system)

        self.input_system = InputSystem(self.world, self) # Pass ShowBase instance
        self.world.add_system(self.input_system)

        # Try to find an assets directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        assets_dir = os.path.join(script_dir, "assets")
        if not os.path.exists(assets_dir):
            os.makedirs(assets_dir)
            print(f"Created assets directory at: {assets_dir}")
            print("Please add a test image (e.g., 'player.png') to this directory.")

        test_image_path = Filename.fromOsSpecific(os.path.join(assets_dir, "player.png")).getFullpath()
        print("TEST IMAGE PATH: ", test_image_path)
        # Check if the placeholder image exists, if not, we can't run the example entity
        if not os.path.exists(test_image_path):
            print(f"ERROR: Test image not found at {test_image_path}")
            print("Please create a placeholder image (e.g., 'player.png') in the 'assets' directory to see the sprite.")
        else:
            player_entity = self.world.create_entity("player") # Named for easier debugging
            self.world.add_component(player_entity.id, TransformComponent(position=Vec2(100, 100), scale=Vec2(100,100))) # Adjusted scale
            self.world.add_component(player_entity.id, SpriteComponent(image_path=test_image_path, layer=1))

            # Setup Input for the player entity
            player_input_bindings = {
                "move_left": [
                    InputBinding(input_type="key", event_name="a"),
                    InputBinding(input_type="key", event_name="arrow_left"),
                    InputBinding(input_type="gamepad_button", event_name="gamepad-dpad_left"),
                    InputBinding(input_type="gamepad_axis", event_name="lstick_x", axis_direction="negative", axis_threshold=0.3)
                ],
                "move_right": [
                    InputBinding(input_type="key", event_name="d"),
                    InputBinding(input_type="key", event_name="arrow_right"),
                    InputBinding(input_type="gamepad_button", event_name="gamepad-dpad_right"),
                    InputBinding(input_type="gamepad_axis", event_name="lstick_x", axis_direction="positive", axis_threshold=0.3)
                ],
                "fire": [
                    InputBinding(input_type="key", event_name="space"),
                    InputBinding(input_type="mouse_button", event_name="mouse1"), # Left mouse button
                    InputBinding(input_type="gamepad_button", event_name="gamepad-face_x") # 'X' on Xbox, Square on PS
                ],
                "alt_fire": [
                    InputBinding(input_type="gamepad_button", event_name="gamepad-rtrigger"), # Panda uses 'gamepad-rtrigger' for button press
                    InputBinding(input_type="gamepad_axis", event_name="rtrigger", axis_direction="positive", axis_threshold=0.1) # For analog trigger
                ]
            }
            self.world.add_component(player_entity.id, InputComponent(action_bindings=player_input_bindings))
            print(f"Added InputComponent to entity: {player_entity.id}")


        # Game loop task
        self.taskMgr.add(self.update_game, "update_game_task")

    def _handle_player_input_debug(self, input_comp: InputComponent):
        """Helper to print player input states for debugging."""
        if input_comp.action_just_pressed.get("fire"):
            print(f"[{globalClock.getFrameTime():.2f}] Player FIRE just pressed!")
        if input_comp.action_active.get("move_left"):
            print(f"[{globalClock.getFrameTime():.2f}] Player MOVE_LEFT active")
        if input_comp.action_active.get("move_right"):
            print(f"[{globalClock.getFrameTime():.2f}] Player MOVE_RIGHT active")
        if input_comp.action_just_released.get("fire"):
            print(f"[{globalClock.getFrameTime():.2f}] Player FIRE just released!")
        if input_comp.action_active.get("alt_fire"):
            print(f"[{globalClock.getFrameTime():.2f}] Player ALT_FIRE active (check gamepad trigger)")

    def update_game(self, task):
        # Access globalClock directly as it's part of ShowBase
        dt = globalClock.getDt()
        self.world.update(dt)

        # Example: Check input states for the player entity
        entities = self.world.get_entities_with_components(InputComponent)
        for entity in entities:
            # Since we've created only one entity with InputComponent (the player)
            input_comp = self.world.get_component(entity.id, InputComponent)
            if input_comp:
                self._handle_player_input_debug(input_comp)

        return task.cont

if __name__ == '__main__':
    app = Game()
    app.run()
