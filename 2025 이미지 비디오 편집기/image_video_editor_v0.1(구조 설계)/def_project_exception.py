class ProjectError(Exception):
    """Base exception for project-related errors."""
    pass
class ProjectCreationError(ProjectError):
    """Raised when a project fails to be created."""
    pass
class ProjectLoadError(ProjectError):
    """Raised when a project fails to load."""
    pass
class ProjectSaveError(ProjectError):
    """Raised when a project fails to save."""
    pass