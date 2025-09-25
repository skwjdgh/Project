import cv2

def save_image_result(img_path, drawer):
    im = cv2.imread(img_path)
    vis = drawer(im)
    out = img_path.rsplit(".",1)[0] + "_out.jpg"
    cv2.imwrite(out, vis)
    return out.replace("\\","/")

def save_video_result(vid_path, infer_fn):
    cap = cv2.VideoCapture(vid_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    w  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h  = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    out_path = vid_path.rsplit(".",1)[0] + "_out.mp4"
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(out_path, fourcc, fps, (w,h))

    agg = {}
    idx = 0
    while True:
        ok, frame = cap.read()
        if not ok: break
        if idx % 2 == 0:
            dets = infer_fn(frame)
            for d in dets:
                agg[d["label"]] = agg.get(d["label"], 0) + 1
            vis = draw_frame(frame, dets)
        else:
            vis = frame
        writer.write(vis); idx += 1

    cap.release(); writer.release()
    return out_path.replace("\\","/"), agg

def draw_frame(frame, dets):
    from Utility.Imp_calc import draw_boxes
    return draw_boxes(frame, dets)
