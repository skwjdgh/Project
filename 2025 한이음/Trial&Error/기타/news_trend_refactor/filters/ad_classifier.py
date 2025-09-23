import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from typing import Optional
from config import AD_LABEL_NAME

class AdClassifier:
    def __init__(self, model_path: str = "distilbert-base-multilingual-cased"):
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_path)
            self.model = AutoModelForSequenceClassification.from_pretrained(model_path)
            self.id2label = self.model.config.id2label
        except Exception as e:
            print(f"[WARN] 광고 모델 로드 실패: {e}. 모든 기사 비광고로 처리합니다.")
            self.tokenizer, self.model, self.id2label = None, None, {}

    def is_ad(self, text: str, threshold: float = 0.5) -> bool:
        if not self.model:
            return False  # 모델 없음 -> 광고 아님 처리
        inputs = self.tokenizer(text, return_tensors='pt', truncation=True, max_length=512)
        with torch.no_grad():
            logits = self.model(**inputs).logits.softmax(dim=-1).squeeze()
        ad_idx = self._label_to_id(AD_LABEL_NAME)
        if ad_idx is None:
            # 라벨을 못 찾으면 1번 id를 광고로 가정
            ad_idx = 1 if logits.numel() > 1 else 0
        ad_prob = logits[ad_idx].item()
        return ad_prob >= threshold

    def _label_to_id(self, label: str) -> Optional[int]:
        label = label.upper()
        for i, l in self.id2label.items():
            if l.upper() == label:
                return int(i)
        return None
