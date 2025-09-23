# -*- coding: utf-8 -*-
"""
독립 실험 단위별 성능 집계/시각화 스크립트
- 실행 위치: data_reviewed/
- 입력: input_data/*.csv  (열: file,keyword,text_a,text_b,text_c,text_d,match_a,match_b,match_c,match_d,condition)
- 출력: summary_results.csv + 그래프 (PNG)
"""

import os, re, glob
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt

# -----------------------------
# 설정
# -----------------------------
DATA_DIR = "input_data"
OUT_DIR  = "."

AGE_KEYS    = ["child", "youngadult", "middleaged", "senior"]
REGION_KEYS = ["표준어","경상도","강원도","충청도","전라도","제주도"]
VOICE_KEYS  = ["nova","shimmer","echo","onyx","alloy"]
VALID_NOISES = [0, 5, 10, 20, 30]

COLORS = {
    "A":"#9467bd","B":"#2ca02c","C":"#ff7f0e","D":"#d62728",
    "gender": {"male":"#1f77b4","female":"#e377c2"},
    "age": {"child":"#2ca02c","youngadult":"#1f77b4","middleaged":"#ff7f0e","senior":"#d62728"},
    "voice": {"nova":"#1f77b4","shimmer":"#aec7e8","echo":"#ff7f0e","onyx":"#98df8a","alloy":"#2ca02c"},
    "regions_cycle":["#1f77b4","#ff7f0e","#2ca02c","#d62728","#9467bd","#8c564b"]
}

# -----------------------------
# 한글 폰트
# -----------------------------
def set_korean_font():
    for name in ["Malgun Gothic","AppleGothic","NanumGothic"]:
        try:
            matplotlib.rcParams["font.family"] = name
            break
        except Exception:
            continue
    matplotlib.rcParams["axes.unicode_minus"] = False
set_korean_font()

# -----------------------------
# 유틸
# -----------------------------
def parse_gender(s: str):
    if not s: return None
    s = str(s).lower()
    if "female" in s: return "female"   # female 우선
    if "male"   in s: return "male"
    return None

def contains_any(s: str, keys):
    s = (s or "").lower()
    for k in keys:
        if k.lower() in s:
            return k
    return None

def parse_basevoice(s: str):
    if not s: return None
    s = str(s).lower()
    for k in VOICE_KEYS:
        if k in s:
            return k
    return None

def extract_noise_from(name: str):
    if not name: return None
    m = re.search(r"(?:노이즈|noise)\s*([0-9]+)", str(name).lower())
    if m:
        val = int(m.group(1))
        if val in VALID_NOISES:   # 0,5,10,20,30만 허용
            return val
    return None

def bar_save(labels, values, title, fname, xlabel="", ylabel="정확도 (%)", colors=None, ylim=(0,100)):
    plt.figure(figsize=(6,4))
    plt.bar(labels, values, color=colors)
    plt.title(title)
    if xlabel: plt.xlabel(xlabel)
    if ylabel: plt.ylabel(ylabel)
    if ylim:   plt.ylim(*ylim)
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, fname), dpi=150)
    plt.close()

# -----------------------------
# 데이터 읽기 + 실험별 집계
# -----------------------------
results, all_dfs = [], []
files = sorted(glob.glob(os.path.join(DATA_DIR, "*.csv")))
if not files:
    raise FileNotFoundError(f"No CSV files found in {DATA_DIR}")

