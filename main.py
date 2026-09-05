import os
import sys
import subprocess

# ===========================================================================
# 1. AUTO-CONFIGURATION & REQUIREMENTS SETUP
# ===========================================================================
def setup_environment():
    requirements = [
        "fastapi==0.109.2",
        "uvicorn==0.27.1",
        "torch==2.2.1",
        "torchvision==0.17.1",
        "torchaudio==2.2.1",
        "pillow==10.2.0",
        "numpy==1.26.4",
        "python-multipart==0.0.9",
        "opencv-python==4.9.0.80",
    ]

    with open("requirements.txt", "w") as f:
        f.write("\n".join(requirements))

    try:
        import torch
        import fastapi
    except ImportError:
        print("Installing exact framework versions ...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        os.execv(sys.executable, [sys.executable] + sys.argv)

setup_environment()

# ===========================================================================
# 2. IMPORTS & AI MODEL INITIALISATION
# ===========================================================================
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from PIL import Image, ExifTags
import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import transforms
import torchaudio
import cv2
import tempfile
import numpy as np

app = FastAPI(title="SudoScorpStingVision — Multi-Media AI Detector")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Model architectures (must match train.py)
# ---------------------------------------------------------------------------

class DeepfakeDetectorCNN(nn.Module):
    """Original scratch CNN from the repo (for backward-compatible weights)."""

    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv2d(3, 32, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.conv3 = nn.Conv2d(64, 128, kernel_size=3, padding=1)
        self.pool = nn.MaxPool2d(2, 2)
        self.fc1 = nn.Linear(128 * 28 * 28, 512)
        self.fc2 = nn.Linear(512, 2)

    def forward(self, x):
        x = self.pool(F.relu(self.conv1(x)))
        x = self.pool(F.relu(self.conv2(x)))
        x = self.pool(F.relu(self.conv3(x)))
        x = x.view(x.size(0), -1)
        x = F.relu(self.fc1(x))
        x = self.fc2(x)
        return x


class ResNetDetector(nn.Module):
    """
    Pretrained ResNet18 backbone (default in train.py).
    Early layers frozen; last conv block + classifier fine-tuned.
    """

    def __init__(self):
        super().__init__()
        from torchvision.models import ResNet18_Weights, resnet18
        weights = ResNet18_Weights.DEFAULT
        self.backbone = resnet18(weights=weights)
        for param in self.backbone.parameters():
            param.requires_grad = False
        for param in self.backbone.layer4.parameters():
            param.requires_grad = True
        self.backbone.fc = nn.Sequential(nn.Dropout(0.3), nn.Linear(512, 2))

    def forward(self, x):
        return self.backbone(x)


# ---------------------------------------------------------------------------
# Load trained weights if available (architecture auto-detected)
# ---------------------------------------------------------------------------

MODEL_WEIGHTS_PATH = "model_weights.pth"
CLASS_MAP_PATH = "class_map.json"
ARCH_PATH = "model_arch.json"

model = None
weights_loaded = False
architecture = "unknown"

class_names = ["real", "ai"]
class_to_idx = {"real": 0, "ai": 1}

def _detect_and_load():
    global model, weights_loaded, architecture, class_names, class_to_idx

    if not os.path.exists(MODEL_WEIGHTS_PATH):
        print("[INFO] No model_weights.pth found — running with untrained weights.")
        print("       Train with:  python train.py")
        model = DeepfakeDetectorCNN()
        return

    # Determine architecture from saved marker, or sniff the state dict.
    arch = "cnn"
    if os.path.exists(ARCH_PATH):
        try:
            import json
            with open(ARCH_PATH) as f:
                arch = json.load(f).get("architecture", "cnn")
        except Exception:
            pass

    state = torch.load(MODEL_WEIGHTS_PATH, map_location="cpu", weights_only=True)
    # ResNet state dicts carry 'backbone.' prefix; the scratch CNN does not.
    if arch == "resnet" or any(k.startswith("backbone.") for k in state.keys()):
        architecture = "resnet"
        model = ResNetDetector()
        print("[OK] Detected ResNet18-based weights — loading ResNetDetector.")
    else:
        architecture = "cnn"
        model = DeepfakeDetectorCNN()
        print("[OK] Detected scratch CNN weights — loading DeepfakeDetectorCNN.")

    try:
        model.load_state_dict(state)
        weights_loaded = True
        print(f"[OK] Trained weights loaded from {MODEL_WEIGHTS_PATH}  (arch={architecture})")
    except Exception as e:
        print(f"[WARN] Could not load weights: {e}")
        print("       The server will run with untrained weights until you fix the file.")

    if os.path.exists(CLASS_MAP_PATH):
        try:
            import json
            with open(CLASS_MAP_PATH) as f:
                cmap = json.load(f)
            class_names = cmap["classes"]
            class_to_idx = cmap["class_to_idx"]
            print(f"[OK] Class map: {class_names}")
        except Exception as e:
            print(f"[WARN] Could not load class map: {e}")

_detect_and_load()

# ===========================================================================
# 3. UTILITY FUNCTIONS
# ===========================================================================

def extract_metadata(file_path, file_type):
    metadata = {"file_size_mb": round(os.path.getsize(file_path) / (1024 * 1024), 2)}
    try:
        if file_type == "image":
            img = Image.open(file_path)
            metadata["format"] = img.format
            metadata["dimensions"] = f"{img.width}x{img.height}"
            exif = img._getexif()
            if exif:
                metadata["exif_tags"] = {ExifTags.TAGS.get(k, k): str(v) for k, v in exif.items()}
        elif file_type == "video":
            cap = cv2.VideoCapture(file_path)
            metadata["fps"] = cap.get(cv2.CAP_PROP_FPS)
            metadata["frame_count"] = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            cap.release()
        elif file_type == "audio":
            info = torchaudio.info(file_path)
            metadata["sample_rate"] = info.sample_rate
            metadata["channels"] = info.num_channels
    except Exception as e:
        metadata["warning"] = f"Metadata extraction failed: {e}"
    return metadata


def scan_invisible_watermarks(file_path):
    """Placeholder — replace with real DCT / fingerprint inspection in production."""
    return "No invisible watermarks detected (scan not implemented)"


def mock_external_policy_check(ai_prob, file_type):
    if ai_prob > 0.95:
        return "Flagged for manual review: High confidence AI-generated content"
    return "Passes community standards"


# ===========================================================================
# 4. MEDIA PROCESSING FUNCTIONS
# ===========================================================================

def process_image(file_path):
    img = Image.open(file_path).convert("RGB").resize((224, 224))
    tensor = transforms.ToTensor()(img).unsqueeze(0)
    with torch.no_grad():
        outputs = model(tensor)
        probabilities = F.softmax(outputs, dim=1)
        ai_prob = probabilities[0][1].item()
    return ai_prob, class_names[1] if ai_prob > 0.5 else class_names[0]


def process_video(file_path):
    cap = cv2.VideoCapture(file_path)
    frames = []
    frame_count = 0
    while cap.isOpened() and frame_count < 16:
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = cv2.resize(frame, (224, 224))
        frames.append(transforms.ToTensor()(Image.fromarray(frame)))
        frame_count += 1
    cap.release()
    if not frames:
        return 0.0, class_names[0]
    batch = torch.stack(frames)
    with torch.no_grad():
        outputs = model(batch)
        probabilities = F.softmax(outputs, dim=1)
        ai_prob = torch.mean(probabilities[:, 1]).item()
    return ai_prob, class_names[1] if ai_prob > 0.5 else class_names[0]


def process_audio(file_path):
    waveform, sample_rate = torchaudio.load(file_path)
    if waveform.shape[0] > 1:
        waveform = waveform.mean(dim=0, keepdim=True)
    mel_spec = torchaudio.transforms.MelSpectrogram(sample_rate=sample_rate, n_mels=128)(waveform)
    log_mel = torchaudio.transforms.AmplitudeToDB()(mel_spec)
    log_mel = F.interpolate(
        log_mel.unsqueeze(0), size=(224, 224), mode="bilinear", align_corners=False
    ).squeeze(0)
    three_channel = log_mel.repeat(3, 1, 1).unsqueeze(0)
    with torch.no_grad():
        outputs = model(three_channel)
        probabilities = F.softmax(outputs, dim=1)
        ai_prob = probabilities[0][1].item()
    return ai_prob, class_names[1] if ai_prob > 0.5 else class_names[0]


async def save_temp_file(file: UploadFile):
    suffix = os.path.splitext(file.filename)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp:
        temp_path = temp.name
        while content := await file.read(5 * 1024 * 1024):
            temp.write(content)
    return temp_path


# ===========================================================================
# 5. API ENDPOINTS
# ===========================================================================

class HealthResponse(BaseModel):
    status: str
    weights_loaded: bool
    architecture: str
    class_names: list[str]
    device: str


@app.get("/health", response_model=HealthResponse)
def health():
    import torch
    return HealthResponse(
        status="ok",
        weights_loaded=weights_loaded,
        architecture=architecture,
        class_names=class_names,
        device=torch.device("cuda" if torch.cuda.is_available() else "cpu").type,
    )


@app.post("/api/image")
async def detect_image(file: UploadFile = File(...)):
    temp_path = None
    try:
        temp_path = await save_temp_file(file)
        metadata = extract_metadata(temp_path, "image")
        watermark = scan_invisible_watermarks(temp_path)
        ai_prob, generator = process_image(temp_path)
        is_ai = ai_prob > 0.5
        policy = mock_external_policy_check(ai_prob, "image")
        return {
            "aiGenerated": is_ai,
            "confidence": round(ai_prob, 4),
            "generator": generator if is_ai else "N/A",
            "metadata": metadata,
            "watermarkScan": watermark,
            "policyCheck": policy,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


@app.post("/api/video")
async def detect_video(file: UploadFile = File(...)):
    temp_path = None
    try:
        temp_path = await save_temp_file(file)
        metadata = extract_metadata(temp_path, "video")
        watermark = scan_invisible_watermarks(temp_path)
        ai_prob, generator = process_video(temp_path)
        is_ai = ai_prob > 0.5
        policy = mock_external_policy_check(ai_prob, "video")
        return {
            "aiGenerated": is_ai,
            "confidence": round(ai_prob, 4),
            "generator": generator if is_ai else "N/A",
            "metadata": metadata,
            "watermarkScan": watermark,
            "policyCheck": policy,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


@app.post("/api/audio")
async def detect_audio(file: UploadFile = File(...)):
    temp_path = None
    try:
        temp_path = await save_temp_file(file)
        metadata = extract_metadata(temp_path, "audio")
        watermark = scan_invisible_watermarks(temp_path)
        ai_prob, generator = process_audio(temp_path)
        is_ai = ai_prob > 0.5
        policy = mock_external_policy_check(ai_prob, "audio")
        return {
            "aiGenerated": is_ai,
            "confidence": round(ai_prob, 4),
            "generator": generator if is_ai else "N/A",
            "metadata": metadata,
            "watermarkScan": watermark,
            "policyCheck": policy,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
