# HSG explainer video

Generates `hsg_theory_explained.mp4`, a narrated video explaining the sign-convention
correction to the "Harmonic Substrate Gravity" (HSG) theory: what the bug was, what
it changed, what survived unaffected, and how the corrected theory compares against
DESI DR2 data. Content is sourced from the sign-convention-correction writeup and
analysis report supplied alongside this task.

Unrelated to the rest of this repository (SudoScorpStingVision, a deepfake detection
platform) — this folder was added standalone for the video-generation task.

## Pipeline

1. `content.py` — slide text + narration script, one Python dict per slide.
2. `render.py` — renders each slide to a 1920x1080 PNG (matplotlib + mplot3d):
   dark gradient background, glass-card panels, a 3D lit sphere on the title slide,
   3D gravity-well diagrams for the sign-flip slides, and 3D bar charts for the
   numeric comparisons.
3. `narrate.py` — synthesizes narration per slide with `espeak-ng` using the
   `mb-us1` Mbrola voice (American English, female), resampled to 22050 Hz.
4. `make_music.py` — composes a slow D-minor string/violin drone as MIDI and
   renders it with `fluidsynth` against the FluidR3 GM soundfont.
5. `build.py` — assembles everything: per-slide video segments timed to their
   narration, narration loudness-normalized, music lowpass-filtered/reverbed and
   mixed in quietly underneath, muxed to the final H.264/AAC MP4.

## Regenerating

Requires `ffmpeg`, `espeak-ng` + `mbrola` + `mbrola-us1`, `fluidsynth` +
`fluid-soundfont-gm`, and the Python packages `matplotlib`, `numpy`, `mido`.

```
python3 render.py     # slides/*.png
python3 narrate.py    # audio/*.wav + audio/durations.json
python3 make_music.py && fluidsynth -ni /usr/share/sounds/sf2/FluidR3_GM.sf2 \
    music.mid -F music_raw.wav -r 44100
python3 build.py      # hsg_theory_explained.mp4
```

## Known limitations

This runs in a sandboxed environment with no general internet access (only a few
package registries are reachable), so:

- **Voice**: no access to a hosted neural TTS. Uses the best available fully
  offline voice — `espeak-ng` + the `mb-us1` Mbrola diphone voice — which is
  clearer than default formant synthesis but still noticeably synthetic, not a
  studio-quality neural voice.
- **Music**: no licensed audio available. The background drone is an originally
  composed MIDI piece rendered through a General MIDI violin/strings patch via
  FluidSynth — not a real recorded performance.
- **Visuals**: "3D" here means genuine matplotlib `mplot3d` renders with
  light-source shading (lit sphere, gravity-well surfaces, 3D bar charts), not
  a Blender-grade photorealistic render.

## Output

`hsg_theory_explained.mp4` — 1920x1080, 30fps, ~11 minutes.
