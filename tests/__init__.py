# tests/__init__.py
"""
Test suite for 2D Game Engine

This package contains:
- integration/: Custom integration tests that test full workflows
- unit/: pytest unit tests for individual components and systems  
- fixtures/: Test data and utilities shared across tests
"""

import os
import sys

# Add project root to path for test imports
TEST_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(TEST_DIR)
sys.path.insert(0, PROJECT_ROOT)
