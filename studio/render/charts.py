"""Animated charts: the picture of a data-explainer episode.

A chart renders to a clip exactly as a parallax shot does, so assembly cannot tell
the two apart. Three things are enforced here by construction rather than hoped for:

- **Nothing is static.** The chart builds in, then holds under a slow horizontal
  drift, because the production standard fails any frame held beyond 2.5 s.
- **Every chart credits its source in the frame.** A number on screen is a claim.
- **Layout follows the platform's caption safe area,** so one spec renders as a
  16:9 master shot and as a native 9:16 vertical, rather than a centre crop that
  cuts the chart in half.

Uses matplotlib's object API on the Agg canvas and never `pyplot` or `rc_context`,
both of which mutate global state that B6's thread pool would race on.
"""

from __future__ import annotations

import bisect
import contextlib
import subprocess
import textwrap
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter, MaxNLocator

from studio.core.schemas import ChartSpec

FFMPEG = ["ffmpeg", "-hide_banner", "-nostats", "-loglevel", "error", "-y"]
FPS = 30
DPI = 100
BUILD_SECONDS = 1.4
MAX_DRIFT_PX = 90


@dataclass(frozen=True)
class ChartStyle:
    """One look per show. The defaults match trade-atlas's thumbnail concept:
    near-black ground, white type, one amber accent kept for the number that matters."""

    background: str = "#0B0F14"
    text: str = "#F2F2F0"
    muted: str = "#8A94A3"
    grid: str = "#1E2630"
    series: str = "#4EA8DE"
    accent: str = "#FFC53D"
    font: str = "DejaVu Sans"    # ships inside matplotlib, so every machine renders alike


@dataclass(frozen=True)
class _Frame:
    """Pixel geometry on a canvas widened by the drift distance.

    The visible window slides right by `drift` px across the clip, so content lives
    in canvas x ∈ [drift, width] — the strip every frame of the window contains.
    """

    width: int
    height: int
    drift: int
    safe: dict = field(default_factory=dict)

    @property
    def canvas_w(self) -> int:
        return self.width + self.drift

    @property
    def base(self) -> float:
        return min(self.width, self.height) / 1080

    def px(self, size_at_1080: float) -> float:
        return size_at_1080 * self.base

    def pt(self, size_at_1080: float) -> float:
        return self.px(size_at_1080) * 72 / DPI

    @property
    def left(self) -> float:
        return self.drift + self.safe.get("left", 0.05) * self.width

    @property
    def right(self) -> float:
        return self.width - self.safe.get("right", 0.05) * self.width

    @property
    def top(self) -> float:
        return self.safe.get("top", 0.06) * self.height

    @property
    def bottom(self) -> float:
        return self.height - self.safe.get("bottom", 0.12) * self.height

    def fx(self, x: float) -> float:
        return x / self.canvas_w

    def fy(self, y_from_top: float) -> float:
        return 1 - y_from_top / self.height


Draw = Callable[[float], None]


