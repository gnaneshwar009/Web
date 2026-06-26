from dataclasses import dataclass


@dataclass(frozen=True)
class TryOnConfig:
    """Runtime settings for local virtual try-on inference."""

    backend: str = "sdxl"
    model_id: str = "diffusers/stable-diffusion-xl-1.0-inpainting-0.1"
    external_backend_command: str = ""
    device: str = "cuda"
    width: int = 768
    height: int = 1024
    guidance_scale: float = 7.5
    num_inference_steps: int = 30
    seed: int | None = 42
    preserve_face_ratio: float = 0.18
    strength: float = 0.86
    mask_blur_radius: int = 14
    category: str = "full"
    run_quality_checks: bool = True
    enable_vae_tiling: bool = True
    enable_model_cpu_offload: bool = False
    max_upload_mb: int = 25
