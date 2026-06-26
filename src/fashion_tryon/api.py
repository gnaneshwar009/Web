from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from .pipeline import FashionTryOnPipeline

app = FastAPI(title="Local Fashion Try-On Assistant")
_pipeline: FashionTryOnPipeline | None = None


def get_pipeline() -> FashionTryOnPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = FashionTryOnPipeline()
    return _pipeline


@app.post("/try-on")
async def try_on(
    person: UploadFile = File(...),
    prompt: str = Form(...),
    category: str = Form("full"),
    garment: UploadFile | None = File(None),
) -> FileResponse:
    tmp = tempfile.TemporaryDirectory()
    tmpdir = Path(tmp.name)
    suffix = Path(person.filename or "person.jpg").suffix or ".jpg"
    person_path = tmpdir / f"person{suffix}"
    output_path = tmpdir / "tryon.png"
    report_path = tmpdir / "quality.txt"
    person_path.write_bytes(await person.read())

    garment_path = None
    if garment is not None:
        garment_suffix = Path(garment.filename or "garment.jpg").suffix or ".jpg"
        garment_path = tmpdir / f"garment{garment_suffix}"
        garment_path.write_bytes(await garment.read())

    _, report = get_pipeline().generate(
        person_path,
        prompt,
        output_path,
        garment_path=garment_path,
        category=category,
        report_output_path=report_path,
    )
    headers = {}
    if report is not None:
        headers = {f"x-quality-{key.replace('_', '-')}": str(value) for key, value in report.to_dict().items()}
    return FileResponse(
        output_path,
        media_type="image/png",
        filename="tryon.png",
        headers=headers,
        background=BackgroundTask(tmp.cleanup),
    )
