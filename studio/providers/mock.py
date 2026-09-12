"""Mock providers.

The entire pipeline runs on these before a single model weight is downloaded, so
the state machine, the gates and the assembly can be proven correct for free. They
emit real files — FFmpeg-generated colour fields and tones — because a mock that
returns an empty path proves nothing about whether the assembly step works.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

FFMPEG = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"]


def _run(args: list[str]) -> None:
    subprocess.run(args, check=True, capture_output=True)


def _hue(seed: str) -> str:
    """Deterministic colour per prompt, so identical prompts look identical."""
    h = hashlib.sha256(seed.encode()).digest()
    return f"0x{h[0]:02x}{h[1]:02x}{h[2]:02x}"


class MockText:
    """Returns structured stand-ins, not lorem ipsum, so schemas actually validate."""

    def __init__(self) -> None:
        self.calls: list[str] = []

    def complete(self, prompt: str, *, system: str = "", max_tokens: int = 2048) -> str:
        self.calls.append(prompt)
        return json.dumps({"mock": True, "prompt_sha": hashlib.sha256(prompt.encode()).hexdigest()[:12]})


class MockImage:
    def generate(self, prompt: str, out: Path, *, width: int, height: int,
                 reference: Path | None = None, lora: str | None = None) -> Path:
        out.parent.mkdir(parents=True, exist_ok=True)
        # A grid over the deterministic colour. A flat field looks identical under
        # any camera move, so the still must carry structure for the video stage
        # to have something to move across — see MockVideo.animate.
        _run(FFMPEG + ["-f", "lavfi", "-i", f"color=c={_hue(prompt)}:s={width}x{height}",
                       "-vf", "drawgrid=w=96:h=96:t=3:color=white@0.35",
                       "-frames:v", "1", str(out)])
        return out


class MockVideo:
    """Stands in for both parallax and AI video; the caller cannot tell which."""

    def animate(self, still: Path, out: Path, *, duration_ms: int, motion: str) -> Path:
        """A slow pan, which is what parallax2d will actually do.

        The mock used to hold a single frame, and `check_master` rightly called
        that a slideshow — nothing is ever fully static in the production
        standard. That stopped every mock walk at LOCK 3 and left B10 and B11
        with no end-to-end coverage. A crop-and-pan costs the same as the still
        encode it replaces (measured: 0.35 s against 0.36 s for a 3 s clip) and
        is closer to the real renderer besides.
        """
        out.parent.mkdir(parents=True, exist_ok=True)
        seconds = max(duration_ms / 1000, 0.1)
        pan = (f"crop=w=iw*0.94:h=ih*0.94:x=(iw-ow)*(t/{seconds:.3f}):y=(ih-oh)/2,"
               "scale=trunc(iw/2)*2:trunc(ih/2)*2")
        _run(FFMPEG + ["-loop", "1", "-i", str(still),
                       "-t", f"{seconds:.3f}", "-r", "30",
                       "-c:v", "libx264", "-preset", "ultrafast",
                       "-pix_fmt", "yuv420p", "-vf", pan, str(out)])
        return out


class MockStock:
    def fetch(self, query: str, out: Path) -> Path | None:
        return MockImage().generate(f"stock:{query}", out, width=1920, height=1080)


class MockTTS:
    """Duration tracks word count at ~2.6 words/second, so timings are plausible."""

    WORDS_PER_SECOND = 2.6

    def speak(self, text: str, out: Path, *, voice: str, lang: str = "en") -> Path:
        out.parent.mkdir(parents=True, exist_ok=True)
        seconds = max(0.4, len(text.split()) / self.WORDS_PER_SECOND)
        freq = 200 if lang == "en" else 170
        _run(FFMPEG + ["-f", "lavfi", "-i", f"sine=frequency={freq}:duration={seconds:.3f}",
                       "-ar", "48000", "-ac", "1", str(out)])
        return out


class MockAlign:
    """Even word spacing. Enough to exercise clause-boundary cutting."""

    def align(self, audio: Path, text: str) -> list[dict]:
        words = text.split()
        dur = _probe_duration(audio)
        if not words:
            return []
        step = dur / len(words)
        return [{"word": w, "start": round(i * step, 3), "end": round((i + 1) * step, 3)}
                for i, w in enumerate(words)]


class MockDepth:
    def depth(self, image: Path, out: Path) -> Path:
        out.parent.mkdir(parents=True, exist_ok=True)
        _run(FFMPEG + ["-i", str(image), "-vf", "format=gray", "-frames:v", "1", str(out)])
        return out


class MockPublish:
    """Degrades the way the real chain degrades: a folder drop with its caption."""

    def __init__(self, drop_dir: Path) -> None:
        self.drop_dir = drop_dir

    def publish(self, video: Path, meta: dict) -> str:
        self.drop_dir.mkdir(parents=True, exist_ok=True)
        target = self.drop_dir / video.name
        target.write_bytes(video.read_bytes())
        (self.drop_dir / f"{video.stem}.caption.txt").write_text(
            json.dumps(meta, indent=2), encoding="utf-8"
        )
        return f"mock://{target}"


def _probe_duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(path)],
        check=True, capture_output=True, text=True,
    )
    return float(out.stdout.strip())


REGISTRY = {
    "text": MockText, "image": MockImage, "video": MockVideo, "stock": MockStock,
    "tts": MockTTS, "align": MockAlign, "depth": MockDepth,
}
