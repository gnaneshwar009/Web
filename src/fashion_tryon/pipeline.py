from __future__ import annotations

from pathlib import Path

import torch
from diffusers import AutoPipelineForInpainting
from PIL import Image

from .config import TryOnConfig
from .preprocess import prepare_person


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

    def generate(self, person_path: str | Path, prompt: str, output_path: str | Path) -> Image.Image:
        prepared = prepare_person(
            person_path,
            width=self.config.width,
            height=self.config.height,
            preserve_face_ratio=self.config.preserve_face_ratio,
        )
        generator = None
        if self.config.seed is not None:
            generator = torch.Generator(device=self.device).manual_seed(self.config.seed)

        final_prompt = (
            "photorealistic full body fashion try-on, preserve the person's face, skin tone, "
            "body proportions, height impression, pose, hands, and background; outfit: "
            f"{prompt}"
        )
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
        ).images[0]
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        result.save(output_path)
        return result
