# session/session.py
import logging
from typing import Optional
from PyQt6.QtCore import QObject, pyqtSignal
from manage_project import VideoProject
from .def_session_exception import NoActiveProjectError
class AppSession(QObject):
    project_changed = pyqtSignal(object)
    def __init__(self):
        super().__init__()
        self.active_project: Optional[VideoProject] = None
        logging.info("Application Session (AppSession) started.")
    def set_active_project(self, project: Optional[VideoProject]):
        self.active_project = project
        if project:
            logging.info(f"Active project set to '{project.name}'.")
        else:
            logging.info("Active project closed.")
        self.project_changed.emit(self.active_project)
    def get_active_project(self) -> VideoProject:
        if self.active_project is None:
            raise NoActiveProjectError("There is no active project.")
        return self.active_project