#!/usr/bin/env python3
"""
AgTools Professional - Desktop Application

Entry point for the PyQt6 crop consulting application.

Usage:
    python main.py

Requirements:
    - Python 3.10+
    - PyQt6
    - See requirements.txt for full dependencies
"""

import sys
import os

# Add the frontend directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_application


def main() -> int:
    """
    Main entry point for the application.

    Returns:
        Exit code (0 for success)
    """
    # Create the application
    app = create_application()

    # Create and show the main window
    window = app.create_main_window()
    window.show()

    # Run the event loop
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
