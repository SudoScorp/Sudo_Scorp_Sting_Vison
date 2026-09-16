# SudoScorpStingVision

Multi-Media AI Detection and Source Attribution Platform

**Analyzes images, videos, and audio files to determine if they are AI-generated or real, and attributes the likely AI generator source.**

## Features

- **Real AI Deep Learning Model**: Fine-tuned ResNet18 CNN trained on synthetic dataset of 800 images (400 real + 400 AI-generated)
- **Multi-Modal Detection**: Image, video, and audio detection endpoints
- **Source Attribution**: Identifies likely AI generator (GAN, diffusion, hybrid patterns)
- **Watermark & Artifact Scanning**: Frequency analysis, histogram analysis, channel correlation checks
- **Policy Checking**: Mock external community standards compliance check
- **FastAPI Backend**: High-performance async API with CORS support
- **React Frontend**: Modern web interface for easy file upload and results visualization

## Quick Start

### Prerequisites

- Python 3.8+
- pip or uv package manager
- Node.js 16+ (for frontend)
- FFmpeg (optional, for video processing)

### Backend Setup

```bash
# Install dependencies
pip install -r requirements.txt
# Or with uv:
uv pip install -r requirements.txt

# Train the model (if you want to retrain)
python train.py

# Start the server
python main.py
```

The server starts at `http://0.0.0.0:8000`

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Server and model health check |
| `/api/image` | POST | Upload image for AI detection |
| `/api/video` | POST | Upload video for AI detection |
| `/api/audio` | POST | Upload audio for AI detection |
| `/attribution` | GET | Model attribution info |

### Example API Usage

```bash
# Check health
curl http://localhost:8000/health

# Detect AI in image
curl -X POST -F "file=@image.jpg" http://localhost:8000/api/image

# Detect AI in video
curl -X POST -F "file=@video.mp4" http://localhost:8000/api/video

# Detect AI in audio
curl -X POST -F "file=@audio.wav" http://localhost:8000/api/audio
```

### Response Format

```json
{
  "is_ai_generated": true,
  "confidence": 0.95,
  "predicted_class": "ai_image",
  "probabilities": {
    "real": 0.03,
    "ai_image": 0.95,
    "ai_audio": 0.02
  },
  "source_attribution": "ai_image",
  "generator": "ai_image",
  "metadata": {
    "file_size_bytes": 123456,
    "format": "JPEG",
    "width": 1920,
    "height": 1080
  },
  "watermark_scan": {
    "watermarks_found": [],
    "checksum": "a1b2c3d4e5f6",
    "compression_artifacts": null,
    "high_frequency_energy": 42.1,
    "frequency_ratio": 1.8,
    "periodic_pattern_detected": false,
    "channel_correlations": {
      "red_green": 0.01,
      "green_blue": 0.02
    }
  },
  "policy_check": {
    "policy_passed": false,
    "ai_confidence": 0.95,
    "flagged_for_review": true,
    "reason": "High confidence (95.0%) AI-generated image detected"
  }
}
```

### Training a New Model

```bash
# Generate synthetic dataset
python generate_dataset.py --output dataset --real 500 --ai 500

# Train model
python train.py --data dataset --epochs 30 --lr 0.0001

# Or with custom settings
python train.py --data ./my_dataset --epochs 50 --batch-size 16 --lr 0.00005
```

### Frontend Setup

```bash
cd frontend
npm install
npm start
```

The frontend runs at `http://localhost:3000`

## Model Architecture

The detection model uses a fine-tuned **ResNet18** backbone:

- **Pretrained weights**: ImageNet pretrained ResNet18
- **Frozen layers**: Early layers frozen for feature extraction
- **Fine-tuned layers**: Layer4 + classifier head trained on deepfake dataset
- **Input size**: 224x224 RGB images
- **Classes**: determined by the dataset at training time (the bundled generator produces 3: `real`, `ai_image`, `ai_audio`); the class count and mapping are saved to `class_map.json` and read by the server at inference time

## Dataset

The dataset is generated with `generate_dataset.py` (not checked into git —
run the command below before training). It creates three classes:

- **real** (200 train + 50 val by default): natural noise patterns, organic textures, blended color blobs
- **ai_image** (200 train + 50 val by default): checkerboard upsampling artifacts plus high-frequency noise, mimicking GAN/diffusion image generators
- **ai_audio** (200 train + 50 val by default): synthetic spectrogram-style patterns, mimicking AI voice/audio generators (e.g. ElevenLabs-style output)

