from collections import defaultdict

def accumulate(detections_list):
    """
    detections_list: iterable of list[{'cls_name':str, 'conf':float}]
    return: dict {name: count}
    """
    counts = defaultdict(int)
    for dets in detections_list:
        for d in dets:
            counts[d["cls_name"]] += 1
    return dict(counts)
