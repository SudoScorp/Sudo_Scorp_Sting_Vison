"""
================================================================================
🔥 SUDOSCORPSTINGVISION — SYNTHETIC DATASET GENERATOR
================================================================================
Generates realistic training images where the "real" and "ai" classes
have statistically detectable differences in the frequency domain and
noise characteristics -- the same kinds of signals that real deepfake
detectors exploit.

"real" images:
  - Natural colour / luminance distributions
  - 1/f-style frequency falloff (natural images are not white noise)
  - Sensor-style noise: Gaussian + Poisson mixture
  - Natural textures via filtered noise

"ai" images:
  - Smooth base (mimics diffusion / GAN upsampled output)
  - Periodic upsampling artefacts (peaks in the frequency domain)
  - Abnormal high-frequency energy in a band (diffusion-like sharpening)
  - Synthetic noise with different statistics than sensor noise

These differences are NOT a perfect model of any one generator, but they
capture the *class* of signals that frequency-domain deepfake detectors
actually use, so a model trained on them transfers better to real media
than pure-random synthetic data.

Usage:
    python generate_synthetic_data.py [--train N] [--val M] [--outdir D]
"""

import os
import sys
import random
import argparse
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops
from scipy import ndimage

RNG = random.Random(42)
NOISE_RNG = np.random.default_rng(42)


# ---------------------------------------------------------------------------
#  Frequency-domain helpers
# ---------------------------------------------------------------------------

def _fft_spectrum(img_array):
    """Return log-magnitude spectrum of a grayscale image (H, W)."""
    f = np.fft.fft2(img_array.astype(np.float32))
    fshift = np.fft.fftshift(f)
    magnitude = np.abs(fshift)
    # avoid log(0)
    magnitude = np.clip(magnitude, 1e-6, None)
    return np.log(magnitude)


def _radial_profile(spectrum, n_bands=8):
    """Average magnitude in concentric square rings -- cheap radial profile."""
    H, W = spectrum.shape
    cy, cx = H // 2, W // 2
    max_r = min(cy, cx)
    profile = np.zeros(n_bands, dtype=np.float32)
    counts = np.zeros(n_bands, dtype=np.float32)
    Y, X = np.ogrid[:H, :W]
    r = np.maximum(np.abs(X - cx), np.abs(Y - cy))
    for b in range(n_bands):
        lo = int(b * max_r / n_bands)
        hi = int((b + 1) * max_r / n_bands)
        mask = (r >= lo) & (r < hi)
        profile[b] = spectrum[mask].mean()
        counts[b] = mask.sum()
    return profile / (counts + 1e-6)


# ---------------------------------------------------------------------------
#  Real-image generators
# ---------------------------------------------------------------------------

def _natural_noise(H, W, strength=1.0):
    """Filtered noise that mimics natural image texture (low-pass biased)."""
    raw = NOISE_RNG.standard_normal((H, W)).astype(np.float32)
    # mild gaussian blur to knock out the highest frequencies a bit
    raw = ndimage.gaussian_filter(raw, sigma=0.6)
    # re-normalise
    raw = (raw - raw.mean()) / (raw.std() + 1e-6)
    return raw * strength


