"""Assemble slide PNGs + narration WAVs into hsg_theory_explained.mp4."""
import json
import os
import subprocess

from content import SLIDES

HERE = os.path.dirname(__file__)
SLIDES_DIR = os.path.join(HERE, "slides")
AUDIO_DIR = os.path.join(HERE, "audio")
SEG_DIR = os.path.join(HERE, "segments")
os.makedirs(SEG_DIR, exist_ok=True)

LEAD = 0.6   # seconds of silence before narration starts
TRAIL = 0.6  # seconds of silence after narration ends
FADE = 0.35  # video fade in/out per segment
FPS = 30
SR = 22050   # espeak-ng default sample rate for these renders

with open(os.path.join(AUDIO_DIR, "durations.json")) as f:
    DURATIONS = json.load(f)


def run(cmd):
    result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    if result.returncode != 0:
        print(result.stderr.decode(errors="replace")[-4000:])
        raise subprocess.CalledProcessError(result.returncode, cmd)


def make_silence(path, dur):
    run([
        "ffmpeg", "-y", "-f", "lavfi", "-i", f"anullsrc=r={SR}:cl=mono",
        "-t", f"{dur:.3f}", "-c:a", "pcm_s16le", path,
    ])


def build_segment_audio(slide_id, narration_wav, out_wav):
    lead_path = os.path.join(SEG_DIR, f"{slide_id}_lead.wav")
    trail_path = os.path.join(SEG_DIR, f"{slide_id}_trail.wav")
    make_silence(lead_path, LEAD)
    make_silence(trail_path, TRAIL)
    list_path = os.path.join(SEG_DIR, f"{slide_id}_audio_list.txt")
    with open(list_path, "w") as f:
        for p in (lead_path, narration_wav, trail_path):
            f.write(f"file '{os.path.abspath(p)}'\n")
    run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_path,
        "-c:a", "pcm_s16le", out_wav,
    ])


def build_segment_video(slide_id, png_path, out_mp4, total_dur):
    vf = (
        f"fps={FPS},format=yuv420p,"
        f"fade=t=in:st=0:d={FADE},fade=t=out:st={max(total_dur - FADE, 0):.3f}:d={FADE}"
    )
    run([
        "ffmpeg", "-y", "-loop", "1", "-i", png_path, "-t", f"{total_dur:.3f}",
        "-vf", vf, "-r", str(FPS), "-pix_fmt", "yuv420p", "-an", out_mp4,
    ])


def main():
    seg_video_list = os.path.join(SEG_DIR, "video_list.txt")
    seg_audio_list = os.path.join(SEG_DIR, "audio_list.txt")
    video_entries = []
    audio_entries = []

    for s in SLIDES:
        sid = s["id"]
        narration_wav = os.path.join(AUDIO_DIR, f"{sid}.wav")
        seg_audio = os.path.join(SEG_DIR, f"{sid}_segaudio.wav")
        build_segment_audio(sid, narration_wav, seg_audio)

        total_dur = LEAD + DURATIONS[sid] + TRAIL
        png_path = os.path.join(SLIDES_DIR, f"{sid}.png")
        seg_video = os.path.join(SEG_DIR, f"{sid}_segvideo.mp4")
        build_segment_video(sid, png_path, seg_video, total_dur)

        video_entries.append(seg_video)
        audio_entries.append(seg_audio)
        print(f"segment {sid}: {total_dur:.2f}s")

    with open(seg_video_list, "w") as f:
        for p in video_entries:
            f.write(f"file '{os.path.abspath(p)}'\n")
    with open(seg_audio_list, "w") as f:
        for p in audio_entries:
            f.write(f"file '{os.path.abspath(p)}'\n")

    concat_video = os.path.join(HERE, "_concat_video.mp4")
    concat_audio = os.path.join(HERE, "_concat_audio.wav")

    run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", seg_video_list,
        "-c", "copy", concat_video,
    ])
    run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", seg_audio_list,
        "-c:a", "pcm_s16le", concat_audio,
    ])

    total_dur = sum(LEAD + DURATIONS[s["id"]] + TRAIL for s in SLIDES)
    narration_norm = os.path.join(HERE, "_narration_norm.wav")
    run([
        "ffmpeg", "-y", "-i", concat_audio,
        "-af", "loudnorm=I=-16:TP=-1.5:LRA=8",
        "-ar", "44100", "-ac", "2", narration_norm,
    ])

    music_raw = os.path.join(HERE, "music_raw.wav")
    music_bed = os.path.join(HERE, "_music_bed.wav")
    run([
        "ffmpeg", "-y", "-i", music_raw,
        "-af",
        (
            "lowpass=f=3400,"
            "aecho=0.8:0.7:80|140:0.22|0.14,"
            "loudnorm=I=-31:TP=-3:LRA=7,"
            f"atrim=0:{total_dur:.3f},"
            "afade=t=in:st=0:d=3,"
            f"afade=t=out:st={max(total_dur - 4, 0):.3f}:d=4"
        ),
        "-ar", "44100", "-ac", "2", music_bed,
    ])

    mixed_audio = os.path.join(HERE, "_mixed_audio.wav")
    run([
        "ffmpeg", "-y", "-i", narration_norm, "-i", music_bed,
        "-filter_complex", "amix=inputs=2:duration=first:weights=1 1,alimiter=limit=0.97",
        "-ar", "44100", "-ac", "2", mixed_audio,
    ])

    final_out = os.path.join(HERE, "hsg_theory_explained.mp4")
    run([
        "ffmpeg", "-y", "-i", concat_video, "-i", mixed_audio,
        "-c:v", "libx264", "-crf", "20", "-preset", "medium",
        "-c:a", "aac", "-b:a", "192k", "-shortest",
        "-movflags", "+faststart", final_out,
    ])
    print("wrote", final_out)


if __name__ == "__main__":
    main()
