import os
import pandas as pd
from tqdm import tqdm
import whisper
import time
import warnings
import logging

# 설정 및 유틸리티 함수 임포트
import def_config as config
from Utility.func_tokenizer import tokenize_text
from Utility.func_noisecanceller import enhance_speech_in_memory
from Utility.func_sorter import analyze_data_distribution
from Utility.func_visualization import plot_accuracy_results, plot_data_distribution
from def_exception import ExperimentError

# 경고 메시지 무시
warnings.filterwarnings("ignore", category=UserWarning)

def setup_logger():
    """Setup the logging system to file and console."""
    # Ensure the results directory exists for the log file
    os.makedirs(config.RESULTS_DIR, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] - %(message)s',
        handlers=[
            logging.FileHandler(config.LOG_FILE_PATH, mode='a', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

def find_audio_files(directory):
    """Recursively find audio files in a given directory."""
    audio_paths = []
    for root, _, files in os.walk(directory):
        # Exclude the 'text' subdirectory from the audio file search
        if os.path.basename(root) == 'text':
            continue
        for file in files:
            if file.endswith(('.mp3', '.wav')):
                audio_paths.append(os.path.join(root, file))
    return audio_paths

def run_experiment():
    """Main function to run the entire experiment."""
    # --- 1. Setup and Initialization ---
    setup_logger()
    logging.info("="*50)
    logging.info("Starting the experiment.")

    # Create necessary directories based on config
    os.makedirs(config.INPUT_DIR, exist_ok=True)
    for sub_dir in config.SUB_DIRS:
        os.makedirs(os.path.join(config.INPUT_DIR, sub_dir), exist_ok=True)
    logging.info(f"Input/Result directories are ready.")

    # Load Whisper model
    try:
        logging.info(f"Loading Whisper model: '{config.WHISPER_MODEL}'...")
        model = whisper.load_model(config.WHISPER_MODEL)
        logging.info("Whisper model loaded successfully.")
    except Exception as e:
        raise ExperimentError(f"Failed to load Whisper model: {e}")

    # Load text data and create a validation set for keywords
    try:
        if not os.path.exists(config.TEXT_DATA_PATH):
            logging.error(f"Text data file not found at '{config.TEXT_DATA_PATH}'.")
            logging.error("Please place 'united.csv' in the 'Input_data/text/' directory.")
            return
        keywords_df = pd.read_csv(config.TEXT_DATA_PATH)
        valid_keywords = set(keywords_df['종류'].unique())
        logging.info(f"Loaded {len(keywords_df)} sentences. Found {len(valid_keywords)} unique keywords for validation.")
    except Exception as e:
        raise ExperimentError(f"Failed to load text data: {e}")

    # Get the list of audio files
    all_audio_files = find_audio_files(config.INPUT_DIR)
    if not all_audio_files:
        logging.warning(f"No audio files found in '{config.INPUT_DIR}' and its subdirectories (excluding 'text').")
        logging.warning("Please add audio files to 'Input_data/voice/' or 'Input_data/test/'.")
        return

    # --- 2. Resume Experiment Logic ---
    results_csv_path = os.path.join(config.RESULTS_DIR, "detailed_results.csv")
    processed_files = set()
    if os.path.exists(results_csv_path):
        logging.info(f"Found existing results file. Attempting to resume experiment.")
        try:
            processed_df = pd.read_csv(results_csv_path)
            processed_files = set(processed_df['file_id'].unique())
            logging.info(f"{len(processed_files)} files have already been processed and will be skipped.")
        except Exception as e:
            logging.warning(f"Could not read existing results file. Starting from scratch. Error: {e}")

    audio_files_to_process = [f for f in all_audio_files if os.path.basename(f) not in processed_files]
    logging.info(f"Total audio files found: {len(all_audio_files)}. Files to process now: {len(audio_files_to_process)}.")

    if not audio_files_to_process:
        logging.info("No new audio files to process. Finalizing results based on existing data.")
    else:
        # --- 3. Input Data Analysis (Run only if there are files to process) ---
        audio_filenames = [os.path.basename(p) for p in all_audio_files]
        dist_df, analysis_results = analyze_data_distribution(audio_filenames)
        dist_df.to_csv(os.path.join(config.RESULTS_DIR, "input_data_distribution.csv"), index=False, encoding='utf-8-sig')
        for category, data in analysis_results.items():
            if not data.empty:
                plot_data_distribution(data, category, os.path.join(config.RESULTS_DIR, f"{category}_distribution.png"))

        # --- 4. STT and Accuracy Measurement ---
        results = []
        for file_path in tqdm(audio_files_to_process, desc="Experiment Progress"):
            audio_file_name = os.path.basename(file_path)
            
            try:
                ground_truth_keyword = audio_file_name.split('_')[1]
                if ground_truth_keyword not in valid_keywords:
                    logging.warning(f"Keyword '{ground_truth_keyword}' from file '{audio_file_name}' not found in 'united.csv'. Skipping file.")
                    continue
            except IndexError:
                logging.warning(f"Filename '{audio_file_name}' does not follow the naming convention. Skipping file.")
                continue

            # A: Baseline
            transcription_a = model.transcribe(file_path, fp16=config.USE_FP16)['text']
            match_a = 1 if ground_truth_keyword in transcription_a else 0
            results.append({"file_id": audio_file_name, "condition": "A (Baseline)", "transcript": transcription_a, "keyword": ground_truth_keyword, "match": match_a})

            # B: Tokenization
            tokens_b = tokenize_text(transcription_a)
            match_b = 1 if ground_truth_keyword in tokens_b else 0
            results.append({"file_id": audio_file_name, "condition": "B (Tokenization)", "transcript": " | ".join(tokens_b), "keyword": ground_truth_keyword, "match": match_b})
            
            # C: Noise Cancellation (In-Memory)
            enhanced_audio_data = enhance_speech_in_memory(file_path)
            transcription_c = transcription_a
            if enhanced_audio_data is not None:
                 transcription_c = model.transcribe(enhanced_audio_data, fp16=config.USE_FP16)['text']
            match_c = 1 if ground_truth_keyword in transcription_c else 0
            results.append({"file_id": audio_file_name, "condition": "C (Noise Cancellation)", "transcript": transcription_c, "keyword": ground_truth_keyword, "match": match_c})
            
            # D: Tokenization + NC
            tokens_d = tokenize_text(transcription_c)
            match_d = 1 if ground_truth_keyword in tokens_d else 0
            results.append({"file_id": audio_file_name, "condition": "D (Tokenization + NC)", "transcript": " | ".join(tokens_d), "keyword": ground_truth_keyword, "match": match_d})
        
        # Append new results to the existing file
        new_results_df = pd.DataFrame(results)
        new_results_df.to_csv(results_csv_path, mode='a', header=not os.path.exists(results_csv_path), index=False, encoding='utf-8-sig')
        logging.info(f"Appended {len(new_results_df)} new results to '{results_csv_path}'.")

    # --- 5. Finalize Results ---
    if not os.path.exists(results_csv_path):
        logging.info("No results were generated. Exiting.")
        return
        
    final_results_df = pd.read_csv(results_csv_path)
    accuracy_summary = final_results_df.groupby('condition')['match'].mean().reset_index()
    accuracy_summary.rename(columns={'match': 'accuracy'}, inplace=True)
    accuracy_summary['accuracy'] = accuracy_summary['accuracy'] * 100
    
    summary_csv_path = os.path.join(config.RESULTS_DIR, "accuracy_summary.csv")
    accuracy_summary.to_csv(summary_csv_path, index=False, encoding='utf-8-sig')
    
    logging.info("\n--- Final Results Summary ---\n" + accuracy_summary.to_string(index=False) + "\n---------------------------")

    plot_accuracy_results(accuracy_summary, os.path.join(config.RESULTS_DIR, "accuracy_comparison.png"))
    logging.info(f"Accuracy comparison chart saved.")
    logging.info("Experiment finished successfully.")


if __name__ == "__main__":
    try:
        run_experiment()
    except ExperimentError as e:
        logging.error(f"An experiment-specific error occurred: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}", exc_info=True)