def render_chart(spec: ChartSpec, out: Path, *, duration_ms: int, width: int = 1920,
                 height: int = 1080, safe_area: dict | None = None,
                 style: ChartStyle = ChartStyle()) -> Path:
    """Render one chart shot to an MP4 of `duration_ms`, to the nearest frame."""
    if width % 2 or height % 2:
        raise ValueError(f"{width}x{height}: yuv420p needs even dimensions")
    frames = max(1, round(duration_ms * FPS / 1000))
    build = max(1, min(round(BUILD_SECONDS * FPS), frames // 2))
    f = _Frame(width, height, drift=min(frames, MAX_DRIFT_PX), safe=safe_area or {})

    # +0.5 px so Agg's int() truncation of figsize*dpi can never round a pixel away.
    fig = Figure(figsize=((f.canvas_w + 0.5) / DPI, (height + 0.5) / DPI), dpi=DPI,
                 facecolor=style.background)
    canvas = FigureCanvasAgg(fig)
    draw = _SCENES[spec.kind](fig, spec, style, f)

    out.parent.mkdir(parents=True, exist_ok=True)
    # A crash must never leave a truncated clip under the name of a finished one.
    partial = out.with_name(f"{out.stem}.partial{out.suffix}")
    _encode(_frames(canvas, draw, f, frames, build), partial, f, frames)
    partial.replace(out)
    return out


# --------------------------------------------------------------------------
# Scenes. Each lays out a figure and returns draw(progress in 0..1).
# --------------------------------------------------------------------------

def _bar(fig: Figure, spec: ChartSpec, style: ChartStyle, f: _Frame) -> Draw:
    top, bottom = _chrome(fig, spec, style, f)
    n = len(spec.values)
    slot = (f.right - f.left) / n
    labels = [_wrap(label, f.px(28), slot * 0.9) for label in spec.labels]
    tick_room = max(t.count("\n") + 1 for t in labels) * f.px(28) * 1.3 + f.px(18)
    ax = _axes(fig, style, f, top + f.px(40), bottom - tick_room, left_pad=0)
    ax.yaxis.set_visible(False)
    ax.spines["left"].set_visible(False)

    colours = [style.accent if i == spec.highlight else style.series for i in range(n)]
    bars = ax.bar(range(n), [0.0] * n, width=0.62, color=colours)
    lo, hi = min(0.0, *spec.values), max(0.0, *spec.values)
    span = (hi - lo) or 1.0
    ax.set_ylim(lo - (0.18 * span if lo < 0 else 0), hi + 0.18 * span)
    ax.set_xlim(-0.6, n - 0.4)
    ax.set_xticks(range(n), [_lit(t) for t in labels])
    ax.tick_params(axis="x", colors=style.text, labelsize=f.pt(28),
                   labelfontfamily=style.font)

    texts = []
    for i, v in enumerate(spec.values):
        shown = spec.display[i] if spec.display else _fmt(v, spec.unit)
        texts.append(ax.text(
            i, 0, _lit(shown), ha="center", va="bottom" if v >= 0 else "top",
            color=style.accent if i == spec.highlight else style.text,
            fontsize=f.pt(40), fontweight="bold", fontfamily=style.font, alpha=0))
    gap = 0.025 * span

    def draw(p: float) -> None:
        for i, (bar, v, t) in enumerate(zip(bars, spec.values, texts)):
            start = 0.4 * i / (n - 1) if n > 1 else 0.0
            q = _ease_out((p - start) / 0.6)
            bar.set_height(v * q)
            t.set_y(v * q + (gap if v >= 0 else -gap))
            t.set_alpha(_clamp((q - 0.7) / 0.3))

    return draw


def _line(fig: Figure, spec: ChartSpec, style: ChartStyle, f: _Frame) -> Draw:
    top, bottom = _chrome(fig, spec, style, f)
    categorical = isinstance(spec.x[0], str)
    xs = [float(i) for i in range(len(spec.x))] if categorical else [float(v) for v in spec.x]
    tick_room = f.px(28) * 1.6 + (f.px(28) * 1.8 if spec.x_label else 0) + f.px(12)
    ax = _axes(fig, style, f, top + f.px(20), bottom - tick_room, left_pad=f.px(130))
    ax.spines["left"].set_visible(False)
    ax.grid(axis="y", color=style.grid, linewidth=f.pt(2))
    ax.set_axisbelow(True)
    ax.yaxis.set_major_locator(MaxNLocator(4))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: _lit(_fmt(v, spec.unit))))

    lo, hi = min(0.0, *spec.y), max(0.0, *spec.y)
    pad = 0.14 * ((hi - lo) or 1.0)
    ax.set_ylim(lo - (pad if lo < 0 else 0), hi + pad)
    if categorical:
        every = max(1, -(-len(xs) // 6))
        ax.set_xticks(xs[::every], [_lit(str(v)) for v in spec.x[::every]])
        ax.set_xlim(-0.3, len(xs) - 0.7)
    else:
        ax.xaxis.set_major_locator(MaxNLocator(6))
        ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: _lit(_fmt(v))))
        margin = 0.02 * (xs[-1] - xs[0])
        ax.set_xlim(xs[0] - margin, xs[-1] + margin)
    if spec.x_label:
        ax.set_xlabel(_lit(spec.x_label), color=style.muted, fontsize=f.pt(26),
                      fontfamily=style.font, labelpad=f.px(14))

    width = f.pt(7)
    (line,) = ax.plot([], [], color=style.series, linewidth=width, solid_capstyle="round")
    (head,) = ax.plot([], [], "o", color=style.series, markersize=f.pt(22))

    span = xs[-1] - xs[0]
    renderer = fig.canvas.get_renderer()
    dense = np.linspace(xs[0], xs[-1], 2000)
    path = ax.transData.transform(np.column_stack([dense, np.interp(dense, xs, spec.y)]))
    bounds = ax.get_window_extent(renderer)
    marks = []
    for c in spec.callouts:
        cx = xs[spec.x.index(c.x)] if categorical else float(c.x)
        cy = float(np.interp(cx, xs, spec.y))
        (dot,) = ax.plot([cx], [cy], "o", color=style.accent, markersize=f.pt(28),
                         alpha=0, zorder=5)
        label = ax.annotate(
            _lit(c.text), (cx, cy), textcoords="offset pixels", xytext=(0, 0),
            color=style.accent, fontsize=f.pt(38), fontweight="bold",
            fontfamily=style.font, alpha=0, zorder=6)
        _place(label, path, bounds, renderer, gap=(f.px(22), f.px(26)), pad=f.px(8))
        marks.append((cx, dot, label))

    def draw(p: float) -> None:
        cut = xs[0] + _ease_in_out(p) * span
        k = bisect.bisect_right(xs, cut)
        px, py = xs[:k], list(spec.y[:k])
        if k < len(xs):
            px, py = px + [cut], py + [float(np.interp(cut, xs, spec.y))]
        line.set_data(px, py)
        head.set_data([px[-1]], [py[-1]])
        for cx, dot, label in marks:
            # Fades in over the last 6% of the approach, so a callout on the final
            # point is fully visible when the line arrives rather than never.
            a = _clamp((cut - cx) / (0.06 * span) + 1)
            dot.set_alpha(a)
            label.set_alpha(a)

    return draw


