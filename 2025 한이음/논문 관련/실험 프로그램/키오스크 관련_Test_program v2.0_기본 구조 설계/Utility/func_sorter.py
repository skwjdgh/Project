import os
import pandas as pd
import logging

def analyze_data_distribution(file_list):
    """Parses a list of filenames to analyze the data distribution."""
    records = []
    for filename in file_list:
        parts = os.path.splitext(filename)[0].split('_')
        if len(parts) >= 5:
            record = {
                'filename': filename,
                'region': parts[0],
                'keyword': parts[1],
                'age': parts[2],
                'gender': parts[3],
                'voice': parts[4]
            }
            records.append(record)
        else:
            logging.warning(f"Filename format warning during distribution analysis: '{filename}' will be excluded.")

    if not records:
        return pd.DataFrame(), {}
        
    df = pd.DataFrame(records)
    
    # Calculate distribution for each category
    # --- 수정된 부분 ---
    # pandas 최신 버전에 맞게 rename 로직을 수정했습니다.
    # 기존 열 이름(keyword, age 등)을 'item'으로 변경합니다. 'count' 열은 자동으로 생성됩니다.
    analysis_results = {
        'keyword': df['keyword'].value_counts().reset_index().rename(columns={'keyword': 'item'}),
        'age': df['age'].value_counts().reset_index().rename(columns={'age': 'item'}),
        'gender': df['gender'].value_counts().reset_index().rename(columns={'gender': 'item'}),
        'region': df['region'].value_counts().reset_index().rename(columns={'region': 'item'})
    }
    return df, analysis_results