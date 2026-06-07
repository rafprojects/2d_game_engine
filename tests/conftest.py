# tests/conftest.py
"""
pytest configuration and shared fixtures for 2D Game Engine tests
"""

import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))

# These files cannot be collected by pytest:
# - The ShowBase scripts spin up a Panda3D window at import time (headless CI-hostile).
# - The asset pipeline integration test uses an outdated ResourceManager API that
#   requires a live ShowBase/loader; it cannot run in a unit-test environment.
collect_ignore = [
    os.path.join(_HERE, "integration", "test_final_implementation.py"),
    os.path.join(_HERE, "integration", "test_critical_fixes.py"),
    os.path.join(_HERE, "integration", "test_asset_pipeline_integration.py"),
]

# Add project root to path
TEST_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(TEST_DIR)
sys.path.insert(0, PROJECT_ROOT)

@pytest.fixture
def mock_world():
    """Provide a clean World instance for testing."""
    from engine.core.system import World
    return World()

@pytest.fixture  
def mock_showbase():
    """Provide a mock ShowBase for testing without graphics."""
    from tests.fixtures import MockShowBase
    return MockShowBase()

@pytest.fixture
def sample_entity(mock_world):
    """Provide a test entity with basic components."""
    from tests.fixtures import create_test_entity
    return create_test_entity(mock_world)

# Configure pytest for this project
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow (may create windows)")
    config.addinivalue_line("markers", "integration: marks tests as integration tests") 
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "graphics: marks tests that require graphics context")
