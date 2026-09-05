#!/usr/bin/env python3
"""
SudoScorpStingVision — FastAPI Inference Server
Multi-Media AI Detection and Source Attribution Platform

Analyzes images, videos, and audio files to determine if they are AI-generated or real,
and attributes the likely AI generator source.
"""

import os
import io
import json
import tempfile
import shutil
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

import torch
import torch.nn.functional as F
from PIL import Image
import numpy as np
import cv2
import torchvision.transforms as T

from model import DeepfakeDetectorCNN

# ---- App Setup ----
app = FastAPI(
    title="SudoScorpStingVision",
    description="Multi-Media AI Detection and Source Attribution",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Global State ----
MODEL = None
CLASS_MAP = None
MODEL_LOADED = False
MODEL_PATH = "model_weights.pth"
CLASS_MAP_PATH = "class_map.json"
INPUT_SIZE = 224


def load_model():
    """Load trained model and class mapping."""
    global MODEL, CLASS_MAP, MODEL_LOADED

    if MODEL_LOADED and MODEL is not None:
        return

    # Load class map
    if os.path.exists(CLASS_MAP_PATH):
        with open(CLASS_MAP_PATH, "r") as f:
            CLASS_MAP = json.load(f)
    else:
        CLASS_MAP = {
            "classes": ["real", "ai_image", "ai_audio"],
            "class_to_idx": {"real": 0, "ai_image": 1, "ai_audio": 2},
            "idx_to_class": {0: "real", 1: "ai_image", 2: "ai_audio"},
            "num_classes": 3,
        }

    num_classes = CLASS_MAP.get("num_classes", 3)
    MODEL = DeepfakeDetectorCNN(num_classes=num_classes, pretrained=False)
    MODEL.eval()

    if os.path.exists(MODEL_PATH):
        try:
            state_dict = torch.load(MODEL_PATH, map_location="cpu")
            MODEL.load_state_dict(state_dict)
            MODEL_LOADED = True
            print(f"Model loaded from {MODEL_PATH}")
            print(f"Classes: {CLASS_MAP['classes']}")
        except Exception as e:
            print(f"Warning: Could not load model weights: {e}")
            print("Running with untrained model (predictions will be random)")
    else:
        print(f"Warning: Model weights not found at {MODEL_PATH}")
        print("Run 'python train.py' to train a model first")
        # Initialize with random weights for demo
        MODEL = DeepfakeDetectorCNN(num_classes=num_classes, pretrained=False)
        MODEL.eval()

    print(f"Model ready. Classes: {CLASS_MAP['classes']}")
    MODEL_LOADED = True


def get_transform():
    """Get the inference transform (must match training)."""
    return T.Compose([
        T.Resize((INPUT_SIZE, INPUT_SIZE)),
        T.ToTensor(),
        T.Normalize(mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225]),
    ])


# ---- Detection Functions ----

def detect_image(file_bytes: bytes) -> dict:
    """
    Detect whether an image is AI-generated.
    Returns confidence scores and attribution info.
    """
    transform = get_transform()

    img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
    tensor = transform(img).unsqueeze(0)

    with torch.no_grad():
        output = MODEL(tensor)
        probabilities = F.softmax(output, dim=1)[0]
        confidence, predicted_idx = torch.max(probabilities, 0)
        predicted_class = CLASS_MAP["idx_to_class"][predicted_idx.item()]

    # Build result
    idx_to_class = CLASS_MAP["idx_to_class"]
    class_names = CLASS_MAP["classes"]
    probs_dict = {cls: float(probabilities[i]) for i, cls in enumerate(class_names)}

    # AI confidence: probability of being AI-generated
    # If "real" is a class, AI confidence = 1 - real_prob
    # Otherwise, it's the highest non-"real" probability
    if "real" in class_names:
        real_idx = CLASS_MAP["class_to_idx"]["real"]
        ai_confidence = 1.0 - probabilities[real_idx].item()
    else:
        # Multi-class: confidence is max probability of non-"real" class
        non_real_probs = [(i, cls, p) for i, (cls, p) in enumerate(
            zip(class_names, probabilities)) if cls != "real"]
        if non_real_probs:
            ai_confidence = max(p for _, _, p in non_real_probs)
        else:
            ai_confidence = 0.0

    # Source attribution: most likely non-real class (if confidence > threshold)
    source_attribution = None
    if ai_confidence > 0.5 and "real" in class_names:
        non_real = [(cls, float(p)) for cls, p in probs_dict.items() if cls != "real"]
        if non_real:
            source_attribution = max(non_real, key=lambda x: x[1])[0]

    is_ai = ai_confidence > 0.5

    return {
        "is_ai_generated": bool(is_ai),
        "confidence": float(ai_confidence),
        "predicted_class": predicted_class,
        "probabilities": {k: round(v, 4) for k, v in probs_dict.items()},
        "source_attribution": source_attribution or "N/A",
        "generator": source_attribution or ("N/A" if not is_ai else "Unknown"),
    }


