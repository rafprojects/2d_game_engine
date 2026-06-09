# 2D Game Engine

A versatile 2D game engine built with Python and Panda3D, using an Entity-Component-System (ECS) architecture. This engine aims to provide a flexible foundation for creating a variety of 2D games, such as top-down RPGs, vertical shooters, and side-scrolling action games.

## Sprite Animation System

The engine includes (or will include) a powerful sprite animation system that supports:

- Static sprites with position, scaling, and layering
- Animated sprites using sprite sheets
- Multiple animations per entity with seamless transitions
- Full control over animation playback (play, pause, stop, reset)
- Support for looping and non-looping animations

## Table of Contents

- [2D Game Engine](#2d-game-engine)
  - [Table of Contents](#table-of-contents)
  - [Introduction](#introduction)
  - [Core Concepts (ECS)](#core-concepts-ecs)
    - [Entities](#entities)
    - [Components](#components)
    - [Systems](#systems)
    - [World](#world)
    - [Events](#events)
  - [Getting Started](#getting-started)
    - [Prerequisites](#prerequisites)
    - [Installation](#installation)
    - [Cartridge Quick Start (Recommended)](#cartridge-quick-start-recommended)
    - [Running an Example (Legacy Path)](#running-an-example-legacy-path)
  - [Engine Architecture](#engine-architecture)
    - [Directory Structure](#directory-structure)
    - [Key Modules](#key-modules)
  - [Creating Your First Game](#creating-your-first-game)
    - [1. Setting up the Game Class](#1-setting-up-the-game-class)
    - [2. Creating Entities](#2-creating-entities)
    - [3. Adding Components](#3-adding-components)
    - [4. Implementing Systems](#4-implementing-systems)
    - [5. Game Loop and Updates](#5-game-loop-and-updates)
  - [Available Components](#available-components)
  - [Available Systems](#available-systems)
  - [Event System Usage](#event-system-usage)
  - [Contributing](#contributing)
  - [License](#license)

## Introduction

This engine leverages the power of Panda3D for rendering and low-level operations, while providing a higher-level ECS framework to organize game logic. The ECS pattern promotes decoupling and reusability of game elements.

## Core Concepts (ECS)

The engine is built around the Entity-Component-System pattern.

### Entities

An **Entity** is a general-purpose object, essentially a unique identifier (UUID). Entities themselves don\'t contain data or behavior. They are just "things" in your game world (e.g., the player, an enemy, a bullet, a tile).

### Components

**Components** are plain data containers that define the properties or aspects of an entity. They don\'t have behavior. For example:

- `TransformComponent`: Stores position, rotation, and scale.
- `SpriteComponent`: Stores information needed to render a sprite (image path, layer).
- `HealthComponent`: Stores current and maximum health.

An entity can have multiple components, and components can be added or removed at runtime.

### Systems

**Systems** contain the logic and behavior. They operate on entities that possess a specific set of components. For example:

- `RenderSystem`: Queries for entities with `TransformComponent` and `SpriteComponent` to draw them on the screen.
- `MovementSystem`: Queries for entities with `TransformComponent` and `VelocityComponent` to update their positions.
- `CollisionSystem`: Queries for entities with `TransformComponent` and `ColliderComponent` to detect and resolve collisions.

Systems typically run every frame, processing all relevant entities.

### World

The **World** is the central manager in the ECS. It:

- Creates and destroys entities.
- Adds and removes components from entities.
- Manages all the systems.
- Provides methods to query for entities based on their components.
- Houses the `EventManager`.

### Events

The engine includes an **Event System** (`EventManager` and `Event` base class) to allow different parts of the engine and game to communicate in a decoupled manner. Systems can publish events, and other systems (or game logic) can subscribe to these events to react accordingly.

- Example: `EntityDestroyedEvent`, `ComponentAddedEvent`.

## Getting Started

### Prerequisites

- Python (3.8 or newer recommended)
- Panda3D SDK

### Installation

1. **Clone the repository (if applicable, otherwise skip for local development):**

   ```bash
   # git clone <repository-url>
   # cd <repository-directory>
   ```

2. **Set up a virtual environment (recommended):**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   ```

3. **Install dependencies:**

   The primary dependency is Panda3D. Ensure it\'s installed in your Python environment. You can typically install it via pip:

   ```bash
   pip install panda3d
   ```

   If a `requirements.txt` file is provided with specific versions or other dependencies:

   ```bash
   pip install -r requirements.txt
   ```

### Cartridge Quick Start (Recommended)

The primary way to build and run games is with **cartridges** — self-contained bundles with their own code, assets, and manifest.

```bash
# Run the reference cartridge (The Guardian Legend-inspired demo — canonical P1-G example)
python main.py --cartridge examples/cartridges/tgl_demo

# Or create your own (see P1-D tooling)
py2d-cartridge init "My First Game"
cd my-first-game
py2d-cartridge .                 # pack (optional for dev)
python -m main --cartridge .     # or full path to engine main.py
```

`tgl_demo` (`examples/cartridges/tgl_demo`) is the **canonical reference cartridge** for cartridge system validation (P1-G). It exercises the full modern surface end-to-end (manifest, dir + .car, context, assets, visual hitboxes, CollisionLayer, dev tooling, hot-restart via `reset()`, SaveStateProvider, etc.) and is the live canary for the loader and related polish.

See:
- `docs/guides/cartridge_loader_guide.md`
- `examples/cartridges/tgl_demo/README.md` (dev loop, hotkeys, reset contract, packaging)
- `docs/PHASE1_CARTRIDGE_SYSTEM_POLISH.md` (P1-D scaffolding + P1-G reference validation)

**Cartridges vs. legacy `examples/games/`**: The cartridge model (with `config/cartridge.json`, private `assets/`, `python/<pkg>/entrypoint.py` implementing `initialize(context)`, `py2d-cartridge` pack) is the modern, primary authoring path. The old direct layout under `examples/games/` is still supported for compatibility but is no longer the advertised default.

### Running an Example (Legacy Path)

The `main.py` file can still run a basic built-in demo for quick engine tests.

1. **Ensure you have a test asset:** ...

2. **Run the main script:**

   ```bash
   python main.py
   ```

   For the full modern experience, prefer the cartridge quick start above.

## Engine Architecture

### Directory Structure

```text
.
├── main.py               # Main application entry point
├── README.md             # This file
├── requirements.txt      # Python dependencies
├── assets/               # Game assets (images, sounds, etc.)
└── engine/
    ├── __init__.py
    ├── game_object.py    # (Optional) Higher-level game object wrapper
    ├── core/
    │   ├── __init__.py
    │   ├── component.py      # Base Component class
    │   ├── entity.py         # Entity class
    │   ├── events.py         # EventManager and base Event class
    │   ├── system.py         # Base System class and World class
    │   └── components/       # Core, general-purpose components (e.g., TransformComponent)
    │       └── __init__.py
    │   └── systems/          # Core, general-purpose systems
    │       └── __init__.py
    ├── graphics/
    │   ├── __init__.py
    │   ├── components/       # Graphics-related components (e.g., SpriteComponent)
    │   └── systems/          # Graphics-related systems (e.g., RenderSystem)
    ├── input/
    │   ├── __init__.py
    │   ├── components/       # Input-related components
    │   └── systems/          # Input-related systems
    ├── physics/
    │   ├── __init__.py
    │   ├── components/       # Physics-related components
    │   └── systems/          # Physics-related systems
    └── examples/             # Example game implementations
        └── __init__.py
```

### Key Modules

- **`engine.core.entity`**: Defines the `Entity` class.
- **`engine.core.component`**: Defines the base `Component` class.
- **`engine.core.system`**: Defines the base `System` class and the main `World` class that manages the ECS.
- **`engine.core.events`**: Defines the `EventManager` and base `Event` classes for decoupled communication.
- **`engine.core.components.*`**: Contains fundamental components like `TransformComponent`.
- **`engine.graphics.*`**: Modules for rendering, including `SpriteComponent` and `RenderSystem`.
- **`main.py`**: The entry point that initializes Panda3D (`ShowBase`), the `World`, and adds initial systems and entities.

## Creating Your First Game (Legacy Direct Approach)

**Note (P1-E):** The modern, recommended way to create games is with the **cartridge system** (see "Cartridge Quick Start" above, `py2d-cartridge init`, and `examples/cartridges/tgl_demo`). This section documents the older direct/embedded approach under `examples/games/` for continuity; it is now secondary.

Here's a conceptual guide to building a game with this engine using the legacy layout:

### 1. Setting up the Game Class

Your main game file (e.g., `my_game.py` or by modifying `main.py`) will typically inherit from Panda3D\'s `ShowBase`.

```python
from direct.showbase.ShowBase import ShowBase
from engine.core.system import World
# Import your systems and components

class MyGame(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        self.world = World()

        # Initialize and add your systems to the world
        # self.my_render_system = MyRenderSystem(self.world, self)
        # self.world.add_system(self.my_render_system)
        # self.my_input_system = MyInputSystem(self.world, self) # self for ShowBase input events
        # self.world.add_system(self.my_input_system)

        # Create initial game entities
        self.setup_scene()

        # Add the main game update task
        self.taskMgr.add(self.update_game, "update_game_task")

    def setup_scene(self):
        # Create entities and add components here
        pass

    def update_game(self, task):
        dt = globalClock.getDt() # Delta time
        self.world.update(dt)   # This calls update on all systems in the world
        return task.cont

# if __name__ == \'__main__\':
#     game = MyGame()
#     game.run()
```

### 2. Creating Entities

Use `world.create_entity()` to make new game objects.

```python
player_entity = self.world.create_entity()
enemy_entity = self.world.create_entity()
```

### 3. Adding Components

Define what an entity *is* by adding components to it.

```python
from engine.graphics.components.transform_component import TransformComponent
from engine.graphics.components.sprite_component import SpriteComponent
from engine.input.components.input_component import InputComponent
from panda3d.core import Vec2

# For the player
self.world.add_component(player_entity.id, TransformComponent(position=Vec2(100, 50)))
self.world.add_component(player_entity.id, SpriteComponent(image_path="assets/player_sprite.png", layer=1))
self.world.add_component(player_entity.id, InputComponent(action_map={"move_left": "arrow_left", "move_right": "arrow_right"}))

# For an enemy
self.world.add_component(enemy_entity.id, TransformComponent(position=Vec2(300, 50)))
self.world.add_component(enemy_entity.id, SpriteComponent(image_path="assets/enemy_sprite.png", layer=0))
# ... add HealthComponent, AIComponent, etc.
```

### 4. Implementing Systems

Create new systems by inheriting from `engine.core.system.System`. Implement the `update(self, dt)` method.

```python
from engine.core.system import System

class EnemyAISystem(System):
    def __init__(self, world):
        super().__init__(world)

    def update(self, dt):
        # Get all entities that have, for example, AIComponent and TransformComponent
        # entities = self.world.get_entities_with_components(AIComponent, TransformComponent)
        # for entity in entities:
            # ai_data = self.world.get_component(entity.id, AIComponent)
            # transform = self.world.get_component(entity.id, TransformComponent)
            # ... implement AI logic, potentially modifying transform or other components ...
            pass
```

Remember to add instances of your custom systems to the `World`.

### 5. Game Loop and Updates

The `world.update(dt)` call in your main game loop (`update_game` task) will automatically call the `update(dt)` method of all registered systems in the order they were added.

## Available Components

(This section should be populated as components are finalized)

- **`engine.core.components.TransformComponent(position: Vec2, rotation: float, scale: Vec2)`**: Manages an entity\'s position, rotation, and scale in 2D space.
- **`engine.graphics.components.SpriteComponent(image_path: str, layer: int, color: Vec4, opacity: float)`**: Defines how an entity is rendered as a sprite. `panda_node` attribute is used internally by `RenderSystem`.
- **`engine.input.components.InputComponent(action_map: Dict[str, str])`**: Manages input actions for an entity. `action_map` maps custom action names to Panda3D event strings (e.g., {"move_left": "arrow_left"}). The `InputSystem` updates its `action_active`, `action_just_pressed`, and `action_just_released` dictionaries.

## Available Systems

(This section should be populated as systems are finalized)

- **`engine.graphics.systems.RenderSystem`**: Handles rendering of entities with `TransformComponent` and `SpriteComponent`. Manages Panda3D nodes for sprites.
- **`engine.input.systems.InputSystem(world, showbase_instance)`**: Listens for Panda3D input events based on `InputComponent` action maps and updates the component\'s state (active, just pressed, just released). Requires the Panda3D `ShowBase` instance for event handling.

## Event System Usage

The `World` instance has an `event_manager` attribute.

```python
# Publishing an event (e.g., from within a system)
# from engine.core.events import MyCustomEvent
# event = MyCustomEvent(some_data="hello")
# self.world.event_manager.publish(event)

# Subscribing to an event (e.g., in a system\'s __init__)
# def my_event_handler(self, event_data):
#     print(f"Event received: {event_data.some_data}")
#
# self.world.event_manager.subscribe(MyCustomEvent, self.my_event_handler)
```

## Contributing

Details on how to contribute to the engine development (e.g., coding standards, pull request process) will be added here.

## License

This project is licensed under the [MIT License](LICENSE.txt) - see the LICENSE.txt file for details (assuming MIT, you\'ll need to add this file).
