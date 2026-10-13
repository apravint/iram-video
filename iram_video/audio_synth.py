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
    
    if mood in ["cinematic", "trailer", "movie"]:
        # Hans Zimmer Style Hollywood Trailer Score
        # Staccato tension pulses (16th notes at 120 bpm)
        pulse_step = 0.25
        step_t = t % pulse_step
        env_pulse = np.exp(-step_t * 14)
        cellos = (
            np.sin(2 * np.pi * 73.42 * t) +
            0.5 * np.sin(2 * np.pi * 146.83 * t) +
            0.25 * np.sin(2 * np.pi * 220.00 * t)
        ) * env_pulse * 0.16

        # Inception BRAAM Horn Impacts every 9 seconds
        braam_track = np.zeros_like(t)
        braam_interval = 9.0
        num_braams = max(1, int(math.ceil(duration_sec / braam_interval)))
        for b_idx in range(num_braams):
            b_start = b_idx * braam_interval + 0.8
            if b_start >= duration_sec:
                break
            b_mask = (t >= b_start) & (t < min(duration_sec, b_start + 4.5))
            bt = t[b_mask] - b_start
            b_env = np.exp(-bt * 0.75)
            # Pitch drops from 58Hz down to 46Hz
            b_pitch = 58.0 - (12.0 * (bt / 4.5))
            raw_horn = (
                np.sin(2 * np.pi * b_pitch * bt) +
                0.85 * np.sin(2 * np.pi * b_pitch * 2 * bt) +
                0.60 * np.sin(2 * np.pi * b_pitch * 3 * bt) +
                0.45 * np.sin(2 * np.pi * b_pitch * 4 * bt) +
                0.75 * np.sin(2 * np.pi * 38.0 * bt) # Sub-bass rumble
            )
            # Heavy saturated clipping for cinematic brass crunch
            braam_track[b_mask] += np.tanh(raw_horn * 2.4) * b_env * 0.45

        # Sub-bass 808 drops at start of scenes (every ~7 seconds)
        sub_drops = np.zeros_like(t)
        for s_idx in range(max(1, int(duration_sec // 7))):
            s_start = s_idx * 7.0
            s_mask = (t >= s_start) & (t < min(duration_sec, s_start + 2.0))
            st = t[s_mask] - s_start
            s_freq = 110.0 * np.exp(-st * 3.5) + 38.0
            sub_drops[s_mask] += np.sin(2 * np.pi * s_freq * st) * np.exp(-st * 2.0) * 0.35

        mix = cellos + braam_track + sub_drops
        max_val = np.max(np.abs(mix))
        if max_val > 0:
            mix = (mix / max_val) * 0.52

        # Master fade in/out
        fade_len = int(SAMPLE_RATE * 2.0)
        if len(mix) > fade_len * 2:
            mix[:fade_len] *= np.linspace(0, 1, fade_len)
            mix[-fade_len:] *= np.linspace(1, 0, fade_len)

        audio_int16 = (mix * 32767).astype(np.int16)
        with wave.open(str(output_path), "w") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(audio_int16.tobytes())
        return

    if mood in ["documentary", "acoustic", "piano", "real"]:
        # Warm Acoustic / Piano documentary progression (Cmaj7 -> G6 -> Am7 -> Fmaj7)
        chords = [
            [130.81, 164.81, 196.00, 246.94], # Cmaj7
            [98.00, 146.83, 196.00, 246.94],  # G6
            [110.00, 164.81, 220.00, 261.63], # Am7
            [87.31, 130.81, 174.61, 261.63]   # Fmaj7
        ]
        chord_len = 10.0
    elif mood in ["corporate", "business", "inspirational"]:
        # Uplifting Corporate progression (G -> D -> Em -> C)
        chords = [
            [196.00, 246.94, 293.66, 392.00], # G
            [146.83, 220.00, 293.66, 370.00], # D
            [164.81, 196.00, 246.94, 329.63], # Em
            [130.81, 164.81, 196.00, 261.63]  # C
        ]
        chord_len = 8.0
    elif mood in ["energetic", "promo", "upbeat", "launch"]:
        # Driving Tech / Promo progression (Am -> F -> C -> G)
        chords = [
            [220.00, 261.63, 329.63, 440.00], # Am
            [174.61, 220.00, 261.63, 349.23], # F
            [130.81, 164.81, 196.00, 261.63], # C
            [196.00, 246.94, 293.66, 392.00]  # G
        ]
        chord_len = 6.0
    elif mood in ["minimal", "subtle"]:
        # Minimalist soft ambient (Cmaj9 -> Am9)
        chords = [
            [130.81, 164.81, 196.00, 293.66], # Cmaj9
            [110.00, 164.81, 220.00, 246.94]  # Am9
        ]
        chord_len = 16.0
    elif mood == "lofi":
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
