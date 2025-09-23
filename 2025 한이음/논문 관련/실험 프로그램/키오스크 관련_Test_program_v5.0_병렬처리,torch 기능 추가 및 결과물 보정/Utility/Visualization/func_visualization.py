# -*- coding: utf-8 -*-
"""
Visualization
- 정확도 막대그래프
- 성별/연령(4분류)/지역(파일명 첫 토큰)/기본음성(파일명 '4번째 토큰') 분포
- 기본음성(basevoice)은 nova/shimmer/echo/onyx/alloy 로 정규화
"""
import os, re
from collections import Counter
import matplotlib
matplotlib.use("Agg")  # 저장 전용 백엔드 강제 (윈도우 GUI 블로킹 방지)
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import font_manager, rcParams

def _set_korean_font():
    # 설치된 폰트 중에서 우선순위대로 선택
    candidates = ["Malgun Gothic", "NanumGothic", "AppleGothic",
                  "Noto Sans CJK KR", "Noto Sans KR"]
    available = {f.name for f in font_manager.fontManager.ttflist}
    for name in candidates:
        if name in available:
            rcParams["font.family"] = name
            break
    rcParams["axes.unicode_minus"] = False  # 음수 기호 깨짐 방지

_set_korean_font()

# ---- 색상 유틸 ----
def _get_colors(n: int, cmap_name: str = "tab20"):
    """막대 개수 n개에 대해 서로 다른 색상 리스트 생성."""
    cmap = plt.get_cmap(cmap_name)
    base = list(getattr(cmap, "colors", []))
    if not base:  # 연속형 컬러맵 대비
        base = [cmap(i / max(n, 1)) for i in range(n)]
    if n <= len(base):
        return base[:n]
    # 항목이 더 많으면 순환
    return [base[i % len(base)] for i in range(n)]

# ---- 기본 유틸 ----
def _norm(s: str) -> str:
    """파일명 파싱용: 영숫자/한글만 남김."""
    return re.sub(r"[^가-힣A-Za-z0-9]+", "", str(s)).lower()

def _only_letters(s: str) -> str:
    """소문자 + 알파벳만 남김 (basevoice 식별용)."""
    return re.sub(r"[^a-z]+", "", str(s).lower())

# basevoice 정규화 룰 (서브스트링 매칭)
_BASEVOICE_ALIASES = {
    "nova":    ("nova", "nv", "tts_nova", "novav2", "novax"),
    "shimmer": ("shimmer", "shmr", "tts_shimmer"),
    "echo":    ("echo", "ec", "tts_echo"),
    "onyx":    ("onyx", "onx", "tts_onyx"),
    "alloy":   ("alloy", "aly", "tts_alloy"),
}
_BASEVOICE_ORDER = ["nova", "shimmer", "echo", "onyx", "alloy"]

def _canon_basevoice_from_parts(parts: list[str]) -> str:
    """parts[4] 우선, 실패 시 전체 토큰에서 서브스트링으로 식별."""
    def _map_one(s: str) -> str:
        ss = _only_letters(s)
        if not ss:
            return ""
        for canon, aliases in _BASEVOICE_ALIASES.items():
            for a in aliases:
                if _only_letters(a) in ss:
                    return canon
        return ""
    # 4번째 토큰(0-based index 4) 우선
    if len(parts) > 4:
        m = _map_one(parts[4])
        if m:
            return m
    # 폴백: 전체 탐색
    for p in parts:
        m = _map_one(p)
        if m:
            return m
    return "unknown"

def _tokens(fname: str):
    """
    파일명 규칙(예시: 강원도_가족관계증명서_child_female_nova_0059.mp3):
    - 0번째: 지역(region)          -> parts[0]
    - 2번째: 연령(child/youngadult/middleaged/senior) -> parts[2]
    - 3번째: 성별 (male/female)    -> 어디에 있어도 식별
    - 4번째: 기본음성(basevoice)   -> parts[4] (원칙), 필요 시 전체에서 보정 탐색
    """
    name = os.path.splitext(os.path.basename(fname))[0]
    parts = name.split("_")

    region = parts[0] if len(parts) > 0 else "unknown"

    age_raw = parts[2] if len(parts) > 2 else "unknown"
    mp_age = {
        "child":"child","kid":"child","children":"child",
        "youngadult":"youngadult","young_adult":"youngadult","yadult":"youngadult","youthadult":"youngadult",
        "middleaged":"middleaged","middle_aged":"middleaged","midaged":"middleaged","middle":"middleaged",
        "senior":"senior","elderly":"senior","old":"senior",
    }
    age = mp_age.get(_norm(age_raw), "unknown")

    # 성별은 어디에 있어도 male/female을 탐지
    gender = "unknown"
    for p in parts:
        q = _norm(p)
        if q in ("male", "man", "m"):
            gender = "male"; break
        if q in ("female", "woman", "f"):
            gender = "female"; break

    # 기본음성은 nova/shimmer/echo/onyx/alloy 중 하나로 정규화
    basevoice = _canon_basevoice_from_parts(parts)

    return region, age, gender, basevoice

