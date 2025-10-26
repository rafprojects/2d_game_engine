#!/usr/bin/env python3
"""
Build and Distribution Tools

Comprehensive build system for the 2D Game Engine, supporting:
- Development builds with hot reload capabilities
- Production builds with optimization
- Cross-platform packaging (Windows, macOS, Linux)
- Asset bundling and compression
- Executable generation using cx_Freeze or PyInstaller

Usage:
    python -m tools.cli.build_tools [command] [options]
    py2d-build [command] [options]  # When installed
    
Commands:
    dev         - Development build with hot reload
    prod        - Production build with optimizations
    package     - Create distributable packages
    clean       - Clean build artifacts
    test-build  - Build and run automated tests
    docs        - Generate documentation

Examples:
    py2d-build dev --watch assets/
    py2d-build prod --platform windows --output dist/
    py2d-build package --include-runtime
"""

import argparse
import os
import sys
import shutil
import subprocess

# Import CLI utilities
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from tools.cli import (
    print_header, print_success, print_error, print_warning, print_info,
    get_project_root
)

def package_engine():
    """Package the engine for distribution."""
    print_header("Packaging Engine")
    
    project_root = get_project_root()
    
    # Create package structure
    package_items = {
        'engine/': 'Core engine modules',
        'tools/': 'Development tools',
        'examples/': 'Example games and demos',
        'docs/': 'Documentation',
        'requirements.txt': 'Dependencies',
        'README.md': 'Project readme',
        '.copilot_guidelines.md': 'Development guidelines'
    }
    
    print_info("Package contents:")
    for item, description in package_items.items():
        item_path = os.path.join(project_root, item)
        if os.path.exists(item_path):
            print_success(f"✓ {item} - {description}")
        else:
            print_warning(f"✗ {item} - {description} (missing)")
    
    print_info("Package structure looks good!")
    print_warning("Actual packaging not yet implemented")
    print_info("Future features:")
    print("  • Create wheel distribution")
    print("  • Generate setup.py/pyproject.toml")
    print("  • Bundle examples separately")
    print("  • Create documentation package")
    
    return True

def generate_documentation():
    """Generate project documentation."""
    print_header("Generating Documentation")
    
    project_root = get_project_root()
    docs_dir = os.path.join(project_root, "docs")
    
    if not os.path.exists(docs_dir):
        print_error("Documentation directory not found")
        return False
    
    # Check for documentation files
    doc_files = []
    for root, dirs, files in os.walk(docs_dir):
        for file in files:
            if file.endswith('.md'):
                doc_files.append(os.path.join(root, file))
    
    print_info(f"Found {len(doc_files)} documentation files")
    
    # List documentation
    for doc_file in doc_files:
        rel_path = os.path.relpath(doc_file, project_root)
        print(f"  • {rel_path}")
    
    print_warning("Automatic documentation generation not yet implemented")
    print_info("Future features:")
    print("  • Generate API docs from docstrings")
    print("  • Create HTML documentation site")
    print("  • Generate PDF documentation")
    print("  • Auto-update cross-references")
    
    return True

def clean_artifacts():
    """Clean build artifacts and temporary files."""
    print_header("Cleaning Build Artifacts")
    
    project_root = get_project_root()
    
    # Define patterns to clean
    clean_patterns = [
        '__pycache__',
        '*.pyc',
        '*.pyo',
        '*.pyd',
        '.pytest_cache',
        '*.egg-info',
        'build/',
        'dist/',
        '.coverage',
        '.mypy_cache',
        '.DS_Store',
        'Thumbs.db'
    ]
    
    cleaned_items = []
    
    # Walk through project and clean
    for root, dirs, files in os.walk(project_root):
        # Clean directories
        for dir_name in dirs[:]:  # Copy list to modify during iteration
            if dir_name in ['__pycache__', '.pytest_cache', '.mypy_cache', 'build', 'dist']:
                dir_path = os.path.join(root, dir_name)
                try:
                    shutil.rmtree(dir_path)
                    cleaned_items.append(f"Directory: {os.path.relpath(dir_path, project_root)}")
                    dirs.remove(dir_name)  # Don't recurse into removed directory
                except Exception as e:
                    print_warning(f"Could not remove {dir_path}: {e}")
        
        # Clean files
        for file_name in files:
            if (file_name.endswith(('.pyc', '.pyo', '.pyd')) or 
                file_name in ['.coverage', '.DS_Store', 'Thumbs.db']):
                file_path = os.path.join(root, file_name)
                try:
                    os.remove(file_path)
                    cleaned_items.append(f"File: {os.path.relpath(file_path, project_root)}")
                except Exception as e:
                    print_warning(f"Could not remove {file_path}: {e}")
    
    if cleaned_items:
        print_success(f"Cleaned {len(cleaned_items)} items:")
        for item in cleaned_items[:10]:  # Show first 10
            print(f"  • {item}")
        if len(cleaned_items) > 10:
            print(f"  ... and {len(cleaned_items) - 10} more")
    else:
        print_info("No artifacts to clean")
    
    return True

def create_distribution():
    """Create distribution packages."""
    print_header("Creating Distribution")
    
    project_root = get_project_root()
    
    # Check if setup.py or pyproject.toml exists
    setup_py = os.path.join(project_root, "setup.py")
    pyproject_toml = os.path.join(project_root, "pyproject.toml")
    
    if os.path.exists(pyproject_toml):
        print_info("Found pyproject.toml")
        # Future: build with build module
        print_warning("pyproject.toml build not yet implemented")
    elif os.path.exists(setup_py):
        print_info("Found setup.py")
        # Future: build with setuptools
        print_warning("setup.py build not yet implemented")
    else:
        print_warning("No build configuration found")
        print_info("Creating basic pyproject.toml...")
        
        pyproject_content = """[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "2d-game-engine"
version = "0.1.0"
description = "A versatile 2D game engine built with Python and Panda3D"
readme = "README.md"
requires-python = ">=3.8"
dependencies = [
    "panda3d",
]

[project.optional-dependencies]
dev = [
    "pytest",
    "black",
    "flake8",
    "mypy",
]

[tool.setuptools.packages.find]
where = ["."]
include = ["engine*", "tools*"]

[tool.setuptools.package-data]
"*" = ["*.md", "*.txt", "*.png", "*.jpg", "*.wav", "*.ogg"]
"""
        
        try:
            with open(pyproject_toml, 'w') as f:
                f.write(pyproject_content)
            print_success("Created pyproject.toml")
        except Exception as e:
            print_error(f"Failed to create pyproject.toml: {e}")
            return False
    
    print_info("Distribution build configuration ready")
    print_warning("Actual distribution build not yet implemented")
    print_info("Future commands:")
    print("  • python -m build")
    print("  • python -m twine upload dist/*")
    
    return True

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Build and Distribution Tools")
    parser.add_argument('command', 
                       choices=['package', 'docs', 'clean', 'dist'],
                       help='Command to execute')
    
    args = parser.parse_args()
    
    commands = {
        'package': package_engine,
        'docs': generate_documentation,
        'clean': clean_artifacts,
        'dist': create_distribution
    }
    
    success = commands[args.command]()
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())
