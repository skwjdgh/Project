# utility/actions/save_project_action.py
import logging
from utility.action.def_actions import IAction
from session.session import AppSession
class SaveProjectAction(IAction):
    def __init__(self, session: AppSession):
        self.session = session
    def execute(self):
        logging.debug("SaveProjectAction: 실행")
        try:
            project = self.session.get_active_project()
            project.save_snapshot()
        except Exception as e:
            logging.error(f"프로젝트 저장 액션 실행 중 오류: {e}")
    def undo(self):
        logging.debug("SaveProjectAction은 undo를 지원하지 않습니다.")
        pass