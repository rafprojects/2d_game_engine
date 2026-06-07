# tests/conftest.py
"""
pytest configuration and shared fixtures for 2D Game Engine tests
"""

import pytest
import sys
import os

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
