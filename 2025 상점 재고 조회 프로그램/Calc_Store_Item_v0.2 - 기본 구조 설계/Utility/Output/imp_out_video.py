import time
from collections import deque
from threading import Thread
from queue import Queue

import cv2

from Utility.Recognization.imp_recog import YOLORecognizer
from .imp_output import draw_result
from Def_config import FRAME_SKIP, QUEUE_MAXSIZE, TARGET_FPS

class AsyncVideoProcessor:
    def __init__(self, cap):
        self.cap = cap
        self.model = YOLORecognizer()
        self.q = Queue(maxsize=QUEUE_MAXSIZE)
        self.running = False
        self.fps_hist = deque(maxlen=30)

    def _reader(self):
        skip = 0
        while self.running:
            ok, frame = self.cap.read()
            if not ok:
                break
            skip = (skip + 1) % max(1, FRAME_SKIP)
            if FRAME_SKIP > 1 and skip != 0:
                continue
            if not self.q.full():
                self.q.put(frame)

    def _infer(self):
        last = time.time()
        while self.running:
            try:
                frame = self.q.get(timeout=0.2)
            except Exception:
                continue

            res = self.model.infer(frame)

            boxes = res.boxes.xyxy.cpu().numpy() if res.boxes is not None else []
            confs = res.boxes.conf.cpu().numpy().tolist() if res.boxes is not None else []
            cls_ids = res.boxes.cls.cpu().numpy().tolist() if res.boxes is not None else []

            names_map = getattr(res, "names", None) or getattr(self.model.model, "names", {}) or {}
            names = [names_map.get(int(i), str(i)) for i in cls_ids]

            now = time.time()
            fps = 1.0 / max(1e-6, now - last)
            last = now
            self.fps_hist.append(fps)
            avg_fps = sum(self.fps_hist) / len(self.fps_hist)
            extra = [f"FPS:{avg_fps:.1f}", f"Objs:{len(names)}"]

            vis = draw_result(frame, boxes, names, confs, extra_text=extra)
            yield vis, [{"cls_name": n, "conf": c} for n, c in zip(names, confs)]

            # 간단한 FPS 제어
            if TARGET_FPS > 0:
                delay = max(0.0, (1.0 / TARGET_FPS) - (time.time() - now))
                if delay > 0:
                    time.sleep(delay)

    def run(self):
        self.running = True
        t = Thread(target=self._reader, daemon=True)
        t.start()
        try:
            yield from self._infer()
        finally:
            self.stop()

    def stop(self):
        self.running = False
        try:
            self.cap.release()
        except Exception:
            pass
