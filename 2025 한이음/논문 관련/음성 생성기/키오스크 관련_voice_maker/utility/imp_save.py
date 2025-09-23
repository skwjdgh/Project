import os
import base64
import re

def clean_filename(s, clean=True):
    """파일명으로 사용할 수 없는 문자를 '_'로 변경합니다."""
    if not clean:
        return s
    # 파일명으로 부적합한 문자를 '_'로 치환
    return re.sub(r'[\\/*?:"<>|]', '_', s)

def save_audio_file(audio_b64, filename, output_dir, clean_filename_flag=True):
    """Base64로 인코딩된 오디오 데이터를 파일로 저장합니다."""
    try:
        audio_bytes = base64.b64decode(audio_b64)
        safe_name = clean_filename(filename, clean_filename_flag)
        filepath = os.path.join(output_dir, safe_name)
        with open(filepath, "wb") as f:
            f.write(audio_bytes)
        return True, filepath
    except Exception as e:
        # 디코딩 또는 파일 쓰기 오류 처리
        from def_exception import handle_error
        handle_error(e, f"Failed to save audio file: {filename}")
        return False, None