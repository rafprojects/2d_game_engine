#!/usr/bin/env python3
"""
Project Generator CLI Tool

Advanced scaffolding and code generation for the 2D Game Engine:
- Complete game project templates (platformer, shooter, RPG, puzzle)
- Component and system templates with best practices
- Custom scene templates
- Asset organization structures
- Testing boilerplate generation
- Documentation templates

Usage:
    python -m tools.cli.project_gen [command] [options]
    py2d-engine [command] [options]  # When installed
    
Commands:
    new-game [name]     - Create a new game project with template
    new-component       - Create component with boilerplate
    new-system          - Create system with boilerplate
    new-scene           - Create scene template
    new-example         - Create example/demo template
    new-test            - Create test template for component/system
    templates           - List available templates
    
Template Types:
    --platformer        - Side-scrolling platformer game
    --top-down          - Top-down action/shooter game
    --puzzle            - Puzzle game mechanics
    --rpg               - RPG-style game with inventory/stats
    --minimal           - Minimal game template

Examples:
    py2d-engine new-game "My Platformer" --template platformer
    py2d-engine new-component PlayerController --with-test
    py2d-engine new-system AudioSystem --events --documentation
"""

import argparse
import os
import sys
from pathlib import Path

# Import CLI utilities  
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from tools.cli import (
    print_header, print_success, print_error, print_warning, print_info,
    get_project_root, get_examples_dir
)