def _plausible_texture(H, W):
    """Multi-octave value noise that looks more 'natural' than white noise."""
    base = np.zeros((H, W), dtype=np.float32)
    for octave, (scale, amp) in enumerate([(2.0, 0.5), (4.0, 0.3), (8.0, 0.2),
                                            (16.0, 0.1), (32.0, 0.05)]):
        sh, sw = max(2, int(H // scale)), max(2, int(W // scale))
        small = NOISE_RNG.standard_normal((sh, sw))
        up = np.array(Image.fromarray(
            ((small - small.min()) / (np.ptp(small) + 1e-6) * 255).astype(np.uint8)
        ).resize((W, H), Image.BICUBIC), dtype=np.float32) / 255.0
        base += up * amp
    base = (base - base.mean()) / (base.std() + 1e-6)
    return base


def generate_real_image(out_path, size=(224, 224)):
    """Generate an image that looks like a natural photograph."""
    H, W = size
    # --- luminance channel ---
    texture = _plausible_texture(H, W)
    # bias toward a soft gradient (natural scenes aren't flat)
    Y, X = np.mgrid[0:H, 0:W].astype(np.float32)
    gradient = 0.3 * np.sin(X / W * 6.28 * 2) * np.cos(Y / H * 6.28 * 1.5)
    luma = np.clip(texture * 0.7 + gradient * 0.3 + 0.5, 0.0, 1.0)

    # --- sensor noise (gaussian + poisson-ish) ---
    gaussian_noise = NOISE_RNG.standard_normal((H, W)).astype(np.float32) * 0.02
    # poisson-like: apply poisson then rescale
    poisson_base = np.clip(luma * 255, 0, 255).astype(np.float32)
    poisson_noise = (
        NOISE_RNG.poisson(poisson_base) - poisson_base
    ) / 255.0 * 0.03
    luma = np.clip(luma + gaussian_noise + poisson_noise, 0.0, 1.0)

    # --- colour : make a plausible RGB from luma ---
    # natural images have correlated colour channels with some variation
    base_colour = np.array([0.4, 0.5, 0.6])  # warm-neutral tint
    rgb = np.stack([
        np.clip(luma * (base_colour[0] + 0.1 * _natural_noise(H, W, 0.05)), 0, 1),
        np.clip(luma * (base_colour[1] + 0.1 * _natural_noise(H, W, 0.05)), 0, 1),
        np.clip(luma * (base_colour[2] + 0.1 * _natural_noise(H, W, 0.05)), 0, 1),
    ], axis=-1)

    # mild chromatic noise (sensor-style)
    for c in range(3):
        rgb[:, :, c] += _natural_noise(H, W, 0.015)

    rgb = np.clip(rgb, 0.0, 1.0)
    img = Image.fromarray((rgb * 255).astype(np.uint8))
    img.save(out_path, format="PNG")


# ---------------------------------------------------------------------------
#  AI-image generators (with detectable artefacts)
# ---------------------------------------------------------------------------

def _upsampling_artefact(H, W, period=8):
    """
    Create a subtle periodic grid artefact that mimics the kind of ringing /
    periodicity introduced by upsampling in GAN / diffusion pipelines.
    Returns an additive pattern (H, W) in [-0.5, 0.5].
    """
    Y, X = np.mgrid[0:H, 0:W].astype(np.float32)
    # periodic ringing at a few scales
    pattern = np.zeros((H, W), dtype=np.float32)
    for p in [period, period * 2, period * 3]:
        pattern += 0.04 * np.sin(2 * np.pi * X / p) * np.sin(2 * np.pi * Y / p)
        pattern += 0.02 * np.cos(2 * np.pi * X / (p * 1.5))
    return pattern


def _diffusion_sharpening_band(H, W):
    """
    Mimic the slightly over-sharp / over-confident high-frequency content
    sometimes seen in diffusion outputs by injecting energy in a narrow
    mid-high frequency band.
    """
    # start from nothing, add filtered noise biased to a band
    raw = NOISE_RNG.standard_normal((H, W)).astype(np.float32)
    # fft -> boost mid-high radii -> ifft
    f = np.fft.fft2(raw)
    fshift = np.fft.fftshift(f)
    Hh, Hw = fshift.shape
    cy, cx = Hh // 2, Hw // 2
    Y, X = np.ogrid[:Hh, :Hw]
    r = np.sqrt((X - cx) ** 2 + (Y - cy) ** 2)
    mask = (r > Hw * 0.12) & (r < Hw * 0.28)
    fshift[mask] *= 2.5
    f_ishift = np.fft.ifftshift(fshift)
    boosted = np.fft.ifft2(f_ishift).real
    boosted = (boosted - boosted.mean()) / (boosted.std() + 1e-6)
    return boosted * 0.04


def generate_ai_image(out_path, size=(224, 224), style="default"):
    """
    Generate an image with artefacts associated with AI-generated content.

    Styles (for attribution training signal):
      - 'default' : generic diffusion-like artefacts
      - 'midjourney' : slightly grainy, high detail, mild periodicity
      - 'stablediffusion' : smooth base + sharpening band + periodicity
      - 'sora' : for video frames -- motion-consistent artefacts (here just
                a variant with less high-freq energy)
    """
    H, W = size
    style = style or "default"

    if style == "midjourney":
        # grainy, detailed, mild periodicity
        base = _plausible_texture(H, W) * 0.6 + 0.5
        base += _upsampling_artefact(H, W, period=12) * 0.5
        grain = _natural_noise(H, W, 0.06)
        luma = np.clip(base + grain, 0, 1)
    elif style == "stablediffusion":
        # smooth base, sharpening band, periodicity
        base = np.ones((H, W), dtype=np.float32) * 0.5
        gradient = 0.2 * np.sin(np.mgrid[0:H, 0:W][1] / W * 6.28)
        base += gradient
        base += _upsampling_artefact(H, W, period=8) * 0.6
        sharpening = _diffusion_sharpening_band(H, W)
        luma = np.clip(base + sharpening, 0, 1)
    elif style == "sora":
        # video-style: smoother, less high-freq, mild periodicity
        base = 0.5 + 0.15 * np.sin(np.mgrid[0:H, 0:W][1] / W * 6.28 * 1.5)
        base += _upsampling_artefact(H, W, period=16) * 0.3
        luma = np.clip(base + _natural_noise(H, W, 0.02), 0, 1)
    else:  # default
        base = 0.5 + 0.1 * np.sin(np.mgrid[0:H, 0:W][1] / W * 6.28 * 2)
        base += _upsampling_artefact(H, W, period=10) * 0.5
        sharpening = _diffusion_sharpening_band(H, W)
        luma = np.clip(base + sharpening + _natural_noise(H, W, 0.03), 0, 1)

    # colour -- AI images sometimes have slightly odd colour correlations
    if style == "midjourney":
        tint = np.array([0.35, 0.45, 0.55])  # slightly cool
    elif style == "stablediffusion":
        tint = np.array([0.5, 0.45, 0.4])  # slightly warm
    elif style == "sora":
        tint = np.array([0.45, 0.45, 0.5])  # neutral-cool
    else:
        tint = np.array([0.45, 0.45, 0.45])

    rgb = np.stack([
        np.clip(luma * (tint[c] + 0.05 * _natural_noise(H, W, 0.03)), 0, 1)
        for c in range(3)
    ], axis=-1)

    # Add very subtle synthetic noise (different stats from sensor noise)
    noise_2d = _natural_noise(H, W, 0.01)
    rgb = np.clip(rgb + noise_2d[:, :, np.newaxis] + 0.005 * (
        NOISE_RNG.standard_normal((H, W, 3)).astype(np.float32)
    ), 0.0, 1.0)
    img = Image.fromarray((rgb * 255).astype(np.uint8))
    img.save(out_path, format="PNG")


# ---------------------------------------------------------------------------
#  Dataset generation
# ---------------------------------------------------------------------------

STYLES = ["default", "midjourney", "stablediffusion", "sora"]


def generate_dataset(outdir="dataset", train_per_class=400, val_per_class=100,
                     img_size=(224, 224)):
    print("=" * 60)
    print("  SUDOSCORPSTINGVISION — SYNTHETIC DATASET GENERATOR")
    print("=" * 60)
    print(f"\nOutput directory : {os.path.abspath(outdir)}")
    print(f"Image size       : {img_size}")
    print(f"Train/class      : {train_per_class}")
    print(f"Val/class        : {val_per_class}")
    print(f"AI styles        : {STYLES}")
    print()

    for split, n in (("train", train_per_class), ("val", val_per_class)):
        for cls in ("real", "ai"):
            path = os.path.join(outdir, split, cls)
            os.makedirs(path, exist_ok=True)

        # --- real images ---
        real_dir = os.path.join(outdir, split, "real")
        for i in range(n):
            generate_real_image(os.path.join(real_dir, f"{i:05d}.png"), img_size)
        print(f"  {split}/real/  ←  {n} images")

        # --- ai images (spread across styles for attribution signal) ---
        ai_dir = os.path.join(outdir, split, "ai")
        per_style = max(1, n // len(STYLES))
        idx = 0
        for style in STYLES:
            for j in range(per_style):
                if idx >= n:
                    break
                generate_ai_image(os.path.join(ai_dir, f"{idx:05d}.png"), img_size, style=style)
                idx += 1
        print(f"  {split}/ai/    ←  {n} images  (styles: {STYLES})")

    print("\nDataset generation complete.")
    print("Train with:  python train.py")


def main():
    p = argparse.ArgumentParser(description="Generate synthetic training dataset.")
    p.add_argument("--train", type=int, default=400, help="Images per class in train split.")
    p.add_argument("--val", type=int, default=100, help="Images per class in val split.")
    p.add_argument("--outdir", default="dataset", help="Root dataset directory.")
    p.add_argument("--size", type=int, nargs=2, default=[224, 224], metavar=("W", "H"),
                   help="Image size.")
    args = p.parse_args()
    generate_dataset(args.outdir, args.train, args.val, tuple(args.size))


if __name__ == "__main__":
    main()
