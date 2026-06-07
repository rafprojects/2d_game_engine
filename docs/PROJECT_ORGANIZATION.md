# Project Organization Guide

*Last Updated: July 4, 2025*

## 📋 **Overview**

This document serves as the master navigation guide for the 2D Game Engine project. It provides a comprehensive overview of the project structure, development workflows, and resource locations.

## 📁 **Project Structure Overview**

```
2d_game_engine/
├── 📂 engine/                    # Core game engine modules
│   ├── 📂 core/                  # Essential ECS components
│   ├── 📂 graphics/              # Rendering and visual systems
│   ├── 📂 input/                 # Input handling and bindings
│   ├── 📂 physics/               # Collision and physics systems
│   └── 📂 animation/             # Animation and tweening systems
├── 📂 tools/                     # Development tools and utilities
│   └── 📂 cli/                   # Command-line interface tools
├── 📂 tests/                     # Test suite organization
│   ├── 📂 integration/           # Full workflow integration tests
│   ├── 📂 unit/                  # pytest unit tests
│   └── 📂 fixtures/              # Test utilities and data
├── 📂 examples/                  # Demos and example implementations
│   ├── 📂 demos/                 # Feature demonstration scripts
│   └── 📂 games/                 # Complete mini-game examples
├── 📂 docs/                      # Project documentation
│   ├── 📂 guides/                # Topic-specific guides
│   ├── 📂 api/                   # API reference documentation
│   └── 📂 tutorials/             # Step-by-step tutorials
├── 📂 assets/                    # Shared project assets
└── 📂 temp/                      # Temporary files and experiments
```

## 🎯 **Quick Navigation**

### **🔧 For Developers**
- **[Engine Core](engine/core/)** - ECS architecture, components, systems
- **[Development Tools](tools/cli/)** - CLI utilities for development
- **[Test Suite](tests/)** - Testing strategy and test files
- **[Project Roadmap](docs/PROJECT_ROADMAP.md)** - Development priorities

### **🎮 For Game Creators**
- **[Getting Started](README.md)** - Basic setup and first game
- **[Examples](examples/)** - Working demos and mini-games
- **[Sprite Animation Guide](docs/sprite_animation_guide.md)** - Animation system
- **[Movement System Guide](docs/movement_tweening_guide.md)** - Movement and tweening

### **📚 For Contributors**
- **[Guidelines](.copilot_guidelines.md)** - Development standards
- **[Architecture Docs](docs/guides/)** - System design documentation
- **[API Reference](docs/api/)** - Component and system APIs

## 🏗️ **Core Architecture**

### **Entity-Component-System (ECS)**
The engine uses a professional ECS architecture:

- **Entities** (`engine/core/system.py`) - Game objects with unique IDs
- **Components** (`engine/*/components/`) - Data containers (Transform, Sprite, Input, etc.)
- **Systems** (`engine/*/systems/`) - Logic processors (Render, Movement, Input, etc.)
- **World** - Manages entities, components, and systems

### **Module Organization**

#### **🎨 Graphics Module** (`engine/graphics/`)
- **Components**: `SpriteComponent` - Visual representation
- **Systems**: `RenderSystem` - Panda3D rendering integration  
- **Utilities**: `SpriteSheet` - Animation frame management

#### **🎮 Input Module** (`engine/input/`)
- **Components**: `InputComponent` - Action-based input bindings
- **Systems**: `InputSystem` - Multi-device input processing
- **Utilities**: `InputBinding` - Flexible input mapping

#### **⚡ Physics Module** (`engine/physics/`)
- **Components**: `ColliderComponent`, `RigidBodyComponent`
- **Systems**: `CollisionSystem` - Collision detection and response

#### **🎭 Animation Module** (`engine/animation/`)
- **Components**: `MovementTweenComponent` - Visual effects
- **Systems**: Tweening manager and easing functions

## 🧪 **Testing Strategy**

### **Test Organization**
- **Integration Tests** (`tests/integration/`) - Full workflow validation
- **Unit Tests** (`tests/unit/`) - Individual component testing
- **Fixtures** (`tests/fixtures/`) - Shared test utilities

