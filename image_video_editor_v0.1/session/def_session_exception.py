# session/def_session_exception.py
class SessionError(Exception):
    """Base exception for session-related errors."""
    pass
class NoActiveProjectError(SessionError):
    """Raised when an operation requires an active project but none is set."""
    pass