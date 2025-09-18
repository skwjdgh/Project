# config/work_log/func_temp_loadfile.py
import os
import json
from .def_worklog_exception import WorkLogLoadError
def load_work_log(project_log_path: str) -> dict:
    main_save_path = os.path.join(project_log_path, "main_save.json")
    if not os.path.exists(main_save_path):
        raise WorkLogLoadError(f"Main save file not found: {main_save_path}")
    try:
        with open(main_save_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (IOError, json.JSONDecodeError) as e:
        raise WorkLogLoadError(f"Failed to load work log: {main_save_path}. Reason: {e}") from e