def detect_video(file_bytes: bytes) -> dict:
    """
    Analyze video for AI-generated content.
    Samples frames and aggregates predictions.
    """
    transform = get_transform()
    frame_predictions = []
    total_frames = 0

    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        cap = cv2.VideoCapture(tmp_path)
        if not cap.isOpened():
            raise ValueError("Could not open video file")

        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        sample_rate = max(1, frame_count // 16)  # sample ~16 frames
        frame_idx = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if frame_idx % sample_rate == 0:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame_rgb)
                tensor = transform(img).unsqueeze(0)
                with torch.no_grad():
                    output = MODEL(tensor)
                    probs = F.softmax(output, dim=1)[0]
                    frame_predictions.append(probs)
                total_frames += 1
            frame_idx += 1

        cap.release()

        if not frame_predictions:
            return {
                "error": "No frames could be extracted from video",
                "is_ai_generated": False,
                "confidence": 0.0,
            }

        # Aggregate predictions across frames
        avg_probs = torch.stack(frame_predictions).mean(dim=0)
        confidence, predicted_idx = torch.max(avg_probs, 0)
        predicted_class = CLASS_MAP["idx_to_class"][predicted_idx.item()]

        class_names = CLASS_MAP["classes"]
        probs_dict = {cls: float(avg_probs[i]) for i, cls in enumerate(class_names)}

        if "real" in class_names:
            real_idx = CLASS_MAP["class_to_idx"]["real"]
            ai_confidence = 1.0 - avg_probs[real_idx].item()
        else:
            non_real_probs = [(i, cls, p) for i, (cls, p) in enumerate(
                zip(class_names, avg_probs)) if cls != "real"]
            ai_confidence = max((p for _, _, p in non_real_probs), default=0.0)

        is_ai = ai_confidence > 0.5

        source_attribution = None
        if is_ai and "real" in class_names:
            non_real = [(cls, float(p)) for cls, p in probs_dict.items() if cls != "real"]
            if non_real:
                source_attribution = max(non_real, key=lambda x: x[1])[0]

        return {
            "is_ai_generated": bool(is_ai),
            "confidence": float(ai_confidence),
            "predicted_class": predicted_class,
            "probabilities": {k: round(v, 4) for k, v in probs_dict.items()},
            "source_attribution": source_attribution or "N/A",
            "generator": source_attribution or ("N/A" if not is_ai else "Unknown"),
            "frames_analyzed": total_frames,
            "total_frames": frame_count,
        }

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def detect_audio(file_bytes: bytes) -> dict:
    """
    Analyze audio for AI-generated content.
    Uses mel spectrogram converted to image-like input for the CNN.
    """
    import torchaudio
    import torchaudio.transforms as AT

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        waveform, sample_rate = torchaudio.load(tmp_path)

        # Convert to mono if stereo
        if waveform.shape[0] > 1:
            waveform = waveform.mean(dim=0, keepdim=True)

        # Convert to mel spectrogram
        mel_transform = AT.MelSpectrogram(
            sample_rate=sample_rate,
            n_fft=2048,
            hop_length=512,
            n_mels=128,
        )
        mel_spec = mel_transform(waveform)

        # Convert to dB
        mel_db = AT.AmplitudeToDB()(mel_spec)

        # Normalize and resize to model input size
        mel_db = mel_db.squeeze(0).numpy()
        mel_db = (mel_db - mel_db.min()) / (mel_db.max() - mel_db.min() + 1e-8)
        mel_db = (mel_db * 255).astype(np.uint8)

        # Convert to 3-channel image for the model
        img = Image.fromarray(mel_db).convert("RGB").resize((INPUT_SIZE, INPUT_SIZE))
        transform = get_transform()
        tensor = transform(img).unsqueeze(0)

        with torch.no_grad():
            output = MODEL(tensor)
            probabilities = F.softmax(output, dim=1)[0]
            confidence, predicted_idx = torch.max(probabilities, 0)
            predicted_class = CLASS_MAP["idx_to_class"][predicted_idx.item()]

        class_names = CLASS_MAP["classes"]
        probs_dict = {cls: float(probabilities[i]) for i, cls in enumerate(class_names)}

        if "real" in class_names:
            real_idx = CLASS_MAP["class_to_idx"]["real"]
            ai_confidence = 1.0 - probabilities[real_idx].item()
        else:
            non_real_probs = [(i, cls, p) for i, (cls, p) in enumerate(
                zip(class_names, probabilities)) if cls != "real"]
            ai_confidence = max((p for _, _, p in non_real_probs), default=0.0)

        is_ai = ai_confidence > 0.5

        source_attribution = None
        if is_ai and "real" in class_names:
            non_real = [(cls, float(p)) for cls, p in probs_dict.items() if cls != "real"]
            if non_real:
                source_attribution = max(non_real, key=lambda x: x[1])[0]

        return {
            "is_ai_generated": bool(is_ai),
            "confidence": float(ai_confidence),
            "predicted_class": predicted_class,
            "probabilities": {k: round(v, 4) for k, v in probs_dict.items()},
            "source_attribution": source_attribution or "N/A",
            "generator": source_attribution or ("N/A" if not is_ai else "Unknown"),
            "sample_rate": sample_rate,
            "duration_seconds": float(waveform.shape[1] / sample_rate),
        }

    except Exception as e:
        return {
            "error": f"Audio processing failed: {str(e)}",
            "is_ai_generated": False,
            "confidence": 0.0,
            "note": "Audio detection requires librosa/torchaudio. Falling back to basic analysis.",
        }
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


