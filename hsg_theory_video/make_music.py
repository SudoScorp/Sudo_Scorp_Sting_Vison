"""Compose a slow, dark violin drone in D minor and render it with fluidsynth."""
import mido
from mido import Message, MidiFile, MidiTrack, MetaMessage

TICKS = 480
TEMPO = mido.bpm2tempo(46)

mid = MidiFile(ticks_per_beat=TICKS)

# Track 0: sustained low string pad (violin section, soft)
pad = MidiTrack()
mid.tracks.append(pad)
pad.append(MetaMessage("set_tempo", tempo=TEMPO, time=0))
pad.append(Message("program_change", program=48, channel=0, time=0))  # Strings Ensemble 1

# D minor, slow moving chord bed: Dm -> B-flat -> F -> A(sus4->3)  (i - VI - III - V), one chord per 8 bars
chords = [
    [38, 50, 57, 62],   # D2 D3 A3 D4  (Dm drone-ish, open)
    [34, 46, 58, 65],   # Bb1 Bb2 Gb.. -> use Bb2 F3 F4 (VI)
    [29, 41, 53, 60],   # F1 F2 F3 C4  (III)
    [33, 45, 52, 57],   # A1 A2 E3 A3  (V)
]
bar_ticks = TICKS * 4
hold = bar_ticks * 8
vel = 46

REPEATS = 4  # ~167s per pass -> long enough to cover an ~11 minute video
for rep in range(REPEATS):
    for chord in chords:
        for i, note in enumerate(chord):
            pad.append(Message("note_on", note=note, velocity=vel - i * 3, channel=0, time=0 if i else 0))
        pad.append(Message("note_off", note=chord[0], velocity=0, channel=0, time=hold))
        for note in chord[1:]:
            pad.append(Message("note_off", note=note, velocity=0, channel=0, time=0))

# Track 1: sparse high solo violin line (dark, minor, very slow, rubato-ish via long notes)
solo = MidiTrack()
mid.tracks.append(solo)
solo.append(Message("program_change", program=40, channel=1, time=0))  # Violin

melody = [
    (74, TICKS * 6, 0),        # D5
    (72, TICKS * 6, TICKS * 2),
    (69, TICKS * 10, TICKS * 2),
    (70, TICKS * 6, TICKS * 4),
    (67, TICKS * 12, TICKS * 2),
    (65, TICKS * 8, TICKS * 6),
    (69, TICKS * 8, TICKS * 4),
    (62, TICKS * 16, TICKS * 10),
]
melody_low = [(n - 12, d, r) for n, d, r in melody]  # an octave down, darker variation
svel = 56
for rep in range(REPEATS):
    phrase = melody if rep % 2 == 0 else melody_low
    for note, dur, rest in phrase:
        solo.append(Message("note_on", note=note, velocity=svel, channel=1, time=rest))
        solo.append(Message("note_off", note=note, velocity=0, channel=1, time=dur))

mid.save("music.mid")
print("wrote music.mid, pad ticks total ~", len(chords) * hold / TICKS, "beats")