for f in files:
    df = pd.read_csv(f)
    for col in ["match_a","match_b","match_c","match_d"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")  # NaN 유지

    file_name = os.path.basename(f)
    noise_level = extract_noise_from(file_name)
    if noise_level is None:
        continue

    acc_a = df["match_a"].mean(skipna=True)*100
    acc_b = df["match_b"].mean(skipna=True)*100
    acc_c = df["match_c"].mean(skipna=True)*100
    acc_d = df["match_d"].mean(skipna=True)*100

    results.append({"file": file_name, "noise": noise_level,
                    "A": acc_a, "B": acc_b, "C": acc_c, "D": acc_d})

    # 메타데이터
    df["gender"]    = df["file"].map(parse_gender)
    df["age"]       = df["file"].map(lambda s: contains_any(s, AGE_KEYS))
    df["region"]    = df["file"].map(lambda s: contains_any(s, REGION_KEYS))
    df["basevoice"] = df["file"].map(parse_basevoice)
    df["noise"]     = noise_level
    all_dfs.append(df)

# 요약 DF: 허용 노이즈만
summary_df = pd.DataFrame(results)
summary_df = summary_df[summary_df["noise"].isin(VALID_NOISES)].sort_values("noise")
summary_df.to_csv(os.path.join(OUT_DIR,"summary_results.csv"), index=False, encoding="utf-8-sig")
print("=== 실험 요약 ===")
print(summary_df)

# 노이즈0 디버그
noise0_df = summary_df[summary_df["noise"] == 0]
if not noise0_df.empty:
    print("\n=== 노이즈0 조건별 정확도 확인 ===")
    print(noise0_df.to_string(index=False))
else:
    print("\n⚠️ 노이즈0 실험 결과가 없습니다.")

# -----------------------------
# 1) 조건별 막대그래프 (노이즈별)
# -----------------------------
for cond, c in [("A",COLORS["A"]),("B",COLORS["B"]),("C",COLORS["C"]),("D",COLORS["D"])]:
    bar_save(summary_df["noise"], summary_df[cond],
             f"조건 {cond} 정확도 (노이즈별)", f"accuracy_{cond}.png",
             xlabel="노이즈 레벨", ylabel="정확도 (%)", colors=[c]*len(summary_df))

# -----------------------------
# 2) 노이즈별 성능 변화 (라인)
# -----------------------------
plt.figure(figsize=(8,5))
for cond, c in [("A",COLORS["A"]),("B",COLORS["B"]),("C",COLORS["C"]),("D",COLORS["D"])]:
    plt.plot(summary_df["noise"], summary_df[cond], marker="o", label=cond, color=c)
plt.title("노이즈 강도별 조건별 성능 변화 (%)")
plt.xlabel("노이즈 레벨")
plt.ylabel("정확도 (%)")
plt.ylim(0,100)
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "noise_performance.png"), dpi=150)
plt.close()

# -----------------------------
# 3) 메타데이터 분포 (허용 노이즈만)
# -----------------------------
if all_dfs:
    meta_df = pd.concat(all_dfs, ignore_index=True)
    meta_df = meta_df[meta_df["noise"].isin(VALID_NOISES)]

    # 성별
    gr = (meta_df["gender"].dropna().value_counts(normalize=True)*100)
    if not gr.empty:
        bar_save(gr.index.tolist(), gr.values.tolist(),
                 "평균 성별 분포 (%)", "gender_distribution.png",
                 xlabel="", ylabel="비율 (%)",
                 colors=[COLORS["gender"][g] for g in gr.index.tolist()], ylim=None)

    # 연령
    ar = (meta_df["age"].dropna().value_counts(normalize=True)*100)
    if not ar.empty:
        bar_save(ar.index.tolist(), ar.values.tolist(),
                 "평균 연령 분포 (%)", "age_distribution.png",
                 xlabel="", ylabel="비율 (%)",
                 colors=[COLORS["age"][a] for a in ar.index.tolist()], ylim=None)

    # 지역
    rr = (meta_df["region"].dropna().value_counts(normalize=True)*100)
    if not rr.empty:
        labels = rr.index.tolist()
        colors = [COLORS["regions_cycle"][i % len(COLORS["regions_cycle"])] for i in range(len(labels))]
        bar_save(labels, rr.values.tolist(),
                 "평균 지역 분포 (%)", "region_distribution.png",
                 xlabel="", ylabel="비율 (%)", colors=colors, ylim=None)

    # 기본 음성
    vr = (meta_df["basevoice"].dropna().value_counts(normalize=True)*100)
    if not vr.empty:
        labels = vr.index.tolist()
        values = vr.values.tolist()
        vcolors = [COLORS["voice"][v] for v in labels]
        bar_save(labels, values,
                 "기본 음성 분포 (%)", "basevoice_distribution.png",
                 xlabel="", ylabel="비율 (%)", colors=vcolors, ylim=None)

print("\n✅ summary_results.csv 및 그래프 저장 완료.")
