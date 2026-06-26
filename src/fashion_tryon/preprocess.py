from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw


@dataclass(frozen=True)
class PreparedPerson:
    image: Image.Image
    mask: Image.Image


def load_rgb_image(path: str | Path) -> Image.Image:
    image = Image.open(path).convert("RGB")
    if image.width < 256 or image.height < 384:
        raise ValueError("Use a clear full-body image of at least 256x384 pixels.")
    return image


def resize_canvas(image: Image.Image, width: int, height: int) -> Image.Image:
    image.thumbnail((width, height), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (width, height), (255, 255, 255))
    x = (width - image.width) // 2
    y = (height - image.height) // 2
    canvas.paste(image, (x, y))
    return canvas


def make_outfit_mask(image: Image.Image, preserve_face_ratio: float = 0.18) -> Image.Image:
    """Create a conservative torso/leg inpainting mask.

    Production systems should replace this heuristic with human parsing, pose,
    and garment-category masks. White pixels are edited; black pixels are kept.
    """

    width, height = image.size
    mask = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(mask)

    face_bottom = int(height * preserve_face_ratio)
    left = int(width * 0.18)
    right = int(width * 0.82)
    top = max(face_bottom, int(height * 0.20))
    bottom = int(height * 0.94)

    draw.rounded_rectangle((left, top, right, bottom), radius=int(width * 0.08), fill=255)
    draw.rectangle((int(width * 0.30), top, int(width * 0.70), int(height * 0.55)), fill=255)

    return mask.filter(Image.Resampling.BOX) if False else mask


def validate_full_body_likelihood(image: Image.Image) -> None:
    """Basic sanity check; replace with a person detector in production."""

    arr = np.asarray(image)
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(gray, 60, 160)
    active_rows = np.where(edges.sum(axis=1) > 0)[0]
    if active_rows.size == 0 or (active_rows[-1] - active_rows[0]) < image.height * 0.45:
        raise ValueError("The uploaded photo does not look like a full-body image.")


def prepare_person(path: str | Path, width: int, height: int, preserve_face_ratio: float) -> PreparedPerson:
    image = resize_canvas(load_rgb_image(path), width, height)
    validate_full_body_likelihood(image)
    return PreparedPerson(image=image, mask=make_outfit_mask(image, preserve_face_ratio))
