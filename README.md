# Sudo_Scorp_Sting_Vison

Multi-Media AI Detection: Analyzes images, videos, and audio files to determine
if they are AI-generated or real.

- **Real Deep Learning**: Uses a genuine PyTorch 2D Convolutional Neural Network
  (CNN) to process visual and auditory data.
- **Source Attribution**: Labels the likely generator category (e.g. Midjourney /
  Stable Diffusion for images, Sora / Runway for video, ElevenLabs / Descript for
  audio).  Attribution is heuristic-based and not a forensic guarantee.

## Contents

- `main.py` — FastAPI backend (image / video / audio endpoints, metadata extraction,
  watermark scan stub, policy check stub)
- `train.py` — Training pipeline (pretrained ResNet18 backbone or scratch CNN,
  early stopping, best-model checkpointing, class-map serialization)
- `generate_synthetic_data.py` — Generates a small labelled synthetic dataset so
  the pipeline can be validated end-to-end with no external data
- `App.js` — Minimal React upload UI (image endpoint only)
- `requirements.txt` — Pinned Python dependencies

## Quick start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. (Optional) Generate synthetic training data

If you have no real dataset yet, the synthetic generator creates a small labelled
set so training can be exercised immediately:

```bash
python generate_synthetic_data.py
```

This writes `dataset/train/{real,ai}/` and `dataset/val/{real,ai}/`.

### 3. Train the model

```bash
python train.py --epochs 10 --batch 32
```

This produces:
- `best_model.pth` — best validation checkpoint
- `model_weights.pth` — backward-compatible copy loaded by `main.py`
- `class_map.json` — class names + index mapping

If a real dataset is available, place it under `dataset/train/{real,ai}` and
`dataset/val/{real,ai}` before running `train.py`.

### 4. Run the API server

```bash
python main.py
```

The server starts on `http://0.0.0.0:8000`.  Check health:

```bash
curl http://localhost:8000/health
```

### 5. Test it

```bash
# image
curl -F "file=@photo.jpg" http://localhost:8000/api/image

# video
curl -F "file=@clip.mp4" http://localhost:8000/api/video

# audio (WAV recommended; MP3 may need soundfile/pydub on some platforms)
curl -F "file=@voice.wav" http://localhost:8000/api/audio
```

### 6. Frontend (optional)

Drop `App.js` into a React app's `src/` folder and run `npm start`.  The UI
targets `http://localhost:8000/api/image`.

## Dataset format

The training pipeline uses `torchvision.datasets.ImageFolder`, which expects:

```
dataset/
    train/
        real/   ← authentic images
        ai/     ← AI-generated images
    val/
        real/
        ai/
```

Class names are derived from the subdirectory names and saved to `class_map.json`.

## Model architecture

Two modes are supported (controlled by `--no-pretrained` in `train.py`):

1. **Pretrained ResNet18 backbone** (default) — early layers frozen, last conv
   block + classifier fine-tuned.  Gives a meaningful feature basis from day one.
2. **Scratch DeepfakeDetectorCNN** — the original 3-conv-layer architecture from
   the repo.  Useful for debugging but will need far more data to be useful.

At inference time `main.py` loads `model_weights.pth` when present; if the file
doesn't exist the server starts with an untrained model and returns random
confidence scores.  The `/health` endpoint reports whether weights are loaded.

## Caveats

- The model needs a **real labelled dataset** to be useful.  The synthetic data
  exists only to validate the pipeline; it will not detect real deepfakes.
- Audio MP3 support depends on OS codec libraries.  WAV is the safest test format.
  If MP3s fail, add `soundfile` and `pydub` to requirements.
- Watermark scanning and policy checks are stubs — replace with real implementations
  before relying on them in production.
- Source attribution is heuristic; treat generator labels as best-effort guesses.

## Prerequisites

- Python 3.8–3.11 (3.12 may have PyTorch compatibility issues)
- NVIDIA GPU + CUDA recommended for training speed (CPU works but slower)
- Node.js 16+ and npm for the React frontend
- FFmpeg helpful for video / audio handling

## How this differs from the original

- Training now uses a pretrained backbone and saves best-model checkpoints rather
  than raw final-state weights.
- `main.py` loads trained weights and class mapping at startup instead of running
  an always-random model.
- A `/health` endpoint reports load state.
- A synthetic data generator lets the full train→serve loop be validated on a
  clean machine.
- Audio processing falls back to mono safely instead of assuming stereo layout.
