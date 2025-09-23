# -*- coding: utf-8 -*-
"""
Sorter
- 실험 요약 DataFrame을 정확도 기준으로 정렬하는 유틸.
"""
import pandas as pd

def sort_conditions_by_accuracy(df: pd.DataFrame) -> pd.DataFrame:
    """'accuracy' 컬럼이 있으면 내림차순 정렬."""
    if 'accuracy' not in df.columns: return df
    return df.sort_values('accuracy', ascending=False).reset_index(drop=True)
