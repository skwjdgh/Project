import random
import logging
from def_config import NOISE_PERCENTAGE, AGES, GENDERS, TONES, EMOTIONS

def add_noise_to_metadata(metadata: tuple, index: int) -> tuple:
    """
    설정된 확률(NOISE_PERCENTAGE)에 따라 메타데이터(age, gender, tone, emotion)에
    의도적인 노이즈를 추가합니다.
    """
    # 노이즈를 적용할지 확률적으로 결정합니다.
    if random.random() < (NOISE_PERCENTAGE / 100.0):
        age, gender, tone, emotion, voice = metadata
        
        # 변경할 속성(age, gender 등)과 현재 값을 맵으로 정의합니다.
        options_map = {
            "age": (AGES, age),
            "gender": (GENDERS, gender),
            "tone": (TONES, tone),
            "emotion": (EMOTIONS, emotion),
        }
        # 어떤 속성을 변경할지 무작위로 선택합니다.
        attr_to_change = random.choice(list(options_map.keys()))
        
        # 선택된 속성의 현재 값을 제외한 다른 값들 중에서 하나를 무작위로 고릅니다.
        possible_values, current_value = options_map[attr_to_change]
        other_values = [v for v in possible_values if v != current_value]
        
        if other_values:
            new_value = random.choice(other_values)
            # 로그를 남겨 어떤 값이 변경되었는지 추적할 수 있게 합니다.
            logging.info(f"Adding noise to index {index}: Changed '{attr_to_change}' from '{current_value}' to '{new_value}'")

            # 메타데이터 튜플의 값을 새로운 값으로 교체합니다.
            if attr_to_change == "age": age = new_value
            elif attr_to_change == "gender": gender = new_value
            elif attr_to_change == "tone": tone = new_value
            elif attr_to_change == "emotion": emotion = new_value
        
        return (age, gender, tone, emotion, voice)
        
    # 노이즈가 적용되지 않은 경우 원본 메타데이터를 그대로 반환합니다.
    return metadata