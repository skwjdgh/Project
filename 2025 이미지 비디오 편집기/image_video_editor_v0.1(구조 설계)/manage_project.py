import os
import logging
from datetime import datetime
from dataclasses import dataclass, field
from typing import Tuple, List

from def_project_exception import *
from config.input_output.def_inout_types import MediaType
from config.work_log.func_temp_savefile import save_main_snapshot, save_action_to_log
from config.work_log.def_worklog_exception import WorkLogSaveError, WorkLogLoadError

@dataclass
class MediaClip:
    file_path: str
    media_type: MediaType
    added_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
class VideoProject:
    """Data model class that defines the data and state of a project."""
    def __init__(self, project_name: str, temp_dir: str, **kwargs):
        self.name = project_name
        self.log_path = os.path.join(temp_dir, self.name)
        self.resolution = kwargs.get('resolution', (1920, 1080))
        self.fps = kwargs.get('fps', 30)
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at
        self._media_clips: List[MediaClip] = []

        if os.path.exists(self.log_path):
            raise ProjectCreationError(f"Project log directory '{self.log_path}' already exists.")

    @property
    def media_clips(self) -> Tuple[MediaClip, ...]:
        """Returns a read-only tuple view of the media clip list."""
        return tuple(self._media_clips)

    def save_snapshot(self):
        """Saves the entire current state (snapshot) of the project."""
        self.updated_at = datetime.now().isoformat()
        main_data = {
            'projectName': self.name, 'resolution': self.resolution, 'fps': self.fps,
            'createdAt': self.created_at, 'updatedAt': self.updated_at,
            'mediaClips': [clip.__dict__ for clip in self._media_clips]
        }
        try:
            save_main_snapshot(self.log_path, main_data)
            logging.info(f"Project snapshot saved successfully: {self.name}")
        except WorkLogSaveError as e:
            raise ProjectSaveError("Failed to save project snapshot") from e

    def log_action(self, action_info: dict):
        """Records a lightweight action log to a file."""
        self.updated_at = datetime.now().isoformat()
        action_data = {'timestamp': self.updated_at, **action_info}
        try:
            save_action_to_log(self.log_path, action_data)
            logging.debug(f"Action log recorded successfully: {action_info['action']}")
        except WorkLogSaveError as e:
            raise ProjectSaveError("Failed to record action log") from e

    @classmethod
    def load(cls, project_log_path: str) -> 'VideoProject':
        try:
            project_data = load_work_log(project_log_path)
        except WorkLogLoadError as e:
            raise ProjectLoadError("Failed to load project from work log") from e

        temp_dir = os.path.dirname(project_log_path)
        project_name = project_data['projectName']
        loaded_project = cls(project_name=project_name, temp_dir=temp_dir)
        loaded_project.log_path = project_log_path
        loaded_project.resolution = tuple(project_data['resolution'])
        loaded_project.fps = project_data['fps']
        loaded_project.created_at = project_data['createdAt']
        loaded_project.updated_at = project_data['updatedAt']
        loaded_project.media_clips = [
            MediaClip(
                file_path=clip_data['file_path'],
                media_type=MediaType[clip_data['media_type'].split('.')[-1]],
                added_at=clip_data['added_at']
            ) for clip_data in project_data['mediaClips']
        ]
        logging.info(f"Project '{loaded_project.name}' loaded successfully.")
        return loaded_project
    
    def __repr__(self):
        return f"<VideoProject name='{self.name}' clips={len(self._media_clips)}>"