### **Running Tests**
```bash
# All tests with pytest
python -m pytest tests/ -v

# Unit tests only
python -m pytest tests/unit/ -v

# Integration tests only  
python -m pytest tests/integration/ -v

# Individual integration test
python tests/integration/test_movement_system.py
```

## 🛠️ **Development Tools**

### **CLI Tools** (`tools/cli/`)
```bash
# Asset management
python -m tools.cli.asset_tools validate
python -m tools.cli.asset_tools organize

# Project generation
python -m tools.cli.project_gen new-game "My Game"
python -m tools.cli.project_gen new-component
python -m tools.cli.project_gen new-system

# Environment setup
python -m tools.cli.dev_setup check
python -m tools.cli.dev_setup install

# Build tools
python -m tools.cli.build_tools clean
python -m tools.cli.build_tools package
```

## 📖 **Documentation Structure**

### **Guides** (`docs/guides/`)
Topic-specific deep-dives:
- Component design patterns
- System interaction best practices
- Performance optimization techniques
- Event system usage

### **Tutorials** (`docs/tutorials/`)
Step-by-step learning:
- Your first 2D game
- Building a platformer
- Advanced animation techniques
- Custom component creation

### **API Reference** (`docs/api/`)
Auto-generated documentation:
- Component APIs
- System interfaces
- Utility functions
- Event types

## 🎯 **Common Tasks**

### **Creating New Components**
1. Add component class in `engine/*/components/`
2. Add to `__init__.py` exports
3. Create unit tests in `tests/unit/`
4. Update documentation

### **Creating New Systems**
1. Add system class in `engine/*/systems/`
2. Register in World initialization
3. Add integration tests
4. Update examples if applicable

### **Adding Examples**
1. Use `tools/cli/project_gen.py new-example`
2. Place in appropriate `examples/` subdirectory
3. Add README with description and controls
4. Test across different platforms

### **Documentation Updates**
1. Update relevant guides when adding features
2. Keep API docs synchronized with code
3. Add cross-references between related docs
4. Update this organization doc for structural changes

## 🚀 **Development Workflow**

### **Getting Started**
1. Clone repository
2. Run `python -m tools.cli.dev_setup check`
3. Install dependencies: `python -m tools.cli.dev_setup install`
4. Run tests: `python -m tools.cli.dev_setup test`

### **Adding Features**
1. Plan component/system design
2. Create unit tests first (TDD)
3. Implement feature with documentation
4. Add integration tests
5. Update examples if needed

### **Quality Assurance**
- All new code should have tests
- Run full test suite before commits
- Keep documentation updated
- Follow established patterns and conventions

## 📋 **File Naming Conventions**

### **Components**
- File: `component_name_component.py`
- Class: `ComponentNameComponent`
- Example: `transform_component.py` → `TransformComponent`

### **Systems**
- File: `system_name_system.py`
- Class: `SystemNameSystem`
- Example: `render_system.py` → `RenderSystem`

### **Tests**
- Unit tests: `test_component_name.py`
- Integration tests: `test_system_workflow.py`
- Fixtures: `mock_objects.py`, `test_utilities.py`

### **Examples**
- Demos: `feature_name_demo.py`
- Games: In subdirectory with `main.py`

## 🔗 **Cross-References**

### **Related Documents**
- **[Development Roadmap](PROJECT_ROADMAP.md)** - Future development plans
- **[Guidelines](.copilot_guidelines.md)** - Development standards
- **[Sprite Animation Guide](sprite_animation_guide.md)** - Animation system details
- **[Movement Guide](movement_tweening_guide.md)** - Movement and effects

### **External Resources**
- **Panda3D Documentation** - https://docs.panda3d.org/
- **ECS Pattern** - Entity-Component-System architecture
- **Python Testing** - pytest framework

---

## 📞 **Getting Help**

### **Documentation Issues**
- Check this organization guide first
- Look for topic-specific guides in `docs/guides/`
- Review examples in `examples/`

### **Development Issues**
- Run environment check: `python -m tools.cli.dev_setup check`
- Check test results: `python -m tools.cli.dev_setup test`
- Review guidelines in `.copilot_guidelines.md`

### **Feature Requests**
- Check roadmap for planned features
- Review existing examples for similar functionality
- Consider creating prototype in `temp/` directory

---

*This document is updated regularly. Last review: July 4, 2025*
