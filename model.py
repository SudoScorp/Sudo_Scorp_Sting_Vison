#!/usr/bin/env python3
"""
SudoScorpStingVision — Model Definition
Fine-tuned ResNet18 for deepfake detection and source attribution.
"""

import torch
import torch.nn as nn
from torchvision.models import ResNet18_Weights, resnet18


class DeepfakeDetectorCNN(nn.Module):
    """
    Deepfake detector using a fine-tuned ResNet18 backbone.
    Transfer learning from ImageNet; freezes early layers, fine-tunes layer4 + classifier.
    Works for binary (real/AI) or multi-class (generator attribution) tasks.
    """

    def __init__(self, num_classes=2, pretrained=True):
        super().__init__()
        weights = ResNet18_Weights.DEFAULT if pretrained else None
        self.backbone = resnet18(weights=weights)

        if pretrained:
            # Freeze all parameters first
            for param in self.backbone.parameters():
                param.requires_grad = False
            # Unfreeze layer4 (last conv block) for fine-tuning
            for param in self.backbone.layer4.parameters():
                param.requires_grad = True

        # Replace classifier head
        num_features = self.backbone.fc.in_features
        self.backbone.fc = nn.Sequential(
            nn.Dropout(0.3),
            nn.Linear(num_features, 256),
            nn.ReLU(inplace=True),
            nn.BatchNorm1d(256),
            nn.Dropout(0.3),
            nn.Linear(256, num_classes),
        )

    def forward(self, x):
        return self.backbone(x)
