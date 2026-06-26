# Stronger models and data plan

For the most accurate local fashion assistant, use this order of preference:

1. **CatVTON** for low-VRAM local deployment. Its official project describes simplified inference under 8 GB VRAM at 1024x768, so it is the best first production upgrade from the SDXL fallback.
2. **IDM-VTON** for high-fidelity in-the-wild try-on and garment-detail preservation when the license fits your use.
3. **StableVITON** when you can support agnostic maps, agnostic masks, DensePose, cloth masks, and garment features.
4. **OOTDiffusion** when you need controllable latent-diffusion try-on with outfit fusion.

The code keeps a stable `FashionTryOnPipeline.generate(...)` interface and now has a backend adapter layer. Use `--backend sdxl` for the built-in fallback, or configure `--backend catvton|idm-vton|ootdiffusion|stableviton --external-backend-command "python path/to/runner.py"` to call a local research repo through a JSON payload.

## Accuracy upgrades before production

- Replace the heuristic mask with human parsing such as SCHP/Graphonomy plus pose keypoints.
- Use CatVTON/IDM-VTON rather than text-only inpainting for exact logos, embroidery, prints, and cuts.
- Add face embeddings to reject identity drift.
- Add DensePose or body-part segmentation to preserve apparent height and body proportions.
- Add prompt-attribute checks so requested colour, sleeve length, and garment category are validated.
- Fine-tune adapters per garment category instead of training one monolithic model immediately.

## Dataset sizing

A practical target is:

- 0 images for pretrained prototyping.
- 500-2,000 licensed pairs for a narrow LoRA/style adapter.
- 5,000-20,000 licensed pairs per garment category for meaningful category fine-tuning.
- 50,000-200,000+ diverse pairs for a general commercial-quality model.

Keep a separate evaluation set with diverse body types, skin tones, lighting, cameras, poses, and garment categories. Never train or evaluate on user photos without explicit consent.

## External backend contract

External backends receive one argument: a JSON payload path. The payload contains:

```json
{
  "person_path": "outputs/request.person.png",
  "mask_path": "outputs/request.mask.png",
  "garment_path": "examples/garment.jpg",
  "prompt": "...",
  "negative_prompt": "...",
  "output_path": "outputs/tryon.png"
}
```

Your runner must write the final RGB image to `output_path`. This lets this repository stay lightweight while still supporting best-in-class local VTON repos.