def _stat(fig: Figure, spec: ChartSpec, style: ChartStyle, f: _Frame) -> Draw:
    top, bottom = _chrome(fig, spec, style, f)
    visible = f.right - f.left
    centre = f.fx((f.left + f.right) / 2)
    size = min(f.px(250), visible / (0.62 * max(1, len(spec.value_text))))
    mid = top + (bottom - top) * 0.42
    value = fig.text(centre, f.fy(mid), _lit(spec.value_text), ha="center", va="center",
                     color=style.accent, fontsize=size * 72 / DPI, fontweight="bold",
                     fontfamily=style.font, alpha=0)
    caption = None
    if spec.caption:
        caption = fig.text(centre, f.fy(mid + size * 0.62 + f.px(30)),
                           _lit(_wrap(spec.caption, f.px(46), visible)),
                           ha="center", va="top", color=style.text, fontsize=f.pt(46),
                           fontfamily=style.font, linespacing=1.3, alpha=0)

    def draw(p: float) -> None:
        q = _ease_out(p / 0.7)
        value.set_alpha(q)
        value.set_fontsize(size * (0.86 + 0.14 * q) * 72 / DPI)
        if caption is not None:
            caption.set_alpha(_clamp((p - 0.4) / 0.6))

    return draw


_SCENES: dict[str, Callable[[Figure, ChartSpec, ChartStyle, _Frame], Draw]] = {
    "bar": _bar, "line": _line, "stat": _stat,
}


# --------------------------------------------------------------------------

def _chrome(fig: Figure, spec: ChartSpec, style: ChartStyle, f: _Frame) -> tuple[float, float]:
    """Title, subtitle and source credit. Returns the vertical band left for content."""
    y, visible = f.top, f.right - f.left
    if spec.title:
        title = _wrap(spec.title, f.px(58), visible)
        fig.text(f.fx(f.left), f.fy(y), _lit(title), color=style.text, fontsize=f.pt(58),
                 fontweight="bold", fontfamily=style.font, va="top", ha="left",
                 linespacing=1.15)
        y += (title.count("\n") + 1) * f.px(58) * 1.25
    if spec.subtitle:
        sub = _wrap(spec.subtitle, f.px(32), visible)
        fig.text(f.fx(f.left), f.fy(y + f.px(8)), _lit(sub), color=style.muted,
                 fontsize=f.pt(32), fontfamily=style.font, va="top", ha="left")
        y += f.px(8) + (sub.count("\n") + 1) * f.px(32) * 1.35
    credit = _wrap(f"Source: {spec.source_label}", f.px(24), visible)
    fig.text(f.fx(f.left), f.fy(f.bottom), _lit(credit), color=style.muted,
             fontsize=f.pt(24), fontfamily=style.font, va="bottom", ha="left",
             linespacing=1.25)
    return y, f.bottom - (credit.count("\n") + 1) * f.px(24) * 1.3 - f.px(24)


def _place(label, path: np.ndarray, bounds, renderer, *, gap: tuple[float, float],
           pad: float) -> None:
    """Put a callout where it covers neither its own line nor the edge of the chart.

    Tries the four diagonals around the point and keeps the first clean one. This is
    measured rather than ruled: "label late points to the left" put EP01's 85 ft
    callout straight onto a curve falling towards it.
    """
    def aim(sx: int, sy: int):
        label.set_position((sx * gap[0], sy * gap[1]))
        label.set_horizontalalignment("left" if sx > 0 else "right")
        label.set_verticalalignment("bottom" if sy > 0 else "top")
        return label.get_window_extent(renderer)

    clear_of_line = None
    for sx, sy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
        box = aim(sx, sy)
        g = box.padded(pad)
        on_line = ((path[:, 0] >= g.x0) & (path[:, 0] <= g.x1)
                   & (path[:, 1] >= g.y0) & (path[:, 1] <= g.y1)).any()
        inside = (bounds.x0 <= box.x0 and box.x1 <= bounds.x1
                  and bounds.y0 <= box.y0 and box.y1 <= bounds.y1)
        if not on_line and inside:
            return
        if not on_line and clear_of_line is None:
            clear_of_line = (sx, sy)
    # Nothing is perfectly clean. Covering the data is worse than touching the edge.
    aim(*(clear_of_line or (1, 1)))


