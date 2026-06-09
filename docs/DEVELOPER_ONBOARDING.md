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

### **2. Run Your First Example**
```bash
# Make sure you have a test image
cp assets/player.png assets/  # Or create a simple PNG

# Run the main demo
python main.py

# Try an example demo
python examples/demos/basic_sprite_demo.py
```

### **3. Explore the Structure**
- **Engine Core**: `engine/` - The main game engine modules
- **Examples**: `examples/` - Learn from working code
- **Documentation**: `docs/` - Comprehensive guides
- **Tools**: `tools/cli/` - Development utilities

## 📚 **Learning Path**

### **Beginner (New to the engine)**
1. **Read** [`README.md`](../README.md) for project overview
2. **Try** examples in `examples/tutorials/`
3. **Follow** sprite animation guide: [`sprite_animation_guide.md`](sprite_animation_guide.md)
4. **Build** your first simple game with `py2d-engine new-game`

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
```bash
# Generate component template
py2d-engine new-component MyComponent --with-test

# Generate system template
py2d-engine new-system MySystem --events

# Add to appropriate engine module
# Write unit tests
# Update documentation
# Test with examples
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
