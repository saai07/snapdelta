from PIL import Image, ImageDraw, ImageFont

COLORS = {
    "added": (46, 204, 113),
    "removed": (231, 76, 60),
    "changed": (241, 196, 15),
}

BORDER_WIDTH = 2


def draw_boxes(image: Image.Image, changes: list[dict], img_width: int, img_height: int) -> Image.Image:
    result = image.copy().convert("RGBA")
    overlay = Image.new("RGBA", result.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    try:
        font = ImageFont.truetype("arial.ttf", 12)
    except OSError:
        font = ImageFont.load_default()

    for change in changes:
        coords = change.get("box_2d", [])
        if len(coords) != 4:
            continue

        y0, x0, y1, x1 = coords
        if y0 > y1:
            y0, y1 = y1, y0
        if x0 > x1:
            x0, x1 = x1, x0

        px_x0 = int(x0 / 1000 * img_width)
        px_y0 = int(y0 / 1000 * img_height)
        px_x1 = int(x1 / 1000 * img_width)
        px_y1 = int(y1 / 1000 * img_height)

        px_x0 = max(0, min(px_x0, img_width - 1))
        px_y0 = max(0, min(px_y0, img_height - 1))
        px_x1 = max(0, min(px_x1, img_width - 1))
        px_y1 = max(0, min(px_y1, img_height - 1))

        if px_x1 - px_x0 < 5 or px_y1 - px_y0 < 5:
            continue

        change_type = change.get("change_type", "changed")
        color = COLORS.get(change_type, (241, 196, 15))
        label_text = change.get("label", "Unknown")
        tag = f"[{change_type.upper()}] {label_text}"

        draw.rectangle(
            [px_x0, px_y0, px_x1, px_y1],
            outline=(*color, 220),
            width=BORDER_WIDTH,
        )

        bbox = font.getbbox(tag)
        text_w = bbox[2] - bbox[0] + 8
        text_h = bbox[3] - bbox[1] + 4

        tag_y = px_y1
        if tag_y + text_h > img_height:
            tag_y = px_y0 - text_h

        draw.rectangle(
            [px_x0, tag_y, px_x0 + text_w, tag_y + text_h],
            fill=(*color, 200),
        )
        draw.text(
            (px_x0 + 4, tag_y + 1),
            tag, fill=(0, 0, 0, 255), font=font,
        )

    result = Image.alpha_composite(result, overlay)
    return result.convert("RGB")
