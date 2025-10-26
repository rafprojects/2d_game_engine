#!/usr/bin/env python3
"""
Asset Management CLI Tool

This tool provides utilities for managing game assets including:
- Sprite sheet processing (integration with external sprite tools package)
- Asset validation and optimization
- Asset directory organization
- Batch processing operations

Usage:
    python -m tools.cli.asset_tools [command] [options]
    py2d-assets [command] [options]  # When installed
    
Commands:
    validate    - Validate assets in the assets directory
    organize    - Organize assets into proper subdirectories
    sprite      - Sprite sheet operations (requires external sprite package)
    optimize    - Optimize assets for game use
    list        - List all assets with metadata
    clean       - Remove unused or orphaned assets

Examples:
    py2d-assets validate assets/
    py2d-assets sprite create input.png --frames 8x4 --output sprites/
    py2d-assets organize assets/ --by-type
"""

import argparse
import os
import sys

# Import CLI utilities
try:
    from tools.cli import (
        print_header, print_success, print_error, print_warning, print_info,
        get_project_root, get_assets_dir
    )
except ImportError:
    # Fallback if running directly
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from tools.cli import (
        print_header, print_success, print_error, print_warning, print_info,
        get_project_root, get_assets_dir
    )

def validate_assets():
    """Validate assets in the assets directory."""
    print_header("Asset Validation")
    
    assets_dir = get_assets_dir()
    if not os.path.exists(assets_dir):
        print_error(f"Assets directory not found: {assets_dir}")
        return False
    
    # Find all asset files
    asset_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tga', '.wav', '.ogg', '.mp3'}
    asset_files = []
    
    for root, dirs, files in os.walk(assets_dir):
        for file in files:
            if any(file.lower().endswith(ext) for ext in asset_extensions):
                asset_files.append(os.path.join(root, file))
    
    print_info(f"Found {len(asset_files)} asset files")
    
    # Basic validation
    issues = []
    for asset_file in asset_files:
        # Check file size
        file_size = os.path.getsize(asset_file)
        if file_size == 0:
            issues.append(f"Empty file: {asset_file}")
        elif file_size > 10 * 1024 * 1024:  # 10MB
            issues.append(f"Large file (>{10}MB): {asset_file}")
    
    if issues:
        print_warning(f"Found {len(issues)} issues:")
        for issue in issues:
            print(f"  • {issue}")
    else:
        print_success("All assets passed validation")
    
    return len(issues) == 0

def organize_assets():
    """Organize assets into proper subdirectories."""
    print_header("Asset Organization")
    
    assets_dir = get_assets_dir()
    if not os.path.exists(assets_dir):
        print_error(f"Assets directory not found: {assets_dir}")
        return False
    
    # Create standard subdirectories
    subdirs = ['sprites', 'textures', 'audio', 'fonts', 'data']
    for subdir in subdirs:
        subdir_path = os.path.join(assets_dir, subdir)
        if not os.path.exists(subdir_path):
            os.makedirs(subdir_path)
            print_success(f"Created directory: {subdir}")
    
    print_info("Asset directory structure organized")
    return True

def sprite_operations():
    """Placeholder for sprite sheet operations using external package."""
    print_header("Sprite Sheet Operations")
    print_warning("This feature requires integration with your external sprite tools package")
    print_info("Placeholder for operations:")
    print("  • Sprite sheet creation from individual images")
    print("  • Sprite sheet splitting into individual frames")
    print("  • Animation data generation")
    print("  • Sprite optimization and compression")
    print()
    print_info("To integrate your sprite tools:")
    print("  1. Add import for your sprite package in this function")
    print("  2. Create command-line interface for sprite operations")
    print("  3. Add sprite validation and processing workflows")
    
    # TODO: Integrate external sprite tools package
    # Example placeholder:
    # try:
    #     import your_sprite_package
    #     your_sprite_package.run_cli_operations()
    # except ImportError:
    #     print_error("Sprite tools package not found")
    #     return False
    
    return True

def optimize_assets():
    """Optimize assets for game use."""
    print_header("Asset Optimization")
    
    assets_dir = get_assets_dir()
    if not os.path.exists(assets_dir):
        print_error(f"Assets directory not found: {assets_dir}")
        return False
    
    print_info("Optimization suggestions:")
    print("  • Convert large PNGs to appropriate formats")
    print("  • Ensure power-of-2 texture dimensions where possible")
    print("  • Compress audio files appropriately")
    print("  • Remove unused assets")
    print()
    print_warning("Automatic optimization not yet implemented")
    print_info("Manual optimization recommended for now")
    
    return True

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Asset Management Tool")
    parser.add_argument('command', 
                       choices=['validate', 'organize', 'sprite', 'optimize'],
                       help='Command to execute')
    
    args = parser.parse_args()
    
    commands = {
        'validate': validate_assets,
        'organize': organize_assets,
        'sprite': sprite_operations,
        'optimize': optimize_assets
    }
    
    success = commands[args.command]()
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())
