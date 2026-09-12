"""The production standard is only real if it is enforced on actual files.

Each test builds a deliberately non-conforming master with FFmpeg and asserts the
check catches it, then builds a conforming one and asserts it passes.
"""

import subprocess

import pytest

from studio.checks import (_audio_channels, _loudness, _mono_loudness,
                           check_captions, check_master)
from studio.core.config import PlatformSpec

FF = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"]
VERTICAL = PlatformSpec.load("vertical")


def _make(path, *, w, h, fps, seconds=4.0, moving=True, stereo_phase_flip=False):
    src = (f"testsrc2=size={w}x{h}:rate={fps}:duration={seconds}" if moving
           else f"color=c=0x203040:size={w}x{h}:rate={fps}:duration={seconds}")
    audio = f"sine=frequency=300:duration={seconds}"
    af = "pan=stereo|c0=c0|c1=-1*c0" if stereo_phase_flip else "pan=stereo|c0=c0|c1=c0"
    subprocess.run(
        FF + ["-f", "lavfi", "-i", src, "-f", "lavfi", "-i", audio,
              "-af", af, "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
              "-c:a", "aac", "-shortest", str(path)],
        check=True, capture_output=True,
    )
    return path


def test_conforming_vertical_master_passes(tmp_path):
    m = _make(tmp_path / "ok.mp4", w=1080, h=1920, fps=30)
    checks = {f.check for f in check_master(m, [], None, spec=VERTICAL)}
    assert "geometry" not in checks and "framerate" not in checks
    assert "static_frame" not in checks
    # The assertion whose absence hid DEBT-003: this fixture is dual mono, and the
    # check used to flag it on the 3.01 LU BS.1770 channel-sum offset alone.
    assert "mono_folddown" not in checks


def test_wrong_geometry_is_caught(tmp_path):
    m = _make(tmp_path / "wide.mp4", w=1920, h=1080, fps=30)
    assert "geometry" in {f.check for f in check_master(m, [], None, spec=VERTICAL)}


def test_low_framerate_judders(tmp_path):
    m = _make(tmp_path / "slow.mp4", w=1080, h=1920, fps=24)
    assert "framerate" in {f.check for f in check_master(m, [], None, spec=VERTICAL)}


def test_static_frame_reads_as_slideshow(tmp_path):
    m = _make(tmp_path / "frozen.mp4", w=1080, h=1920, fps=30, seconds=6.0, moving=False)
    assert "static_frame" in {f.check for f in check_master(m, [], None, spec=VERTICAL)}


def test_mono_folddown_catches_phase_cancellation(tmp_path):
    """Phone speakers are mono. A mix that only survives in stereo does not survive."""
    m = _make(tmp_path / "flipped.mp4", w=1080, h=1920, fps=30, stereo_phase_flip=True)
    assert "mono_folddown" in {f.check for f in check_master(m, [], None, spec=VERTICAL)}


def test_uncleared_music_blocks_the_platform_it_is_not_cleared_for(tmp_path):
    m = _make(tmp_path / "ok.mp4", w=1080, h=1920, fps=30)
    track = {"id": "yt-audio-library-42", "cleared_for": ["youtube_shorts"]}
    findings = check_master(m, ["youtube_shorts", "instagram_reels"], track, spec=VERTICAL)
    detail = " ".join(f.detail for f in findings if f.check == "music_clearance")
    assert "instagram_reels" in detail and "youtube_shorts" not in detail


@pytest.mark.parametrize("caption,expected", [
    ({"y_frac": 0.95, "size_px": 60, "lines": ["a"]}, "caption_safe_area"),
    ({"y_frac": 0.5, "size_px": 30, "lines": ["a"]}, "caption_size"),
    ({"y_frac": 0.5, "size_px": 60, "lines": ["a", "b", "c"]}, "caption_lines"),
])
def test_caption_rules(caption, expected):
    assert expected in {f.check for f in check_captions([caption], VERTICAL)}


def test_dual_mono_is_not_mistaken_for_phase_cancellation(tmp_path):
    """Two identical channels sum to twice the power of one, so BS.1770 measures a
    dual-mono file 3.01 LU louder than its own fold-down with nothing wrong. Every
    narration-led mix is close to dual mono, so a check that counts that offset as
    cancellation fires on correct masters and LOCK 3 can never open."""
    m = _make(tmp_path / "dual.mp4", w=1080, h=1920, fps=30)
    drop = _loudness(m)["input_i"] - _mono_loudness(m)
    assert 2.9 <= drop <= 3.1                      # the artefact, measured
    assert "mono_folddown" not in {f.check for f in check_master(m, [], None, spec=VERTICAL)}


def test_a_mono_master_is_not_folded_down_at_all(tmp_path):
    """A single-channel master has nothing to cancel against, and the downmix
    filter would read a channel it has not got."""
    m = tmp_path / "mono.mp4"
    subprocess.run(
        FF + ["-f", "lavfi", "-i", "testsrc2=size=1080x1920:rate=30:duration=4",
              "-f", "lavfi", "-i", "sine=frequency=300:duration=4",
              "-ac", "1", "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
              "-c:a", "aac", "-shortest", str(m)],
        check=True, capture_output=True,
    )
    assert _audio_channels(m) == 1
    assert "mono_folddown" not in {f.check for f in check_master(m, [], None, spec=VERTICAL)}
