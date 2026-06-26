from __future__ import annotations

import json
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import torch
from diffusers import AutoPipelineForInpainting
from PIL import Image, ImageStat

from .config import TryOnConfig


@dataclass(frozen=True)
class GenerationInputs:
    person_image: Image.Image
    mask_image: Image.Image
    prompt: str
    negative_prompt: str
    output_path: Path
    garment_path: Path | None = None


class TryOnBackend(Protocol):
    name: str

    def generate(self, inputs: GenerationInputs) -> Image.Image:
        """Generate a try-on image from prepared inputs."""


class SDXLInpaintingBackend:
    """Dependency-light local fallback using SDXL inpainting."""

    name = "sdxl"

    def __init__(self, config: TryOnConfig) -> None:
        self.config = config
        dtype = torch.float16 if config.device == "cuda" and torch.cuda.is_available() else torch.float32
        device = config.device if config.device == "cuda" and torch.cuda.is_available() else "cpu"
        self.device = device
        self.pipe = AutoPipelineForInpainting.from_pretrained(
            config.model_id,
            torch_dtype=dtype,
            variant="fp16" if dtype == torch.float16 else None,
        ).to(device)
        if hasattr(self.pipe, "enable_attention_slicing"):
            self.pipe.enable_attention_slicing()
        if config.enable_vae_tiling and hasattr(self.pipe, "enable_vae_tiling"):
            self.pipe.enable_vae_tiling()
        if config.enable_model_cpu_offload and hasattr(self.pipe, "enable_model_cpu_offload"):
            self.pipe.enable_model_cpu_offload()

    def generate(self, inputs: GenerationInputs) -> Image.Image:
        generator = None
        if self.config.seed is not None:
            generator = torch.Generator(device=self.device).manual_seed(self.config.seed)
        return self.pipe(
            prompt=inputs.prompt,
            negative_prompt=inputs.negative_prompt,
            image=inputs.person_image,
            mask_image=inputs.mask_image,
            width=self.config.width,
            height=self.config.height,
            guidance_scale=self.config.guidance_scale,
            num_inference_steps=self.config.num_inference_steps,
            generator=generator,
            strength=self.config.strength,
        ).images[0]


class ExternalCommandBackend:
    """Adapter for stronger local VTON repos such as CatVTON or IDM-VTON.

    The command receives a JSON payload path as its only argument. The external
    script should write the generated image to `output_path` in that payload.
    This keeps this package license-neutral while still making the app ready for
    production backends cloned locally by the user.
    """

    def __init__(self, name: str, command: str) -> None:
        if not command:
            raise ValueError(f"{name} backend requires an external command")
        self.name = name
        self.command = command

    def generate(self, inputs: GenerationInputs) -> Image.Image:
        payload_path = inputs.output_path.with_suffix(f".{self.name}.json")
        person_path = inputs.output_path.with_suffix(".person.png")
        mask_path = inputs.output_path.with_suffix(".mask.png")
        inputs.person_image.save(person_path)
        inputs.mask_image.save(mask_path)
        payload = {
            "person_path": str(person_path),
            "mask_path": str(mask_path),
            "garment_path": str(inputs.garment_path) if inputs.garment_path else None,
            "prompt": inputs.prompt,
            "negative_prompt": inputs.negative_prompt,
            "output_path": str(inputs.output_path),
        }
        payload_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        subprocess.run([*shlex.split(self.command), str(payload_path)], check=True)
        return Image.open(inputs.output_path).convert("RGB")


def describe_garment_reference(garment_path: str | Path | None) -> str:
    """Extract deterministic colour guidance from an optional garment image."""

    if garment_path is None:
        return ""
    image = Image.open(garment_path).convert("RGB").resize((64, 64))
    mean = ImageStat.Stat(image).mean
    red, green, blue = [int(value) for value in mean]
    return f"Use the garment reference as style guidance; approximate dominant RGB colour ({red}, {green}, {blue})."


def build_backend(config: TryOnConfig) -> TryOnBackend:
    backend = config.backend.lower().strip()
    if backend == "sdxl":
        return SDXLInpaintingBackend(config)
    if backend in {"catvton", "idm-vton", "idmvton", "ootdiffusion", "stableviton"}:
        return ExternalCommandBackend(backend, config.external_backend_command)
    raise ValueError(f"Unsupported backend '{config.backend}'. Use sdxl, catvton, idm-vton, ootdiffusion, or stableviton.")
