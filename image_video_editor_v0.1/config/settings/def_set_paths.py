# config/settings/def_set_paths.py
import os
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEMP_DIR = os.path.join(ROOT_DIR, "temp")
OUTPUT_DIR = os.path.join(ROOT_DIR, "output")
LOG_DIR = os.path.join(ROOT_DIR, "logs")