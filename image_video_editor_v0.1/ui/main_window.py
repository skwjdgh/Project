# ui/main_window.py
import logging
from PyQt6.QtWidgets import QMainWindow, QLabel
from PyQt6.QtCore import Qt
from manage_project import VideoProject
from typing import Optional
from session.session import AppSession
from utility.action.manage_actions import ActionManager
from project_editor_by_utility import EditingEngine
from utility.actions.save_project_action import SaveProjectAction
class MainWindow(QMainWindow):
    def __init__(self, app_session: AppSession, action_manager: ActionManager, editor: EditingEngine):
        super().__init__()
        self.session = app_session
        self.action_manager = action_manager
        self.editor = editor
        self._setup_ui()
        self.session.project_changed.connect(self.on_project_changed)
        logging.info(f"Main window created and connected to backend modules.")
    def _setup_ui(self):
        self.setWindowTitle("My Video Editor")
        self.setGeometry(100, 100, 1280, 720)
        central_widget = QLabel("UI will be constructed here.")
        central_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCentralWidget(central_widget)
        self._create_menu_bar()
    def _create_menu_bar(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("File")
        new_project_action = file_menu.addAction("New Project")
        save_project_action = file_menu.addAction("Save Project")
        file_menu.addSeparator()
        exit_action = file_menu.addAction("Exit")
        save_project_action.triggered.connect(self.on_save_project)
        exit_action.triggered.connect(self.close)
    def on_project_changed(self, project: Optional[VideoProject]):
        if project:
            self.setWindowTitle(f"My Video Editor - {project.name}")
        else:
            self.setWindowTitle("My Video Editor")
    def on_save_project(self):
        save_action = SaveProjectAction(self.session)
        save_action.execute()