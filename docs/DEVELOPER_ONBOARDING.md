# Developer Onboarding Guide

*Welcome to the 2D Game Engine project!*

## 🚀 **Quick Start (5 minutes)**

### **1. Environment Setup**
```bash
# Clone the repository
git clone <repository-url>
cd 2d_game_engine

# Set up development environment
python -m tools.cli.dev_setup init

# Verify installation
python -m tools.cli.dev_setup check
```

### **2. Run Your First Cartridge (Recommended)**
```bash
# Run the reference cartridge (modern primary path — canonical P1-G example)
python main.py --cartridge examples/cartridges/tgl_demo

# Create a new one with the scaffold (P1-D)
py2d-cartridge init "My Game"
cd my-game
python /path/to/2d_game_engine/main.py --cartridge .   # run from the engine source checkout root
# (main.py is not an importable module; `python -m main` only works from the engine tree)
```

`tgl_demo` is the canonical reference exercising the complete cartridge surface (manifest, pack/load, hot-restart, providers, dev tooling, etc.). Use it to validate your understanding and as the model for new work.

(For the legacy direct demo: `python main.py` or demos in `examples/demos/`.)

### **3. Explore the Structure**
- **Engine Core**: `engine/` - The main game engine modules
- **Cartridges** (primary): `examples/cartridges/` - Self-contained games (config/cartridge.json + private assets + python package with entrypoint)
- **Legacy examples**: `examples/games/` and `examples/demos/`
- **Documentation**: `docs/` - Comprehensive guides (start with cartridge_loader_guide.md)
- **Tools**: `tools/cli/` - Development utilities (py2d-cartridge is now the main authoring CLI)

## 📚 **Learning Path**

### **Beginner (New to the engine)**
1. **Read** the "Cartridge Quick Start" in [`README.md`](../README.md)
2. **Run** a cartridge: `python main.py --cartridge examples/cartridges/tgl_demo`
3. **Create** one: `py2d-cartridge init "My First Cartridge"`
4. **Follow** `docs/guides/cartridge_loader_guide.md` and the tgl_demo README
5. **(Legacy)** Build with `py2d-engine new-game` only if you need the old embedded layout

### **Intermediate (Ready to contribute)**
1. **Study** the ECS architecture in `engine/core/`
2. **Understand** component patterns in `engine/*/components/`
3. **Explore** system implementations in `engine/*/systems/`
4. **Review** [`PROJECT_ROADMAP.md`](PROJECT_ROADMAP.md) for contribution opportunities

### **Advanced (Engine development)**
1. **Deep dive** into rendering system (`engine/graphics/systems/`)
2. **Understand** event system (`engine/core/events.py`)
3. **Study** performance optimization techniques
4. **Contribute** to core engine features

## 🛠️ **Development Workflow**

### **Daily Development**
```bash
# Start development session
workon pandas311  # Activate virtual environment

# Check current status
py2d-dev check

# Run tests before making changes
pytest tests/unit tests/integration

# Make your changes...

# Run tests again
pytest tests/unit tests/integration

# Run example to verify
python examples/demos/movement_demo.py
```

### **Creating New Features**
For cartridge-specific code, work inside a cartridge's `python/<slug>/` (components/systems) after `py2d-cartridge init`.

For engine extensions:
```bash
# Generate component template
py2d-engine new-component MyComponent --with-test

# Generate system template
py2d-engine new-system MySystem --events

# Add to appropriate engine module
# Write unit tests
# Update documentation
# Test with examples or a cartridge
```

## 🎯 **Key Concepts**

### **Entity-Component-System (ECS)**
- **Entities** - Game objects (player, enemy, bullet)
- **Components** - Data containers (position, sprite, health)
- **Systems** - Logic processors (movement, rendering, collision)

### **Component Design**
```python
from engine.core.component import Component

class MyComponent(Component):
    def __init__(self, value: float = 0.0):
        self.value = value
```

### **System Design**
```python
from engine.core.system import System

class MySystem(System):
    def update(self, dt: float):
        entities = self.world.get_entities_with_components(MyComponent)
        for entity in entities:
            component = self.world.get_component(entity.id, MyComponent)
            # Process component logic
```

### **Event System**
```python
# Publishing events
self.world.event_manager.publish(MyEvent(data))

# Subscribing to events
self.world.event_manager.subscribe(MyEvent, self.handle_my_event)
```

## 🧪 **Testing Philosophy**

### **Test Categories**
- **Unit Tests** - Individual components and systems
- **Integration Tests** - System interactions
- **Custom Scripts** - Manual testing and debugging
- **Benchmarks** - Performance validation

### **Writing Good Tests**
```python
def test_component_creation():
    """Test that components are created with correct defaults."""
    component = MyComponent()
    assert component.value == 0.0

def test_system_processing():
    """Test that systems process entities correctly."""
    world = World()
    system = MySystem(world)
    # Create test entity with component
    # Run system update
    # Assert expected behavior
```

## 📁 **File Organization**

### **Where to Put New Code**
- **Components** → `engine/{module}/components/`
- **Systems** → `engine/{module}/systems/`
- **Utilities** → `engine/{module}/` (root level)
- **Tests** → `tests/unit/` or `tests/integration/`
- **Examples** → `examples/demos/` or `examples/tutorials/`
- **Tools** → `tools/cli/`

### **Import Patterns**
```python
# For tools accessing engine
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Standard engine imports
from engine.core.system import World, System
from engine.core.component import Component
```

## 🎨 **Code Style**

### **Python Standards**
- **PEP 8** compliance
- **Type hints** where beneficial
- **Docstrings** for public APIs
- **Descriptive variable names**

### **Engine Conventions**
- **Components** end with `Component`
- **Systems** end with `System`
- **Events** end with `Event`
- **Use dataclasses** for simple components

## 🔧 **Common Tasks**

### **Adding a New Module**
1. Create directory: `engine/my_module/`
2. Add `__init__.py` with exports
3. Create `components/` and `systems/` subdirectories
4. Update `engine/__init__.py` if needed

### **Debugging Issues**
1. **Use examples** to isolate problems
2. **Check console output** for errors
3. **Add debug prints** in systems
4. **Use custom test scripts** in `tests/custom/`

### **Performance Optimization**
1. **Profile with benchmarks** in `tests/benchmarks/`
2. **Monitor frame rates** in examples
3. **Use efficient data structures**
4. **Minimize object creation in update loops**

## 📞 **Getting Help**

### **Resources**
- **Documentation** - `docs/` directory
- **Examples** - `examples/` directory
- **Guidelines** - `.copilot_guidelines.md`
- **Roadmap** - `docs/PROJECT_ROADMAP.md`

### **Best Practices**
1. **Read existing code** before writing new code
2. **Follow established patterns** in the codebase
3. **Test thoroughly** with multiple examples
4. **Document your changes** in appropriate guides
5. **Ask questions** when patterns aren't clear

## 🎯 **Next Steps**

### **Your First Contribution**
1. Pick a **small task** from [`PROJECT_ROADMAP.md`](PROJECT_ROADMAP.md)
2. **Create a branch** for your changes
3. **Write tests first** (TDD approach)
4. **Implement the feature**
5. **Update documentation**
6. **Submit a pull request**

### **Becoming a Core Contributor**
1. **Understand the full architecture**
2. **Contribute to multiple modules**
3. **Help with code reviews**
4. **Improve documentation**
5. **Mentor new contributors**

---

*Welcome to the team! We're excited to see what you'll build with the engine.*
