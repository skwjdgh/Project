#### **`main.py`**
import sys
import logging
from PyQt6.QtWidgets import QApplication

from config.logging_setup import setup_logging
from config.settings import application

from session.session import AppSession
from utility.action.manage_actions import ActionManager
from project_editor_by_utility import EditingEngine
from ui.main_window import MainWindow

def main():
    """
    Application's main entry point.
    Initializes and connects all modules to start the program.
    """
    setup_logging()
    logging.info(f"Starting application: {application.APP_NAME} v{application.APP_VERSION}")

    # 1. Create all core backend objects
    app_session = AppSession()
    action_manager = ActionManager()
    editor = EditingEngine()
    logging.info("Core backend modules (Session, ActionManager, Editor) created.")

    # 2. Create Qt Application
    app = QApplication(sys.argv)
    
    # 3. Create Frontend (View) object and inject backend objects to connect them
    window = MainWindow(
        app_session=app_session,
        action_manager=action_manager,
        editor=editor
    )
    window.show()
    
    # 4. Start the application event loop
    sys.exit(app.exec())

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logging.critical(f"A critical error occurred while running the application: {e}", exc_info=True)
        sys.exit(1)