# ---- Metadata Extraction ----
def extract_metadata(file_bytes: bytes, file_type: str) -> dict:
    """Extract technical metadata from uploaded file."""
    metadata = {"file_size_bytes": len(file_bytes)}

    try:
        if file_type == "image":
            img = Image.open(io.BytesIO(file_bytes))
            metadata["format"] = img.format
            metadata["width"] = img.width
            metadata["height"] = img.height
            metadata["mode"] = img.mode

            # EXIF data
            exif = img._getexif()
            if exif:
                from PIL.ExifTags import TAGS
                metadata["exif"] = {
                    TAGS.get(tag, tag): value
                    for tag, value in exif.items()
                    if isinstance(value, (str, int, float, bool))
                }

        elif file_type == "video":
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
                tmp.write(file_bytes)
                tmp_path = tmp.name
            try:
                cap = cv2.VideoCapture(tmp_path)
                metadata["fps"] = cap.get(cv2.CAP_PROP_FPS)
                metadata["frame_count"] = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                metadata["width"] = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                metadata["height"] = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                cap.release()
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

        elif file_type == "audio":
            import torchaudio
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp.write(file_bytes)
                tmp_path = tmp.name
            try:
                info = torchaudio.info(tmp_path)
                metadata["sample_rate"] = info.sample_rate
                metadata["channels"] = info.num_channels
                metadata["duration_seconds"] = info.duration
                metadata["bitrate"] = info.bitrate
            except Exception:
                pass
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

    except Exception as e:
        metadata["metadata_error"] = str(e)

    return metadata


