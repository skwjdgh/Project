class EditorError(Exception):
    """Base exception for editor-related errors."""
    pass
class InvalidFilePathError(EditorError):
    """Raised when an invalid file path is provided to the editor."""
    pass
class UnsupportedFileTypeError(EditorError):
    """Raised when an unsupported file type is provided to the editor."""
    pass
class InvalidClipIndexError(EditorError, IndexError):
    """Raised when trying to access a clip with an invalid index."""
    pass