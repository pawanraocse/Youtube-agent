"""FFmpeg assembly: picture to the locked voice-over, then the mix and the master.

Picture is cut to narration, never the other way round. Music ducks under the
voice via sidechain compression, because music sitting at a flat level under
speech is the loudest amateur tell in this medium.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

FFMPEG = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"]


def _run(args: list[str]) -> None:
    subprocess.run(args, check=True, capture_output=True)


def concat_clips(clips: list[Path], out: Path) -> Path:
    """Join shot clips in order. Stream copy — no re-encode, so it is near-instant."""
    out.parent.mkdir(parents=True, exist_ok=True)
    listing = out.with_suffix(".concat.txt")
    listing.write_text("".join(f"file '{c.resolve()}'\n" for c in clips), encoding="utf-8")
    _run(FFMPEG + ["-f", "concat", "-safe", "0", "-i", str(listing), "-c", "copy", str(out)])
    listing.unlink(missing_ok=True)
    return out


def mix_audio(vo: Path, music: Path | None, out: Path, *, duck_db: float = 12.0) -> Path:
    """Voice plus an optional ducked music bed, normalised to broadcast loudness."""
    out.parent.mkdir(parents=True, exist_ok=True)
    if music is None:
        chain = "[0:a]loudnorm=I=-14:TP=-1:LRA=11[out]"
        inputs = ["-i", str(vo)]
    else:
        chain = (
            "[1:a]volume=0.35[bed];"
            f"[bed][0:a]sidechaincompress=threshold=0.05:ratio=8:attack=5:release=250"
            f":makeup={duck_db / 12:.2f}[ducked];"
            "[0:a][ducked]amix=inputs=2:duration=first:dropout_transition=0[mixed];"
            "[mixed]loudnorm=I=-14:TP=-1:LRA=11[out]"
        )
        inputs = ["-i", str(vo), "-i", str(music)]
    _run(FFMPEG + inputs + ["-filter_complex", chain, "-map", "[out]",
                            "-ar", "48000", "-ac", "2", str(out)])
    return out


def mux(video: Path, audio: Path, out: Path, *, nvenc: bool = False) -> Path:
    """Marry picture and mix into the master. Shortest stream wins, so a long
    picture tail cannot leave silence hanging off the end."""
    out.parent.mkdir(parents=True, exist_ok=True)
    vcodec = ["-c:v", "h264_nvenc", "-preset", "p4"] if nvenc else ["-c:v", "copy"]
    _run(FFMPEG + ["-i", str(video), "-i", str(audio), *vcodec,
                   "-c:a", "aac", "-b:a", "192k", "-shortest",
                   "-movflags", "+faststart", str(out)])
    return out


def probe(path: Path) -> dict:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "format=duration:stream=width,height,codec_type",
         "-of", "json", str(path)],
        check=True, capture_output=True, text=True,
    )
    import json as _json
    return _json.loads(out.stdout)
