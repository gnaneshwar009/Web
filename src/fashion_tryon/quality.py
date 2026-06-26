from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path

import cv2
import numpy as np
from PIL import Image


@dataclass(frozen=True)
class QualityReport:
    """Lightweight post-generation checks for identity/body drift."""

    mask_coverage: float
    face_region_similarity: float
    body_edge_similarity: float
    passed: bool

    def to_dict(self) -> dict[str, float | bool]:
        return asdict(self)


def _to_gray(image: Image.Image) -> np.ndarray:
    return cv2.cvtColor(np.asarray(image.convert("RGB")), cv2.COLOR_RGB2GRAY)


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    a = a.astype(np.float32).reshape(-1)
    b = b.astype(np.float32).reshape(-1)
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def compare_outputs(source: Image.Image, generated: Image.Image, mask: Image.Image) -> QualityReport:
    """Compute cheap checks that catch obvious identity/body drift.

    These checks are intentionally dependency-light. Production systems should
    add face-recognition embeddings, pose-keypoint similarity, segmentation IoU,
    and human review thresholds for high-stakes deployments.
    """

    source = source.convert("RGB")
    generated = generated.convert("RGB").resize(source.size)
    mask = mask.convert("L").resize(source.size)

    mask_arr = np.asarray(mask, dtype=np.float32) / 255.0
    mask_coverage = float(mask_arr.mean())

    height = source.height
    face_slice = slice(0, max(1, int(height * 0.20)))
    face_region_similarity = _cosine_similarity(
        _to_gray(source)[face_slice, :],
        _to_gray(generated)[face_slice, :],
    )

    src_edges = cv2.Canny(_to_gray(source), 60, 160)
    gen_edges = cv2.Canny(_to_gray(generated), 60, 160)
    preserve_region = (mask_arr < 0.5).astype(np.uint8)
    body_edge_similarity = _cosine_similarity(src_edges * preserve_region, gen_edges * preserve_region)

    passed = mask_coverage < 0.80 and face_region_similarity >= 0.90 and body_edge_similarity >= 0.55
    return QualityReport(
        mask_coverage=round(mask_coverage, 4),
        face_region_similarity=round(face_region_similarity, 4),
        body_edge_similarity=round(body_edge_similarity, 4),
        passed=passed,
    )


def write_report(report: QualityReport, output_path: str | Path) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"{key}: {value}" for key, value in report.to_dict().items()]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
