from pathlib import Path
from uuid import uuid4
from io import BytesIO
import hashlib

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from PIL import Image

from pixel_diff import find_changed_regions
from gemini_client import label_changes
from drawer import draw_boxes

app = FastAPI(title="SnapDelta", description="Visual diff detection powered by Gemma")

RESULTS_DIR = Path("results")
RESULTS_DIR.mkdir(exist_ok=True)

# Simple in-memory cache
CACHE = {}


@app.post("/diff")
async def create_diff(before: UploadFile = File(...), after: UploadFile = File(...)):
    before_bytes = await before.read()
    after_bytes = await after.read()

    # Check cache first
    img_hash = hashlib.sha256(before_bytes + after_bytes).hexdigest()
    if img_hash in CACHE:
        return CACHE[img_hash]

    before_img = Image.open(BytesIO(before_bytes)).convert("RGB")
    after_img = Image.open(BytesIO(after_bytes)).convert("RGB")

    regions = find_changed_regions(before_img, after_img)

    changes = await label_changes(before_img, after_img, regions)

    diff_img = draw_boxes(after_img, changes, after_img.width, after_img.height)

    job_id = str(uuid4())
    diff_img.save(RESULTS_DIR / f"{job_id}.png")

    result = {"job_id": job_id, "changes_detected": len(changes)}
    CACHE[img_hash] = result
    return result


@app.get("/result/{job_id}")
async def get_result(job_id: str):
    path = RESULTS_DIR / f"{job_id}.png"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Result not found")
    return FileResponse(path, media_type="image/png")
