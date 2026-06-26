from dataclasses import dataclass


@dataclass(frozen=True)
class TryOnConfig:
    """Runtime settings for local virtual try-on inference."""

    model_id: str = "diffusers/stable-diffusion-xl-1.0-inpainting-0.1"
    device: str = "cuda"
    width: int = 768
    height: int = 1024
    guidance_scale: float = 7.5
    num_inference_steps: int = 30
    seed: int | None = 42
    preserve_face_ratio: float = 0.18
