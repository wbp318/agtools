#!/usr/bin/env python3
"""
AgTools Professional - All-in-One Launcher

This launcher starts both the backend API server and the frontend desktop app.
When the frontend closes, it automatically shuts down the backend.

Usage:
    python launcher.py
"""

import sys
import os
import subprocess
import time
import threading
import signal
import socket
import atexit

# Determine if we're running as a frozen executable
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    BASE_DIR = os.path.dirname(sys.executable)
    # Look for backend in the same directory or parent
    BACKEND_DIR = os.path.join(BASE_DIR, 'backend')
    if not os.path.exists(BACKEND_DIR):
        BACKEND_DIR = os.path.join(os.path.dirname(BASE_DIR), 'backend')
else:
    # Running as script
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    BACKEND_DIR = os.path.join(BASE_DIR, 'backend')

FRONTEND_DIR = os.path.join(BASE_DIR, 'frontend')

# Backend configuration
BACKEND_HOST = "127.0.0.1"
BACKEND_PORT = 8000


class BackendProcess:
    """Manages the backend server process."""

    def __init__(self):
        self.process = None
        self.output_thread = None
        self.running = False

    def start(self):
        """Start the backend server."""
        print("Starting AgTools backend server...")

        # Set up environment
        env = os.environ.copy()
        env['PYTHONPATH'] = BACKEND_DIR

        # Start uvicorn with the FastAPI app
        cmd = [
            sys.executable, '-m', 'uvicorn',
            'main:app',
            '--host', BACKEND_HOST,
            '--port', str(BACKEND_PORT),
            '--log-level', 'warning'
        ]

        try:
            self.process = subprocess.Popen(
                cmd,
                cwd=BACKEND_DIR,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            self.running = True

            # Start output monitoring thread
            self.output_thread = threading.Thread(target=self._monitor_output, daemon=True)
            self.output_thread.start()

            return True

        except Exception as e:
            print(f"Failed to start backend: {e}")
            return False

    def _monitor_output(self):
        """Monitor backend output for errors."""
        if self.process and self.process.stdout:
            for line in iter(self.process.stdout.readline, b''):
                if line:
                    text = line.decode('utf-8', errors='ignore').strip()
                    if text and 'error' in text.lower():
                        print(f"[Backend] {text}")

    def wait_until_ready(self, timeout=30):
        """Wait for the backend to be ready to accept connections."""
        print(f"Waiting for backend to be ready on port {BACKEND_PORT}...")

        start_time = time.time()
        while time.time() - start_time < timeout:
            if self._is_port_open():
                print("Backend is ready!")
                return True

            # Check if process died
            if self.process and self.process.poll() is not None:
                print("Backend process exited unexpectedly!")
                return False

            time.sleep(0.5)

        print(f"Backend did not start within {timeout} seconds")
        return False

    def _is_port_open(self):
        """Check if the backend port is open."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((BACKEND_HOST, BACKEND_PORT))
            sock.close()
            return result == 0
        except:
            return False

    def stop(self):
        """Stop the backend server."""
        if self.process and self.running:
            print("Shutting down backend server...")
            self.running = False

            try:
                # Try graceful shutdown first
                if sys.platform == 'win32':
                    self.process.terminate()
                else:
                    self.process.send_signal(signal.SIGTERM)

                # Wait for process to end
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # Force kill if it doesn't stop
                    self.process.kill()
                    self.process.wait()

                print("Backend server stopped.")

            except Exception as e:
                print(f"Error stopping backend: {e}")


def check_port_available(port):
    """Check if the port is available (not in use)."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((BACKEND_HOST, port))
        sock.close()
        return result != 0  # Port is available if connection fails
    except:
        return True


def start_frontend():
    """Start the PyQt6 frontend application."""
    print("Starting AgTools frontend...")

    # Add frontend to path
    if FRONTEND_DIR not in sys.path:
        sys.path.insert(0, FRONTEND_DIR)

    # Import and run the frontend
    try:
        from app import create_application

        app = create_application()
        return app.start()

    except ImportError as e:
        print(f"Failed to import frontend: {e}")
        print("Make sure all frontend dependencies are installed.")
        return 1


def show_splash():
    """Show a simple splash/loading message."""
    print("")
    print("=" * 50)
    print("  AgTools Professional")
    print("  Crop Consulting System")
    print("=" * 50)
    print("")


def main():
    """Main entry point for the all-in-one launcher."""
    show_splash()

    backend = BackendProcess()

    # Register cleanup
    def cleanup():
        backend.stop()

    atexit.register(cleanup)

    # Check if backend port is already in use
    if not check_port_available(BACKEND_PORT):
        print(f"Port {BACKEND_PORT} is already in use.")
        print("Either another instance is running, or the backend is already started.")
        print("Attempting to connect to existing backend...")

        # Try to start frontend with existing backend
        exit_code = start_frontend()
        return exit_code

    # Start backend
    if not backend.start():
        print("Failed to start backend server!")
        print("Please check that all dependencies are installed.")
        input("Press Enter to exit...")
        return 1

    # Wait for backend to be ready
    if not backend.wait_until_ready():
        print("Backend failed to start properly!")
        backend.stop()
        input("Press Enter to exit...")
        return 1

    # Start frontend
    try:
        exit_code = start_frontend()
    except Exception as e:
        print(f"Frontend error: {e}")
        exit_code = 1
    finally:
        # Clean up backend when frontend closes
        backend.stop()

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
