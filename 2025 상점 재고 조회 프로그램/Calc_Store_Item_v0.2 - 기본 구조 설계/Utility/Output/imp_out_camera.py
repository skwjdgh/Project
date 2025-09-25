from Utility.Input.imp_rt_camera import open_camera
from .imp_out_video import AsyncVideoProcessor

def live_camera_stream(cam_index=0):
    cap = open_camera(cam_index)
    proc = AsyncVideoProcessor(cap)
    return proc.run()
