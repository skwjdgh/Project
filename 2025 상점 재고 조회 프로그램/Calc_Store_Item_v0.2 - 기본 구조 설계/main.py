import io
import time
from pathlib import Path
from threading import Lock
from collections import deque

import cv2
from flask import Flask, render_template, request, Response, jsonify

from Def_config import HOST, PORT, DEBUG, UPLOAD_DIR, CAM_INDEX
from Utility.Input.imp_input import load_image, open_video, open_camera
from Utility.Output.imp_out_image import process_image
from Utility.Output.imp_out_video import AsyncVideoProcessor
from Utility.Output.imp_out_camera import live_camera_stream
from Utility.Calc_Output.imp_calc_output import accumulate
from Utility.Category.imp_category import to_category_counts

app = Flask(__name__, template_folder="Templates")

# 상태
latest_frame = None
latest_dets = []
agg_window = deque(maxlen=100)  # 최근 프레임들의 검출 누적
stream_lock = Lock()

# 카메라/비디오 러너 핸들
current_stream_gen = None
stream_mode = "idle"  # 'idle'|'camera'|'video'|'image'

@app.after_request
def nocache(resp):
    resp.headers["Cache-Control"] = "no-store"
    return resp

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/ui/input")
def ui_input():
    return render_template("UI/Input.html")

@app.route("/ui/category")
def ui_category():
    return render_template("UI/Category.html")

@app.route("/ui/output")
def ui_output():
    return render_template("UI/Output.html")

@app.route("/ui/calc_output")
def ui_calc_output():
    return render_template("UI/Calc_Output.html")

@app.post("/api/upload-image")
def api_upload_image():
    global latest_frame, latest_dets, stream_mode, current_stream_gen
    # 이전 스트림 정리
    current_stream_gen = None
    stream_mode = "idle"

    f = request.files.get("image")
    if not f:
        return "no file", 400
    p = UPLOAD_DIR / f.filename
    f.save(p)
    img = load_image(str(p))
    vis, dets = process_image(img)
    latest_frame = vis
    latest_dets = dets
    agg_window.clear()
    agg_window.append(dets)
    stream_mode = "image"
    return "ok", 200

@app.post("/api/upload-video")
def api_upload_video():
    global current_stream_gen, stream_mode, latest_dets
    # 이전 스트림 정리
    current_stream_gen = None
    stream_mode = "idle"

    f = request.files.get("video")
    if not f:
        return "no file", 400
    p = UPLOAD_DIR / f.filename
    f.save(p)
    cap = open_video(str(p))
    runner = AsyncVideoProcessor(cap)
    current_stream_gen = runner.run()
    latest_dets = []
    agg_window.clear()
    stream_mode = "video"
    return "ok", 200

@app.post("/api/start-camera")
def api_start_cam():
    global current_stream_gen, stream_mode, latest_dets
    # 이전 스트림 정리
    current_stream_gen = None
    stream_mode = "idle"

    current_stream_gen = live_camera_stream(CAM_INDEX)
    latest_dets = []
    agg_window.clear()
    stream_mode = "camera"
    return "ok", 200

@app.post("/api/stop-camera")
def api_stop_cam():
    global current_stream_gen, stream_mode
    current_stream_gen = None
    stream_mode = "idle"
    return "ok", 200

@app.get("/api/category")
def api_category():
    cats = to_category_counts(latest_dets)
    return jsonify(cats)

@app.get("/api/aggregate")
def api_aggregate():
    return jsonify(accumulate(list(agg_window)))

def mjpeg_generator():
    global latest_frame, latest_dets, current_stream_gen, stream_mode, agg_window
    while True:
        if stream_mode == "image":
            if latest_frame is None:
                time.sleep(0.05); continue
            frame = latest_frame.copy()
            ok, buf = cv2.imencode(".jpg", frame)
            if not ok:
                time.sleep(0.01); continue
            yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + buf.tobytes() + b"\r\n")
            time.sleep(0.2)

        elif stream_mode in ("camera", "video"):
            if current_stream_gen is None:
                time.sleep(0.05); continue
            try:
                frame, dets = next(current_stream_gen)
                latest_dets = dets
                agg_window.append(dets)
                ok, buf = cv2.imencode(".jpg", frame)
                if not ok:
                    continue
                yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + buf.tobytes() + b"\r\n")
            except StopIteration:
                current_stream_gen = None
                stream_mode = "idle"
            except Exception:
                time.sleep(0.01)
        else:
            time.sleep(0.05)

@app.get("/stream")
def stream():
    def guarded():
        with stream_lock:
            yield from mjpeg_generator()
    return Response(guarded(), mimetype="multipart/x-mixed-replace; boundary=frame")

if __name__ == "__main__":
    app.run(host=HOST, port=PORT, debug=DEBUG, threaded=True)
