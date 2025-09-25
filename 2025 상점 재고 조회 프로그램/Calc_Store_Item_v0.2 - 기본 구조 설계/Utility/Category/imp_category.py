from collections import defaultdict

# 클래스명 → 상위 카테고리 매핑 예시
CATEGORY_MAP = {
    "bottle": "beverage",
    "cup": "beverage",
    "can": "beverage",
    "apple": "grocery",
    "banana": "grocery",
    # 필요 시 확장
}

def to_category_counts(detections):
    """
    detections: list of dict {cls_name, conf}
    return: dict {category: count}
    """
    agg = defaultdict(int)
    for det in detections:
        name = det["cls_name"]
        cat = CATEGORY_MAP.get(name, "others")
        agg[cat] += 1
    return dict(agg)
