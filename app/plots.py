"""Inline SVG plots drawn only from parsed ngspice arrays.

No plotting dependency and no JavaScript.  Every dynamic label is escaped and
every point comes from the parser in ``spice_engine.py``.
"""

from __future__ import annotations

import math
from html import escape

TEAL = "#0c8176"
ORANGE = "#c77a35"
AXIS = "#9cb2c2"
TEXT = "#486275"


def minus_three_db(frequency_hz: list[float], gain_db: list[float]) -> float | None:
    """Return the first −3 dB crossing below the midband reference.

    The reference is the largest measured gain in the sweep, not absolute
    0 dB.  When the target never crosses the trace, return ``None`` so the
    caller can say "not determined in sweep range" instead of inventing a
    number.
    """
    if len(gain_db) < 2:
        return None
    reference = max(gain_db)
    target = reference - 3.0
    for index in range(1, len(gain_db)):
        previous, current = gain_db[index - 1], gain_db[index]
        if (previous - target) * (current - target) <= 0:
            if current == previous:
                return frequency_hz[index]
            ratio = (target - previous) / (current - previous)
            lower = max(frequency_hz[index - 1], 1e-12)
            upper = max(frequency_hz[index], lower * 1.000001)
            return 10 ** (
                math.log10(lower) + ratio * (math.log10(upper) - math.log10(lower))
            )
    return None


def phase_relation(vin: list[float], vout: list[float]) -> str:
    """Classify the output phase from sampled waveforms, not from theory."""
    if len(vin) < 2 or len(vout) < 2:
        return "not determined"
    mean_in = sum(vin) / len(vin)
    mean_out = sum(vout) / len(vout)
    covariance = sum(
        (a - mean_in) * (b - mean_out) for a, b in zip(vin, vout)
    )
    var_in = sum((a - mean_in) ** 2 for a in vin)
    var_out = sum((b - mean_out) ** 2 for b in vout)
    denominator = math.sqrt(var_in * var_out)
    if denominator == 0:
        return "not determined"
    correlation = covariance / denominator
    if correlation <= -0.5:
        return f"inverted (~180°), correlation {correlation:.2f}"
    if correlation >= 0.5:
        return f"in-phase (~0°), correlation {correlation:.2f}"
    return f"unclear, correlation {correlation:.2f}"


def _scale(value: float, low: float, high: float, size: float) -> float:
    if high == low:
        return size / 2
    return (value - low) / (high - low) * size


def _svg_open(width: int, height: int, label: str) -> list[str]:
    return [
        f'<svg class="plot-svg" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="{escape(label)}" '
        f'style="width:100%;height:auto">',
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#f9fcfd" '
        f'stroke="#dce7ee"/>',
    ]


def _text(x: float, y: float, value: object, *, anchor: str = "start",
          size: int = 11, fill: str = TEXT) -> str:
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" '
        f'text-anchor="{anchor}">{escape(str(value))}</text>'
    )


def bode_svg(frequency_hz: list[float], gain_db: list[float],
             phase_deg: list[float], *, width: int = 760,
             height: int = 520) -> str:
    """Magnitude and phase panels from an ``.ac`` run."""
    lines = _svg_open(width, height, "Bode magnitude and phase from real .ac run")
    if not frequency_hz or not gain_db or not phase_deg:
        lines.append(_text(width / 2, height / 2, "No AC data", anchor="middle"))
        lines.append("</svg>")
        return "\n".join(lines)

    left, right, top, bottom = 64, 22, 30, 52
    gap = 28
    plot_width = width - left - right
    panel_height = (height - top - bottom - gap) // 2
    logs = [math.log10(max(f, 1e-12)) for f in frequency_hz]
    xmin, xmax = min(logs), max(logs)
    if xmax == xmin:
        xmax = xmin + 1.0

    def x_of(frequency: float) -> float:
        return left + (math.log10(max(frequency, 1e-12)) - xmin) / (xmax - xmin) * plot_width

    def y_of(value: float, low: float, high: float, panel_top: float) -> float:
        return panel_top + (1.0 - (value - low) / (high - low)) * panel_height

    for panel, (values, colour, label) in enumerate((
        (gain_db, TEAL, "|Gain| (dB)"),
        (phase_deg, ORANGE, "Phase (deg)"),
    )):
        panel_top = top + panel * (panel_height + gap)
        low, high = min(values), max(values)
        padding = max((high - low) * 0.1, 1.0)
        low, high = low - padding, high + padding

        lines.append(
            f'<rect x="{left}" y="{panel_top}" width="{plot_width}" '
            f'height="{panel_height}" fill="#ffffff" stroke="{AXIS}"/>'
        )
        for tick in range(5):
            fraction = tick / 4
            x_pos = left + fraction * plot_width
            frequency = 10 ** (xmin + fraction * (xmax - xmin))
            lines.append(
                f'<line x1="{x_pos:.1f}" y1="{panel_top}" x2="{x_pos:.1f}" '
                f'y2="{panel_top + panel_height}" stroke="#e4edf3"/>'
            )
            lines.append(
                _text(x_pos, panel_top + panel_height + 14,
                      f"{frequency:.3g}", anchor="middle", size=10)
            )
        for tick in range(1, 4):
            y_pos = panel_top + tick * panel_height / 4
            lines.append(
                f'<line x1="{left}" y1="{y_pos:.1f}" x2="{left + plot_width}" '
                f'y2="{y_pos:.1f}" stroke="#e4edf3"/>'
            )
            value = high - tick * (high - low) / 4
            lines.append(
                _text(left - 7, y_pos + 3, f"{value:.0f}", anchor="end", size=10)
            )

        if panel == 0:
            target = max(gain_db) - 3.0
            if low <= target <= high:
                y_ref = y_of(target, low, high, panel_top)
                lines.append(
                    f'<line x1="{left}" y1="{y_ref:.1f}" '
                    f'x2="{left + plot_width}" y2="{y_ref:.1f}" '
                    f'stroke="#a65a2c" stroke-width="1.2" stroke-dasharray="5 4"/>'
                )
                lines.append(
                    _text(left + plot_width - 4, y_ref - 5,
                          "−3 dB from midband", anchor="end", size=10,
                          fill="#a65a2c")
                )

        points = " ".join(
            f"{x_of(f):.1f},{y_of(v, low, high, panel_top):.1f}"
            for f, v in zip(frequency_hz, values)
        )
        lines.append(
            f'<polyline points="{points}" fill="none" stroke="{colour}" '
            f'stroke-width="2.2" stroke-linejoin="round"/>'
        )
        lines.append(_text(left + 8, panel_top + 14, label, size=12, fill=colour))

    lines.append(_text(left + plot_width / 2, height - 10,
                       "Frequency (Hz, log scale)", anchor="middle", size=12))
    lines.append("</svg>")
    return "\n".join(lines)


