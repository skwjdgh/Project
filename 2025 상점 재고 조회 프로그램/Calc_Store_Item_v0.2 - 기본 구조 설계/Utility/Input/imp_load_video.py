import cv2
from .def_exception import InputError

def open_video(path: str):
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise InputError(f"Failed to open video: {path}")
    return cap
