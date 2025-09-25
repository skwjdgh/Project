from flask import Flask, request, jsonify, Response, render_template
from ultralytics import YOLO
import os, cv2, base64, numpy as np, time, traceback
from threading import Lock, Thread
import torch

# CUDA/성능 튜닝
torch.backends.cudnn.benchmark = True
try:
    torch.set_float32_matmul_precision("high")
except Exception:
    pass
cv2.setNumThreads(0)

from Def_exception import register_error_handlers, BadRequestError
from Utility.Imp_input import save_upload
from Utility.Imp_list import normalize_classes
from Utility.Imp_calc import infer_once, draw_boxes, count_by_label
from Utility.Imp_output import save_image_result, save_video_result

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config["UPLOAD_FOLDER"] = "static/out"
app.config["MAX_CONTENT_LENGTH"] = 256 * 1024 * 1024
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

MODEL_LOCK = Lock()
MODEL_PATH = "Model/yolov8x-worldv2.pt"
if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(f"모델 파일 없음: {MODEL_PATH}")
MODEL = YOLO(MODEL_PATH)

# 디바이스 고정 및 half
DEV = "cuda:0" if torch.cuda.is_available() else "cpu"
try:
    MODEL.to(DEV)
except Exception:
    pass
try:
    MODEL.fuse()
except Exception:
    pass
if DEV.startswith("cuda"):
    try:
        MODEL.model.half()
    except Exception:
        pass

ACTIVE_CLASSES = ["person"]
LAST_COUNTS = {}
LAST_FRAME_JPG = None
JPG_PARAMS = [int(cv2.IMWRITE_JPEG_QUALITY), 70]  # 전송 경량화

# 서버 카메라 상태
CAM = {"cap": None, "thread": None, "running": False, "lock": Lock(), "source": 0}

register_error_handlers(app)

def _model_device_str():
    try:
        return str(next(MODEL.model.parameters()).device)
    except Exception:
        return DEV

def _move_clip_to_device(core, device_str: str):
    clip = getattr(core, "clip_model", None)
    try:
        if clip and hasattr(clip, "model"):
            clip.model.to(device_str)
    except Exception:
        pass

def set_world_classes_once(labels):
    """YOLO-World 텍스트 프롬프트 1회 설정. predict()에는 classes 전달 금지."""
    global ACTIVE_CLASSES
    ACTIVE_CLASSES = labels
    core = getattr(MODEL, "model", None)
    dev = _model_device_str()
    try:
        if core and hasattr(core, "set_classes"):
            _move_clip_to_device(core, dev)
            core.set_classes(labels)
        elif hasattr(MODEL, "set_classes"):
            MODEL.set_classes(labels)
        print(f"[OVD] classes -> {labels} on {dev}")
    except Exception:
        print("[OVD] SET_CLASSES_ERROR\n", traceback.format_exc())
        raise BadRequestError("클래스 설정 실패")

# ---------- HTML ----------
@app.get("/")
def index():
    return render_template("index.html")

# ---------- 클래스 업데이트 ----------
@app.post("/update_classes")
def update_classes():
    raw = request.form.get("classes", "")
    labels = normalize_classes(raw)
    if not labels:
        raise BadRequestError("classes가 비었습니다")
    with MODEL_LOCK:
        set_world_classes_once(labels)
    return jsonify({"ok": True, "active_classes": ACTIVE_CLASSES})

# ---------- 이미지 추론 ----------
@app.post("/infer/image")
def infer_image():
    f = request.files.get("file")
    plist_raw = request.form.get("product_list", "")
    if not f or not plist_raw:
        raise BadRequestError("file, product_list 필요")
    img_path = save_upload(f, app.config["UPLOAD_FOLDER"])
    labels = normalize_classes(plist_raw)
    with MODEL_LOCK:
        if labels and labels != ACTIVE_CLASSES:
            set_world_classes_once(labels)
        dets = infer_once(MODEL, img_path)
    counted = count_by_label(dets, labels or ACTIVE_CLASSES)
    out_path = save_image_result(img_path, lambda im: draw_boxes(im, dets))
    return jsonify({"counts": counted, "image_url": f"/{out_path}"}), 200

# ---------- 비디오 추론 ----------
@app.post("/infer/video")
def infer_video():
    f = request.files.get("file")
    plist_raw = request.form.get("product_list", "")
    if not f or not plist_raw:
        raise BadRequestError("file, product_list 필요")
    vid_path = save_upload(f, app.config["UPLOAD_FOLDER"])
    labels = normalize_classes(plist_raw)
    with MODEL_LOCK:
        if labels and labels != ACTIVE_CLASSES:
            set_world_classes_once(labels)
        out_path, final_counts = save_video_result(
            vid_path, lambda frame: infer_once(MODEL, frame)
        )
    base_labels = labels or ACTIVE_CLASSES
    final_counts = {k: int(final_counts.get(k, 0)) for k in base_labels}
    return jsonify({"counts": final_counts, "video_url": f"/{out_path}"}), 200

