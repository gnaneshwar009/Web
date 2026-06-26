# Stronger models and data plan

For the most accurate local fashion assistant, use this order of preference:

1. **CatVTON** for low-VRAM local deployment. It reports simplified inference at 1024x768 with less than 8 GB VRAM and a lightweight trainable setup, making it the best first upgrade from the SDXL inpainting fallback.
2. **IDM-VTON** for high-fidelity in-the-wild try-on when the license fits your use. It is built specifically for authentic virtual try-on and garment-detail preservation.
3. **StableVITON** when you can support agnostic maps, agnostic masks, DensePose, and garment features.
4. **OOTDiffusion** when you need controllable latent-diffusion try-on with outfit fusion.

The code in this repository keeps a stable interface in `FashionTryOnPipeline.generate(...)` so you can replace the current baseline with one of those model backends without changing the CLI or API.

## Accuracy upgrades to add before production

- Replace the heuristic mask with human parsing such as SCHP/Graphonomy plus pose keypoints.
- Add a garment image input and use CatVTON/IDM-VTON rather than text-only inpainting for exact logos, embroidery, prints, and cuts.
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
