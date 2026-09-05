"""
================================================================================
🔥 SUDOSCORPSTINGVISION — IMPROVED TRAINING PIPELINE
================================================================================
Trains a DeepfakeDetectorCNN (or a pretrained ResNet18 backbone) on a
real-vs-AI image dataset and saves trained weights + class mapping.

Dataset layout (ImageFolder convention):
    dataset/
        train/
            real/   <-- authentic images
            ai/     <-- AI-generated images
        val/
            real/
            ai/

If no dataset is found, the script auto-generates a small synthetic dataset
so the pipeline can be exercised end-to-end.
"""

import os
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import datasets, transforms, models
from torchvision.models import ResNet18_Weights
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import random

# ---------------------------------------------------------------------------
# Model definitions
# ---------------------------------------------------------------------------

class DeepfakeDetectorCNN(nn.Module):
    """Original 3-conv-layer CNN from the repo (kept for compatibility)."""

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
    Lightweight wrapper around a pretrained ResNet18.
    Early layers are frozen; only the final FC layer is retrained for
    binary real-vs-AI classification.  This gives the model a meaningful
    feature basis from day one instead of random guessing.
    """

    def __init__(self, freeze_backbone=True):
        super().__init__()
        weights = ResNet18_Weights.DEFAULT
        self.backbone = models.resnet18(weights=weights)

        if freeze_backbone:
            for param in self.backbone.parameters():
                param.requires_grad = False
            # unfreeze the last conv block so the model can still adapt
            for param in self.backbone.layer4.parameters():
                param.requires_grad = True

        # Replace the classifier head: 512 -> 2 (real / ai)
        self.backbone.fc = nn.Sequential(
            nn.Dropout(0.3),
            nn.Linear(512, 2),
        )

    def forward(self, x):
        return self.backbone(x)


# ---------------------------------------------------------------------------
# Synthetic dataset generator (so training works even with no real data)
# ---------------------------------------------------------------------------

def generate_synthetic_dataset(base_dir="dataset", samples_per_class=200):
    """
    Creates a tiny labelled dataset of procedurally-generated images.
    'real'  — photographic-style noise + gradients.
    'ai'    — flat colour fields with sharp geometric artefacts (mimicking
             the kind of tell-tale precision artefacts sometimes seen in
             early generative outputs).  These are NOT real deepfakes — they
             exist purely so the training loop can be validated end-to-end.
    """
    print("[SYNTH] Generating synthetic training dataset ...")
    transforms_gen = {
        "train": os.path.join(base_dir, "train"),
        "val": os.path.join(base_dir, "val"),
    }
    for split, path in transforms_gen.items():
        for cls in ("real", "ai"):
            os.makedirs(os.path.join(path, cls), exist_ok=True)

    rng = random.Random(42)
    for split, path in transforms_gen.items():
        n = samples_per_class if split == "train" else samples_per_class // 4
        for i in range(n):
            for cls in ("real", "ai"):
                img = Image.new("RGB", (224, 224), color=(0, 0, 0))
                draw = ImageDraw.Draw(img)
                if cls == "real":
                    # Noise-like photographic texture
                    arr = np.random.randint(0, 256, (224, 224, 3), dtype=np.uint8)
                    # smooth with a mild blur to look less computer-generated
                    pim = Image.fromarray(arr).filter(ImageFilter.GaussianBlur(radius=2))
                    # add a subtle gradient
                    for y in range(0, 224, 10):
                        shade = int(128 + 64 * np.sin(y / 224 * 6.28))
                        draw.line([(0, y), (224, y)], fill=(shade, shade, shade), width=2)
                    pim = Image.blend(pim, img, 0.3)
                    pim.save(os.path.join(path, cls, f"{i:04d}.png"))
                else:
                    # AI-like: flat colour + sharp geometric shapes
                    base_color = (rng.randint(0, 255), rng.randint(0, 255), rng.randint(0, 255))
                    draw.rectangle([0, 0, 224, 224], fill=base_color)
                    for _ in range(rng.randint(3, 8)):
                        shape_type = rng.choice(["rect", "circle", "line"])
                        if shape_type == "rect":
                            x0, y0 = rng.randint(0, 100), rng.randint(0, 100)
                            x1, y1 = x0 + rng.randint(20, 80), y0 + rng.randint(20, 80)
                            draw.rectangle([x0, y0, x1, y1], fill=(
                                rng.randint(0, 255), rng.randint(0, 255), rng.randint(0, 255)))
                        elif shape_type == "circle":
                            cx, cy = rng.randint(0, 224), rng.randint(0, 224)
                            r = rng.randint(10, 50)
                            draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(
                                rng.randint(0, 255), rng.randint(0, 255), rng.randint(0, 255)))
                        else:
                            x0, y0 = rng.randint(0, 224), rng.randint(0, 224)
                            x1, y1 = rng.randint(0, 224), rng.randint(0, 224)
                            draw.line([(x0, y0), (x1, y1)], fill=(
                                rng.randint(0, 255), rng.randint(0, 255), rng.randint(0, 255)), width=3)
                    img.save(os.path.join(path, cls, f"{i:04d}.png"))
    print(f"[SYNTH] Done — dataset/ tree written with {n} val + {samples_per_class} train images per class.")


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------

def train_model(
    data_dir="dataset",
    batch_size=32,
    epochs=10,
    learning_rate=1e-3,
    use_pretrained=True,
    synthetic_samples=200,
    patience=3,
    checkpoint_path="best_model.pth",
    class_map_path="class_map.json",
):
    print("=" * 60)
    print("  SUDOSCORPSTINGVISION  TRAINING PIPELINE")
    print("=" * 60)

    # --- auto-generate synthetic data if no dataset present ----------------
    if not os.path.isdir(os.path.join(data_dir, "train")):
        print(f"\n[INFO] No dataset found at '{data_dir}'.")
        print("[INFO] Generating synthetic dataset so the pipeline can be validated ...")
        generate_synthetic_dataset(data_dir, samples_per_class=synthetic_samples)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"\nDevice: {device}")

    # --- transforms ---------------------------------------------------------
    data_transforms = {
        "train": transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.RandomHorizontalFlip(),
            transforms.RandomRotation(10),
            transforms.ColorJitter(brightness=0.1, contrast=0.1, saturation=0.1),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ]),
        "val": transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ]),
    }

    image_datasets = {
        x: datasets.ImageFolder(os.path.join(data_dir, x), data_transforms[x])
        for x in ("train", "val")
    }
    dataloaders = {
        x: DataLoader(image_datasets[x], batch_size=batch_size, shuffle=(x == "train"),
                      num_workers=2, pin_memory=True if device.type == "cuda" else False)
        for x in ("train", "val")
    }

    class_names = image_datasets["train"].classes
    class_to_idx = image_datasets["train"].class_to_idx
    # ImageFolder sorts classes alphabetically.  Make sure we know which index
    # corresponds to the "ai" class so inference can read the right probability.
    ai_class_name = "ai"
    if ai_class_name not in class_to_idx:
        raise SystemExit(
            f"[FATAL] Expected a class named '{ai_class_name}' in the dataset, "
            f"but found {class_names}. Rename your ai/ folder accordingly."
        )
    ai_label = class_to_idx[ai_class_name]
    print(f"Classes: {class_names}  (mapping: {class_to_idx}, ai_label={ai_label})")
    print(f"Train samples: {len(image_datasets['train'])}  |  Val samples: {len(image_datasets['val'])}")

    # --- save class mapping (needed at inference time) --------------------
    import json
    with open(class_map_path, "w") as f:
        json.dump({"classes": class_names, "class_to_idx": class_to_idx, "ai_label": ai_label}, f, indent=2)
    print(f"Class map saved → {class_map_path}")

    # --- model --------------------------------------------------------------
    if use_pretrained:
        print("\n[INFO] Using pretrained ResNet18 backbone (fine-tuning last block + classifier).")
        model = ResNetDetector(freeze_backbone=True).to(device)
    else:
        print("\n[INFO] Using scratch DeepfakeDetectorCNN (random init).")
        model = DeepfakeDetectorCNN().to(device)

    criterion = nn.CrossEntropyLoss()
    # higher LR for the trained head, lower for the backbone if unfrozen
    if use_pretrained:
        head_params = list(model.backbone.fc.parameters())
        backbone_params = [p for p in model.backbone.layer4.parameters() if p.requires_grad]
        optimizer = optim.Adam([
            {"params": head_params, "lr": learning_rate},
            {"params": backbone_params, "lr": learning_rate * 0.1},
        ])
    else:
        optimizer = optim.Adam(model.parameters(), lr=learning_rate)

    best_val_acc = 0.0
    best_epoch = 0
    patience_counter = 0

    for epoch in range(epochs):
        print(f"\n--- Epoch {epoch + 1}/{epochs} ---")
        for phase in ("train", "val"):
            model.train() if phase == "train" else model.eval()
            running_loss = 0.0
            running_correct = 0

            for inputs, labels in dataloaders[phase]:
                inputs, labels = inputs.to(device), labels.to(device)
                optimizer.zero_grad()
                with torch.set_grad_enabled(phase == "train"):
                    outputs = model(inputs)
                    _, preds = torch.max(outputs, 1)
                    loss = criterion(outputs, labels)
                    if phase == "train":
                        loss.backward()
                        optimizer.step()

                running_loss += loss.item() * inputs.size(0)
                running_correct += torch.sum(preds == labels.data).item()

            epoch_loss = running_loss / len(image_datasets[phase])
            epoch_acc = running_correct / len(image_datasets[phase])
            print(f"  [{phase.upper()}] Loss: {epoch_loss:.4f}  Acc: {epoch_acc:.4f}")

            if phase == "val" and epoch_acc > best_val_acc:
                best_val_acc = epoch_acc
                best_epoch = epoch + 1
                patience_counter = 0
                torch.save(model.state_dict(), checkpoint_path)
                print(f"  ★ New best model saved → {checkpoint_path}  (val_acc={best_val_acc:.4f})")
            elif phase == "val":
                patience_counter += 1

        if patience_counter >= patience:
            print(f"\n[EARLY STOP] No val improvement for {patience} epochs. Stopping.")
            break

    print(f"\n{'=' * 60}")
    print(f"  Training complete. Best val accuracy: {best_val_acc:.4f} (epoch {best_epoch})")
    print(f"  Best weights: {checkpoint_path}")
    print(f"{'=' * 60}")

    # Also save a copy named model_weights.pth for backward compatibility
    # with the original main.py loader, plus an architecture marker so the
    # server can pick the right model class automatically.
    if os.path.exists(checkpoint_path):
        import json
        arch_name = "resnet" if use_pretrained else "cnn"
        with open("model_arch.json", "w") as f:
            json.dump({"architecture": arch_name, "checkpoint": checkpoint_path}, f, indent=2)
        torch.save(model.state_dict(), "model_weights.pth")
        print("  Compatible copy saved → model_weights.pth")
        print(f"  Architecture marker saved → model_arch.json  (arch={arch_name})")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Train the deepfake detector.")
    parser.add_argument("--data", default="dataset", help="Path to dataset directory.")
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--batch", type=int, default=32)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--no-pretrained", action="store_true", help="Train from scratch (no ResNet18).")
    parser.add_argument("--synthetic", type=int, default=200, help="Synthetic samples per class if no dataset.")
    parser.add_argument("--patience", type=int, default=3)
    args = parser.parse_args()

    train_model(
        data_dir=args.data,
        batch_size=args.batch,
        epochs=args.epochs,
        learning_rate=args.lr,
        use_pretrained=not args.no_pretrained,
        synthetic_samples=args.synthetic,
        patience=args.patience,
    )
