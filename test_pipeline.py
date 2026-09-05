"""Test all detection pipelines directly without HTTP server."""
import sys, os, json
tmpdir = os.path.join(os.environ.get('LOCALAPPDATA', 'C:/Users/sudos/AppData/Local'), 'Temp', 'Sudo_Scorp_Sting_Vison')
if os.path.isdir(tmpdir):
    os.chdir(tmpdir)
    sys.path.insert(0, tmpdir)
    print(f"Working dir: {os.getcwd()}")
else:
    # Try alternative locations
    for p in [r'C:\Users\sudos\AppData\Local\Temp\Sudo_Scorp_Sting_Vison',
              r'C:\Users\sudos\odysseus\Sudo_Scorp_Sting_Vison']:
        if os.path.isdir(p):
            os.chdir(p)
            sys.path.insert(0, p)
            print(f"Working dir: {os.getcwd()}")
            break
    else:
        print("ERROR: Cannot find working directory")
        sys.exit(1)

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import torch
import numpy as np
from PIL import Image
from torchvision import transforms
from model import DeepfakeDetectorCNN

print("="*60)
print("TESTING SUDOSCORPSTINGVISION PIPELINE")
print("="*60)

# Load model
state = torch.load('best_model.pth', map_location='cpu', weights_only=True)
num_classes = state['backbone.fc.5.weight'].shape[0]
model = DeepfakeDetectorCNN(num_classes=num_classes, pretrained=False)
model.load_state_dict(state)
model.eval()

with open('class_map.json') as f:
    class_map = json.load(f)
print(f"Model loaded: {class_map['classes']}")

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

def predict_image(img_path):
    img = Image.open(img_path).convert('RGB')
    tensor = transform(img).unsqueeze(0)
    with torch.no_grad():
        out = model(tensor)
        probs = torch.softmax(out, 1)[0]
    class_names = class_map['classes']
    probs_dict = {c: round(float(probs[i]), 4) for i, c in enumerate(class_names)}
    pred_idx = int(probs.argmax())
    pred_class = class_names[pred_idx]
    
    if 'real' in class_names:
        real_idx = class_map['class_to_idx']['real']
        ai_conf = 1.0 - float(probs[real_idx])
    else:
        ai_conf = max(float(p) for c, p in probs_dict.items() if c != 'real')
    
    is_ai = ai_conf > 0.5
    source = None
    if is_ai:
        non_real = [(c, p) for c, p in probs_dict.items() if c != 'real']
        if non_real:
            source = max(non_real, key=lambda x: x[1])[0]
    
    return {
        'is_ai_generated': is_ai,
        'confidence': round(ai_conf, 4),
        'predicted_class': pred_class,
        'probabilities': probs_dict,
        'source_attribution': source or 'N/A',
        'generator': source or ('N/A' if not is_ai else 'Unknown'),
    }

print("\n--- Testing Real Images (should be class=real, low AI confidence) ---")
real_dir = 'dataset/val/real'
real_files = sorted(os.listdir(real_dir))[:5]
for f in real_files:
    result = predict_image(os.path.join(real_dir, f))
    status = "OK" if not result['is_ai_generated'] else "WRONG"
    print(f"  {f}: {status} — conf={result['confidence']:.2f}, pred={result['predicted_class']}")

print("\n--- Testing AI Images (should be class=ai, high AI confidence) ---")
ai_dir = 'dataset/val/ai'
ai_files = sorted(os.listdir(ai_dir))[:5]
for f in ai_files:
    result = predict_image(os.path.join(ai_dir, f))
    status = "OK" if result['is_ai_generated'] else "WRONG"
    print(f"  {f}: {status} — conf={result['confidence']:.2f}, pred={result['predicted_class']}, gen={result['generator']}")

# Test video pipeline
print("\n--- Video Pipeline ---")
try:
    import cv2
    print("cv2 available — video pipeline ready")
except ImportError:
    print("cv2 NOT available")

# Test audio pipeline
print("\n--- Audio Pipeline ---")
try:
    import torchaudio
    print("torchaudio available — audio pipeline ready")
except ImportError:
    print("torchaudio NOT available")

print("\n" + "="*60)
print("ALL TESTS COMPLETE")
print("="*60)
