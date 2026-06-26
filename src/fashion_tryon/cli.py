from __future__ import annotations

import argparse

from .config import TryOnConfig
from .pipeline import FashionTryOnPipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a local virtual try-on image.")
    parser.add_argument("--person", required=True, help="Path to the user's full-body photo.")
    parser.add_argument("--prompt", required=True, help="Outfit colour, details, fabric, and design.")
    parser.add_argument("--output", default="outputs/tryon.png", help="Output image path.")
    parser.add_argument("--device", default="cuda", choices=["cuda", "cpu"], help="Inference device.")
    parser.add_argument("--steps", type=int, default=30, help="Diffusion inference steps.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = TryOnConfig(device=args.device, num_inference_steps=args.steps)
    FashionTryOnPipeline(config).generate(args.person, args.prompt, args.output)
    print(f"Saved try-on image to {args.output}")


if __name__ == "__main__":
    main()
