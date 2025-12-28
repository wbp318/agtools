#!/usr/bin/env python3
"""
Build script for AgTools Windows executable.

This script:
1. Ensures all dependencies are installed
2. Runs PyInstaller to create the .exe
3. Creates a desktop shortcut
4. Optionally creates an installer

Usage:
    python scripts/build_exe.py
    python scripts/build_exe.py --no-shortcut
"""

import os
import sys
import subprocess
import shutil
import argparse
from pathlib import Path

# Get paths
SCRIPT_DIR = Path(__file__).parent
ROOT_DIR = SCRIPT_DIR.parent
FRONTEND_DIR = ROOT_DIR / "frontend"
DIST_DIR = ROOT_DIR / "dist"
BUILD_DIR = ROOT_DIR / "build"
SPEC_FILE = ROOT_DIR / "AgTools.spec"
ICON_FILE = ROOT_DIR / "agtools.ico"


def print_step(msg: str):
    """Print a step message."""
    print(f"\n{'='*60}")
    print(f"  {msg}")
    print(f"{'='*60}\n")


def check_dependencies():
    """Check that required packages are installed."""
    print_step("Checking dependencies...")

    required = ['PyInstaller', 'PyQt6', 'httpx', 'pyqtgraph', 'numpy']
    missing = []

    for pkg in required:
        try:
            __import__(pkg.lower().replace('-', '_'))
            print(f"  [OK] {pkg}")
        except ImportError:
            print(f"  [MISSING] {pkg}")
            missing.append(pkg)

    if missing:
        print(f"\nInstalling missing packages: {', '.join(missing)}")
        subprocess.run([sys.executable, '-m', 'pip', 'install'] + missing, check=True)

    return True


def clean_build():
    """Clean previous build artifacts."""
    print_step("Cleaning previous build...")

    for dir_path in [DIST_DIR, BUILD_DIR]:
        if dir_path.exists():
            print(f"  Removing {dir_path}")
            shutil.rmtree(dir_path)

    print("  Clean complete.")


def build_executable():
    """Build the executable using PyInstaller."""
    print_step("Building executable with PyInstaller...")

    if not SPEC_FILE.exists():
        print(f"ERROR: Spec file not found: {SPEC_FILE}")
        return False

    # Run PyInstaller
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--clean',
        '--noconfirm',
        str(SPEC_FILE)
    ]

    print(f"  Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(ROOT_DIR))

    if result.returncode != 0:
        print("ERROR: PyInstaller failed!")
        return False

    exe_path = DIST_DIR / "AgTools.exe"
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"\n  SUCCESS! Executable created: {exe_path}")
        print(f"  Size: {size_mb:.1f} MB")
        return True
    else:
        print("ERROR: Executable not found after build!")
        return False


def create_desktop_shortcut():
    """Create a desktop shortcut for AgTools."""
    print_step("Creating desktop shortcut...")

    exe_path = DIST_DIR / "AgTools.exe"
    if not exe_path.exists():
        print("ERROR: Executable not found. Build first!")
        return False

    # Get desktop path
    desktop = Path.home() / "Desktop"
    if not desktop.exists():
        # Try OneDrive Desktop
        desktop = Path.home() / "OneDrive" / "Desktop"

    if not desktop.exists():
        print(f"WARNING: Desktop folder not found at {desktop}")
        desktop = Path.home() / "Desktop"
        desktop.mkdir(exist_ok=True)

    shortcut_path = desktop / "AgTools.lnk"

    # Create shortcut using PowerShell
    ps_script = f'''
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
$Shortcut.TargetPath = "{exe_path}"
$Shortcut.WorkingDirectory = "{DIST_DIR}"
$Shortcut.IconLocation = "{ICON_FILE}"
$Shortcut.Description = "AgTools Professional - Crop Consulting System"
$Shortcut.Save()
'''

    try:
        result = subprocess.run(
            ['powershell', '-Command', ps_script],
            capture_output=True,
            text=True
        )

        if result.returncode == 0 and shortcut_path.exists():
            print(f"  SUCCESS! Shortcut created: {shortcut_path}")
            return True
        else:
            print(f"  PowerShell error: {result.stderr}")
            return False

    except Exception as e:
        print(f"  ERROR creating shortcut: {e}")
        return False


def create_start_menu_shortcut():
    """Create a Start Menu shortcut."""
    print_step("Creating Start Menu shortcut...")

    exe_path = DIST_DIR / "AgTools.exe"
    if not exe_path.exists():
        print("ERROR: Executable not found. Build first!")
        return False

    # Start Menu Programs folder
    start_menu = Path.home() / "AppData" / "Roaming" / "Microsoft" / "Windows" / "Start Menu" / "Programs"

    if not start_menu.exists():
        print(f"WARNING: Start Menu folder not found at {start_menu}")
        return False

    shortcut_path = start_menu / "AgTools.lnk"

    # Create shortcut using PowerShell
    ps_script = f'''
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
$Shortcut.TargetPath = "{exe_path}"
$Shortcut.WorkingDirectory = "{DIST_DIR}"
$Shortcut.IconLocation = "{ICON_FILE}"
$Shortcut.Description = "AgTools Professional - Crop Consulting System"
$Shortcut.Save()
'''

    try:
        result = subprocess.run(
            ['powershell', '-Command', ps_script],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print(f"  SUCCESS! Start Menu shortcut created: {shortcut_path}")
            return True
        else:
            print(f"  PowerShell error: {result.stderr}")
            return False

    except Exception as e:
        print(f"  ERROR creating shortcut: {e}")
        return False


def main():
    """Main build process."""
    parser = argparse.ArgumentParser(description='Build AgTools Windows executable')
    parser.add_argument('--no-shortcut', action='store_true',
                       help='Skip creating desktop shortcut')
    parser.add_argument('--no-clean', action='store_true',
                       help='Skip cleaning previous build')
    parser.add_argument('--shortcut-only', action='store_true',
                       help='Only create shortcuts (skip build)')
    args = parser.parse_args()

    print("\n" + "="*60)
    print("  AgTools Windows Executable Builder")
    print("="*60)

    if args.shortcut_only:
        # Just create shortcuts
        create_desktop_shortcut()
        create_start_menu_shortcut()
        print("\n" + "="*60)
        print("  Shortcuts created!")
        print("="*60 + "\n")
        return 0

    # Full build process
    try:
        check_dependencies()

        if not args.no_clean:
            clean_build()

        if not build_executable():
            return 1

        if not args.no_shortcut:
            create_desktop_shortcut()
            create_start_menu_shortcut()

        print("\n" + "="*60)
        print("  BUILD COMPLETE!")
        print("="*60)
        print(f"\n  Executable: {DIST_DIR / 'AgTools.exe'}")
        print(f"  Icon: {ICON_FILE}")
        if not args.no_shortcut:
            print(f"  Desktop shortcut created")
            print(f"  Start Menu shortcut created")
        print("\n  You can now run AgTools from your desktop!")
        print("="*60 + "\n")

        return 0

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
