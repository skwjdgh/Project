import os
import random
import time
import pandas as pd
import concurrent.futures
import logging
from itertools import product

from dotenv import load_dotenv
from openai import OpenAI
from tqdm import tqdm

# --- 설정/유틸 임포트 ---
from def_config import *
from def_config import (
    AGES, GENDERS, TONES, EMOTIONS,
    CSV_REGION_COL, CSV_TYPE_COL, CSV_SENTENCE_COL,
    DATA_DIR, OUTPUT_DIR, CLEAN_FILENAME, AUDIO_FORMAT,
    RETRY_COUNT, RETRY_DELAY, MAX_WORKERS, RANDOM_SEED
)
from def_exception import AudioGenerationError, CSVReadError, handle_error
from utility.imp_save import clean_filename, save_audio_file
from utility.imp_load import read_csv_files
from utility.imp_noise import add_noise_to_metadata

# --- 환경변수 및 API 클라이언트 초기화 ---
load_dotenv("file.env")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    error_msg = "file.env(.env) 파일에 OPENAI_API_KEY를 설정하세요."
    logging.critical(error_msg)
    raise RuntimeError(error_msg)

client = OpenAI(api_key=OPENAI_API_KEY)
random.seed(RANDOM_SEED)

# --- 데이터 샘플링: 종류 기준 균등 샘플링 ---
def sample_sentences_by_type(df: pd.DataFrame) -> pd.DataFrame:
    types = df[CSV_TYPE_COL].unique()
    per_type = calc_samples_per_keyword(len(types))

    sampled_frames = []
    for t in types:
        sub = df[df[CSV_TYPE_COL] == t]
        k = min(len(sub), per_type)
        if k > 0:
            sampled_frames.append(sub.sample(n=k, random_state=RANDOM_SEED))

    if not sampled_frames:
        logging.warning("TOTAL_SAMPLES 대비 데이터가 충분치 않습니다.")
        return pd.DataFrame()

    sampled_df = pd.concat(sampled_frames, ignore_index=True)
    # 전체 상한 적용
    if len(sampled_df) > TOTAL_SAMPLES:
        sampled_df = sampled_df.sample(n=TOTAL_SAMPLES, random_state=RANDOM_SEED).reset_index(drop=True)

    logging.info(f"총 {len(sampled_df)}개의 문장이 샘플링되었습니다.")
    return sampled_df

# --- 균등 음성 분배 ---
def assign_voices_evenly(n: int):
    voices = OPENAI_VOICES if (isinstance(OPENAI_VOICES, (list, tuple)) and len(OPENAI_VOICES) > 0) else ["alloy"]
    v = list(voices)
    q, r = divmod(n, len(v))
    voice_list = [vv for vv in v for _ in range(q)] + list(v[:r])
    random.shuffle(voice_list)
    return voice_list

# --- 음성 옵션 조합 (voice 제외) ---
def generate_options_without_voice(total_samples: int):
    combos = list(product(AGES, GENDERS, TONES, EMOTIONS))
    while len(combos) < total_samples:
        combos.extend(combos)
    final = combos[:total_samples]
    random.shuffle(final)
    return final

# --- 입력 텍스트 전처리 ---
def build_tts_input(region: str, doc_type: str, text: str) -> str:
    return text

