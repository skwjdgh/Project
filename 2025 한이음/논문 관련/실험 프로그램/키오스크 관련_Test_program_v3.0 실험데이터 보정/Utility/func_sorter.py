# -*- coding: utf-8 -*-

import pandas as pd

def sort_conditions_by_accuracy(df: pd.DataFrame) -> pd.DataFrame:
    """
    정확도 내림차순 정렬된 데이터프레임 반환
    """
    if 'accuracy' not in df.columns:
        return df
    return df.sort_values('accuracy', ascending=False).reset_index(drop=True)
