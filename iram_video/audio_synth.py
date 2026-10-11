import math
import wave
import numpy as np
from pathlib import Path

SAMPLE_RATE = 44100

def synthesize_mood_track(mood: str, duration_sec: float, output_path: Path):
    """Synthesizes high-quality ambient background soundtrack using pure numpy waveform synthesis."""
    if mood == "none":
        # Create silent track
        with wave.open(str(output_path), "w") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(np.zeros(int(SAMPLE_RATE * duration_sec), dtype=np.int16).tobytes())
        return

    t = np.linspace(0, duration_sec, int(SAMPLE_RATE * duration_sec), endpoint=False)
    
    if mood == "lofi":
        # Warm Lofi progression (Am9 -> Dm9 -> G13 -> Cmaj7)
        chords = [
            [220.00, 261.63, 329.63, 493.88], # Am9
            [146.83, 174.61, 220.00, 261.63], # Dm7
            [196.00, 246.94, 293.66, 370.00], # G
            [130.81, 164.81, 196.00, 246.94]  # Cmaj7
        ]
        chord_len = 12.0
    elif mood == "tech":
        # Futuristic Tech progression (F#m -> D -> A -> E)
        chords = [
            [185.00, 220.00, 277.18, 370.00], # F#m
            [146.83, 185.00, 220.00, 293.66], # D
            [220.00, 277.18, 329.63, 440.00], # A
            [164.81, 207.65, 246.94, 329.63]  # E
        ]
        chord_len = 14.0
    else:  # default 'cyber' or 'ambient'
        # Cyber / Dark ambient progression (Dm -> Bb -> F -> C)
        chords = [
            [146.83, 174.61, 220.00, 293.66], # Dm
            [116.54, 146.83, 174.61, 233.08], # Bb
            [87.31, 130.81, 174.61, 220.00],  # F
            [130.81, 164.81, 196.00, 261.63]  # C
        ]
        chord_len = 16.0

    pad = np.zeros_like(t)

    for i, chord in enumerate(chords):
        num_reps = math.ceil(duration_sec / (chord_len * len(chords)))
        for rep in range(num_reps):
            start_t = (rep * len(chords) + i) * chord_len
            if start_t >= duration_sec:
                break
            end_t = min(start_t + chord_len, duration_sec)
            mask = (t >= start_t) & (t < end_t)
            lt = t[mask] - start_t
            dur = end_t - start_t
            
            # Attack and release envelopes
            att = min(3.0, dur / 3)
            rel = min(3.0, dur / 3)
            env = np.ones_like(lt)
            att_m = lt < att
            rel_m = lt > (dur - rel)
            env[att_m] = 0.5 * (1 - np.cos(np.pi * lt[att_m] / att))
            env[rel_m] = 0.5 * (1 + np.cos(np.pi * (lt[rel_m] - (dur - rel)) / rel))

            for freq in chord:
                voice = (
                    0.5 * np.sin(2 * np.pi * freq * lt) +
                    0.25 * np.sin(2 * np.pi * (freq * 1.002) * lt) +
                    0.25 * np.sin(2 * np.pi * (freq * 0.998) * lt) +
                    0.15 * np.sin(2 * np.pi * (freq * 0.5) * lt)
                )
                lfo = 0.85 + 0.15 * np.sin(2 * np.pi * 0.25 * lt)
                pad[mask] += voice * env * lfo * 0.15

    # Gentle ambient rhythmic pulse
    pulse_freq = 60 if mood == "cyber" else 75
    pulse = 0.03 * np.sin(2 * np.pi * pulse_freq * t) * np.exp(-((t % 0.5) * 18))

    mix = pad + pulse
    max_val = np.max(np.abs(mix))
    if max_val > 0:
        mix = (mix / max_val) * 0.45

    # Master fade-in and fade-out
    fade_len = int(SAMPLE_RATE * 3.0)
    if len(mix) > fade_len * 2:
        mix[:fade_len] *= np.linspace(0, 1, fade_len)
        mix[-fade_len:] *= np.linspace(1, 0, fade_len)

    audio_int16 = (mix * 32767).astype(np.int16)
    with wave.open(str(output_path), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio_int16.tobytes())
