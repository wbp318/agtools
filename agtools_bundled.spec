# -*- mode: python ; coding: utf-8 -*-
"""
AgTools Bundled PyInstaller Spec File

Creates a single standalone Windows executable that includes both
the backend server and frontend GUI.

Usage:
    python -m PyInstaller agtools_bundled.spec

Output:
    dist/AgTools.exe - Complete bundled application
"""

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, collect_all

block_cipher = None

# Project root directory (where this spec file is located)
ROOT_DIR = os.path.dirname(os.path.abspath(SPECPATH))
BACKEND_DIR = os.path.join(ROOT_DIR, 'backend')
FRONTEND_DIR = os.path.join(ROOT_DIR, 'frontend')

# ============================================================================
# DATA FILES
# ============================================================================
# Collect all non-Python files needed at runtime

datas = [
    # Backend static files (CSS, JS, icons for mobile web interface)
    (os.path.join(BACKEND_DIR, 'static'), os.path.join('backend', 'static')),

    # Backend templates (Jinja2 HTML templates)
    (os.path.join(BACKEND_DIR, 'templates'), os.path.join('backend', 'templates')),

    # Backend mobile module templates (if any)
    (os.path.join(BACKEND_DIR, 'mobile'), os.path.join('backend', 'mobile')),

    # Backend credentials example
    (os.path.join(BACKEND_DIR, '.credentials.example'), os.path.join('backend', '.credentials.example')),

    # Frontend resources (if they exist)
]

# Add frontend resources if they exist
frontend_resources = os.path.join(FRONTEND_DIR, 'resources')
if os.path.exists(frontend_resources):
    datas.append((frontend_resources, os.path.join('frontend', 'resources')))

# ============================================================================
# HIDDEN IMPORTS
# ============================================================================
# Modules that PyInstaller can't detect automatically

hiddenimports = [
    # === FastAPI / Backend ===
    'uvicorn',
    'uvicorn.logging',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.websockets',
    'uvicorn.protocols.websockets.auto',
    'uvicorn.lifespan',
    'uvicorn.lifespan.on',
    'fastapi',
    'fastapi.middleware',
    'fastapi.middleware.cors',
    'starlette',
    'starlette.middleware',
    'starlette.routing',
    'starlette.responses',
    'starlette.staticfiles',
    'starlette.templating',
    'pydantic',
    'pydantic.fields',
    'pydantic_core',
    'anyio',
    'anyio._backends',
    'anyio._backends._asyncio',
    'httptools',
    'dotenv',
    'email_validator',

    # === Jinja2 Templates ===
    'jinja2',
    'jinja2.ext',

    # === Database ===
    'sqlite3',

    # === PyQt6 / Frontend ===
    'PyQt6',
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
    'PyQt6.sip',

    # === HTTP Client (frontend) ===
    'httpx',
    'httpx._transports',
    'httpx._transports.default',
    'httpcore',

    # === Charting (if used) ===
    'pyqtgraph',

    # === Crypto (for token storage) ===
    'cryptography',
    'cryptography.fernet',
    'cryptography.hazmat.primitives.kdf.pbkdf2',

    # === Date handling ===
    'dateutil',
    'dateutil.parser',
    'dateutil.tz',

    # === Standard library ===
    'json',
    'logging',
    'pathlib',
    'threading',
    'multiprocessing',

    # === Rate limiting ===
    'slowapi',
    'limits',
]

# Collect all submodules for complex packages
for pkg in ['uvicorn', 'starlette', 'fastapi', 'pydantic', 'anyio', 'httpx', 'httpcore']:
    try:
        hiddenimports.extend(collect_submodules(pkg))
    except Exception:
        pass

# ============================================================================
# ANALYSIS
# ============================================================================

a = Analysis(
    ['launcher.py'],  # Entry point
    pathex=[ROOT_DIR, BACKEND_DIR, FRONTEND_DIR],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unused heavy packages to reduce size
        'tkinter',
        'matplotlib',
        'scipy',
        'pandas',
        'PIL',
        'cv2',
        'tensorflow',
        'torch',
        'IPython',
        'notebook',
        'pytest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# ============================================================================
# PACKAGING
# ============================================================================

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='AgTools',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window - GUI app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(FRONTEND_DIR, 'resources', 'icons', 'agtools.ico') if os.path.exists(os.path.join(FRONTEND_DIR, 'resources', 'icons', 'agtools.ico')) else None,
    version='file_version_info.txt' if os.path.exists('file_version_info.txt') else None,
)
