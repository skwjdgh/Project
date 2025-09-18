# config/input_output/func_loadfile.py
import os
import logging
from .def_io_exception import ImportError
def import_media_file(file_path: str) -> bool:
    logging.info(f"Attempting to import media file: {file_path}")
    if not os.path.exists(file_path):
        raise ImportError(f"File to import not found: {file_path}")
    try:
        with open(file_path, 'rb') as f:
            f.read(1)
        logging.info(f"File import successful (simulation): {file_path}")
        return True
    except Exception as e:
        logging.error(f"Error during file import: {file_path}, Reason: {e}")
        raise ImportError(f"An error occurred during file import: {file_path}") from e