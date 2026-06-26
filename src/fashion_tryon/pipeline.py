from __future__ import annotations

from pathlib import Path

import torch
from diffusers import AutoPipelineForInpainting
from PIL import Image, ImageStat

from .config import TryOnConfig
from .preprocess import prepare_person
from .quality import QualityReport, compare_outputs, write_report


class FashionTryOnPipeline:
    """Local text-guided virtual try-on pipeline.

    This is a runnable SDXL-inpainting baseline. For best production results,
    keep this interface and swap the implementation for IDM-VTON or CatVTON.
    """

    def __init__(self, config: TryOnConfig | None = None) -> None:
        self.config = config or TryOnConfig()
        dtype = torch.float16 if self.config.device == "cuda" and torch.cuda.is_available() else torch.float32
        device = self.config.device if self.config.device == "cuda" and torch.cuda.is_available() else "cpu"
        self.device = device
        self.pipe = AutoPipelineForInpainting.from_pretrained(
            self.config.model_id,
            torch_dtype=dtype,
            variant="fp16" if dtype == torch.float16 else None,
        ).to(device)
        if hasattr(self.pipe, "enable_attention_slicing"):
            self.pipe.enable_attention_slicing()

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
        prepared = prepare_person(
            person_path,
            width=self.config.width,
            height=self.config.height,
            preserve_face_ratio=self.config.preserve_face_ratio,
            category=category or self.config.category,
            blur_radius=self.config.mask_blur_radius,
        )
        generator = None
        if self.config.seed is not None:
            generator = torch.Generator(device=self.device).manual_seed(self.config.seed)

        garment_hint = self._describe_garment_reference(garment_path) if garment_path else ""
        final_prompt = (
            "photorealistic editorial full-body fashion virtual try-on, sharp garment seams, "
            "realistic fabric folds, natural shadows, preserve the person's face, skin tone, "
            "apparent body proportions, height impression, pose, hands, hair, and background; outfit: "
            f"{prompt}. {garment_hint}"
        ).strip()
        negative_prompt = (
            "different face, changed identity, changed body shape, changed skin tone, extra limbs, "
            "missing hands, blurry, low quality, distorted anatomy, watermark, text"
        )
        result = self.pipe(
            prompt=final_prompt,
            negative_prompt=negative_prompt,
            image=prepared.image,
            mask_image=prepared.mask,
            width=self.config.width,
            height=self.config.height,
            guidance_scale=self.config.guidance_scale,
            num_inference_steps=self.config.num_inference_steps,
            generator=generator,
            strength=self.config.strength,
        ).images[0]
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
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

    @staticmethod
    def _describe_garment_reference(garment_path: str | Path | None) -> str:
        """Extract a small deterministic hint from an optional garment image.

        SDXL inpainting cannot copy a garment image by itself. This helper still
        improves text-only prompting by appending the dominant reference colour.
        For exact logos/patterns, swap this class for a CatVTON/IDM-VTON backend.
        """

        if garment_path is None:
            return ""
        image = Image.open(garment_path).convert("RGB").resize((64, 64))
        mean = ImageStat.Stat(image).mean
        red, green, blue = [int(value) for value in mean]
        return f"Use the garment reference as style guidance; approximate dominant RGB colour ({red}, {green}, {blue})."