# ---------- 브라우저 카메라 폴링 ----------
@app.post("/infer/live_frame")
def infer_live_frame():
    file = request.files.get("frame")
    if not file:
        raise BadRequestError("frame 누락")
    data = file.read()
    if not data:
        raise BadRequestError("빈 프레임")

    npdata = np.frombuffer(data, np.uint8)
    img = cv2.imdecode(npdata, cv2.IMREAD_COLOR)
    if img is None:
        raise BadRequestError("프레임 디코드 실패")

    try:
        with MODEL_LOCK:
            dets = infer_once(MODEL, img)
    except Exception:
        print("LIVE INFER ERROR:\n", traceback.format_exc())
        return jsonify({"error": {"code": "INFER_ERROR", "message": "infer failed"}}), 500

    vis = draw_boxes(img, dets)
    counts = count_by_label(dets, ACTIVE_CLASSES)

    global LAST_COUNTS, LAST_FRAME_JPG
    LAST_COUNTS = counts.copy()
    ok, buf = cv2.imencode(".jpg", vis, JPG_PARAMS)
    if ok:
        LAST_FRAME_JPG = buf.tobytes()
        b64 = base64.b64encode(LAST_FRAME_JPG).decode("ascii")
        return jsonify({"counts": counts, "image_b64": f"data:image/jpeg;base64,{b64}"}), 200
    else:
        return jsonify({"counts": counts, "image_b64": None}), 200

@app.get("/counts/live")
def counts_live():
    return jsonify({"counts": LAST_COUNTS, "active_classes": ACTIVE_CLASSES}), 200

# ---------- 서버 카메라 스트리밍 ----------
def _open_capture(src):
    if isinstance(src, int):
        cap = cv2.VideoCapture(src, cv2.CAP_DSHOW)  # MSMF 이슈 회피
    else:
        cap = cv2.VideoCapture(src)
    try:
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    except Exception:
        pass
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    return cap

def _cam_loop():
    target_dt = 1.0 / 15.0  # 15fps 목표
    global LAST_COUNTS, LAST_FRAME_JPG
    while CAM["running"]:
        t0 = time.time()
        cap = CAM["cap"]
        if not cap:
            break
        ok, frame = cap.read()
        if not ok:
            time.sleep(0.01)
            continue
        with MODEL_LOCK:
            dets = infer_once(MODEL, frame)  # FP16/IMGSZ는 Imp_calc에서 처리
        vis = draw_boxes(frame, dets)
        counts = count_by_label(dets, ACTIVE_CLASSES)
        with CAM["lock"]:
            LAST_COUNTS = counts
            ok2, buf = cv2.imencode(".jpg", vis, JPG_PARAMS)
            if ok2:
                LAST_FRAME_JPG = buf.tobytes()
        dt = time.time() - t0
        if dt < target_dt:
            time.sleep(target_dt - dt)

def _ensure_cam_stopped():
    if CAM["running"]:
        CAM["running"] = False
        thr = CAM["thread"]
        if thr:
            thr.join(timeout=1.5)
    if CAM["cap"]:
        try:
            CAM["cap"].release()
        except:
            pass
    CAM["cap"] = None
    CAM["thread"] = None

@app.post("/camera/start")
def camera_start():
    src = request.form.get("source", "0")
    source = int(src) if src.isdigit() else src
    with CAM["lock"]:
        _ensure_cam_stopped()
        cap = _open_capture(source)
        if not cap or not cap.isOpened():
            return jsonify({"error": {"code": "CAM_OPEN_FAIL", "message": "카메라 열기 실패"}}), 500
        CAM["cap"] = cap
        CAM["source"] = source
        CAM["running"] = True
        CAM["thread"] = Thread(target=_cam_loop, daemon=True)
        CAM["thread"].start()
    return jsonify({"ok": True})

@app.post("/camera/stop")
def camera_stop():
    with CAM["lock"]:
        _ensure_cam_stopped()
    return jsonify({"ok": True})

@app.get("/stream/detect")
def stream_detect():
    try:
        fps = float(request.args.get("fps", "15"))
        dt = 1.0 / max(1.0, fps)
    except Exception:
        dt = 1.0 / 15.0

    def gen():
        boundary = b"--frame\r\n"
        while True:
            if not CAM["running"]:
                time.sleep(0.05)
                continue
            with CAM["lock"]:
                frame = LAST_FRAME_JPG
            if frame is None:
                time.sleep(0.01)
                continue
            yield boundary + b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
            time.sleep(dt)

    return Response(gen(), mimetype="multipart/x-mixed-replace; boundary=frame")

# ---------- 상태 ----------
@app.get("/status")
def status():
    return jsonify({
        "active_classes": ACTIVE_CLASSES,
        "device": _model_device_str(),
        "server_cam": CAM["running"]
    }), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False, threaded=True)
