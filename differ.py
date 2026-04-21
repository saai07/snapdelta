from difflib import SequenceMatcher


def _iou(box1: list[int], box2: list[int]) -> float:
    y0_1, x0_1, y1_1, x1_1 = box1
    y0_2, x0_2, y1_2, x1_2 = box2

    inter_x0 = max(x0_1, x0_2)
    inter_y0 = max(y0_1, y0_2)
    inter_x1 = min(x1_1, x1_2)
    inter_y1 = min(y1_1, y1_2)

    if inter_x1 <= inter_x0 or inter_y1 <= inter_y0:
        return 0.0

    inter_area = (inter_x1 - inter_x0) * (inter_y1 - inter_y0)
    area1 = (x1_1 - x0_1) * (y1_1 - y0_1)
    area2 = (x1_2 - x0_2) * (y1_2 - y0_2)
    union_area = area1 + area2 - inter_area

    if union_area == 0:
        return 0.0

    return inter_area / union_area


def _label_sim(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def find_changes(before_elements: list[dict], after_elements: list[dict]) -> list[dict]:
    changes = []
    matched_before = set()
    matched_after = set()

    for i, after_el in enumerate(after_elements):
        best_j = None
        best_score = 0.0

        for j, before_el in enumerate(before_elements):
            if j in matched_before:
                continue

            iou = _iou(after_el["box_2d"], before_el["box_2d"])
            label_score = _label_sim(after_el["label"], before_el["label"])

            score = iou * 0.7 + label_score * 0.3

            if score > best_score and (iou > 0.15 or label_score > 0.5):
                best_score = score
                best_j = j

        if best_j is not None:
            matched_before.add(best_j)
            matched_after.add(i)
        else:
            matched_after.add(i)
            changes.append({**after_el, "change_type": "added"})

    for j, before_el in enumerate(before_elements):
        if j not in matched_before:
            changes.append({**before_el, "change_type": "removed"})

    return changes
