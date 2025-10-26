# tools/cli/__init__.py
"""
Command-line interface tools for 2D Game Engine

Available commands:
- asset_tools: Sprite sheet and asset management utilities
- project_gen: Project scaffolding and template generation
- dev_setup: Development environment configuration
- build_tools: Build and packaging utilities
"""

import sys
import os

# Add project root to path for CLI tools
CLI_DIR = os.path.dirname(os.path.abspath(__file__))
TOOLS_DIR = os.path.dirname(CLI_DIR)
PROJECT_ROOT = os.path.dirname(TOOLS_DIR)
sys.path.insert(0, PROJECT_ROOT)

def get_project_root():
    """Get the project root directory."""
    return PROJECT_ROOT

def get_assets_dir():
    """Get the project assets directory."""
    return os.path.join(PROJECT_ROOT, "assets")

def get_examples_dir():
    """Get the project examples directory."""
    return os.path.join(PROJECT_ROOT, "examples")

# CLI utility functions
def print_header(title):
    """Print a formatted header for CLI tools."""
    print("=" * 60)
    print(f"  {title}")
    print("=" * 60)

def print_success(message):
    """Print a success message."""
    print(f"✅ {message}")

def print_error(message):
    """Print an error message."""
    print(f"❌ {message}")

def print_warning(message):
    """Print a warning message."""
    print(f"⚠️  {message}")

def print_info(message):
    """Print an info message."""
    print(f"ℹ️  {message}")
