import re
ALIAS = {"persion":"person","pepole":"people","humans":"person"}

def normalize_classes(text: str):
    text = text.replace(",", "\n")
    items = []
    for line in text.splitlines():
        t = line.strip().lower()
        if not t: 
            continue
        t = re.sub(r"\s+", " ", t)
        t = ALIAS.get(t, t)
        items.append(t)
    # 중복 제거(순서 보존)
    seen = set(); out=[]
    for x in items:
        if x in seen: 
            continue
        seen.add(x); out.append(x)
    return out[:50]
