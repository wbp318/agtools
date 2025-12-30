#!/usr/bin/env python3
"""
AgTools Professional - All-in-One Launcher

Starts the backend server and frontend desktop app together.
The .pyw extension runs without a console window on Windows.
"""

import sys
import os
import subprocess
import time
import socket
import atexit

# Get the directory where this script lives
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(BASE_DIR, 'backend')
FRONTEND_DIR = os.path.join(BASE_DIR, 'frontend')

# Backend configuration
BACKEND_HOST = "127.0.0.1"
BACKEND_PORT = 8000

# Global backend process
backend_process = None


def is_port_in_use(port):
    """Check if a port is already in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((BACKEND_HOST, port)) == 0


def wait_for_backend(timeout=30):
    """Wait for the backend to be ready."""
    start = time.time()
    while time.time() - start < timeout:
        if is_port_in_use(BACKEND_PORT):
            return True
        time.sleep(0.5)
    return False


def start_backend():
    """Start the backend server."""
    global backend_process

    if is_port_in_use(BACKEND_PORT):
        print("Backend already running on port", BACKEND_PORT)
        return True

    env = os.environ.copy()
    env['PYTHONPATH'] = BACKEND_DIR
    env['AGTOOLS_DEV_MODE'] = '1'  # Enable dev mode for local desktop

    # Start uvicorn in background (no window on Windows)
    startupinfo = None
    if sys.platform == 'win32':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE

    backend_process = subprocess.Popen(
        [sys.executable, '-m', 'uvicorn', 'main:app',
         '--host', BACKEND_HOST, '--port', str(BACKEND_PORT)],
        cwd=BACKEND_DIR,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        startupinfo=startupinfo
    )

    return wait_for_backend()


def stop_backend():
    """Stop the backend server."""
    global backend_process
    if backend_process:
        backend_process.terminate()
        try:
            backend_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            backend_process.kill()


def start_frontend():
    """Start the PyQt6 frontend."""
    sys.path.insert(0, FRONTEND_DIR)
    os.chdir(FRONTEND_DIR)

    from app import create_application
    app = create_application()
    return app.start()


def main():
    """Main entry point."""
    # Register cleanup
    atexit.register(stop_backend)

    # Start backend
    if not start_backend():
        # Show error dialog
        try:
            from PyQt6.QtWidgets import QApplication, QMessageBox
            app = QApplication(sys.argv)
            QMessageBox.critical(None, "AgTools Error",
                "Failed to start the backend server.\n\n"
                "Please make sure all dependencies are installed:\n"
                "pip install -r backend/requirements.txt")
        except:
            pass
        return 1

    # Start frontend
    try:
        exit_code = start_frontend()
    finally:
        stop_backend()

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
