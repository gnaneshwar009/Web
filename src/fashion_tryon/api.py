from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import FileResponse

from .pipeline import FashionTryOnPipeline

app = FastAPI(title="Local Fashion Try-On Assistant")
_pipeline: FashionTryOnPipeline | None = None


def get_pipeline() -> FashionTryOnPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = FashionTryOnPipeline()
    return _pipeline


@app.post("/try-on")
async def try_on(person: UploadFile = File(...), prompt: str = Form(...)) -> FileResponse:
    suffix = Path(person.filename or "person.jpg").suffix or ".jpg"
    with tempfile.TemporaryDirectory() as tmpdir:
        person_path = Path(tmpdir) / f"person{suffix}"
        output_path = Path(tmpdir) / "tryon.png"
        person_path.write_bytes(await person.read())
        get_pipeline().generate(person_path, prompt, output_path)
        permanent = Path("outputs") / "api_tryon.png"
        permanent.parent.mkdir(exist_ok=True)
        permanent.write_bytes(output_path.read_bytes())
    return FileResponse(permanent, media_type="image/png", filename="tryon.png")