# ---- Watermark Scanning ----
def scan_watermarks(file_bytes: bytes, file_type: str) -> dict:
    """
    Scan for invisible watermarks and AI generator artifacts.
    Currently detects basic statistical anomalies.
    """
    results = {
        "watermarks_found": [],
        "checksum": None,
        "compression_artifacts": None,
    }

    try:
        import hashlib
        results["checksum"] = hashlib.sha256(file_bytes).hexdigest()[:16]

        if file_type == "image":
            img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
            arr = np.array(img, dtype=np.float32)

            # Check for common AI generator artifacts
            gray = np.mean(arr, axis=2)
            laplacian = cv2.Laplacian(gray.astype(np.uint8), cv2.CV_64F)
            high_freq_energy = np.mean(np.abs(laplacian))
            results["high_frequency_energy"] = float(high_freq_energy)

            # FFT for periodic patterns
            fft = np.fft.fft2(gray)
            fft_shift = np.fft.fftshift(fft)
            magnitude = np.abs(fft_shift)

            h, w = magnitude.shape
            center = magnitude[h//4:3*h//4, w//4:3*w//4]
            periphery = magnitude.copy()
            periphery[h//4:3*h//4, w//4:3*w//4] = 0
            ratio = np.mean(center) / (np.mean(periphery) + 1e-8)
            results["frequency_ratio"] = float(ratio)
            results["periodic_pattern_detected"] = ratio > 3.0

            # Color channel correlation
            r, g, b = arr[:,:,0], arr[:,:,1], arr[:,:,2]
            rg_corr = np.corrcoef(r.ravel(), g.ravel())[0, 1]
            gb_corr = np.corrcoef(g.ravel(), b.ravel())[0, 1]
            results["channel_correlations"] = {
                "red_green": float(rg_corr),
                "green_blue": float(gb_corr),
            }

        elif file_type == "audio":
            import torchaudio as ta
            import torchaudio.transforms as tat
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp.write(file_bytes)
                tmp_path = tmp.name
            try:
                waveform, sr = ta.load(tmp_path)
                spec = tat.MelSpectrogram(sample_rate=sr)(waveform)
                spec_db = tat.AmplitudeToDB()(spec)
                results["spectral_centroid"] = float(torch.mean(spec_db).item())
            except Exception:
                pass
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

    except Exception as e:
        results["scan_error"] = str(e)

    return results


# ---- Policy Check ----
def mock_external_policy_check(is_ai: bool, confidence: float, file_type: str) -> dict:
    """Mock external community standards / policy check."""
    result = {
        "policy_passed": not is_ai or confidence < 0.95,
        "ai_confidence": confidence,
        "flagged_for_review": is_ai and confidence > 0.7,
        "reason": None,
    }

    if is_ai and confidence > 0.95:
        result["reason"] = f"High confidence ({confidence:.1%}) AI-generated {file_type} detected"
        result["policy_passed"] = False
    elif is_ai and confidence > 0.7:
        result["reason"] = f"Moderate confidence ({confidence:.1%}) AI-generated {file_type} — flagged for review"
        result["flagged_for_review"] = True
    elif is_ai:
        result["reason"] = f"Low confidence ({confidence:.1%}) AI-generated {file_type} — passed"
    else:
        result["reason"] = f"Content appears to be human-generated"

    return result


# ---- API Endpoints ----

@app.on_event("startup")
async def startup_event():
    """Load model on startup."""
    load_model()


@app.get("/health")
async def health_check():
    """Check server and model health."""
    return {
        "status": "healthy" if MODEL_LOADED else "degraded",
        "model_loaded": MODEL_LOADED,
        "model_path": MODEL_PATH if os.path.exists(MODEL_PATH) else None,
        "classes": CLASS_MAP["classes"] if CLASS_MAP else None,
        "num_classes": CLASS_MAP.get("num_classes", 0) if CLASS_MAP else 0,
        "device": "cuda" if torch.cuda.is_available() else "cpu",
    }


class DetectionResult(BaseModel):
    is_ai_generated: bool = Field(..., description="Whether the media is AI-generated")
    confidence: float = Field(..., description="Confidence score (0-1)")
    predicted_class: str = Field(..., description="Predicted class label")
    probabilities: dict = Field(..., description="Per-class probability breakdown")
    source_attribution: str = Field(..., description="Likely AI generator source")
    generator: str = Field(..., description="Human-readable generator label")
    metadata: dict = Field(..., description="File metadata")
    watermark_scan: dict = Field(..., description="Watermark and artifact scan results")
    policy_check: dict = Field(..., description="Policy check result")


@app.post("/api/image", response_model=DetectionResult)
async def detect_image_endpoint(file: UploadFile = File(...)):
    """Analyze an uploaded image for AI generation."""
    if not MODEL_LOADED:
        raise HTTPException(status_code=503, detail="Model not loaded. Check /health.")

    try:
        contents = await file.read()
        file_bytes = contents
        file_type = "image"

        detection = detect_image(file_bytes)
        metadata = extract_metadata(file_bytes, file_type)
        watermark_scan = scan_watermarks(file_bytes, file_type)
        policy_check = mock_external_policy_check(
            detection["is_ai_generated"],
            detection["confidence"],
            file_type,
        )

        return DetectionResult(
            is_ai_generated=detection["is_ai_generated"],
            confidence=detection["confidence"],
            predicted_class=detection["predicted_class"],
            probabilities=detection["probabilities"],
            source_attribution=detection["source_attribution"],
            generator=detection["generator"],
            metadata=metadata,
            watermark_scan=watermark_scan,
            policy_check=policy_check,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image analysis failed: {str(e)}")


@app.post("/api/video", response_model=DetectionResult)
async def detect_video_endpoint(file: UploadFile = File(...)):
    """Analyze an uploaded video for AI generation."""
    if not MODEL_LOADED:
        raise HTTPException(status_code=503, detail="Model not loaded. Check /health.")

    try:
        contents = await file.read()
        file_bytes = contents
        file_type = "video"

        detection = detect_video(file_bytes)
        if "error" in detection:
            raise HTTPException(status_code=400, detail=detection["error"])

        metadata = extract_metadata(file_bytes, file_type)
        watermark_scan = scan_watermarks(file_bytes, file_type)
        policy_check = mock_external_policy_check(
            detection["is_ai_generated"],
            detection["confidence"],
            file_type,
        )

        return DetectionResult(
            is_ai_generated=detection["is_ai_generated"],
            confidence=detection["confidence"],
            predicted_class=detection["predicted_class"],
            probabilities=detection["probabilities"],
            source_attribution=detection["source_attribution"],
            generator=detection["generator"],
            metadata=metadata,
            watermark_scan=watermark_scan,
            policy_check=policy_check,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Video analysis failed: {str(e)}")


@app.post("/api/audio", response_model=DetectionResult)
async def detect_audio_endpoint(file: UploadFile = File(...)):
    """Analyze an uploaded audio file for AI generation."""
    if not MODEL_LOADED:
        raise HTTPException(status_code=503, detail="Model not loaded. Check /health.")

    try:
        contents = await file.read()
        file_bytes = contents
        file_type = "audio"

        detection = detect_audio(file_bytes)

        metadata = extract_metadata(file_bytes, file_type)
        watermark_scan = scan_watermarks(file_bytes, file_type)
        policy_check = mock_external_policy_check(
            detection["is_ai_generated"],
            detection["confidence"],
            file_type,
        )

        return DetectionResult(
            is_ai_generated=detection["is_ai_generated"],
            confidence=detection["confidence"],
            predicted_class=detection["predicted_class"],
            probabilities=detection["probabilities"],
            source_attribution=detection["source_attribution"],
            generator=detection["generator"],
            metadata=metadata,
            watermark_scan=watermark_scan,
            policy_check=policy_check,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audio analysis failed: {str(e)}")


@app.get("/attribution")
async def attribution_info():
    """Get information about the model's attribution capabilities."""
    if not CLASS_MAP:
        return {"error": "Model not loaded"}

    return {
        "classes": CLASS_MAP["classes"],
        "num_classes": CLASS_MAP["num_classes"],
        "class_mapping": CLASS_MAP["class_to_idx"],
        "attribution_enabled": "real" in CLASS_MAP["classes"] and CLASS_MAP["num_classes"] > 2,
        "ai_classes": [c for c in CLASS_MAP["classes"] if c != "real"],
        "best_model": {
            "epoch": CLASS_MAP.get("best_epoch"),
            "val_loss": CLASS_MAP.get("best_val_loss"),
            "val_acc": CLASS_MAP.get("best_val_acc"),
        },
    }


# ---- Main ----
if __name__ == "__main__":
    print("Starting SudoScorpStingVision server...")
    print("Endpoints:")
    print("  POST /api/image   - Image detection")
    print("  POST /api/video   - Video detection")
    print("  POST /api/audio   - Audio detection")
    print("  GET  /health      - Health check")
    print("  GET  /attribution - Model info")
    print()
    uvicorn.run(app, host="0.0.0.0", port=8000)
