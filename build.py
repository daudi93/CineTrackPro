#!/usr/bin/env python3
"""
Build script for CineTrack Pro Blender extension
Run: python build.py
"""

import os
import subprocess
import sys

def main():
    # Check if we're in the right directory
    if not os.path.exists("blender_manifest.toml"):
        print("Error: blender_manifest.toml not found!")
        print("Run this script from the extension root directory")
        sys.exit(1)
    
    # Find Blender executable
    blender_paths = [
        "blender",  # if in PATH
        "C:/Program Files/Blender Foundation/Blender 4.2/blender.exe",  # Windows
        "/Applications/Blender.app/Contents/MacOS/Blender",  # macOS
        "/usr/bin/blender",  # Linux
    ]
    
    blender_exe = None
    for path in blender_paths:
        try:
            subprocess.run([path, "--version"], capture_output=True)
            blender_exe = path
            break
        except FileNotFoundError:
            continue
    
    if not blender_exe:
        print("Error: Could not find Blender executable")
        print("Please specify the path manually")
        sys.exit(1)
    
    print(f"Using Blender: {blender_exe}")
    
    # Build extension
    print("\nBuilding extension...")
    result = subprocess.run([blender_exe, "--command", "extension", "build"])
    
    if result.returncode == 0:
        print("\n✅ Build successful!")
        print("Extension file created: cinetrack_pro-2.1.0.zip")
        
        # Validate
        print("\nValidating extension...")
        subprocess.run([blender_exe, "--command", "extension", 
                       "validate", "cinetrack_pro-2.1.0.zip"])
    else:
        print("\n❌ Build failed")
        sys.exit(1)

if __name__ == "__main__":
    main()