"""Provider interfaces.

Narrow on purpose. A caller never branches on which implementation is active; the
chain is chosen by config so swapping Wan for LTX, or Kokoro for something else,
touches one line of YAML and no Python.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable


@runtime_checkable
class TextProvider(Protocol):
    def complete(self, prompt: str, *, system: str = "", max_tokens: int = 2048) -> str: ...


@runtime_checkable
class ImageProvider(Protocol):
    def generate(self, prompt: str, out: Path, *, width: int, height: int,
                 reference: Path | None = None, lora: str | None = None) -> Path: ...


@runtime_checkable
class VideoProvider(Protocol):
    def animate(self, still: Path, out: Path, *, duration_ms: int, motion: str) -> Path: ...


@runtime_checkable
class StockProvider(Protocol):
    def fetch(self, query: str, out: Path) -> Path | None: ...


@runtime_checkable
class TTSProvider(Protocol):
    def speak(self, text: str, out: Path, *, voice: str, lang: str = "en") -> Path: ...


@runtime_checkable
class AlignProvider(Protocol):
    def align(self, audio: Path, text: str) -> list[dict]:
        """Word-level timings. Gives clause boundaries for cuts, free."""
        ...


@runtime_checkable
class DepthProvider(Protocol):
    def depth(self, image: Path, out: Path) -> Path: ...


@runtime_checkable
class PublishProvider(Protocol):
    def publish(self, video: Path, meta: dict) -> str:
        """Returns an external id, or a local path when it degraded to a folder drop."""
        ...
