import torch
from Def_config import MODEL_WEIGHT, CONF_THRES, IOU_THRES, USE_HALF
from .def_exception import ModelLoadError, InferenceError

class YOLORecognizer:
    def __init__(self):
        try:
            from ultralytics import YOLO  # pip install ultralytics
        except Exception as e:
            raise ModelLoadError(f"Ultralytics import failed: {e}")

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        try:
            self.model = YOLO(MODEL_WEIGHT)
            if self.device == "cuda" and USE_HALF and hasattr(self.model.model, "half"):
                self.model.model.half()
            self.model.to(self.device)  # predict()에서 device 생략
        except Exception as e:
            raise ModelLoadError(f"Model load failed: {e}")

    @torch.inference_mode()
    def infer(self, img_bgr):
        try:
            res = self.model.predict(
                source=img_bgr,
                conf=CONF_THRES,
                iou=IOU_THRES,
                verbose=False
            )
            return res[0]
        except Exception as e:
            raise InferenceError(str(e))
