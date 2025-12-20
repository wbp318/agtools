"""
Mobile/Crew Interface Module
AgTools v2.6.0 Phase 6

Server-rendered mobile web interface for crew members.
"""

from .auth import get_session_user, set_session_cookie, clear_session_cookie, require_session
from .routes import router as mobile_router, configure_templates

__all__ = [
    'get_session_user',
    'set_session_cookie',
    'clear_session_cookie',
    'require_session',
    'mobile_router',
    'configure_templates',
]
