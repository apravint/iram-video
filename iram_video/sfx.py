import math
import wave
import numpy as np
from pathlib import Path

SR = 44100

class SoundEffectsSynthesizer:
    """Procedural synthesis of Hollywood-grade cinema sound effects (SFX) and Foley."""

    @staticmethod
    def generate_impact(out_path: Path, duration: float = 2.5):
        """Heavy cinematic sub-bass impact drop (808 / theatrical hit)."""
        t = np.linspace(0, duration, int(SR * duration), endpoint=False)
        # Pitch sweep from 140 Hz down to 36 Hz with exponential decay
        freq = 38.0 + 102.0 * np.exp(-t * 5.0)
        phase = 2 * np.pi * np.cumsum(freq) / SR
        env = np.exp(-t * 2.2)
        transient = np.exp(-t * 35.0) * np.sin(2 * np.pi * 320.0 * t)
        sub = np.sin(phase) * env
        rumble = np.sin(2 * np.pi * 32.0 * t) * np.exp(-t * 1.2) * 0.4
        
        hit = transient * 0.6 + sub * 0.8 + rumble
        hit = np.tanh(hit * 1.8) * 0.85
        
        audio_int16 = (hit * 32767).astype(np.int16)
        with wave.open(str(out_path), "w") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(SR)
            wf.writeframes(audio_int16.tobytes())

    @staticmethod
    def generate_whoosh(out_path: Path, duration: float = 1.2):
        """Cinematic whoosh / camera sweep transition."""
        t = np.linspace(0, duration, int(SR * duration), endpoint=False)
        # Bandpassed noise with frequency sweep
        white = np.random.normal(0, 0.2, len(t))
        # Bell curve envelope
        center = duration / 2.0
        env = np.exp(-((t - center) ** 2) / (2 * (0.2 ** 2)))
        # Pitch carrier sweep
        carrier_freq = 200.0 + 800.0 * np.sin(np.pi * t / duration)
        carrier = np.sin(2 * np.pi * carrier_freq * t)
        
        whoosh = (white * 0.6 + carrier * 0.4) * env
        whoosh = np.tanh(whoosh * 1.5) * 0.7
        
        audio_int16 = (whoosh * 32767).astype(np.int16)
        with wave.open(str(out_path), "w") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(SR)
            wf.writeframes(audio_int16.tobytes())

    @staticmethod
    def generate_telemetry(out_path: Path, duration: float = 2.0):
        """Sci-Fi quantum computer telemetry / processing beeps."""
        t = np.linspace(0, duration, int(SR * duration), endpoint=False)
        mix = np.zeros_like(t)
        
        # Series of blips
        rng = np.random.RandomState(42)
        for _ in range(12):
            blip_t = rng.uniform(0.1, duration - 0.2)
            b_freq = rng.choice([880.0, 1174.66, 1318.51, 1760.0, 2093.0])
            b_mask = (t >= blip_t) & (t < blip_t + 0.08)
            bt = t[b_mask] - blip_t
            mix[b_mask] += np.sin(2 * np.pi * b_freq * bt) * np.exp(-bt * 55.0) * 0.35
            
        audio_int16 = (mix * 32767).astype(np.int16)
        with wave.open(str(out_path), "w") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(SR)
            wf.writeframes(audio_int16.tobytes())
