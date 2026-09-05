#!/usr/bin/env python3
"""
SudoScorpStingVision — Synthetic Dataset Generator
Creates a labeled dataset for training the deepfake detection model
with support for source attribution (real, AI image, AI audio).
"""

import os
import numpy as np
from PIL import Image, ImageFilter
import random

def create_real_image(path, size=(224, 224)):
    """Create a realistic-looking image with natural noise patterns."""
    # Natural-ish base with noise
    base = np.random.randn(*size, 3) * 40 + 128
    img = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8))
    img = img.filter(ImageFilter.GaussianBlur(radius=1.5))
    
    # Add film grain
    grain = np.random.randn(*size, 3) * 15
    img_arr = np.clip(np.array(img).astype(np.float32) + grain, 0, 255).astype(np.uint8)
    
    # Add some random blobs (like objects in a scene)
    for _ in range(random.randint(1, 5)):
        cx, cy = random.randint(0, size[0]-1), random.randint(0, size[1]-1)
        r = random.randint(10, 50)
        y, x = np.ogrid[:size[1], :size[0]]
        mask = (x - cx)**2 + (y - cy)**2 <= r**2
        color = np.random.randint(50, 200, 3)
        img_arr[mask] = np.clip(img_arr[mask] * 0.5 + color * 0.5, 0, 255).astype(np.uint8)
    
    Image.fromarray(img_arr).save(path)

def create_ai_image(path, size=(224, 224)):
    """Create an AI-generated looking image with synthetic patterns."""
    # Smooth, uniform base
    base = np.random.rand(*size, 3) * 255
    img = Image.fromarray(base.astype(np.uint8))
    
    # Add checkerboard artifacts (common in GAN upsampling)
    img_arr = np.array(img).astype(np.float32)
    block_size = random.choice([8, 16, 32])
    for x in range(0, size[0], block_size):
        for y in range(0, size[1], block_size):
            if ((x // block_size) + (y // block_size)) % 2 == 0:
                img_arr[y:y+block_size//2, x:x+block_size//2] += 30
    
    # Add high-frequency noise (diffusion artifacts)
    noise = np.random.randn(*size, 3) * 20
    img_arr = np.clip(img_arr + noise, 0, 255).astype(np.uint8)
    
    Image.fromarray(img_arr).save(path)

def create_ai_audio_spectrogram(path, size=(224, 224)):
    """Create an image that looks like an audio spectrogram (for ElevenLabs-style)."""
    # Create spectrogram-like pattern
    img_arr = np.zeros((*size, 3), dtype=np.uint8)
    
    # Frequency bands (horizontal stripes)
    for i in range(0, size[1], 20):
        intensity = random.randint(50, 200)
        img_arr[:, i:i+10, 0] = intensity
        img_arr[:, i:i+10, 1] = random.randint(50, 200)
        img_arr[:, i:i+10, 2] = random.randint(50, 200)
    
    # Add some harmonic lines
    for _ in range(random.randint(3, 10)):
        y = random.randint(0, size[1]-1)
        img_arr[:, y, :] = 255
    
    # Add noise typical of audio
    noise = np.random.randn(*size, 3) * 15
    img_arr = np.clip(img_arr.astype(np.float32) + noise, 0, 255).astype(np.uint8)
    
    Image.fromarray(img_arr).save(path)

def create_dataset(base_dir="dataset", train_per_class=200, val_per_class=50, seed=42):
    """Create the full dataset structure."""
    random.seed(seed)
    np.random.seed(seed)
    
    classes = ["real", "ai_image", "ai_audio"]
    generators = {
        "real": create_real_image,
        "ai_image": create_ai_image,
        "ai_audio": create_ai_audio_spectrogram,
    }
    
    print(f"Creating dataset in: {os.path.abspath(base_dir)}")
    print(f"Classes: {classes}")
    print(f"Train samples per class: {train_per_class}")
    print(f"Val samples per class: {val_per_class}")
    print()
    
    for split, n in [("train", train_per_class), ("val", val_per_class)]:
        for cls in classes:
            dir_path = os.path.join(base_dir, split, cls)
            os.makedirs(dir_path, exist_ok=True)
            
            generator = generators[cls]
            for i in range(n):
                path = os.path.join(dir_path, f"{i:04d}.png")
                generator(path)
            
            print(f"  Created {n} samples in {dir_path}")
    
    print()
    print("Dataset creation complete!")
    print(f"Total training samples: {train_per_class * len(classes)}")
    print(f"Total validation samples: {val_per_class * len(classes)}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate synthetic dataset for SudoScorpStingVision")
    parser.add_argument("--output", "-o", default="dataset", help="Output directory")
    parser.add_argument("--train", "-t", type=int, default=200, help="Train samples per class")
    parser.add_argument("--val", "-v", type=int, default=50, help="Val samples per class")
    parser.add_argument("--seed", "-s", type=int, default=42, help="Random seed")
    args = parser.parse_args()
    
    create_dataset(
        base_dir=args.output,
        train_per_class=args.train,
        val_per_class=args.val,
        seed=args.seed
    )
