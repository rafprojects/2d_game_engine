#!/usr/bin/env python3
"""
Development Environment Setup Tool

Comprehensive development environment management for the 2D Game Engine:
- Virtual environment creation and management
- Development dependency installation
- Pre-commit hooks setup
- IDE configuration (VS Code, PyCharm)
- Testing environment configuration
- Development database/asset setup

Usage:
    python -m tools.cli.dev_setup [command] [options]
    py2d-dev [command] [options]  # When installed
    
Commands:
    init        - Initialize complete development environment
    check       - Check development environment status
    install     - Install development dependencies
    venv        - Create/manage virtual environment
    test        - Run full test suite
    hooks       - Setup pre-commit hooks
    ide         - Configure IDE settings
    docs        - Setup documentation environment

Examples:
    py2d-dev init --python 3.11
    py2d-dev check --verbose
    py2d-dev test --coverage
    py2d-dev ide --vscode --pylsp
"""

import argparse
import os
import sys
import subprocess
import platform

# Import CLI utilities
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from tools.cli import (
    print_header, print_success, print_error, print_warning, print_info,
    get_project_root
)

def check_environment():
    """Check development environment setup."""
    print_header("Development Environment Check")
    
    issues = []
    
    # Check Python version
    python_version = sys.version_info
    print_info(f"Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version < (3, 8):
        issues.append("Python 3.8+ required")
    else:
        print_success("Python version OK")
    
    # Check for required packages
    required_packages = ['panda3d']
    
    for package in required_packages:
        try:
            __import__(package)
            print_success(f"{package} installed")
        except ImportError:
            issues.append(f"Missing package: {package}")
            print_error(f"{package} not found")
    
    # Check for optional packages
    optional_packages = ['pytest', 'black', 'flake8']
    
    for package in optional_packages:
        try:
            __import__(package)
            print_success(f"{package} installed (optional)")
        except ImportError:
            print_warning(f"{package} not found (optional)")
    
    # Check project structure
    project_root = get_project_root()
    required_dirs = ['engine', 'tools', 'tests', 'docs', 'examples']
    
    for dir_name in required_dirs:
        dir_path = os.path.join(project_root, dir_name)
        if os.path.exists(dir_path):
            print_success(f"Directory exists: {dir_name}")
        else:
            issues.append(f"Missing directory: {dir_name}")
            print_error(f"Missing directory: {dir_name}")
    
    # Summary
    if issues:
        print_warning(f"Found {len(issues)} issues:")
        for issue in issues:
            print(f"  • {issue}")
        return False
    else:
        print_success("Development environment looks good!")
        return True

def install_dependencies():
    """Install development dependencies."""
    print_header("Installing Development Dependencies")
    
    project_root = get_project_root()
    requirements_file = os.path.join(project_root, "requirements.txt")
    
    if not os.path.exists(requirements_file):
        print_error("requirements.txt not found")
        return False
    
    try:
        # Install main requirements
        print_info("Installing main requirements...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', requirements_file], 
                      check=True)
        print_success("Main requirements installed")
        
        # Install development requirements
        dev_packages = ['pytest', 'black', 'flake8', 'mypy']
        print_info("Installing development packages...")
        
        for package in dev_packages:
            try:
                subprocess.run([sys.executable, '-m', 'pip', 'install', package], 
                              check=True, capture_output=True)
                print_success(f"Installed {package}")
            except subprocess.CalledProcessError:
                print_warning(f"Failed to install {package}")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print_error(f"Installation failed: {e}")
        return False

def create_virtual_environment():
    """Create a virtual environment for the project."""
    print_header("Creating Virtual Environment")
    
    project_root = get_project_root()
    venv_path = os.path.join(project_root, "venv")
    
    if os.path.exists(venv_path):
        print_warning("Virtual environment already exists")
        return True
    
    try:
        print_info("Creating virtual environment...")
        subprocess.run([sys.executable, '-m', 'venv', venv_path], check=True)
        print_success(f"Virtual environment created at: {venv_path}")
        
        # Determine activation script
        if platform.system() == "Windows":
            activate_script = os.path.join(venv_path, "Scripts", "activate.bat")
            print_info("To activate on Windows:")
            print(f"  {activate_script}")
        else:
            activate_script = os.path.join(venv_path, "bin", "activate")
            print_info("To activate on Unix/Mac:")
            print(f"  source {activate_script}")
        
        print_info("After activation, run:")
        print("  python -m tools.cli.dev_setup install")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to create virtual environment: {e}")
        return False

def run_tests():
    """Run the test suite."""
    print_header("Running Test Suite")
    
    project_root = get_project_root()
    tests_dir = os.path.join(project_root, "tests")
    
    if not os.path.exists(tests_dir):
        print_error("Tests directory not found")
        return False
    
    # Try to run pytest first
    try:
        print_info("Running pytest...")
        result = subprocess.run([sys.executable, '-m', 'pytest', tests_dir, '-v'], 
                               capture_output=True, text=True)
        
        if result.returncode == 0:
            print_success("All pytest tests passed!")
            print(result.stdout)
        else:
            print_warning("Some pytest tests failed")
            print(result.stdout)
            print(result.stderr)
            
    except (subprocess.CalledProcessError, FileNotFoundError):
        print_warning("pytest not available, running integration tests manually...")
        
        # Run integration tests manually
        integration_dir = os.path.join(tests_dir, "integration")
        if os.path.exists(integration_dir):
            test_files = [f for f in os.listdir(integration_dir) if f.startswith('test_') and f.endswith('.py')]
            
            for test_file in test_files:
                test_path = os.path.join(integration_dir, test_file)
                print_info(f"Running {test_file}...")
                
                try:
                    result = subprocess.run([sys.executable, test_path], 
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        print_success(f"{test_file} passed")
                    else:
                        print_error(f"{test_file} failed")
                        print(result.stderr)
                except Exception as e:
                    print_error(f"Error running {test_file}: {e}")
    
    return True

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Development Environment Setup")
    parser.add_argument('command', 
                       choices=['init', 'check', 'install', 'venv', 'test', 'hooks', 'ide', 'docs'],
                       help='Command to execute')
    
    args = parser.parse_args()
    
    commands = {
        'check': check_environment,
        'install': install_dependencies,
        'venv': create_virtual_environment,
        'test': run_tests
    }
    
    success = commands[args.command]()
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())
