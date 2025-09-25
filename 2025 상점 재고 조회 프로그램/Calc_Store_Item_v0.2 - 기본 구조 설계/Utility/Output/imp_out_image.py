from Utility.Recognization.imp_recog import YOLORecognizer
from .imp_output import draw_result

def process_image(img_bgr):
    model = YOLORecognizer()
    res = model.infer(img_bgr)

    boxes = res.boxes.xyxy.cpu().numpy() if res.boxes is not None else []
    confs = res.boxes.conf.cpu().numpy().tolist() if res.boxes is not None else []
    cls_ids = res.boxes.cls.cpu().numpy().tolist() if res.boxes is not None else []

    names_map = getattr(res, "names", None) or getattr(model.model, "names", {}) or {}
    names = [names_map.get(int(i), str(i)) for i in cls_ids]

    dets = [{"cls_name": n, "conf": c} for n, c in zip(names, confs)]
    out = draw_result(img_bgr.copy(), boxes, names, confs)
    return out, dets
