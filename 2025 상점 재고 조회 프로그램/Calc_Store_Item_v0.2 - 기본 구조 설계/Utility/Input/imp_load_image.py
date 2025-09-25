import cv2
from .def_exception import InputError

def load_image(path: str):
    img = cv2.imread(path)
    if img is None:
        raise InputError(f"Failed to read image: {path}")
    return img
