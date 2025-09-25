from pathlib import Path

# 경로
BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "Model"
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# 모델
MODEL_WEIGHT = str(MODEL_DIR / "yolo_world.pt")  # Ultralytics 호환 .pt
CONF_THRES = 0.25
IOU_THRES = 0.5
USE_HALF = True  # CUDA일 때만 적용

# 스트리밍
CAM_INDEX = 0
TARGET_FPS = 15
FRAME_SKIP = 1          # 1이면 스킵 없음. 2면 1프레임 건너뜀
QUEUE_MAXSIZE = 4

# 웹
HOST = "0.0.0.0"
PORT = 5000
DEBUG = False
