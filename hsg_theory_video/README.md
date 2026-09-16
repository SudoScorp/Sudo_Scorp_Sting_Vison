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
   Written for a general audience: everyday analogies (a rubber sheet for
   gravity, a balloon for cosmic expansion), short sentences, jargon defined
   on first use.
2. `render.py` — renders each slide to a 1920x1080 PNG (matplotlib + mplot3d):
   dark gradient background, glass-card panels, a 3D lit sphere on the title
   slide, a 3D rubber-sheet gravity well with a rolling marble, a balloon/dots
   expansion diagram, 3D gravity-well "bug vs. fix" diagrams, a donut chart
   for the universe's energy budget, and 3D bar charts for the numeric
   comparisons.
3. `narrate.py` — synthesizes narration per slide with SVOX **Pico** TTS
   (`pico2wave`, en-US), sentence-chunked and lightly slowed/pitched down with
   ffmpeg's `rubberband` filter for a calmer, warmer delivery. Noticeably more
   natural than espeak/Mbrola formant or diphone synthesis.
4. `make_music.py` — composes a slow D-minor string/violin drone as MIDI and
   renders it with `fluidsynth` against the FluidR3 GM soundfont.
5. `build.py` — assembles everything: per-slide video segments timed to their
   narration, narration loudness-normalized, music lowpass-filtered/reverbed and
   mixed in quietly underneath, muxed to the final H.264/AAC MP4.

## Regenerating

Requires `ffmpeg` (built with `librubberband`), `libttspico-utils` (pico2wave),
`fluidsynth` + `fluid-soundfont-gm`, and the Python packages `matplotlib`,
`numpy`, `mido`.

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
  offline voice found — SVOX Pico (`pico2wave`) — which is a corpus-based
  engine and noticeably warmer than espeak/Mbrola, but still not a
  studio-quality neural voice.
- **Music**: no licensed audio available. The background drone is an originally
  composed MIDI piece rendered through a General MIDI violin/strings patch via
  FluidSynth — not a real recorded performance.
- **Visuals**: "3D" here means genuine matplotlib `mplot3d` renders with
  light-source shading (lit sphere, gravity-well/rubber-sheet surfaces, 3D bar
  charts), not a Blender-grade photorealistic render or stock imagery — there's
  no image-generation tool or general internet access in this sandbox to source
  either.

## Output

`hsg_theory_explained.mp4` — 1920x1080, 30fps, ~10 minutes.