def _axes(fig: Figure, style: ChartStyle, f: _Frame, top: float, bottom: float, *,
          left_pad: float):
    left = f.left + left_pad
    ax = fig.add_axes((f.fx(left), f.fy(bottom), f.fx(f.right - left), (bottom - top) / f.height))
    ax.set_facecolor(style.background)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(style.grid)
        ax.spines[side].set_linewidth(f.pt(2))
    ax.tick_params(colors=style.muted, labelsize=f.pt(26), length=0, pad=f.px(12),
                   labelfontfamily=style.font)
    return ax


def _frames(canvas: FigureCanvasAgg, draw: Draw, f: _Frame, count: int,
            build: int) -> Iterator[bytes]:
    """Re-render only while the chart is moving; the hold repeats the last frame
    and the drift comes from the crop window, which costs nothing to compute."""
    expected = f.canvas_w * f.height * 4
    held = b""
    for i in range(count):
        if i < build:
            draw(i / (build - 1) if build > 1 else 1.0)
            canvas.draw()
            held = bytes(canvas.buffer_rgba())
            if len(held) != expected:
                raise RuntimeError(f"canvas rendered {len(held)} bytes, expected {expected} "
                                   f"for {f.canvas_w}x{f.height} RGBA")
        yield held


def _encode(frames: Iterator[bytes], out: Path, f: _Frame, count: int) -> None:
    # floor(n*drift/count) steps whole pixels; at drift == count that is exactly one
    # pixel per frame, which is smooth where a fractional crop would judder.
    pan = f"crop={f.width}:{f.height}:x='floor(n*{f.drift}/{count})':y=0"
    proc = subprocess.Popen(
        FFMPEG + ["-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{f.canvas_w}x{f.height}",
                  "-framerate", str(FPS), "-i", "-", "-vf", pan,
                  "-c:v", "libx264", "-preset", "fast", "-tune", "animation", "-crf", "19",
                  "-profile:v", "high", "-pix_fmt", "yuv420p", str(out)],
        stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
    )
    try:
        for frame in frames:
            proc.stdin.write(frame)
        proc.stdin.close()
    except BrokenPipeError:
        # ffmpeg exited early. Its own stderr, raised below, names the real cause;
        # a broken pipe only says that something, somewhere, went wrong.
        with contextlib.suppress(BrokenPipeError):
            proc.stdin.close()
    except BaseException:
        proc.kill()
        proc.wait()
        raise
    err = proc.stderr.read().decode(errors="replace").strip()
    if proc.wait() != 0:
        raise RuntimeError(f"ffmpeg failed rendering {out.name}: {err[-400:]}")


def _fmt(v: float, unit: str = "") -> str:
    """Compact, broadcast-style numbers: $5.3M, $135K, $0.21, 8.6%, 82 ft."""
    a = abs(v)
    if a >= 1e9:
        n, suffix = v / 1e9, "B"
    elif a >= 1e6:
        n, suffix = v / 1e6, "M"
    elif a >= 1e4:
        n, suffix = v / 1e3, "K"
    else:
        n, suffix = v, ""
    num = f"{n:,.{1 if suffix else 2}f}".rstrip("0").rstrip(".") + suffix
    if unit == "$":
        return f"-${num[1:]}" if num.startswith("-") else f"${num}"
    if unit == "%":
        return f"{num}%"
    return f"{num} {unit}" if unit else num


def _lit(text: str) -> str:
    """Escape dollars so a price pair like '$0.21 vs $27' is never parsed as mathtext.

    matplotlib renders text between two unescaped '$' as TeX, and unescapes '\\$'
    in text that is not maths — so escaping every dollar is literal either way,
    without the global `text.parse_math` switch that threads would race on.
    """
    return text.replace("$", r"\$")


def _wrap(text: str, size_px: float, width_px: float) -> str:
    # 0.62 em per character: bold DejaVu measured 0.564 em on a real title, so this
    # leaves about 10% headroom rather than none.
    return textwrap.fill(text, max(8, int(width_px / (0.62 * size_px))))


def _clamp(v: float) -> float:
    return max(0.0, min(1.0, v))


def _ease_out(t: float) -> float:
    return 1 - (1 - _clamp(t)) ** 3


def _ease_in_out(t: float) -> float:
    t = _clamp(t)
    return 4 * t ** 3 if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2
