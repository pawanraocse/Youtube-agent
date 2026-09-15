"""Charts are the picture of a data-explainer episode, so they are held to the
production standard on real rendered files, exactly as a master is."""

import math
import subprocess

import numpy as np
import pytest
from pydantic import ValidationError

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

from studio.checks import _freeze_spans, _video_props
from studio.core.config import PlatformSpec
from studio.core.schemas import ChartSpec
from studio.render import charts
from studio.render.charts import ChartStyle, _fmt, render_chart

SRC = {"source_ids": ["s9"], "source_label": "Stantec for the ACP, 2018"}

BAR = ChartSpec(kind="bar", title="What a cubic metre of water costs",
                labels=["Household", "Canal average", "Auction slot"],
                values=[0.21, 2.13, 26.9], display=["$0.21", "~$2.13", "~$27"],
                highlight=2, unit="$", **SRC)
LINE = ChartSpec(kind="line", title="The fresh water surcharge", x=[78.0, 80.0, 82.0, 84.0, 86.0],
                 y=[9.2, 7.7, 5.0, 2.3, 0.8], unit="%", x_label="Gatun Lake depth (ft)",
                 callouts=[{"x": 82.0, "text": "82 ft"}], **SRC)
STAT = ChartSpec(kind="stat", value_text="82 FT", caption="where the price of water turns", **SRC)


def _frame_count(path) -> int:
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_frames",
                          "-show_entries", "stream=nb_read_frames", "-of", "csv=p=0", str(path)],
                         check=True, capture_output=True, text=True)
    return int(out.stdout.strip())


