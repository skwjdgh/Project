import noisereduce as nr
from pydub import AudioSegment
import numpy as np
import logging

import def_config as config

def enhance_speech_in_memory(input_path):
    """
    Reduces noise in an audio file and returns the processed data as a
    NumPy array for in-memory processing.
    """
    try:
        # pydub handles various formats and converts to a standard format
        audio = AudioSegment.from_file(input_path)
        
        # Convert to 16kHz mono, which is preferred by Whisper
        audio = audio.set_frame_rate(16000).set_channels(1)
        
        # Convert to a NumPy array and normalize to float32 range [-1.0, 1.0]
        samples = np.array(audio.get_array_of_samples()).astype(np.float32)
        samples /= np.iinfo(np.int16).max
        rate = audio.frame_rate
        
    except Exception as e:
        logging.error(f"Error loading audio file '{input_path}': {e}")
        return None

    # Apply noise reduction using the strength defined in the config
    reduced_noise_data = nr.reduce_noise(y=samples, sr=rate, prop_decrease=config.NOISE_REDUCTION_STRENGTH)
    
    return reduced_noise_data

