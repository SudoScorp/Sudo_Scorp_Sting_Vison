#!/usr/bin/env python3
"""
SudoScorpStingVision — Training Pipeline
Fine-tunes a ResNet18-based model to detect AI-generated media and attribute sources.
"""

import os
import argparse
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import transforms
from torchvision.datasets import ImageFolder
import numpy as np

from model import DeepfakeDetectorCNN as DeepfakeDetector


def get_transforms(img_size=224, augment=True):
    """Image transforms for training/validation."""
    if augment:
        train_tf = transforms.Compose([
            transforms.Resize((img_size + 32, img_size + 32)),
            transforms.RandomResizedCrop(img_size, scale=(0.8, 1.0)),
            transforms.RandomHorizontalFlip(0.5),
            transforms.RandomRotation(20),
            transforms.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.3),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                std=[0.229, 0.224, 0.225]),
        ])
    else:
        train_tf = transforms.Compose([
            transforms.Resize((img_size, img_size)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                std=[0.229, 0.224, 0.225]),
        ])
    
    val_tf = transforms.Compose([
        transforms.Resize((img_size, img_size)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                            std=[0.229, 0.224, 0.225]),
    ])
    
    return train_tf, val_tf


def train(args):
    """Main training loop."""
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")
    
    data_dir = args.data
    img_size = args.img_size
    
    if not os.path.isdir(data_dir):
        print(f"ERROR: Dataset directory not found: {data_dir}")
        print("Generate one first: python generate_dataset.py")
        return False
    
    # Discover classes
    class_dirs = sorted([d for d in os.listdir(data_dir) 
                         if os.path.isdir(os.path.join(data_dir, d))])
    
    if len(class_dirs) < 2:
        print(f"ERROR: Need at least 2 class directories, found: {class_dirs}")
        return False
    
    print(f"Classes ({len(class_dirs)}): {class_dirs}")
    
    # Transforms
    train_tf, val_tf = get_transforms(img_size, augment=args.augment)
    
    # Datasets with train/val split
    train_dir = os.path.join(data_dir, "train")
    val_dir = os.path.join(data_dir, "val")
    
    if not os.path.isdir(train_dir) or not os.path.isdir(val_dir):
        print("Creating train/val split from dataset directory...")
        os.makedirs(train_dir, exist_ok=True)
        os.makedirs(val_dir, exist_ok=True)
        
        for cls in class_dirs:
            src = os.path.join(data_dir, cls)
            if os.path.isdir(src):
                files = sorted(os.listdir(src))
                split_idx = int(len(files) * 0.8)
                for i, fname in enumerate(files):
                    src_path = os.path.join(src, fname)
                    if i < split_idx:
                        dst = os.path.join(train_dir, cls, fname)
                    else:
                        dst = os.path.join(val_dir, cls, fname)
                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                    if not os.path.exists(dst):
                        import shutil
                        shutil.copy2(src_path, dst)
    
    train_dataset = ImageFolder(train_dir, transform=train_tf)
    val_dataset = ImageFolder(val_dir, transform=val_tf)
    
    num_classes = len(train_dataset.classes)
    print(f"Number of classes: {num_classes}")
    print(f"Class mapping: {train_dataset.class_to_idx}")
    print(f"Train samples: {len(train_dataset)}")
    print(f"Val samples: {len(val_dataset)}")
    
    # DataLoaders
    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, 
                             shuffle=True, num_workers=args.num_workers, pin_memory=True)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size,
                           shuffle=False, num_workers=args.num_workers, pin_memory=True)
    
    # Model
    model = DeepfakeDetector(num_classes=num_classes, pretrained=args.pretrained)
    model = model.to(device)
    
    # Loss and optimizer
    class_counts = np.bincount([label for _, label in train_dataset], minlength=num_classes)
    class_weights = 1.0 / (class_counts + 1)
    class_weights = class_weights / class_weights.sum() * num_classes
    criterion = nn.CrossEntropyLoss(weight=torch.FloatTensor(class_weights).to(device))
    
    optimizer = optim.AdamW([
        {'params': model.backbone.fc.parameters(), 'lr': args.lr},
        {'params': [p for n, p in model.backbone.named_parameters() 
                    if 'layer4' in n and p.requires_grad], 'lr': args.lr * 0.1},
    ], weight_decay=args.weight_decay)
    
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', 
                                                      factor=0.5, patience=3)
    
    # Training loop
    best_val_acc = 0.0
    best_model_state = None
    history = {'train_loss': [], 'train_acc': [], 'val_loss': [], 'val_acc': []}
    
    print(f"\nTraining for {args.epochs} epochs...")
    print("-" * 60)
    
    for epoch in range(args.epochs):
        # Training
        model.train()
        train_loss = 0.0
        train_correct = 0
        train_total = 0
        
        for inputs, labels in train_loader:
            inputs, labels = inputs.to(device), labels.to(device)
            
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item() * inputs.size(0)
            _, predicted = outputs.max(1)
            train_correct += predicted.eq(labels).sum().item()
            train_total += labels.size(0)
        
        train_loss /= train_total
        train_acc = train_correct / train_total
        
        # Validation
        model.eval()
        val_loss = 0.0
        val_correct = 0
        val_total = 0
        
        with torch.no_grad():
            for inputs, labels in val_loader:
                inputs, labels = inputs.to(device), labels.to(device)
                outputs = model(inputs)
                loss = criterion(outputs, labels)
                
                val_loss += loss.item() * inputs.size(0)
                _, predicted = outputs.max(1)
                val_correct += predicted.eq(labels).sum().item()
                val_total += labels.size(0)
        
        val_loss /= val_total
        val_acc = val_correct / val_total
        
        scheduler.step(val_loss)
        
        # Logging
        current_lr = optimizer.param_groups[0]['lr']
        print(f"Epoch {epoch+1:3d}/{args.epochs} | "
              f"Train Loss: {train_loss:.4f} Acc: {train_acc:.4f} | "
              f"Val Loss: {val_loss:.4f} Acc: {val_acc:.4f} | "
              f"LR: {current_lr:.6f}")
        
        history['train_loss'].append(train_loss)
        history['train_acc'].append(train_acc)
        history['val_loss'].append(val_loss)
        history['val_acc'].append(val_acc)
        
        # Save best
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            best_model_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
            print(f"  -> Best model! (val_acc: {val_acc:.4f})")
    
    # Save best model
    if best_model_state is not None:
        torch.save(best_model_state, "best_model.pth")
        print(f"\nBest model saved (val_acc: {best_val_acc:.4f})")
    
    # Copy to model_weights.pth for the server
    if os.path.exists("best_model.pth"):
        import shutil
        shutil.copy("best_model.pth", "model_weights.pth")
        print("Copied to model_weights.pth")
    
    # Save class map
    class_map = {
        "classes": train_dataset.classes,
        "class_to_idx": {c: i for i, c in enumerate(train_dataset.classes)},
        "idx_to_class": {i: c for i, c in enumerate(train_dataset.classes)},
        "num_classes": num_classes,
        "best_val_acc": float(best_val_acc),
    }
    
    import json
    with open("class_map.json", "w") as f:
        json.dump(class_map, f, indent=2)
    print("class_map.json saved")
    
    # Save training history
    history['classes'] = train_dataset.classes
    with open("training_history.json", "w") as f:
        json.dump(history, f, indent=2)
    print("training_history.json saved")
    
    print(f"\nTraining complete! Best val accuracy: {best_val_acc:.4f}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Train SudoScorpStingVision model")
    parser.add_argument("--data", "-d", default="dataset", help="Dataset directory")
    parser.add_argument("--epochs", "-e", type=int, default=30, help="Number of epochs")
    parser.add_argument("--batch-size", "-b", type=int, default=32, help="Batch size")
    parser.add_argument("--lr", type=float, default=0.001, help="Learning rate")
    parser.add_argument("--weight-decay", type=float, default=1e-4, help="Weight decay")
    parser.add_argument("--img-size", "-s", type=int, default=224, help="Image size")
    parser.add_argument("--no-augment", action="store_true", help="Disable data augmentation")
    parser.add_argument("--no-pretrained", action="store_true", help="Don't use pretrained weights")
    parser.add_argument("--num-workers", "-w", type=int, default=2, help="DataLoader workers")
    args = parser.parse_args()
    
    args.augment = not args.no_augment
    args.pretrained = not args.no_pretrained
    
    success = train(args)
    if success:
        print("\nDone! Run 'python main.py' to start the inference server.")
    else:
        print("\nTraining failed!")
        import sys
        sys.exit(1)


if __name__ == "__main__":
    main()
