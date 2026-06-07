# tests/fixtures/__init__.py
"""
Test fixtures and utilities for 2D Game Engine tests

Provides:
- Shared test data
- Mock objects and utilities
- Test asset creation helpers
- Common test setup functions
"""

from panda3d.core import Vec2
import os
import tempfile

class MockShowBase:
    """Mock ShowBase for testing without creating windows."""
    def __init__(self):
        self.loader = MockLoader()
        self.aspect2d = MockNodePath("aspect2d")
        self.taskMgr = MockTaskManager()
        
class MockLoader:
    """Mock loader for testing."""
    def loadTexture(self, path):
        # Return a mock texture object
        return MockTexture()

class MockTexture:
    """Mock texture for testing."""
    def __init__(self):
        self.x_size = 64
        self.y_size = 64
    
    def getXSize(self):
        return self.x_size
    
    def getYSize(self):
        return self.y_size

class MockNodePath:
    """Mock NodePath for testing."""
    def __init__(self, name="mock_node"):
        self.name = name
        self.children = []
        self.position = Vec2(0, 0)
        self.scale = Vec2(1, 1)
        self.rotation = 0.0
        self.color = (1, 1, 1, 1)
        
    def getName(self):
        return self.name
        
    def setPos(self, x, y, z=0):
        self.position = Vec2(x, z)
        
    def setScale(self, x, y=None, z=None):
        if y is None:
            self.scale = Vec2(x, x)
        else:
            self.scale = Vec2(x, y)
            
    def setR(self, rotation):
        self.rotation = rotation
        
    def setColor(self, r, g=None, b=None, a=1):
        if g is None:
            self.color = r
        else:
            self.color = (r, g, b, a)
            
    def removeNode(self):
        pass
        
    def reparentTo(self, parent):
        if hasattr(parent, 'children'):
            parent.children.append(self)
            
    def getChildren(self):
        return self.children
        
    def find(self, pattern):
        return MockNodePath("not_found")
        
    def isEmpty(self):
        return self.name == "not_found"
        
    def getTexture(self):
        return MockTexture()
        
    def setTexture(self, texture):
        pass
        
    def setTransparency(self, mode):
        pass

class MockTaskManager:
    """Mock task manager for testing."""
    def add(self, task, name):
        pass

def create_test_world():
    """Create a world instance for testing."""
    from engine.core.system import World
    return World()

def create_test_entity(world, name="test_entity"):
    """Create a test entity with common components."""
    from engine.graphics.components.transform_component import TransformComponent
    entity = world.create_entity(name)
    world.add_component(entity.id, TransformComponent())
    return entity

def get_test_asset_path(filename):
    """Get path to test asset, creating if needed."""
    test_assets_dir = os.path.join(os.path.dirname(__file__), "test_assets")
    return os.path.join(test_assets_dir, filename)

def create_temp_test_file(content="test", suffix=".txt"):
    """Create a temporary test file."""
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False)
    temp_file.write(content)
    temp_file.close()
    return temp_file.name
