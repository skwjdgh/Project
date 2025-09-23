# -*- coding: utf-8 -*-
import os
from collections import Counter
import re
import matplotlib.pyplot as plt
import pandas as pd

def _norm(s: str) -> str:
    return re.sub(r"[^가-힣A-Za-z0-9]+", "", str(s)).lower()

def _tokens(fname: str):
    """파일명에서 (지역, 연령, 성별, 기본음성) 추출.
       규칙: 0=지역, 2=연령(child/youngadult/middleaged/senior), 3=기본음성
       성별은 어디에 있어도 male/female 문자열을 탐지."""
    name = os.path.splitext(os.path.basename(fname))[0]
    parts = name.split("_")
    region = parts[0] if len(parts) > 0 else "unknown"

    age_raw = parts[2] if len(parts) > 2 else "unknown"
    mp = {
        "child":"child","kid":"child","children":"child",
        "youngadult":"youngadult","young_adult":"youngadult","yadult":"youngadult","youthadult":"youngadult",
        "middleaged":"middleaged","middle_aged":"middleaged","midaged":"middleaged","middle":"middleaged",
        "senior":"senior","elderly":"senior","old":"senior",
    }
    age = mp.get(_norm(age_raw), "unknown")

    basevoice = parts[3] if len(parts) > 3 else "unknown"

    gender = "unknown"
    for p in parts:
        p2 = _norm(p)
        if p2 in ("male","man","m"):    gender = "male";   break
        if p2 in ("female","woman","f"): gender = "female"; break

    return region, age, gender, basevoice

def _save_bar(counter: Counter, title: str, outpath: str, order=None, top=None, xlabel="", ylabel="개수"):
    items = counter.items()
    if order:
        items = [(k, counter.get(k, 0)) for k in order]
    else:
        items = sorted(items, key=lambda x: (-x[1], str(x[0])))
        if top:
            items = items[:top]

    labels = [str(k) for k,_ in items]
    values = [int(v) for _,v in items]

    plt.figure(figsize=(10,5))
    plt.bar(labels, values)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    plt.savefig(outpath, dpi=150)
    plt.close()

def plot_accuracy(summary_df: pd.DataFrame, outpath: str):
    plt.figure(figsize=(7,4))
    plt.bar(summary_df["condition"], summary_df["accuracy"])
    plt.ylabel("Accuracy (%)")
    plt.title("Condition-wise Accuracy")
    plt.ylim(0, 100)
    for i, v in enumerate(summary_df["accuracy"].tolist()):
        plt.text(i, v + 1, f"{v:.1f}%", ha="center", va="bottom", fontsize=9)
    plt.tight_layout()
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    plt.savefig(outpath, dpi=150)
    plt.close()

def plot_gender_ratio(filenames: list[str], outpath: str):
    cnt = Counter()
    for f in filenames:
        _, _, gender, _ = _tokens(f)
        cnt[gender] += 1
    _save_bar(cnt, "성별 분포", outpath, order=["male","female"], xlabel="성별")

def plot_age_distribution(filenames: list[str], outpath: str):
    """연령 카테고리: child / youngadult / middleaged / senior (+ unknown)"""
    cnt = Counter()
    for f in filenames:
        _, age, _, _ = _tokens(f)
        cnt[age] += 1
    order = ["child","youngadult","middleaged","senior"]
    _save_bar(cnt, "연령 분포", outpath, order=order, xlabel="연령대")

def plot_region_distribution(filenames: list[str], outpath: str, top_n: int = 20):
    """파일명 첫 토큰(지역명) 분포"""
    cnt = Counter()
    for f in filenames:
        region, _, _, _ = _tokens(f)
        cnt[region] += 1
    _save_bar(cnt, "지역 분포 (상위)", outpath, top=top_n, xlabel="지역")

def plot_basevoice_distribution(filenames: list[str], outpath: str, top_n: int = 20):
    """파일명 4번째 토큰(기본 음성) 분포"""
    cnt = Counter()
    for f in filenames:
        _, _, _, basevoice = _tokens(f)
        cnt[basevoice] += 1
    _save_bar(cnt, "기본 음성 분포 (상위)", outpath, top=top_n, xlabel="기본 음성")
