import pandas as pd
import glob
import os
from def_exception import CSVReadError

def _read_csv_with_fallback(path: str) -> pd.DataFrame:
    # UTF-8 with BOM 우선, 실패 시 CP949로 재시도
    try:
        return pd.read_csv(path, encoding="utf-8-sig")
    except UnicodeDecodeError:
        return pd.read_csv(path, encoding="cp949")

def read_csv_files(data_dir: str, required_cols=("지역", "종류", "내용")) -> pd.DataFrame:
    """지정된 디렉토리의 모든 CSV 파일을 읽어 하나의 DataFrame으로 합칩니다."""
    csv_files = glob.glob(os.path.join(data_dir, "*.csv"))
    if not csv_files:
        raise CSVReadError(f"No CSV files found in the directory: {data_dir}")

    frames = []
    for f in csv_files:
        df = _read_csv_with_fallback(f)
        # 필수 컬럼 존재 여부 확인
        if not set(required_cols).issubset(df.columns):
            raise CSVReadError(f"'{f}'에 필수 컬럼 {required_cols} 중 일부가 없습니다.")
        frames.append(df[list(required_cols)])

    return pd.concat(frames, ignore_index=True)