"""Generate narration WAVs per slide with SVOX Pico TTS and report durations.

Pico (pico2wave) is a corpus-based offline voice, noticeably warmer and more
natural than espeak/Mbrola formant/diphone synthesis. It's synthesized
sentence-by-sentence (its internal buffer truncates very long strings) and
then lightly slowed + pitched down with rubberband for a calmer, warmer read.
"""
import json
import os
import re
import subprocess

from content import SLIDES

AUDIO_DIR = os.path.join(os.path.dirname(__file__), "audio")
os.makedirs(AUDIO_DIR, exist_ok=True)

LANG = "en-US"
SR = 22050        # standardized output rate
TEMPO = 0.93       # slight slow-down, calmer pace
PITCH = 0.97       # slight pitch drop, warmer tone


def split_sentences(text):
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p for p in parts if p]


def synth_sentence(text, out_path):
    subprocess.run(
        ["pico2wave", "-l", LANG, "-w", out_path, text],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )


def synth(text, out_path):
    sentences = split_sentences(text)
    tmp_dir = out_path + ".parts"
    os.makedirs(tmp_dir, exist_ok=True)
    parts = []
    for i, sent in enumerate(sentences):
        p = os.path.join(tmp_dir, f"{i:03d}.wav")
        synth_sentence(sent, p)
        parts.append(p)

    concat_list = os.path.join(tmp_dir, "list.txt")
    with open(concat_list, "w") as f:
        for p in parts:
            f.write(f"file '{os.path.abspath(p)}'\n")
    raw_concat = out_path + ".rawconcat.wav"
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_list,
         "-c:a", "pcm_s16le", raw_concat],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    subprocess.run(
        ["ffmpeg", "-y", "-i", raw_concat,
         "-af", f"rubberband=tempo={TEMPO}:pitch={PITCH}",
         "-ar", str(SR), "-ac", "1", out_path],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )

    for p in parts:
        os.remove(p)
    os.remove(concat_list)
    os.remove(raw_concat)
    os.rmdir(tmp_dir)


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
