#!/usr/bin/env python3
"""
AgTools Professional - Unified Launcher

Single entry point that starts both backend server and frontend GUI.
For use with bundled executable (PyInstaller) or development.

Usage:
    python launcher.py           # Start both backend and frontend
    python launcher.py --help    # Show options
"""

import os
import sys
import time
import socket
import logging
import threading
import urllib.request
import urllib.error
from pathlib import Path

# Configure logging before any imports that might use it
LOG_DIR = None
LOG_FILE = None


def get_app_data_dir() -> Path:
    """Get the application data directory (for database, logs, credentials)."""
    if getattr(sys, 'frozen', False):
        app_data = os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))
        return Path(app_data) / 'AgTools'
    else:
        return Path(__file__).parent


def get_base_path() -> Path:
    """Get the base path for bundled resources."""
    if getattr(sys, 'frozen', False):
        # Running as bundled exe - resources are in _MEIPASS
        return Path(sys._MEIPASS)
    else:
        # Development mode - use project root
        return Path(__file__).parent


def setup_logging():
    """Set up logging to file in AppData."""
    global LOG_DIR, LOG_FILE

    app_data_dir = get_app_data_dir()
    LOG_DIR = app_data_dir / 'logs'
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    LOG_FILE = LOG_DIR / 'agtools.log'

    handlers = [logging.FileHandler(LOG_FILE, encoding='utf-8')]

    # Only log to console in development
    if not getattr(sys, 'frozen', False):
        handlers.append(logging.StreamHandler())

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )


setup_logging()
logger = logging.getLogger(__name__)


def find_available_port(start_port: int = 8000, max_attempts: int = 10) -> int:
    """Find an available port starting from start_port."""
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                return port
        except OSError:
            continue
    raise RuntimeError(f"No available port found in range {start_port}-{start_port + max_attempts}")


def wait_for_backend(host: str, port: int, timeout: float = 30.0) -> bool:
    """
    Wait for backend to be ready by polling health endpoint.

    Args:
        host: Backend host
        port: Backend port
        timeout: Maximum time to wait in seconds

    Returns:
        True if backend is ready, False if timeout
    """
    url = f"http://{host}:{port}/api/v1/auth/health"
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                if response.status == 200:
                    logger.info("Backend is ready")
                    return True
        except (urllib.error.URLError, urllib.error.HTTPError, OSError):
            pass
        time.sleep(0.5)

    logger.error("Backend failed to start within %s seconds", timeout)
    return False


def setup_bundled_environment():
    """Set up environment for bundled executable mode."""
    base_path = get_base_path()
    app_data_dir = get_app_data_dir()

    # Ensure app data directory exists
    app_data_dir.mkdir(parents=True, exist_ok=True)

    # Add backend to path
    backend_path = base_path / 'backend'
    if str(backend_path) not in sys.path:
        sys.path.insert(0, str(backend_path))

    # Set database path to AppData
    db_path = app_data_dir / 'agtools.db'
    os.environ['AGTOOLS_DB_PATH'] = str(db_path)

    # Set backend directory for static files and templates
    os.environ['AGTOOLS_BACKEND_DIR'] = str(backend_path)

    # Handle credentials file
    creds_file = app_data_dir / '.credentials'
    if not creds_file.exists():
        # Copy example credentials if available
        example_creds = backend_path / '.credentials.example'
        if example_creds.exists():
            logger.info("Copying example credentials to AppData - please configure!")
            import shutil
            shutil.copy(example_creds, creds_file)

    logger.info("Bundled environment configured:")
    logger.info("  Database: %s", db_path)
    logger.info("  Backend: %s", backend_path)
    logger.info("  Credentials: %s", creds_file)


def setup_dev_environment():
    """Set up environment for development mode."""
    base_path = get_base_path()

    # Add backend to path
    backend_path = base_path / 'backend'
    if str(backend_path) not in sys.path:
        sys.path.insert(0, str(backend_path))

    logger.info("Development environment configured:")
    logger.info("  Backend: %s", backend_path)


