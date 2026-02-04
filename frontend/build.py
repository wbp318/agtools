#!/usr/bin/env python
"""
AgTools Build Script
Creates a standalone executable using PyInstaller.

Usage:
    python build.py           # Build the executable
    python build.py --clean   # Clean build artifacts first
"""

import os
import sys
import shutil
import subprocess
import argparse
from pathlib import Path

# Get the frontend directory
FRONTEND_DIR = Path(__file__).parent.absolute()
DIST_DIR = FRONTEND_DIR / "dist"
BUILD_DIR = FRONTEND_DIR / "build"
SPEC_FILE = FRONTEND_DIR / "agtools.spec"


def clean():
    """Remove build artifacts."""
    print("Cleaning build artifacts...")

    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
        print(f"  Removed {BUILD_DIR}")

    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
        print(f"  Removed {DIST_DIR}")

    # Remove __pycache__ directories
    for pycache in FRONTEND_DIR.rglob("__pycache__"):
        shutil.rmtree(pycache)
        print(f"  Removed {pycache}")

    print("Clean complete.")


def check_dependencies():
    """Check if required dependencies are installed."""
    print("Checking dependencies...")

    try:
        import PyInstaller
        print(f"  PyInstaller: {PyInstaller.__version__}")
    except ImportError:
        print("  ERROR: PyInstaller not installed. Run: pip install pyinstaller")
        return False

    try:
        import PyQt6
        print(f"  PyQt6: OK")
    except ImportError:
        print("  ERROR: PyQt6 not installed. Run: pip install PyQt6")
        return False

    return True


def build():
    """Build the executable."""
    print("\n" + "=" * 60)
    print("Building AgTools Professional")
    print("=" * 60 + "\n")

    if not check_dependencies():
        print("\nBuild failed: Missing dependencies")
        return False

    # Run PyInstaller
    print("\nRunning PyInstaller...")
    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--clean",
        "--noconfirm",
        str(SPEC_FILE)
    ]

    result = subprocess.run(cmd, cwd=str(FRONTEND_DIR))

    if result.returncode != 0:
        print("\nBuild failed!")
        return False

    # Check if executable was created
    exe_path = DIST_DIR / "AgTools.exe"
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print("\n" + "=" * 60)
        print("BUILD SUCCESSFUL")
        print("=" * 60)
        print(f"\nExecutable: {exe_path}")
        print(f"Size: {size_mb:.1f} MB")
        print("\nTo run: double-click AgTools.exe or run from command line")
        print("\nNote: Make sure the backend server is running before launching.")
        return True
    else:
        print("\nBuild failed: Executable not found")
        return False


def main():
    parser = argparse.ArgumentParser(description="Build AgTools executable")
    parser.add_argument("--clean", action="store_true", help="Clean build artifacts before building")
    parser.add_argument("--clean-only", action="store_true", help="Only clean, don't build")
    args = parser.parse_args()

    os.chdir(FRONTEND_DIR)

    if args.clean_only:
        clean()
        return

    if args.clean:
        clean()

    success = build()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
