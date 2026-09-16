"""Generate narration WAVs per slide with espeak-ng and report durations."""
import json
import os
import subprocess

from content import SLIDES

AUDIO_DIR = os.path.join(os.path.dirname(__file__), "audio")
os.makedirs(AUDIO_DIR, exist_ok=True)

VOICE = "mb-us1"  # American English female (Mbrola), calmer/smoother than default espeak formant voice
SPEED = 142       # words per minute -- slightly slower, calmer pace
PITCH = 38        # slightly lower pitch reads as calmer/more measured
AMP = 190
GAP = 8           # extra pause between words (centiseconds), measured delivery
SR = 22050        # standardized output rate -- mbrola voices render natively at 16kHz,
                   # so every file is resampled to this to match the silence clips in build.py


def synth(text, out_path):
    raw_path = out_path + ".raw.wav"
    subprocess.run(
        ["espeak-ng", "-v", VOICE, "-s", str(SPEED), "-p", str(PITCH),
         "-a", str(AMP), "-g", str(GAP), text, "-w", raw_path],
        check=True,
    )
    subprocess.run(
        ["ffmpeg", "-y", "-i", raw_path, "-ar", str(SR), "-ac", "1", out_path],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    os.remove(raw_path)


def duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        check=True, capture_output=True, text=True,
    )
    return float(out.stdout.strip())


def main():
    durations = {}
    for s in SLIDES:
        out_path = os.path.join(AUDIO_DIR, f"{s['id']}.wav")
        synth(s["narration"], out_path)
        d = duration(out_path)
        durations[s["id"]] = d
        print(f"{s['id']:20s} {d:6.2f}s  narration_chars={len(s['narration'])}")
    with open(os.path.join(AUDIO_DIR, "durations.json"), "w") as f:
        json.dump(durations, f, indent=2)
    print("total narration seconds:", sum(durations.values()))


if __name__ == "__main__":
    main()
