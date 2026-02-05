#!/usr/bin/env python
"""
AgTools Bundled Build Script

Creates a single standalone executable containing both backend and frontend.
Users can double-click to launch - no separate server setup required.

Usage:
    python build_bundled.py           # Build the bundled executable
    python build_bundled.py --clean   # Clean build artifacts first

Output:
    dist/AgTools.exe - Complete standalone application (~150-200 MB)

Database Location (after running):
    %LOCALAPPDATA%\\AgTools\\agtools.db
"""

import os
import sys
import shutil
import subprocess
import argparse
from pathlib import Path

# Get the project root directory
ROOT_DIR = Path(__file__).parent.absolute()
DIST_DIR = ROOT_DIR / "dist"
BUILD_DIR = ROOT_DIR / "build"
SPEC_FILE = ROOT_DIR / "agtools_bundled.spec"


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
    for pycache in ROOT_DIR.rglob("__pycache__"):
        if ".venv" not in str(pycache) and "venv" not in str(pycache):
            try:
                shutil.rmtree(pycache)
                print(f"  Removed {pycache}")
            except PermissionError:
                print(f"  Could not remove {pycache} (in use)")

    print("Clean complete.")


def check_dependencies():
    """Check if required dependencies are installed."""
    print("Checking dependencies...")

    missing = []

    try:
        import PyInstaller
        print(f"  PyInstaller: {PyInstaller.__version__}")
    except ImportError:
        missing.append("pyinstaller")

    try:
        import PyQt6
        print("  PyQt6: OK")
    except ImportError:
        missing.append("PyQt6")

    try:
        import fastapi
        print("  FastAPI: OK")
    except ImportError:
        missing.append("fastapi")

    try:
        import uvicorn
        print("  Uvicorn: OK")
    except ImportError:
        missing.append("uvicorn")

    try:
        import httpx
        print("  HTTPX: OK")
    except ImportError:
        missing.append("httpx")

    if missing:
        print(f"\n  ERROR: Missing packages: {', '.join(missing)}")
        print("  Run: pip install " + " ".join(missing))
        return False

    return True


def build():
    """Build the bundled executable."""
    print("\n" + "=" * 60)
    print("Building AgTools Professional (Bundled)")
    print("=" * 60 + "\n")

    if not check_dependencies():
        print("\nBuild failed: Missing dependencies")
        return False

    if not SPEC_FILE.exists():
        print(f"\nBuild failed: Spec file not found: {SPEC_FILE}")
        return False

    # Run PyInstaller
    print("\nRunning PyInstaller (this may take several minutes)...")
    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--clean",
        "--noconfirm",
        str(SPEC_FILE)
    ]

    result = subprocess.run(cmd, cwd=str(ROOT_DIR))

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
        print("\n" + "-" * 60)
        print("USAGE INSTRUCTIONS")
        print("-" * 60)
        print("\n1. Copy AgTools.exe to any folder")
        print("2. Double-click to run")
        print("3. On first run, configure credentials in:")
        print("   %LOCALAPPDATA%\\AgTools\\.credentials")
        print("\nData is stored in: %LOCALAPPDATA%\\AgTools\\")
        print("  - agtools.db (database)")
        print("  - .credentials (admin login)")
        print("  - logs/ (application logs)")
        return True
    else:
        print("\nBuild failed: Executable not found")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Build AgTools bundled executable",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python build_bundled.py           Build the executable
    python build_bundled.py --clean   Clean first, then build
    python build_bundled.py --clean-only   Only clean artifacts
        """
    )
    parser.add_argument("--clean", action="store_true",
                        help="Clean build artifacts before building")
    parser.add_argument("--clean-only", action="store_true",
                        help="Only clean, don't build")
    args = parser.parse_args()

    os.chdir(ROOT_DIR)

    if args.clean_only:
        clean()
        return

    if args.clean:
        clean()

    success = build()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
