import os
import json
import re
import logging
from google import genai
from google.genai import types
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

LABEL_PROMPT = """These are BEFORE and AFTER screenshots of the same UI.

I detected {count} regions that visually differ. For each region, look at that area in both images and classify:

{region_list}

For each region return:
- "label": short description (e.g. "Banner added", "Search bar removed", "Avatar changed")
- "change_type": "added" (only in AFTER), "removed" (only in BEFORE), or "changed"
- "box_2d": the EXACT same coordinates I gave you

Return ONLY a JSON array. No markdown."""


async def label_changes(
    before: Image.Image, after: Image.Image, regions: list[dict]
) -> list[dict]:
    if not regions:
        return []

    region_list = "\n".join(
        f"Region {i + 1}: box_2d={r['box_2d']}" for i, r in enumerate(regions)
    )
    prompt = LABEL_PROMPT.format(count=len(regions), region_list=region_list)

    try:
        response = await client.aio.models.generate_content(
            model="gemma-4-31b-it",
            contents=[prompt, "BEFORE:", before, "AFTER:", after],
            config=types.GenerateContentConfig(temperature=0),
        )
        text = response.text.strip()
        logging.info(f"Gemma response: {text[:300]}")
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        return json.loads(text)
    except Exception as e:
        logging.warning(f"Gemma labeling failed: {e}")
        return [
            {"label": f"Changed region {i + 1}", "change_type": "changed", "box_2d": r["box_2d"]}
            for i, r in enumerate(regions)
        ]
