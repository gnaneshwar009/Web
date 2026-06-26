from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from starlette.background import BackgroundTask

from .config import TryOnConfig
from .pipeline import FashionTryOnPipeline
from .validation import read_limited_upload, validate_image_filename, validate_prompt

app = FastAPI(title="Local Fashion Try-On Assistant")
_config = TryOnConfig()
_pipeline: FashionTryOnPipeline | None = None


def get_pipeline() -> FashionTryOnPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = FashionTryOnPipeline(_config)
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
    try:
        prompt = validate_prompt(prompt)
        suffix = validate_image_filename(person.filename)
    except ValueError as exc:
        tmp.cleanup()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    person_path = tmpdir / f"person{suffix}"
    output_path = tmpdir / "tryon.png"
    report_path = tmpdir / "quality.txt"
    try:
        person_path.write_bytes(await read_limited_upload(person, _config.max_upload_mb))
    except ValueError as exc:
        tmp.cleanup()
        raise HTTPException(status_code=413, detail=str(exc)) from exc

    garment_path = None
    if garment is not None:
        try:
            garment_suffix = validate_image_filename(garment.filename)
        except ValueError as exc:
            tmp.cleanup()
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        garment_path = tmpdir / f"garment{garment_suffix}"
        try:
            garment_path.write_bytes(await read_limited_upload(garment, _config.max_upload_mb))
        except ValueError as exc:
            tmp.cleanup()
            raise HTTPException(status_code=413, detail=str(exc)) from exc

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


@app.get("/health")
def health() -> dict[str, str | int | bool]:
    return {
        "status": "ok",
        "backend": _config.backend,
        "width": _config.width,
        "height": _config.height,
        "quality_checks": _config.run_quality_checks,
    }


@app.get("/models")
def models() -> JSONResponse:
    return JSONResponse(
        {
            "active_backend": _config.backend,
            "available_backends": ["sdxl", "catvton", "idm-vton", "ootdiffusion", "stableviton"],
            "note": "External VTON backends require a local command configured in TryOnConfig.external_backend_command.",
        }
    )