def create_new_game(game_name):
    """Create a new game project structure."""
    print_header(f"Creating New Game: {game_name}")
    
    # Sanitize game name
    safe_name = "".join(c for c in game_name if c.isalnum() or c in ('_', '-')).lower()
    if not safe_name:
        print_error("Invalid game name")
        return False
    
    # Create game directory
    examples_dir = get_examples_dir()
    game_dir = os.path.join(examples_dir, "games", safe_name)
    
    if os.path.exists(game_dir):
        print_error(f"Game directory already exists: {game_dir}")
        return False
    
    os.makedirs(game_dir, exist_ok=True)
    
    # Create basic game structure
    files_to_create = {
        "main.py": create_main_py_template(game_name, safe_name),
        "README.md": create_readme_template(game_name),
        "requirements.txt": "# Add any additional requirements here\n",
        "assets/.gitkeep": "",
        "components/__init__.py": "# Game-specific components\n",
        "systems/__init__.py": "# Game-specific systems\n"
    }
    
    for file_path, content in files_to_create.items():
        full_path = os.path.join(game_dir, file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        with open(full_path, 'w') as f:
            f.write(content)
        
        print_success(f"Created: {file_path}")
    
    print_success(f"Game '{game_name}' created at: {game_dir}")
    print_info("To run your game:")
    print(f"  cd {game_dir}")
    print(f"  python main.py")
    
    return True

def create_main_py_template(game_name, safe_name):
    """Create main.py template for new game."""
    return f'''#!/usr/bin/env python3
"""
{game_name}

A game built with the 2D Game Engine.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from direct.showbase.ShowBase import ShowBase
from direct.showbase.ShowBaseGlobal import globalClock
from panda3d.core import Vec2, loadPrcFileData

# Engine imports
from engine.core.system import World
from engine.graphics.components.transform_component import TransformComponent
from engine.graphics.components.sprite_component import SpriteComponent
from engine.graphics.systems.render_system import RenderSystem
from engine.input.components.input_component import InputComponent
from engine.input.systems.input_system import InputSystem
from engine.input.input_bindings import InputBinding

# Set window properties
loadPrcFileData("", "win-size 800 600")
loadPrcFileData("", f"window-title {game_name}")

class {game_name.replace(' ', '').replace('-', '').replace('_', '')}Game(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        print(f"🎮 {{game_name}} initialized!")
        
        # Set background color
        self.setBackgroundColor(0.1, 0.1, 0.2)  # Dark blue
        
        # Create world and systems
        self.world = World()
        
        # Add render system
        self.render_system = RenderSystem(self.world, self)
        self.world.add_system(self.render_system)
        
        # Add input system
        self.input_system = InputSystem(self.world, self)
        self.world.add_system(self.input_system)
        
        # Initialize game
        self.setup_game()
        
        # Start game loop
        self.taskMgr.add(self.update_game, "update_game")
        
    def setup_game(self):
        """Initialize game entities and components."""
        print("Setting up game...")
        
        # Example: Create a player entity
        # player = self.world.create_entity("player")
        # self.world.add_component(player.id, TransformComponent(x=0.0, y=0.0))
        # 
        # # Add sprite if asset exists
        # player_sprite_path = os.path.join("assets", "player.png")
        # if os.path.exists(player_sprite_path):
        #     self.world.add_component(player.id, SpriteComponent(image_path=player_sprite_path))
        # 
        # # Add input controls
        # input_bindings = {{
        #     "move_left": [InputBinding(input_type="key", event_name="a")],
        #     "move_right": [InputBinding(input_type="key", event_name="d")],
        #     "move_up": [InputBinding(input_type="key", event_name="w")],
        #     "move_down": [InputBinding(input_type="key", event_name="s")]
        # }}
        # self.world.add_component(player.id, InputComponent(action_bindings=input_bindings))
        
        print("Game setup complete!")
        
    def update_game(self, task):
        """Main game update loop."""
        dt = globalClock.getDt()
        self.world.update(dt)
        
        # Add your game logic here
        
        return task.cont

if __name__ == '__main__':
    game = {game_name.replace(' ', '').replace('-', '').replace('_', '')}Game()
    game.run()
'''

def create_readme_template(game_name):
    """Create README.md template for new game."""
    return f'''# {game_name}

A game built with the 2D Game Engine.

## Description

[Add your game description here]

## Controls

[Add your game controls here]

## How to Run

1. Make sure the 2D Game Engine is set up
2. Navigate to this directory
3. Run: `python main.py`

## Assets

Place your game assets in the `assets/` directory:
- `assets/sprites/` - Character and object sprites
- `assets/textures/` - Background textures and tiles
- `assets/audio/` - Sound effects and music
- `assets/fonts/` - Custom fonts

## Development

- `components/` - Game-specific components
- `systems/` - Game-specific systems
- `main.py` - Main game entry point

## Features

- [ ] [Add your planned features here]
- [ ] [Feature 2]
- [ ] [Feature 3]

## Credits

Built with the 2D Game Engine.
'''

def create_new_component():
    """Create a new component template."""
    print_header("Creating New Component")
    
    component_name = input("Component name (e.g., 'Health'): ").strip()
    if not component_name:
        print_error("Component name required")
        return False
    
    # Sanitize component name
    class_name = component_name.replace(" ", "").title() + "Component"
    file_name = component_name.lower().replace(" ", "_") + "_component.py"
    
    # Create component template
    template = f'''from engine.core.component import Component

class {class_name}(Component):
    """
    {component_name} component for entities.
    
    Add your component documentation here.
    """
    
    def __init__(self):
        # Add your component properties here
        # Example:
        # self.value = 100
        # self.max_value = 100
        pass
    
    # Add your component methods here
    # Example:
    # def modify_value(self, amount):
    #     self.value = max(0, min(self.max_value, self.value + amount))
    #     return self.value
'''
    
    # Save to engine components directory or ask where to save
    print_info(f"Component template created for {class_name}")
    print_info("Template content:")
    print(template)
    print_warning("Save this template to the appropriate components directory")
    
    return True

def create_new_system():
    """Create a new system template."""
    print_header("Creating New System")
    
    system_name = input("System name (e.g., 'Health'): ").strip()
    if not system_name:
        print_error("System name required")
        return False
    
    # Sanitize system name
    class_name = system_name.replace(" ", "").title() + "System"
    file_name = system_name.lower().replace(" ", "_") + "_system.py"
    
    # Create system template
    template = f'''from engine.core.system import System

class {class_name}(System):
    """
    {system_name} system for processing entities.
    
    Add your system documentation here.
    """
    
    def __init__(self, world):
        super().__init__(world)
        # Add system initialization here
    
    def update(self, dt):
        """
        Update method called every frame.
        dt: delta time since last frame.
        """
        # Get entities with required components
        # entities = self.world.get_entities_with_components(ComponentType)
        
        # Process entities
        # for entity in entities:
        #     component = self.world.get_component(entity.id, ComponentType)
        #     if component:
        #         # Process component
        #         pass
        
        pass
    
    # Optional lifecycle methods:
    # def on_entity_added(self, entity_id):
    #     pass
    #     
    # def on_component_added(self, entity_id, component_instance):
    #     pass
    #     
    # def on_entity_removed(self, entity_id, entity_components):
    #     pass
    #     
    # def on_component_removed(self, entity_id, component_instance):
    #     pass
'''
    
    print_info(f"System template created for {class_name}")
    print_info("Template content:")
    print(template)
    print_warning("Save this template to the appropriate systems directory")
    
    return True

def create_new_example():
    """Create a new example/demo template."""
    print_header("Creating New Example")
    
    example_name = input("Example name (e.g., 'Sprite Animation Demo'): ").strip()
    if not example_name:
        print_error("Example name required")
        return False
    
    # Sanitize example name
    safe_name = "".join(c for c in example_name if c.isalnum() or c in ('_', '-', ' ')).lower().replace(' ', '_')
    file_name = safe_name + "_demo.py"
    
    examples_dir = get_examples_dir()
    demos_dir = os.path.join(examples_dir, "demos")
    os.makedirs(demos_dir, exist_ok=True)
    
    example_path = os.path.join(demos_dir, file_name)
    
    if os.path.exists(example_path):
        print_error(f"Example already exists: {example_path}")
        return False
    
    # Create example template
    template = f'''#!/usr/bin/env python3
"""
{example_name}

Description of what this example demonstrates.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from direct.showbase.ShowBase import ShowBase
from direct.showbase.ShowBaseGlobal import globalClock
from panda3d.core import Vec2, loadPrcFileData

# Engine imports
from engine.core.system import World
from engine.graphics.components.transform_component import TransformComponent
from engine.graphics.components.sprite_component import SpriteComponent
from engine.graphics.systems.render_system import RenderSystem

# Set window properties
loadPrcFileData("", "win-size 800 600")
loadPrcFileData("", "window-title {example_name}")

class {example_name.replace(' ', '').replace('-', '').title()}(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        print("🎮 {example_name} started!")
        
        # Set background
        self.setBackgroundColor(0.2, 0.2, 0.2)
        
        # Create world and systems
        self.world = World()
        self.render_system = RenderSystem(self.world, self)
        self.world.add_system(self.render_system)
        
        # Setup demo
        self.setup_demo()
        
        # Start update loop
        self.taskMgr.add(self.update, "update")
    
    def setup_demo(self):
        """Setup the demonstration."""
        print("Setting up demo...")
        
        # Add your demo setup here
        # Example:
        # entity = self.world.create_entity("demo_entity")
        # self.world.add_component(entity.id, TransformComponent(x=0.0, y=0.0))
        
        print("Demo setup complete!")
    
    def update(self, task):
        """Update loop."""
        dt = globalClock.getDt()
        self.world.update(dt)
        
        # Add your demo logic here
        
        return task.cont

if __name__ == '__main__':
    demo = {example_name.replace(' ', '').replace('-', '').title()}()
    demo.run()
'''
    
    with open(example_path, 'w') as f:
        f.write(template)
    
    print_success(f"Example created: {example_path}")
    print_info(f"To run: python {example_path}")
    
    return True

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Project Generator Tool")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # New game command
    game_parser = subparsers.add_parser('new-game', help='Create a new game project')
    game_parser.add_argument('name', help='Name of the new game')
    
    # New component command
    subparsers.add_parser('new-component', help='Create a new component template')
    
    # New system command
    subparsers.add_parser('new-system', help='Create a new system template')
    
    # New example command
    subparsers.add_parser('new-example', help='Create a new example/demo template')
    
    # New test command
    subparsers.add_parser('new-test', help='Create a new test template for component/system')
    
    # Templates command
    templates_parser = subparsers.add_parser('templates', help='List available templates')
    templates_parser.add_argument('--type', choices=['game', 'component', 'system', 'scene', 'example', 'test'], help='Type of template to list')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    commands = {
        'new-game': lambda: create_new_game(args.name),
        'new-component': create_new_component,
        'new-system': create_new_system,
        'new-example': create_new_example,
        'new-test': lambda: (print("New test template creation not implemented yet."), False)[1],
        'templates': lambda: (print("Available templates:\n- Platformer\n- Shooter\n- RPG\n- Puzzle\n- Minimal"), True)[1]
    }
    
    if args.command not in commands:
        print_error(f"Unknown command: {args.command}")
        parser.print_help()
        return 1
    success = commands[args.command]()
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())
