# config/input_output/def_inout_types.py
import os
from enum import Enum, auto
class MediaType(Enum):
    VIDEO = auto()
    AUDIO = auto()
    IMAGE = auto()
    UNKNOWN = auto()
SUPPORTED_EXTENSIONS = {'.mp4': MediaType.VIDEO, '.mov': MediaType.VIDEO, '.avi': MediaType.VIDEO, '.mp3': MediaType.AUDIO, '.wav': MediaType.AUDIO, '.m4a': MediaType.AUDIO, '.jpg': MediaType.IMAGE, '.jpeg': MediaType.IMAGE, '.png': MediaType.IMAGE}
def get_media_type(file_path: str) -> MediaType:
    _, ext = os.path.splitext(file_path)
    return SUPPORTED_EXTENSIONS.get(ext.lower(), MediaType.UNKNOWN)