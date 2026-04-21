import numpy as np
from PIL import Image, ImageFilter


def find_changed_regions(
    before: Image.Image,
    after: Image.Image,
    threshold: int = 35,
    cell_size: int = 20,
    min_cells: int = 5,
    cell_change_ratio: float = 0.12,
) -> list[dict]:
    if before.size != after.size:
        before = before.resize(after.size, Image.LANCZOS)

    before_blur = before.filter(ImageFilter.GaussianBlur(radius=3))
    after_blur = after.filter(ImageFilter.GaussianBlur(radius=3))

    b = np.array(before_blur, dtype=np.float32)
    a = np.array(after_blur, dtype=np.float32)
    diff = np.abs(b - a).mean(axis=2)

    img_h, img_w = diff.shape
    rows = img_h // cell_size
    cols = img_w // cell_size

    changed_cells = set()
    for r in range(rows):
        for c in range(cols):
            y0 = r * cell_size
            x0 = c * cell_size
            cell_region = diff[y0 : y0 + cell_size, x0 : x0 + cell_size]
            if (cell_region > threshold).mean() > cell_change_ratio:
                changed_cells.add((r, c))

    if not changed_cells:
        return []

    visited = set()
    regions = []

    for cell in changed_cells:
        if cell in visited:
            continue
        component = []
        queue = [cell]
        while queue:
            current = queue.pop(0)
            if current in visited or current not in changed_cells:
                continue
            visited.add(current)
            component.append(current)
            cr, cc = current
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    neighbor = (cr + dr, cc + dc)
                    if neighbor in changed_cells and neighbor not in visited:
                        queue.append(neighbor)

        if len(component) >= min_cells:
            min_r = min(p[0] for p in component)
            max_r = max(p[0] for p in component)
            min_c = min(p[1] for p in component)
            max_c = max(p[1] for p in component)

            pad = cell_size
            x0 = max(0, min_c * cell_size - pad)
            y0 = max(0, min_r * cell_size - pad)
            x1 = min(img_w, (max_c + 1) * cell_size + pad)
            y1 = min(img_h, (max_r + 1) * cell_size + pad)

            box_2d = [
                int(y0 / img_h * 1000),
                int(x0 / img_w * 1000),
                int(y1 / img_h * 1000),
                int(x1 / img_w * 1000),
            ]

            regions.append({"box_2d": box_2d})

    return regions
