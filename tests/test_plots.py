"""SVG plots are data-driven: change the arrays, change the rendered markup."""

from __future__ import annotations

import pytest

from app import plots


FREQ = [10.0, 100.0, 1e3, 1e4, 1e5]
GAIN = [20.0, 10.0, 0.0, -10.0, -20.0]
PHASE = [-10.0, -40.0, -90.0, -140.0, -170.0]


def test_minus_three_db_interpolates_between_samples():
    crossing = plots.minus_three_db(FREQ, GAIN)
    assert crossing == pytest.approx(3700.0)


def test_minus_three_db_returns_none_when_not_crossed():
    assert plots.minus_three_db(FREQ, [1.0] * len(FREQ)) is None


def test_phase_relation_detects_inversion_from_samples():
    time = list(range(20))
    vin = [1.0 if i % 4 < 2 else -1.0 for i in time]
    vout = [-v for v in vin]
    assert "inverted" in plots.phase_relation(vin, vout)


def test_bode_svg_contains_axes_and_data_points():
    svg = plots.bode_svg(FREQ, GAIN, PHASE)
    assert "Frequency (Hz, log scale)" in svg
    assert "|Gain| (dB)" in svg and "Phase (deg)" in svg
    assert "<polyline" in svg
    assert "10k" in svg or "1e+04" in svg


def test_bode_svg_changes_when_data_changes():
    first = plots.bode_svg(FREQ, GAIN, PHASE)
    second = plots.bode_svg(FREQ, [g + 7 for g in GAIN], PHASE)
    assert first != second


def test_waveform_svg_contains_both_legends_and_changes_with_data():
    time = [0.0, 0.1, 0.2, 0.3]
    first = plots.waveform_svg(time, [1.0, 0.0, -1.0, 0.0],
                               [-1.0, 0.0, 1.0, 0.0])
    second = plots.waveform_svg(time, [2.0, 0.0, -2.0, 0.0],
                                [-1.0, 0.0, 1.0, 0.0])
    assert "Time (ms)" in first
    assert "Vin (V)" in first and "Vout (V)" in first
    assert first != second
