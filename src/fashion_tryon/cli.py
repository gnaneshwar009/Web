from __future__ import annotations

import argparse

from .config import TryOnConfig
from .pipeline import FashionTryOnPipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a local virtual try-on image.")
    parser.add_argument("--person", required=True, help="Path to the user's full-body photo.")
    parser.add_argument("--prompt", required=True, help="Outfit colour, details, fabric, and design.")
    parser.add_argument("--output", default="outputs/tryon.png", help="Output image path.")
    parser.add_argument("--garment", default=None, help="Optional garment reference image for colour/style hints.")
    parser.add_argument("--category", default="full", choices=["upper", "lower", "full"], help="Garment area to edit.")
    parser.add_argument("--mask-output", default=None, help="Optional path to save the generated edit mask.")
    parser.add_argument("--report-output", default="outputs/quality.txt", help="Path to save quality metrics.")
    parser.add_argument("--device", default="cuda", choices=["cuda", "cpu"], help="Inference device.")
    parser.add_argument("--steps", type=int, default=30, help="Diffusion inference steps.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = TryOnConfig(device=args.device, num_inference_steps=args.steps)
    _, report = FashionTryOnPipeline(config).generate(
        args.person,
        args.prompt,
        args.output,
        garment_path=args.garment,
        category=args.category,
        mask_output_path=args.mask_output,
        report_output_path=args.report_output,
    )
    print(f"Saved try-on image to {args.output}")
    if report is not None:
        print(f"Quality report: {report.to_dict()}")


if __name__ == "__main__":
    main()