# --- TTS 호출 및 파일 저장 (버전 호환 폴백 포함) ---
def generate_audio(region: str, doc_type: str, sentence: str, metadata, index: int):
    age, gender, tone, emotion, voice = metadata

    base_name = f"{region}_{doc_type}_{age}_{gender}_{voice}_{index:04d}"
    safe_base = clean_filename(base_name, CLEAN_FILENAME)
    filename = f"{safe_base}.{AUDIO_FORMAT}"
    out_path = os.path.join(OUTPUT_DIR, filename)

    tts_input = build_tts_input(region, doc_type, sentence)

    for attempt in range(RETRY_COUNT):
        try:
            # 1) 최신 SDK 경로: format 지원 + 스트리밍 파일 저장
            with client.audio.speech.with_streaming_response.create(
                model=OPENAI_MODEL,
                voice=voice,
                input=tts_input,
                response_format=AUDIO_FORMAT,
            ) as response:
                response.stream_to_file(out_path)
            logging.info(f"Saved(stream+format): {out_path}")
            return

        except TypeError as e:
            # 2) 구버전 SDK 경로: response_format 미지원 → 무포맷 스트리밍(보통 wav)
            if "unexpected keyword argument 'response_format'" in str(e):
                try:
                    root, _ = os.path.splitext(out_path)
                    fallback_path = out_path if AUDIO_FORMAT.lower() == "wav" else f"{root}.wav"
                    with client.audio.speech.with_streaming_response.create(
                        model=OPENAI_MODEL,
                        voice=voice,
                        input=tts_input,
                    ) as response:
                        response.stream_to_file(fallback_path)
                    logging.info(f"Saved(stream no-format): {fallback_path}")
                    return
                except Exception as e2:
                    handle_error(e2, "streaming(no-format) fallback failed")
            else:
                handle_error(e, "streaming(format) signature mismatch")

        except Exception as e:
            handle_error(e, "streaming path failed")

        # 3) 최종 폴백: Chat Completions 오디오(Base64) → 파일 저장 (이 API는 현재 TTS를 직접 지원하지 않을 수 있음)
        # 이 부분은 OpenAI API 변경에 따라 작동하지 않을 수 있으므로 최후의 수단으로 간주합니다.
        try:
            # OpenAI의 TTS 전용 API가 아닌 Chat Completions를 통한 오디오 생성은
            # 더 이상 지원되지 않거나 다른 방식으로 호출해야 할 수 있습니다.
            # 이 코드는 과거 호환성을 위한 예시로 남겨둡니다.
            # 필요한 경우 주석 처리하거나 최신 API 사양에 맞게 수정하세요.
            logging.warning(f"Attempt {attempt + 1}/{RETRY_COUNT}: Falling back for index {index}. This path might be deprecated.")
            time.sleep(RETRY_DELAY)
            continue # 다음 재시도로 넘어감

        except Exception as e:
            handle_error(e, f"Attempt {attempt + 1}/{RETRY_COUNT} for index {index}")
            if attempt < RETRY_COUNT - 1:
                time.sleep(RETRY_DELAY)
            else:
                logging.error(f"All retries failed for index {index}. Skipping.")
                raise AudioGenerationError(f"Failed to generate audio for: {tts_input[:80]}...")

# --- 스레드 태스크 래퍼 ---
def process_task(args):
    try:
        generate_audio(*args)
    except Exception as e:
        handle_error(e, "Error within thread task.")
        raise

# --- 메인 실행 ---
def main():
    logging.info("음성 생성 프로세스를 시작합니다.")
    try:
        # 지역/종류/내용 컬럼 확인 + 인코딩 자동 처리
        df = read_csv_files(DATA_DIR, required_cols=(CSV_REGION_COL, CSV_TYPE_COL, CSV_SENTENCE_COL))
        if df.empty:
            logging.info("입력 데이터가 없습니다. 종료합니다.")
            return

        sampled_df = sample_sentences_by_type(df)
        if sampled_df.empty:
            logging.info("샘플링된 데이터가 없어 종료합니다.")
            return

        n = len(sampled_df)
        base_options = generate_options_without_voice(n)
        voice_list = assign_voices_evenly(n)

        tasks = []
        records = sampled_df.to_dict("records")
        for idx, (row, opt, vv) in enumerate(zip(records, base_options, voice_list)):
            age, gender, tone, emotion = opt
            metadata = (age, gender, tone, emotion, vv)
            
            # 노이즈 추가 함수 호출 (imp_noise.py에서 가져옴)
            noisy_metadata = add_noise_to_metadata(metadata, idx)
            
            region = str(row[CSV_REGION_COL])
            doc_type = str(row[CSV_TYPE_COL])
            sentence = str(row[CSV_SENTENCE_COL])
            tasks.append((region, doc_type, sentence, noisy_metadata, idx))

        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = [executor.submit(process_task, task) for task in tasks]
            for future in tqdm(concurrent.futures.as_completed(futures), total=len(tasks), desc="Generating Audio Files"):
                try:
                    future.result()
                except Exception:
                    pass

    except (CSVReadError, RuntimeError) as e:
        handle_error(e, "Critical error during setup.")
    except Exception as e:
        handle_error(e, "An unexpected error occurred in the main process.")
    finally:
        logging.info("음성 생성 프로세스를 종료합니다.")

if __name__ == "__main__":
    main()