def waveform_svg(time_ms: list[float], vin: list[float], vout: list[float],
                 *, width: int = 760, height: int = 360) -> str:
    """Vin / Vout overlay from a ``.tran`` run."""
    lines = _svg_open(width, height, "Vin at v(base) and Vout at v(out) from real .tran run")
    if not time_ms or not vin or not vout:
        lines.append(_text(width / 2, height / 2, "No transient data",
                           anchor="middle"))
        lines.append("</svg>")
        return "\n".join(lines)

    left, right, top, bottom = 64, 22, 30, 52
    plot_width = width - left - right
    plot_height = height - top - bottom
    xmin, xmax = min(time_ms), max(time_ms)
    if xmax == xmin:
        xmax = xmin + 1.0
    low = min(min(vin), min(vout))
    high = max(max(vin), max(vout))
    padding = max((high - low) * 0.1, 0.01)
    low, high = low - padding, high + padding

    def x_of(value: float) -> float:
        return left + (value - xmin) / (xmax - xmin) * plot_width

    def y_of(value: float) -> float:
        return top + (1.0 - (value - low) / (high - low)) * plot_height

    lines.append(
        f'<rect x="{left}" y="{top}" width="{plot_width}" height="{plot_height}" '
        f'fill="#ffffff" stroke="{AXIS}"/>'
    )
    for tick in range(5):
        fraction = tick / 4
        x_pos = left + fraction * plot_width
        lines.append(
            f'<line x1="{x_pos:.1f}" y1="{top}" x2="{x_pos:.1f}" '
            f'y2="{top + plot_height}" stroke="#e4edf3"/>'
        )
        lines.append(
            _text(x_pos, top + plot_height + 14,
                  f"{xmin + fraction * (xmax - xmin):.2f}",
                  anchor="middle", size=10)
        )
    for tick in range(1, 4):
        y_pos = top + tick * plot_height / 4
        lines.append(
            f'<line x1="{left}" y1="{y_pos:.1f}" x2="{left + plot_width}" '
            f'y2="{y_pos:.1f}" stroke="#e4edf3"/>'
        )
        lines.append(
            _text(left - 7, y_pos + 3,
                  f"{high - tick * (high - low) / 4:.2f}",
                  anchor="end", size=10)
        )

    for values, colour in ((vin, TEAL), (vout, ORANGE)):
        points = " ".join(f"{x_of(t):.1f},{y_of(v):.1f}"
                          for t, v in zip(time_ms, values))
        lines.append(
            f'<polyline points="{points}" fill="none" stroke="{colour}" '
            f'stroke-width="2" stroke-linejoin="round"/>'
        )

    lines.append(_text(left + plot_width / 2, height - 10,
                       "Time (ms)", anchor="middle", size=12))
    lines.append(_text(left + 8, top + 14, "Vin = v(base) (V)", size=12, fill=TEAL))
    lines.append(_text(left + 150, top + 14, "Vout = v(out) (V)", size=12, fill=ORANGE))
    lines.append("</svg>")
    return "\n".join(lines)