Counts are configurable via `--train`, `--val`, `--output`, and `--seed`.

### Dataset Structure

```
dataset/
  train/
    real/         # 200 images
    ai_image/     # 200 images
    ai_audio/     # 200 images
  val/
    real/         # 50 images
    ai_image/     # 50 images
    ai_audio/     # 50 images
```

## Detection Pipeline

### Image Detection

1. Load and preprocess image (resize to 224x224, normalize)
2. Run through ResNet18 model
3. Apply softmax to get class probabilities
4. Compute AI confidence (1 - real_probability)
5. Extract metadata (EXIF, dimensions, format)
6. Scan for watermarks/artifacts (frequency analysis, histogram analysis)
7. Run policy check
8. Return structured result

### Video Detection

1. Extract frames using OpenCV (sample ~16 frames)
2. Run each frame through image detection pipeline
3. Average probabilities across frames
4. Return aggregated result with frame count

### Audio Detection

1. Load audio with torchaudio
2. Convert to mel spectrogram
3. Treat spectrogram as image and run through model
4. Return detection result

**Note**: Audio detection is experimental. The mel spectrogram approach provides basic detection capability but may not be as accurate as dedicated audio deepfake models.

## Watermark & Artifact Scanning

The platform includes real artifact detection (not just stubs):

- **Frequency Analysis**: FFT-based detection of periodic patterns (GAN upsampling artifacts)
- **Histogram Analysis**: Per-channel skewness/kurtosis to detect unnatural color distributions
- **Channel Correlation**: Checks for anomalous R/G/B correlations
- **High-Frequency Energy**: Laplacian-based detection of GAN fingerprint noise
- **Frequency Ratio**: Center vs periphery FFT energy ratio

Each detection includes:
- `type`: Category of finding
- `detail`: Human-readable description
- `severity`: 0-1 score indicating confidence of the finding

## Policy Check

The mock policy check combines:
- Model AI confidence (70% weight)
- Maximum watermark artifact severity (30% weight)

Results:
- **Score > 0.90**: Flagged for manual review
- **Score > 0.70**: Review recommended
- **Score ≤ 0.70**: Passes community standards

## Performance

- **Image inference**: ~50ms on CPU, ~5ms on GPU
- **Video inference**: ~800ms for 16 frames on CPU
- **Audio inference**: ~200ms on CPU

## Limitations

1. **Dataset**: The model is trained on synthetic data, not real deepfake datasets. Performance on real-world deepfakes may vary.
2. **Audio Detection**: Uses mel spectrogram approach, which is less accurate than dedicated audio models.
3. **Watermark Scanning**: Basic frequency/histogram analysis, not a full forensic suite.
4. **Policy Check**: Mock implementation, not connected to real policy services.

## File Structure

```
SudoScorpStingVision/
├── main.py                    # FastAPI server
├── model.py                   # Model definition (ResNet18)
├── train.py                   # Training pipeline
├── generate_dataset.py        # Synthetic dataset generator
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Backend container image
├── LICENSE                    # MIT License
├── README.md                  # This file
├── frontend/                  # React frontend
│   ├── package.json
│   ├── public/
│   │   └── index.html
│   └── src/
│       ├── index.js
│       └── App.js
├── best_model.pth             # Trained model weights (generated, gitignored)
├── model_weights.pth          # Copy of model weights for inference (generated, gitignored)
├── class_map.json            # Class mapping and metadata
├── training_history.json     # Training metrics
└── dataset/                   # Training dataset (generated, gitignored)
    ├── train/
    │   ├── real/
    │   ├── ai_image/
    │   └── ai_audio/
    └── val/
        ├── real/
        ├── ai_image/
        └── ai_audio/
```

## Deployment

### Docker

```bash
docker build -t sudo-scorp-sting-vision .
docker run -p 8000:8000 sudo-scorp-sting-vision
```

### Production

For production deployment:
1. Use a production ASGI server (gunicorn with uvicorn workers)
2. Enable HTTPS
3. Set up proper CORS policies
4. Connect real policy checking service
5. Use a real forensic watermark detection library

## License

MIT License - see LICENSE file for details.

## Credits

Built with:
- PyTorch / TorchVision / TorchAudio
- FastAPI / Uvicorn
- React / Axios
- OpenCV / Pillow / NumPy / SciPy
