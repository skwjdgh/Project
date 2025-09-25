import os, time
from werkzeug.utils import secure_filename

ALLOWED_IMG = {"jpg","jpeg","png","bmp"}
ALLOWED_VID = {"mp4","avi","mov","mkv"}

def save_upload(file, out_dir):
    fn = secure_filename(file.filename or "")
    if "." not in fn:
        raise ValueError("파일명 오류")
    ext = fn.rsplit(".",1)[-1].lower()
    if ext not in (ALLOWED_IMG | ALLOWED_VID):
        raise ValueError("허용되지 않는 파일 형식")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"{int(time.time()*1000)}_{fn}")
    file.save(path)
    return path.replace("\\","/")
