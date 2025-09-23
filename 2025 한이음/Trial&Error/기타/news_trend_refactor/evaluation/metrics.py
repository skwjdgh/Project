from rouge_score import rouge_scorer as rouge_lib
from bert_score import score as bertscore

rouge = rouge_lib.RougeScorer(['rouge1','rougeL'], use_stemmer=True)

def calc_rouge(original: str, summary: str):
    s = rouge.score(original, summary)
    return {'rouge1': s['rouge1'].fmeasure, 'rougeL': s['rougeL'].fmeasure}

def calc_bertscore(original: str, summary: str, lang: str = 'ko'):
    # bertscore API expects lists
    P, R, F1 = bertscore([summary], [original], lang=lang)
    return {'bertscore': float(F1.mean())}

def evaluate_summary(original: str, summary: str, is_ad: bool = False) -> dict:
    try:
        r = calc_rouge(original, summary)
        b = calc_bertscore(original, summary)
        out = {**r, **b, 'is_ad': is_ad}
    except Exception as e:
        print(f"[WARN] evaluation failed: {e}")
        out = {'rouge1': 0.0, 'rougeL': 0.0, 'bertscore': 0.0, 'is_ad': is_ad}
    return out
