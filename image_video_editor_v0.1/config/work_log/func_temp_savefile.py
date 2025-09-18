# config/work_log/func_temp_savefile.py
import os
import json
from .def_worklog_exception import WorkLogSaveError
def save_main_snapshot(project_log_path: str, main_data: dict):
    try:
        if not os.path.exists(project_log_path):
            os.makedirs(project_log_path)
        main_save_path = os.path.join(project_log_path, "main_save.json")
        with open(main_save_path, 'w', encoding='utf-8') as f:
            json.dump(main_data, f, indent=4, ensure_ascii=False)
    except (IOError, OSError) as e:
        raise WorkLogSaveError(f"Failed to save main snapshot: {e}") from e
def save_action_to_log(project_log_path: str, action_data: dict):
    try:
        if not os.path.exists(project_log_path):
            os.makedirs(project_log_path)
        existing_actions = [f for f in os.listdir(project_log_path) if f.endswith('.action.json')]
        next_action_number = len(existing_actions) + 1
        action_filename = f"{next_action_number:04d}.action.json"
        action_save_path = os.path.join(project_log_path, action_filename)
        with open(action_save_path, 'w', encoding='utf-8') as f:
            json.dump(action_data, f, indent=4, ensure_ascii=False)
    except (IOError, OSError) as e:
        raise WorkLogSaveError(f"Failed to save action log: {e}") from e