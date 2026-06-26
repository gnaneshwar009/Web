from __future__ import annotations

from pathlib import Path

from PIL import Image

from .backends import GenerationInputs, build_backend, describe_garment_reference
from .config import TryOnConfig
from .preprocess import prepare_person
from .quality import QualityReport, compare_outputs, write_report


class FashionTryOnPipeline:
    """Local virtual try-on pipeline with swappable generation backends."""

    def __init__(self, config: TryOnConfig | None = None) -> None:
        self.config = config or TryOnConfig()
        self.backend = build_backend(self.config)

    def generate(
        self,
        person_path: str | Path,
        prompt: str,
        output_path: str | Path,
        garment_path: str | Path | None = None,
        category: str | None = None,
        mask_output_path: str | Path | None = None,
        report_output_path: str | Path | None = None,
    ) -> tuple[Image.Image, QualityReport | None]:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        garment = Path(garment_path) if garment_path else None
        prepared = prepare_person(
            person_path,
            width=self.config.width,
            height=self.config.height,
            preserve_face_ratio=self.config.preserve_face_ratio,
            category=category or self.config.category,
            blur_radius=self.config.mask_blur_radius,
        )

        final_prompt = self._build_prompt(prompt, garment)
        negative_prompt = self._build_negative_prompt()
        result = self.backend.generate(
            GenerationInputs(
                person_image=prepared.image,
                mask_image=prepared.mask,
                prompt=final_prompt,
                negative_prompt=negative_prompt,
                output_path=output_path,
                garment_path=garment,
            )
        )
        result.save(output_path)

        if mask_output_path is not None:
            mask_path = Path(mask_output_path)
            mask_path.parent.mkdir(parents=True, exist_ok=True)
            prepared.mask.save(mask_path)

        report = None
        if self.config.run_quality_checks:
            report = compare_outputs(prepared.image, result, prepared.mask)
            if report_output_path is not None:
                write_report(report, report_output_path)
        return result, report

    def _build_prompt(self, outfit_prompt: str, garment_path: Path | None) -> str:
        garment_hint = describe_garment_reference(garment_path) if garment_path else ""
        return (
            "photorealistic editorial full-body fashion virtual try-on, sharp garment seams, "
            "realistic fabric folds, natural shadows, physically plausible cloth drape, "
            "preserve the person's face, skin tone, apparent body proportions, height impression, "
            "pose, hands, hair, and background; outfit: "
            f"{outfit_prompt}. {garment_hint}"
        ).strip()

    @staticmethod
    def _build_negative_prompt() -> str:
        return (
            "different face, changed identity, changed body shape, changed skin tone, changed pose, "
            "extra limbs, missing hands, fused fingers, distorted anatomy, blurry, low quality, "
            "bad fabric, floating garment, watermark, text"
        )
