"""
Generates a tiny labelled synthetic dataset so the training pipeline can be
exercised end-to-end even when no real media collection is available.

Layout (ImageFolder convention):
    dataset/
        train/
            real/   <-- "photographic" noise textures
            ai/     <-- flat colour fields + sharp geometric artefacts
        val/
            real/
            ai/

These images are NOT real deepfakes.  They exist purely so the training loop
can be validated on a developer machine without a real dataset.
"""

import os
import random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

RNG = random.Random(42)


def make_real(idx: int, out_dir: str) -> None:
    """Photographic-style noise + subtle gradient → looks 'natural'."""
    arr = np.random.randint(0, 256, (224, 224, 3), dtype=np.uint8)
    pim = Image.fromarray(arr).filter(ImageFilter.GaussianBlur(radius=2))
    base = Image.new("RGB", (224, 224), (0, 0, 0))
    draw = ImageDraw.Draw(base)
    for y in range(0, 224, 10):
        shade = int(128 + 64 * np.sin(y / 224 * 6.283))
        draw.line([(0, y), (224, y)], fill=(shade, shade, shade), width=2)
    pim = Image.blend(pim, base, 0.3)
    pim.save(os.path.join(out_dir, f"{idx:04d}.png"))


def make_ai(idx: int, out_dir: str) -> None:
    """Flat colour + sharp geometric primitives → 'computer-generated' look."""
    img = Image.new("RGB", (224, 224), RNG.choice([(30, 30, 180), (180, 30, 30), (30, 180, 30), (220, 220, 220)]))
    draw = ImageDraw.Draw(img)
    for _ in range(RNG.randint(3, 8)):
        kind = RNG.choice(["rect", "circle", "line"])
        c = (RNG.randint(0, 255), RNG.randint(0, 255), RNG.randint(0, 255))
        if kind == "rect":
            x0, y0 = RNG.randint(0, 100), RNG.randint(0, 100)
            x1, y1 = x0 + RNG.randint(20, 80), y0 + RNG.randint(20, 80)
            draw.rectangle([x0, y0, x1, y1], fill=c)
        elif kind == "circle":
            cx, cy = RNG.randint(0, 224), RNG.randint(0, 224)
            r = RNG.randint(10, 50)
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=c)
        else:
            x0, y0 = RNG.randint(0, 224), RNG.randint(0, 224)
            x1, y1 = RNG.randint(0, 224), RNG.randint(0, 224)
            draw.line([(x0, y0), (x1, y1)], fill=c, width=RNG.randint(2, 5))
    img.save(os.path.join(out_dir, f"{idx:04d}.png"))


def generate(base_dir="dataset", train_per_class=200, val_per_class=50):
    print("=" * 50)
    print("  SYNTHETIC DATASET GENERATOR")
    print("=" * 50)

    for split, n in (("train", train_per_class), ("val", val_per_class)):
        for cls in ("real", "ai"):
            path = os.path.join(base_dir, split, cls)
            os.makedirs(path, exist_ok=True)
            fn = make_real if cls == "real" else make_ai
            for i in range(n):
                fn(i, path)
            print(f"  {split}/{cls}/  ←  {n} images")

    print("\nDone. Train with:  python train.py")


if __name__ == "__main__":
    generate()
