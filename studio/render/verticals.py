"""Derivative cuts.

Clips are chosen at the beat sheet, not hunted for after the master exists, so a
vertical is a moment that was designed to stand alone. Geometry is one spec for
Shorts, Reels and TikTok; only the duration cap and the hook differ.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

FFMPEG = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"]


def cut_vertical(master: Path, out: Path, *, start_ms: int, end_ms: int,
                 width: int, height: int) -> Path:
    """Centre-crop to portrait and trim. Re-encodes, because a crop must."""
    out.parent.mkdir(parents=True, exist_ok=True)
    duration = (end_ms - start_ms) / 1000
    vf = (
        f"crop='min(iw,ih*{width}/{height})':'min(ih,iw*{height}/{width})',"
        f"scale={width}:{height}"
    )
    subprocess.run(
        FFMPEG + ["-ss", f"{start_ms / 1000:.3f}", "-i", str(master),
                  "-t", f"{duration:.3f}", "-vf", vf,
                  "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
                  "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(out)],
        check=True, capture_output=True,
    )
    return out
