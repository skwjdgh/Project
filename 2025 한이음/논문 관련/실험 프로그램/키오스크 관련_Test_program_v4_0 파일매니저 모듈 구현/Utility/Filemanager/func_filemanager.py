# -*- coding: utf-8 -*-
"""
Filemanager
- 오디오/CSV 경로 처리와 GT 매핑 유틸
- 탐색 범위를 '프로젝트 루트'로 제한해 광범위 rglob로 인한 멈춤을 방지
"""
import os, csv, re
from pathlib import Path
from typing import List, Dict
from def_exception import DataLoadError
import def_config as config

# 프로젝트 루트(= .../Test_program). 이 파일: .../Utility/Filemanager/func_filemanager.py
_PROJECT_ROOT = Path(__file__).resolve().parents[2]

def stem_noext(p: str) -> str:
    """파일명에서 확장자 제거한 스템."""
    return os.path.splitext(os.path.basename(p))[0]

def _norm(s: str) -> str:
    return re.sub(r"[^0-9a-z가-힣]", "", str(s).lower())

def resolve_csv_path(path_like: str) -> str:
    """
    CSV 경로 해석(멈춤 방지):
    1) 절대/상대 경로 직접 확인
    2) CWD 기준 확인
    3) 프로젝트 루트 기준 확인
    4) 파일명만 주면 '프로젝트 루트' 내부만 rglob
    """
    p = Path(path_like)
    if p.is_file():
        return str(p.resolve())

    for base in (Path.cwd(), _PROJECT_ROOT):
        cand = (base / path_like)
        if cand.is_file():
            return str(cand.resolve())

    name = Path(path_like).name
    has_sep = any(s in path_like for s in (os.sep, "/", "\\"))
    if name and not has_sep:
        # 광범위 탐색 금지: 프로젝트 루트 내부만 탐색
        for found in _PROJECT_ROOT.rglob(name):
            if found.is_file():
                return str(found.resolve())

    raise DataLoadError(f"Ground truth csv not found: {path_like}")

def read_csv_rows(csv_path: str) -> List[dict]:
    """인코딩(utf-8/utf-8-sig/cp949) 자동 시도."""
    for enc in ("utf-8", "utf-8-sig", "cp949"):
        try:
            with open(csv_path, "r", encoding=enc, newline="") as f:
                return list(csv.DictReader(f))
        except UnicodeDecodeError:
            continue
    raise DataLoadError(f"CSV decode failed: {csv_path}")

def list_audio_files(root: str) -> List[str]:
    """
    지원 확장자 파일 재귀 수집.
    - root 절대/상대 허용
    - 없으면 CWD/root → _PROJECT_ROOT/root 순으로 재시도
    """
    exts = getattr(config, "AUDIO_EXTS", {".wav", ".mp3", ".m4a", ".flac", ".ogg"})
    bases = [Path(root), Path.cwd() / root, _PROJECT_ROOT / root]
    base = next((b for b in bases if b.is_dir()), None)
    if base is None:
        raise DataLoadError(f"Audio dir not found: {root} | tried={bases}")

    files: List[str] = []
    for ext in exts:
        files += [str(p) for p in base.rglob(f"*{ext}")]
    files = sorted(set(files))
    if not files:
        raise DataLoadError("No audio files found")
    return files

def _pick_keyword_col(headers: List[str]) -> str:
    if getattr(config, "GT_KEYWORD_COL", "") in headers:
        return getattr(config, "GT_KEYWORD_COL")
    for c in ["keyword","label","answer","text","phrase","utterance",
              "키워드","정답","문구","문장","대사","텍스트","내용","종류"]:
        if c in headers:
            return c
    return ""

def _pick_file_col(headers: List[str]) -> str:
    if getattr(config, "GT_FILE_COL", "") in headers:
        return getattr(config, "GT_FILE_COL")
    for c in ["file","filename","filepath","path","audio","wav","mp3",
              "파일","파일명","경로","음성","오디오","파일경로"]:
        if c in headers:
            return c
    return ""

def _map_by_filecol(rows: List[dict], file_col: str, kw_col: str) -> Dict[str, str]:
    m: Dict[str, str] = {}
    for r in rows:
        f = (r.get(file_col) or "").strip()
        k = (r.get(kw_col) or "").strip()
        if f and k:
            m[stem_noext(f)] = k
    return m

def _map_by_contains(rows: List[dict], kw_col: str, audio_files: List[str]) -> Dict[str, str]:
    cand = [(r.get(kw_col).strip(), _norm(r.get(kw_col).strip()))
            for r in rows if r.get(kw_col)]
    m: Dict[str, str] = {}
    for af in audio_files:
        stem = stem_noext(af)
        norm = _norm(stem) + _norm(os.path.dirname(af))
        hit = [ori for (ori, nk) in cand if nk and nk in norm]
        if hit:
            m[stem] = max(hit, key=lambda s: len(_norm(s)))
    return m

def build_ground_truth_map(csv_path: str, audio_files: List[str],
                           kw_col_hint: str = "", file_col_hint: str = "") -> Dict[str, str]:
    """
    GT 매핑:
    - 파일 컬럼이 있으면 정확 매핑
    - 없으면 파일명/경로에 키워드 부분일치로 추정 매핑
    """
    real = resolve_csv_path(csv_path)
    rows = read_csv_rows(real)
    headers = list(rows[0].keys())

    kw_col = kw_col_hint if kw_col_hint in headers else _pick_keyword_col(headers)
    if not kw_col:
        raise DataLoadError(f"Keyword column not found. headers={headers}")

    file_col = file_col_hint if file_col_hint in headers else _pick_file_col(headers)

    if file_col:
        gt = _map_by_filecol(rows, file_col, kw_col)
        if not gt:
            raise DataLoadError(f"No valid rows for file_col='{file_col}'")
        return gt

    gt = _map_by_contains(rows, kw_col, audio_files)
    if not gt:
        raise DataLoadError("No filename matched any keyword in CSV.")
    return gt