# ---- 공통 바차트 저장 ----
def _save_bar(counter: Counter, title: str, outpath: str, order=None, top=None, xlabel="", ylabel="개수"):
    """카운터 → 정렬/상위 N → 막대그래프 저장(막대별 서로 다른 색 적용)."""
    items = counter.items()
    if order:
        items = [(k, counter.get(k, 0)) for k in order]
    else:
        items = sorted(items, key=lambda x: (-x[1], str(x[0])))
        if top:
            items = items[:top]
    labels = [str(k) for k, _ in items]
    values = [int(v) for _, v in items]

    colors = _get_colors(len(labels), cmap_name="tab20")

    plt.figure(figsize=(10, 5))
    plt.bar(labels, values, color=colors)  # ← 막대별 다른 색
    plt.title(title); plt.xlabel(xlabel); plt.ylabel(ylabel)
    plt.xticks(rotation=30, ha="right")
    for i, v in enumerate(values):
        ytxt = v + (max(values) * 0.02 if values else 0.5)
        plt.text(i, ytxt, f"{v}", ha="center", va="bottom", fontsize=9)
    plt.tight_layout()
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    plt.savefig(outpath, dpi=150); plt.close()

# ---- 플롯들 ----
def plot_accuracy(summary_df: pd.DataFrame, outpath: str):
    """조건별 정확도(%) 막대그래프(막대별 다른 색)."""
    labels = summary_df["condition"].tolist()
    values = summary_df["accuracy"].tolist()
    colors = _get_colors(len(labels), cmap_name="tab20")

    plt.figure(figsize=(7, 4))
    plt.bar(labels, values, color=colors)  # ← 막대별 다른 색
    plt.ylabel("Accuracy (%)"); plt.title("Condition-wise Accuracy"); plt.ylim(0, 100)
    for i, v in enumerate(values):
        plt.text(i, v + 1, f"{v:.1f}%", ha="center", va="bottom", fontsize=9)
    plt.tight_layout(); os.makedirs(os.path.dirname(outpath), exist_ok=True)
    plt.savefig(outpath, dpi=150); plt.close()

def plot_gender_ratio(filenames, outpath):
    """성별 분포(male/female)."""
    cnt = Counter()
    for f in filenames:
        _, _, g, _ = _tokens(f)
        if g in ("male", "female"):
            cnt[g] += 1
    _save_bar(cnt, "성별 분포", outpath, order=["male", "female"], xlabel="성별")

def plot_age_distribution(filenames, outpath):
    """연령 4분류(child/youngadult/middleaged/senior + unknown)."""
    cnt = Counter()
    for f in filenames:
        _, a, _, _ = _tokens(f)
        cnt[a] += 1
    _save_bar(cnt, "연령 분포", outpath,
              order=["child", "youngadult", "middleaged", "senior"],
              xlabel="연령대")

def plot_region_distribution(filenames, outpath, top_n: int = 20):
    """지역 분포(파일명 첫 토큰). '지역', 'unknown' 제외, 상위 N만 표시."""
    cnt = Counter()
    for f in filenames:
        r, _, _, _ = _tokens(f)
        rn = _norm(r)
        if not rn or rn in ("지역", "unknown"):
            continue
        cnt[rn] += 1
    _save_bar(cnt, "지역 분포 (상위)", outpath, top=top_n, xlabel="지역")

def plot_basevoice_distribution(filenames, outpath):
    """
    기본 음성 분포: nova / shimmer / echo / onyx / alloy
    - 순서 고정 출력
    """
    cnt = Counter()
    for f in filenames:
        _, _, _, b = _tokens(f)
        cnt[b] += 1
    _save_bar(cnt, "기본 음성 분포", outpath, order=_BASEVOICE_ORDER, xlabel="기본 음성")
