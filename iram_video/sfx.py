import math
import wave
import numpy as np
from pathlib import Path

SR = 44100

class SoundEffectsSynthesizer:
    """Procedural synthesis of Hollywood-grade cinema sound effects (SFX) and Foley in stereo."""

    @staticmethod
    def _write_wav(out_path: Path, mono_signal: np.ndarray):
        """Converts floating-point mono audio array into standard 16-bit dual-channel stereo WAV."""
        audio_int16 = (np.clip(mono_signal, -1.0, 1.0) * 32767).astype(np.int16)
        stereo_signal = np.stack((audio_int16, audio_int16), axis=-1)
        with wave.open(str(out_path), "w") as wf:
            wf.setnchannels(2)  # Stereo Configuration Channel
            wf.setsampwidth(2)  # 16-bit depth
            wf.setframerate(SR)  # 44100 Hz
            wf.writeframes(stereo_signal.tobytes())

    @classmethod
    def generate_impact(cls, out_path: Path, duration: float = 2.5):
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
        hit = np.tanh(hit * 1.8) * 0.70
        cls._write_wav(out_path, hit)

    @classmethod
    def generate_whoosh(cls, out_path: Path, duration: float = 1.2):
        """Cinematic whoosh / camera sweep transition."""
        t = np.linspace(0, duration, int(SR * duration), endpoint=False)
        # Bandpassed noise with frequency sweep
        white = np.random.normal(0, 0.2, len(t))
        # Bell curve envelope
        center = duration / 2.0
        env = np.exp(-((t - center) ** 2) / (2 * (0.2 ** 2)))
        # Pitch carrier sweep
        carrier_freq = 200.0 + 800.0 * np.sin(np.pi * t / duration)
        phase = 2 * np.pi * np.cumsum(carrier_freq) / SR
        carrier = np.sin(phase)
        
        whoosh = (white * 0.6 + carrier * 0.4) * env
        whoosh = np.tanh(whoosh * 1.5) * 0.70
        cls._write_wav(out_path, whoosh)

    @classmethod
    def generate_telemetry(cls, out_path: Path, duration: float = 2.0):
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
            
        cls._write_wav(out_path, mix * 0.70)

    @classmethod
    def generate_ding(cls, out_path: Path, duration: float = 0.4):
        """Short 880Hz chime with exponential decay (ported from Automated-Video-Generator)."""
        t = np.linspace(0, duration, int(SR * duration), endpoint=False)
        envelope = np.exp(-t * 8.0)
        signal = np.sin(2 * np.pi * 880.0 * t) * envelope * 0.45
        cls._write_wav(out_path, signal * 0.70)

    @classmethod
    def generate_click(cls, out_path: Path, duration: float = 0.05):
        """Crisp mechanical impulse click."""
        t = np.linspace(0, duration, int(SR * duration), endpoint=False)
        noise = np.random.normal(0, 0.4, len(t))
        envelope = np.exp(-t * 120.0)
        signal = noise * envelope * 0.5
        cls._write_wav(out_path, signal * 0.70)

    @classmethod
    def generate_pop(cls, out_path: Path, duration: float = 0.08):
        """Short bubble pop."""
        t = np.linspace(0, duration, int(SR * duration), endpoint=False)
        freq = 320.0 + 400.0 * np.exp(-t * 45.0)
        phase = 2 * np.pi * np.cumsum(freq) / SR
        envelope = np.exp(-t * 35.0)
        signal = np.sin(phase) * envelope * 0.55
        cls._write_wav(out_path, signal * 0.70)

    @classmethod
    def generate_notification(cls, out_path: Path, duration: float = 0.3):
        """Two-tone UI chime: 440Hz followed by 880Hz."""
        half = duration / 2.0
        t1 = np.linspace(0, half, int(SR * half), endpoint=False)
        t2 = np.linspace(0, half, int(SR * half), endpoint=False)
        tone1 = np.sin(2 * np.pi * 440.0 * t1) * np.exp(-t1 * 10.0) * 0.4
        tone2 = np.sin(2 * np.pi * 880.0 * t2) * np.exp(-t2 * 8.0) * 0.45
        signal = np.concatenate([tone1, tone2])
        cls._write_wav(out_path, signal * 0.70)

    @classmethod
    def generate_swish(cls, out_path: Path, duration: float = 0.15):
        """Quick high-frequency sweep for code cards and animated list items."""
        t = np.linspace(0, duration, int(SR * duration), endpoint=False)
        carrier_freq = 400.0 + 1200.0 * (t / duration)
        phase = 2 * np.pi * np.cumsum(carrier_freq) / SR
        carrier = np.sin(phase)
        noise = np.random.normal(0, 0.2, len(t))
        envelope = np.sin(np.pi * t / duration)
        signal = (carrier * 0.4 + noise * 0.25) * envelope * 0.5
        cls._write_wav(out_path, signal * 0.70)

    @classmethod
    def generate_transition(cls, out_path: Path, duration: float = 0.4):
        """Sweep + noise blend for scene transitions."""
        t = np.linspace(0, duration, int(SR * duration), endpoint=False)
        noise = np.random.normal(0, 0.25, len(t))
        carrier_freq = 150.0 + 850.0 * np.sin(np.pi * t / duration)
        phase = 2 * np.pi * np.cumsum(carrier_freq) / SR
        env = np.sin(np.pi * t / duration) ** 1.5
        signal = (noise * 0.4 + np.sin(phase) * 0.35) * env * 0.55
        cls._write_wav(out_path, signal * 0.70)

    @classmethod
    def generate_bounce(cls, out_path: Path, duration: float = 0.35):
        """Rising two-tone bounce for positive reveals."""
        t = np.linspace(0, duration, int(SR * duration), endpoint=False)
        freq = 300.0 + 223.0 * (t / duration)
        phase = 2 * np.pi * np.cumsum(freq) / SR
        env = np.sin(np.pi * t / duration)
        signal = np.sin(phase) * env * 0.45
        cls._write_wav(out_path, signal * 0.70)

    @classmethod
    def generate_riser(cls, out_path: Path, duration: float = 1.5):
        """Ascending frequency riser for tension building."""
        t = np.linspace(0, duration, int(SR * duration), endpoint=False)
        freq = 80.0 + 1200.0 * (t / duration) ** 2
        phase = 2 * np.pi * np.cumsum(freq) / SR
        env = (t / duration) ** 1.2
        signal = np.sin(phase) * env * 0.5
        cls._write_wav(out_path, signal * 0.70)

    @classmethod
    def generate_sfx(cls, kind: str, out_path: Path, duration: float = None) -> Path:
        """Universal SFX dispatcher with disk caching."""
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        if out_path.exists() and out_path.stat().st_size > 500:
            return out_path

        k = kind.lower().strip()
        dispatch = {
            "impact": (cls.generate_impact, 2.5),
            "hit": (cls.generate_impact, 2.5),
            "whoosh": (cls.generate_whoosh, 1.2),
            "swoosh": (cls.generate_whoosh, 1.2),
            "telemetry": (cls.generate_telemetry, 2.0),
            "ding": (cls.generate_ding, 0.4),
            "bell": (cls.generate_ding, 0.4),
            "click": (cls.generate_click, 0.05),
            "pop": (cls.generate_pop, 0.08),
            "notification": (cls.generate_notification, 0.3),
            "swish": (cls.generate_swish, 0.15),
            "transition": (cls.generate_transition, 0.4),
            "bounce": (cls.generate_bounce, 0.35),
            "riser": (cls.generate_riser, 1.5),
        }

        func, def_dur = dispatch.get(k, (cls.generate_whoosh, 1.2))
        dur = duration if duration is not None else def_dur
        func(out_path, duration=dur)
        return out_path
