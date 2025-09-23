# utility/actions/add_media_action.py
import logging
from utility.action.def_actions import IAction
from project_editor_by_utility import EditingEngine
from session.session import AppSession
class AddMediaAction(IAction):
    def __init__(self, editor: EditingEngine, session: AppSession, file_path: str):
        self.editor = editor
        self.session = session
        self.file_path = file_path
        self._project = session.get_active_project()
        self.added_clip = None
    def execute(self):
        logging.debug(f"AddMediaAction: 실행 ({self.file_path})")
        clip_count_before = len(self._project._media_clips)
        self.editor.add_media_to_project(self._project, self.file_path)
        if len(self._project._media_clips) > clip_count_before:
            self.added_clip = self._project._media_clips[-1]
        self._project.log_action(action_info={'action': 'add_media', 'path': self.file_path})
    def undo(self):
        logging.debug(f"AddMediaAction: 실행 취소 ({self.file_path})")
        if self.added_clip and self.added_clip in self._project._media_clips:
            self._project._media_clips.remove(self.added_clip)
            self._project.log_action(action_info={'action': 'undo_add_media', 'path': self.file_path})

