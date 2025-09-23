import os
import logging
from manage_project import VideoProject, MediaClip
from config.settings import paths
from config.input_output.def_inout_types import get_media_type, MediaType
from def_editor_exception import *

class EditingEngine:
    """Core controller that performs the actual editing logic."""
    def create_project(self, project_name: str) -> VideoProject:
        project = VideoProject(project_name=project_name, temp_dir=paths.TEMP_DIR)
        os.makedirs(project.log_path)
        project.log_action(action_info={'action': 'create_project'})
        logging.info(f"Project '{project.name}' created successfully.")
        return project

    def add_media_to_project(self, project: VideoProject, file_path: str):
        if not os.path.exists(file_path):
            raise InvalidFilePathError(f"File not found: {file_path}")
        media_type = get_media_type(file_path)
        if media_type == MediaType.UNKNOWN:
            raise UnsupportedFileTypeError(f"Unsupported file type: {file_path}")
        clip = MediaClip(file_path=file_path, media_type=media_type)
        project._media_clips.append(clip)
        logging.info(f"Media added (in memory): {os.path.basename(file_path)}")

    def remove_media_from_project(self, project: VideoProject, clip_index: int):
        try:
            removed_clip = project._media_clips.pop(clip_index)
            logging.info(f"Media removed (in memory): {os.path.basename(removed_clip.file_path)}")
        except IndexError:
            raise InvalidClipIndexError(f"Clip index out of range: {clip_index}")