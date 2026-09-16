FROM python:3.11-slim

WORKDIR /app

# System libraries required by opencv-python-headless (video) and
# torchaudio/soundfile (audio) at runtime.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libsndfile1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Run `python train.py` before building (or mount best_model.pth,
# model_weights.pth and class_map.json into /app) to serve real
# predictions. Without trained weights the server starts in demo mode
# with untrained (random) weights — see main.py's load_model().
CMD ["python", "main.py"]
