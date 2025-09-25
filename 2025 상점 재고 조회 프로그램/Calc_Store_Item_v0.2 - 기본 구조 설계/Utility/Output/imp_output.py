import cv2

def draw_result(frame, boxes_xyxy, names, confs, extra_text=None):
    for (x1, y1, x2, y2), name, conf in zip(boxes_xyxy, names, confs):
        cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
        cv2.putText(
            frame,
            f"{name} {conf:.2f}",
            (int(x1), max(0, int(y1) - 6)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2,
            cv2.LINE_AA,
        )
    if extra_text:
        y0 = 24
        for line in extra_text:
            cv2.putText(
                frame,
                line,
                (8, y0),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2,
                cv2.LINE_AA,
            )
            y0 += 24
    return frame