def run_backend(host: str, port: int):
    """
    Run the backend server in the current thread (blocking).

    Args:
        host: Host to bind to
        port: Port to bind to
    """
    logger.info("Starting backend server on %s:%d", host, port)

    if getattr(sys, 'frozen', False):
        setup_bundled_environment()
    else:
        setup_dev_environment()

    try:
        # Import and run the backend using programmatic uvicorn
        from main import run_server
        run_server(host=host, port=port)
    except Exception as e:
        logger.exception("Backend server error: %s", e)
        raise


def run_frontend(api_port: int):
    """
    Run the frontend GUI.

    Args:
        api_port: Port the backend is running on
    """
    logger.info("Starting frontend GUI (API on port %d)", api_port)

    base_path = get_base_path()

    # Add frontend to path
    if getattr(sys, 'frozen', False):
        frontend_path = base_path / 'frontend'
    else:
        frontend_path = base_path / 'frontend'

    if str(frontend_path) not in sys.path:
        sys.path.insert(0, str(frontend_path))

    # Set API URL to use the local backend
    os.environ['AGTOOLS_API_URL'] = f'http://127.0.0.1:{api_port}'

    try:
        # Import and run the frontend
        from app import create_application
        app = create_application()
        return app.start()
    except Exception as e:
        logger.exception("Frontend error: %s", e)
        raise


def show_splash():
    """Show startup information."""
    print("")
    print("=" * 50)
    print("  AgTools Professional")
    print("  Farm Management System")
    print("=" * 50)
    print("")
    logger.info("=" * 60)
    logger.info("AgTools Launcher Starting")
    logger.info("Frozen: %s", getattr(sys, 'frozen', False))
    logger.info("Base path: %s", get_base_path())
    logger.info("App data: %s", get_app_data_dir())
    logger.info("=" * 60)


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='AgTools - Farm Management System')
    parser.add_argument('--port', type=int, default=8000,
                        help='Backend server port (default: 8000)')
    parser.add_argument('--host', type=str, default='127.0.0.1',
                        help='Backend server host (default: 127.0.0.1)')
    parser.add_argument('--backend-only', action='store_true',
                        help='Run only the backend server')
    parser.add_argument('--frontend-only', action='store_true',
                        help='Run only the frontend (requires backend already running)')
    args = parser.parse_args()

    show_splash()

    # Ensure app data directory exists
    app_data_dir = get_app_data_dir()
    app_data_dir.mkdir(parents=True, exist_ok=True)

    if args.frontend_only:
        # Just run the frontend (assume backend is already running)
        exit_code = run_frontend(args.port)
        return exit_code

    # Find available port
    try:
        port = find_available_port(args.port)
        if port != args.port:
            logger.info("Port %d in use, using port %d instead", args.port, port)
            print(f"Port {args.port} in use, using port {port}")
    except RuntimeError as e:
        logger.error("Failed to find available port: %s", e)
        print(f"Error: {e}")
        sys.exit(1)

    if args.backend_only:
        # Just run the backend (blocking)
        run_backend(args.host, port)
        return

    # Start backend in a daemon thread
    backend_thread = threading.Thread(
        target=run_backend,
        args=(args.host, port),
        daemon=True,
        name='BackendServer'
    )
    backend_thread.start()

    # Wait for backend to be ready
    print("Waiting for backend server...")
    if not wait_for_backend(args.host, port, timeout=30.0):
        logger.error("Backend failed to start. Check logs at: %s", LOG_FILE)
        print(f"Backend failed to start. Check logs at: {LOG_FILE}")
        sys.exit(1)

    print("Backend ready, starting frontend...")

    # Run frontend (blocks until GUI closes)
    exit_code = run_frontend(port)

    # When frontend exits, the daemon thread will be cleaned up automatically
    logger.info("AgTools exiting with code %d", exit_code)
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
