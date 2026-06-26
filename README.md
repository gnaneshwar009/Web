# Local Fashion Try-On Assistant

This repository contains a practical local AI/ML starter for a fashion assistant that accepts a full-body user photo plus a text outfit prompt and generates a try-on image. The recommended production architecture is **not** to train a whole model from scratch first. Start with a strong open virtual try-on diffusion model, add identity/pose/body-preservation controls, then fine-tune only when you have enough licensed paired fashion data.

## Best architecture

Use a **diffusion virtual try-on pipeline** with these components:

1. **Person preprocessing**
   - Full-body person detection/crop.
   - Pose/keypoints for arms, legs, shoulders, and torso.
   - Human parsing/segmentation to isolate hair, face, skin, existing clothes, and background.
   - Optional depth/normal estimation for body geometry.
2. **Outfit conditioning**
   - Text prompt: colour, fabric, design details, sleeve length, fit, occasion.
   - Optional garment reference image for higher realism. Text-only outfit generation is possible, but garment-image try-on is much more reliable for exact patterns and logos.
3. **Try-on generator**
   - Recommended local baseline: **IDM-VTON-style two-stream diffusion** for preserving garment details and identity.
   - Alternative baselines: **CatVTON**, **LaDI-VTON**, or **VITON-HD** depending on your GPU and license needs.
4. **Identity/body preservation**
   - Keep face and exposed skin from the source photo with masks.
   - Use pose/depth conditioning so height, body shape, and limb placement are not changed unnecessarily.
   - Use face/identity similarity checks after generation and reject outputs that drift too much.
5. **Safety and quality gates**
   - Reject non-full-body inputs.
   - Warn that exact weight/height cannot be measured from one photo; the system can preserve apparent body proportions, not medically accurate measurements.
   - Run automated checks for face similarity, pose similarity, segmentation consistency, and prompt adherence.

## Model recommendation

For a local PC, choose based on VRAM:

| GPU VRAM | Recommended path | Notes |
| --- | --- | --- |
| 6-8 GB | Quantized/inference-only CatVTON or SD inpainting fallback | Lower resolution, slower, less exact details. |
| 12 GB | SDXL inpainting + ControlNet/OpenPose + segmentation masks | Good prototype. |
| 16-24 GB | IDM-VTON or CatVTON at 768-1024 px | Best local balance. |
| 24+ GB | Fine-tune LoRA/adapters on VITON-HD + Dress Code | Practical research setup. |

The starter code below uses a **local SDXL inpainting fallback** because it is straightforward to run and customize. It now supports garment-category masks, optional garment-reference colour hints, mask export, and quality reports. For production quality, replace `src/fashion_tryon/pipeline.py` with an IDM-VTON/CatVTON inference wrapper while keeping the same API. See `MODELS_AND_DATA.md` for the stronger model roadmap.

## Datasets

Use only datasets whose license permits your intended use.

| Dataset | Approximate use | Why it matters |
| --- | --- | --- |
| Dress Code | Multi-category dresses, upper-body, lower-body | High-resolution full-body pairs and better category coverage. |
| VITON-HD | Upper-body high-resolution try-on | Classic benchmark for 1024x768 virtual try-on. |
| DeepFashion / DeepFashion-MultiModal | Fashion attributes and parsing support | Useful for labels, attributes, pose, and category learning. |
| Your own consented photos | Domain adaptation | Needed for your camera, lighting, region, and target fashion style. |

### How much data is enough?

There is no dataset size that trains a model "perfectly". A realistic plan is:

- **Prototype/inference only:** 0 training images; use pretrained weights.
- **LoRA/style adapter:** 500-2,000 high-quality licensed image pairs per category.
- **Category-specific fine-tune:** 5,000-20,000 paired examples per category.
- **General production model:** 50,000-200,000+ diverse paired examples across body types, skin tones, poses, garment categories, lighting, and cameras.
- **Evaluation holdout:** keep at least 10-15% unseen examples and include real user photos, not only catalog images.

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m fashion_tryon.cli \
  --backend sdxl \
  --person examples/person.jpg \
  --garment examples/garment.jpg \
  --prompt "navy blue slim-fit tuxedo with satin lapels" \
  --category full \
  --seed 42 \
  --width 768 \
  --height 1024 \
  --guidance-scale 7.5 \
  --strength 0.86 \
  --mask-output outputs/mask.png \
  --report-output outputs/quality.txt \
  --output outputs/tryon.png
```

For CatVTON/IDM-VTON-style local repos, keep this app and call an external runner:

```bash
python -m fashion_tryon.cli \
  --backend catvton \
  --external-backend-command "python external/catvton_runner.py" \
  --person examples/person.jpg \
  --garment examples/garment.jpg \
  --prompt "black velvet prom suit with silver embroidery"
```

Or run the API:

```bash
uvicorn fashion_tryon.api:app --host 127.0.0.1 --port 8000
# Health: http://127.0.0.1:8000/health
# Models: http://127.0.0.1:8000/models
```

Then send a multipart request:

```bash
curl -X POST http://127.0.0.1:8000/try-on \
  -F 'person=@examples/person.jpg' \
  -F 'garment=@examples/garment.jpg' \
  -F 'category=full' \
  -F 'prompt=emerald green embroidered sherwani with gold buttons' \
  --output outputs/result.png
```

## Training plan

1. Start with pretrained inference and collect failures.
2. Label failure types: face drift, hand artifacts, wrong colour, bad garment length, body-shape distortion.
3. Fine-tune LoRA/adapters before full-model training.
4. Train with paired try-on data plus preservation losses:
   - face identity similarity,
   - pose/keypoint similarity,
   - body segmentation consistency,
   - garment texture/detail reconstruction,
   - prompt/attribute consistency.
5. Evaluate by body type, skin tone, gender presentation, garment category, and lighting. Do not claim accurate weight or height from a single image.

## Project layout

```text
src/fashion_tryon/
  api.py          FastAPI HTTP endpoint
  cli.py          Command-line entry point
  config.py       Runtime settings
  backends.py     SDXL backend plus external CatVTON/IDM-VTON command adapter
  pipeline.py     Local diffusion inpainting pipeline
  validation.py   Upload and prompt validation
  preprocess.py   Person image validation and mask generation
  quality.py      Post-generation identity/body drift checks
```
