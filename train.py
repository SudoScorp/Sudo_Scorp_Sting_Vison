"""
================================================================================
🔥 SUDOSCORPSTINGVISION NEURAL NETWORK TRAINING PIPELINE TEMPLATE
================================================================================
This script initializes the exact DeepfakeDetectorCNN architectural layer layout
used in your FastAPI production file. It reads training datasets organized into 
directories, trains the classification tensors via backpropagation, and outputs 
a production 'model_weights.pth' state dictionary directly to your disk.

Dataset Directory Requirements Layout:
    dataset/
        train/
            real/   <-- (Place standard authentic media here)
            ai/     <-- (Place synthetic AI generated media here)
        val/
            real/
            ai/
"""

import os
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import datasets, transforms

class DeepfakeDetectorCNN(nn.Module):
    def __init__(self):
        super(DeepfakeDetectorCNN, self).__init__()
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

def train_model(data_dir="dataset", batch_size=32, epochs=10, learning_rate=0.001):
    print("-------------------------------------------------------")
    print("Initializing Deep Learning CNN Tensor Optimization Run...")
    print("-------------------------------------------------------")
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Target execution engine hardware device identified as: {device}")
    
    data_transforms = {
        'train': transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.RandomHorizontalFlip(),
            transforms.ToTensor(),
        ]),
        'val': transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
        ]),
    }
    
    if not os.path.exists(data_dir):
        print(f"[CRITICAL ERROR] Target path folder directory '{data_dir}' not found.")
        return

    image_datasets = {x: datasets.ImageFolder(os.path.join(data_dir, x), data_transforms[x]) for x in ['train', 'val']}
    dataloaders = {x: DataLoader(image_datasets[x], batch_size=batch_size, shuffle=True, num_workers=2) for x in ['train', 'val']}
    
    model = DeepfakeDetectorCNN().to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)
    
    for epoch in range(epochs):
        print(f"\n--- Epoch Cycle {epoch + 1}/{epochs} ---")
        for phase in ['train', 'val']:
            if phase == 'train':
                model.train()
            else:
                model.eval()
                
            running_loss = 0.0
            running_corrects = 0
            
            for inputs, labels in dataloaders[phase]:
                inputs, labels = inputs.to(device), labels.to(device)
                optimizer.zero_grad()
                with torch.set_grad_enabled(phase == 'train'):
                    outputs = model(inputs)
                    _, preds = torch.max(outputs, 1)
                    loss = criterion(outputs, labels)
                    if phase == 'train':
                        loss.backward()
                        optimizer.step()
                        
                running_loss += loss.item() * inputs.size(0)
                running_corrects += torch.sum(preds == labels.data)
                
            epoch_loss = running_loss / len(image_datasets[phase])
            epoch_acc = running_corrects.double() / len(image_datasets[phase])
            print(f"[{phase.upper()} PHASE] Loss: {epoch_loss:.4f} | Accuracy: {epoch_acc:.4f}")
            
    output_filename = "model_weights.pth"
    torch.save(model.state_dict(), output_filename)
    print(f"\nMatrix states successfully serialized as: '{output_filename}'")

if __name__ == '__main__':
    train_model(data_dir="dataset", epochs=5)
