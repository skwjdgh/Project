import os
import cv2
from .def_exception import InputError

def open_camera(index: int = 0, width: int = 1280, height: int = 720):
    api = cv2.CAP_DSHOW if os.name == "nt" else 0
    cap = cv2.VideoCapture(index, api)
    if not cap.isOpened():
        raise InputError(f"Failed to open camera: {index}")
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    return cap
