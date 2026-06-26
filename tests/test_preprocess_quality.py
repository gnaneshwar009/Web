import pytest

PIL = pytest.importorskip("PIL")
from PIL import Image, ImageDraw

from fashion_tryon.preprocess import make_outfit_mask
from fashion_tryon.quality import compare_outputs
from fashion_tryon.validation import validate_image_filename, validate_prompt


def _person_image() -> Image.Image:
    image = Image.new("RGB", (768, 1024), "white")
    draw = ImageDraw.Draw(image)
    draw.ellipse((330, 80, 438, 188), fill=(180, 130, 90))
    draw.rectangle((280, 190, 488, 650), fill=(90, 90, 90))
    draw.line((310, 650, 270, 980), fill="black", width=24)
    draw.line((458, 650, 500, 980), fill="black", width=24)
    return image


def test_category_masks_have_expected_relative_coverage() -> None:
    image = _person_image()
    upper = make_outfit_mask(image, category="upper")
    lower = make_outfit_mask(image, category="lower")
    full = make_outfit_mask(image, category="full")
    upper_coverage = sum(upper.getdata())
    lower_coverage = sum(lower.getdata())
    full_coverage = sum(full.getdata())
    assert full_coverage > upper_coverage
    assert full_coverage > lower_coverage


def test_quality_report_passes_for_identical_images() -> None:
    image = _person_image()
    mask = make_outfit_mask(image, category="full")
    report = compare_outputs(image, image.copy(), mask)
    assert report.face_region_similarity >= 0.99
    assert report.body_edge_similarity >= 0.99


def test_validation_rejects_bad_inputs() -> None:
    assert validate_image_filename("photo.png") == ".png"
    assert validate_prompt("red silk dress with gold embroidery")
    try:
        validate_image_filename("payload.exe")
    except ValueError:
        pass
    else:
        raise AssertionError("Expected invalid suffix to fail")
