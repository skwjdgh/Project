import cv2, numpy as np, torch

USE_HALF = torch.cuda.is_available()
IMGSZ = 736  # 더 빠르게: 640

def _to_bgr_ndarray(source):
    if isinstance(source, str):
        return source  # 파일 경로
    if isinstance(source, np.ndarray):
        return source  # OpenCV BGR
    raise TypeError("지원하지 않는 입력")

@torch.no_grad()
def infer_once(model, source, conf=0.35, iou=0.5, imgsz=IMGSZ):
    # classes 절대 전달 금지
    kwargs = dict(source=_to_bgr_ndarray(source),
                  conf=conf, iou=iou, imgsz=imgsz, verbose=False)
    # half는 모델 상태와 autocast로 처리
    if USE_HALF:
        with torch.cuda.amp.autocast(dtype=torch.float16):
            res = model.predict(**kwargs)
    else:
        res = model.predict(**kwargs)

    r = res[0]
    if r.boxes is None:
        return []
    boxes = r.boxes
    xyxy = boxes.xyxy.cpu().numpy()
    confs = boxes.conf.cpu().numpy()
    clsi = boxes.cls.cpu().numpy().astype(int)
    names = r.names if hasattr(r, "names") else {}
    dets = []
    for i, bb in enumerate(xyxy):
        dets.append({
            "xyxy": bb.tolist(),
            "cls": names.get(int(clsi[i]), str(int(clsi[i]))),
            "conf": float(confs[i])
        })
    return dets

def draw_boxes(img_bgr, dets, color=(0, 255, 0)):
    out = img_bgr.copy()
    for d in dets:
        x1, y1, x2, y2 = map(int, d["xyxy"])
        cv2.rectangle(out, (x1, y1), (x2, y2), color, 2)
        txt = f'{d["cls"]} {d["conf"]:.2f}'
        tw = max(60, 8 * len(txt))
        cv2.rectangle(out, (x1, max(0, y1 - 20)), (x1 + tw, y1), color, -1)
        cv2.putText(out, txt, (x1 + 3, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
    return out

def count_by_label(dets, allowlist=None):
    counts = {}
    allow = {a.strip().lower() for a in allowlist} if allowlist else None
    for d in dets:
        k = d["cls"].lower()
        if allow is None or k in allow:
            counts[k] = counts.get(k, 0) + 1
    return counts