def _frame(path, w, h, *, last: bool) -> np.ndarray:
    seek = ["-sseof", "-0.1"] if last else ["-ss", "0"]
    raw = subprocess.run(["ffmpeg", "-v", "error", *seek, "-i", str(path),
                          "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         check=True, capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.uint8).reshape(h, w, 3).astype(int)


# ---- rendering ------------------------------------------------------------

@pytest.mark.parametrize("spec", [BAR, LINE, STAT], ids=["bar", "line", "stat"])
def test_a_chart_clip_meets_the_production_standard(tmp_path, spec):
    """4 s at 30 fps builds in 1.4 s and holds for 2.6 s — past the 2.5 s freeze
    limit, so this fails the moment the hold drift stops moving the frame."""
    out = render_chart(spec, tmp_path / "c.mp4", duration_ms=4000, width=640, height=360)
    props = _video_props(out)
    assert (props["width"], props["height"]) == (640, 360)
    assert props["fps"] == pytest.approx(30.0)
    assert _frame_count(out) == 120
    assert _freeze_spans(out, threshold_s=2.5) == []


def test_the_same_spec_renders_as_a_native_vertical_inside_the_safe_area(tmp_path):
    """Nothing may be drawn where the platform's own UI sits, in any frame.

    The window drifts right across the clip, so the right margin is tightest in
    the first frame and the left margin in the last; both are checked. The source
    credit is long on purpose — an unwrapped one ran past the right margin in the
    first render of EP01's payoff chart.
    """
    v = PlatformSpec.load("vertical")
    w, h, safe = v.width // 2, v.height // 2, v.caption_safe_area
    spec = BAR.model_copy(update={"source_label": (
        "Stantec for the Panama Canal Authority (2018); Panama Canal Authority Annual "
        "Report FY2025; gCaptain; The Maritime Executive, 2026")})
    out = render_chart(spec, tmp_path / "v.mp4", duration_ms=2000, width=w, height=h,
                       safe_area=safe)
    bg = np.array([int(ChartStyle.background[i:i + 2], 16) for i in (1, 3, 5)])
    first, last = _frame(out, w, h, last=False), _frame(out, w, h, last=True)
    inset = 2    # chroma subsampling bleeds a pixel or so across a band edge

    def bare(region, where):
        assert np.abs(region - bg).max() <= 8, f"something was drawn in the {where} safe margin"

    for frame in (first, last):
        bare(frame[: int(safe["top"] * h) - inset], "top")
        bare(frame[h - int(safe["bottom"] * h) + inset:], "bottom")
    bare(first[:, w - int(safe["right"] * w) + inset:], "right")
    bare(last[:, : int(safe["left"] * w) - inset], "left")
    assert np.abs(last - bg).max() > 60, "the chart itself did not render"


def test_a_callout_never_sits_on_its_line_or_outside_the_chart():
    """On a falling curve, a label placed up-left of a late point lands on the line
    itself — which is what the first render of EP01's tariff curve did at 85 ft."""
    xs = [77 + i * 0.25 for i in range(41)]
    ys = [100 * 0.10 / (1 + math.exp(0.6 * (x - 82))) for x in xs]
    callouts = [{"x": 79.0, "text": "2023 floor · 8.6%"}, {"x": 82.0, "text": "82 ft · 5%"},
                {"x": 85.0, "text": "Normal pool · 1.4%"}]
    spec = ChartSpec(kind="line", title="t", x=xs, y=ys, unit="%", callouts=callouts, **SRC)
    f = charts._Frame(1920, 1080, drift=90, safe=PlatformSpec.load("youtube-long").caption_safe_area)
    fig = Figure(figsize=((f.canvas_w + 0.5) / charts.DPI, (f.height + 0.5) / charts.DPI),
                 dpi=charts.DPI)
    canvas = FigureCanvasAgg(fig)
    charts._line(fig, spec, ChartStyle(), f)(1.0)
    canvas.draw()
    renderer = canvas.get_renderer()
    ax = fig.axes[0]
    dense = np.linspace(xs[0], xs[-1], 3000)
    path = ax.transData.transform(np.column_stack([dense, np.interp(dense, xs, ys)]))
    frame = ax.get_window_extent(renderer)

    labels = [t for t in ax.texts if t.get_text() in {c["text"] for c in callouts}]
    assert len(labels) == 3
    for label in labels:
        box = label.get_window_extent(renderer)
        grazed = box.padded(f.px(4))
        on_line = ((path[:, 0] >= grazed.x0) & (path[:, 0] <= grazed.x1)
                   & (path[:, 1] >= grazed.y0) & (path[:, 1] <= grazed.y1))
        assert not on_line.any(), f"{label.get_text()!r} is drawn on top of its line"
        assert (frame.x0 <= box.x0 and box.x1 <= frame.x1
                and frame.y0 <= box.y0 and box.y1 <= frame.y1), \
            f"{label.get_text()!r} spills outside the chart"


def test_a_dollar_pair_is_never_parsed_as_mathtext(tmp_path):
    """Unescaped, the text between two '$' is TeX, and '\\bid' is an unknown symbol
    that raises at draw. A price pair in a title must render literally."""
    spec = ChartSpec(kind="stat", title=r"From $\bid to $5.3M", value_text="$5.3M", **SRC)
    render_chart(spec, tmp_path / "d.mp4", duration_ms=500, width=640, height=360)


def test_a_failed_encode_raises_and_leaves_no_clip_behind(tmp_path, monkeypatch):
    """A failing FFmpeg must raise with its own error, never leave a plausible file."""
    monkeypatch.setattr(charts, "FFMPEG", charts.FFMPEG + ["-no-such-option"])
    out = tmp_path / "c.mp4"
    with pytest.raises(RuntimeError, match="ffmpeg failed"):
        render_chart(STAT, out, duration_ms=1000, width=640, height=360)
    assert not out.exists()


def test_odd_dimensions_are_refused_before_rendering(tmp_path):
    with pytest.raises(ValueError, match="even dimensions"):
        render_chart(STAT, tmp_path / "o.mp4", duration_ms=500, width=641, height=360)


# ---- the spec -------------------------------------------------------------

@pytest.mark.parametrize("bad,why", [
    (dict(kind="bar", labels=["a", "b"], values=[1.0]), "one value per label"),
    (dict(kind="bar", labels=["a"], values=[1.0], highlight=3), "not a bar index"),
    (dict(kind="bar", labels=["a"], values=[1.0], display=["x", "y"]), "one string per bar"),
    (dict(kind="line", x=[1.0], y=[1.0]), "at least two points"),
    (dict(kind="line", x=[2.0, 1.0], y=[1.0, 2.0]), "strictly increase"),
    (dict(kind="line", x=[1.0, "b"], y=[1.0, 2.0]), "not a mix"),
    (dict(kind="line", x=[1.0, 2.0], y=[1.0, 2.0], callouts=[{"x": 9.0, "text": "t"}]),
     "outside the x range"),
    (dict(kind="line", x=["a", "b"], y=[1.0, 2.0], callouts=[{"x": "c", "text": "t"}]),
     "names no category"),
    (dict(kind="stat"), "needs value_text"),
])
def test_a_malformed_chart_is_refused(bad, why):
    with pytest.raises(ValidationError, match=why):
        ChartSpec(**SRC, **bad)


@pytest.mark.parametrize("ids", [[], [""]], ids=["no-ids", "empty-id"])
def test_a_chart_without_a_source_is_refused(ids):
    with pytest.raises(ValidationError):
        ChartSpec(kind="stat", value_text="82 FT", source_ids=ids, source_label="ACP")


@pytest.mark.parametrize("value,unit,expected", [
    (5_300_000, "$", "$5.3M"), (135_000, "$", "$135K"), (0.21, "$", "$0.21"),
    (27.0, "$", "$27"), (8.6, "%", "8.6%"), (82, "ft", "82 ft"), (1_500, "", "1,500"),
    (1_600_000_000, "$", "$1.6B"), (-2.5, "$", "-$2.5"), (0.0, "", "0"),
])
def test_numbers_are_formatted_for_broadcast(value, unit, expected):
    assert _fmt(value, unit) == expected
