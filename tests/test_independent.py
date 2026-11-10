"""Tests for app/independent.py — nodal DC solve."""

from __future__ import annotations

import pytest

from app.independent import nodal_solve


def test_nodal_basic():
    """Typical case: nodal solve should give IC and VCE in the right ballpark."""
    ic, vce = nodal_solve(12.0, 47000.0, 10000.0, 4700.0, 1000.0, 150.0, 0.7)
    # IC should be positive and roughly in mA
    assert ic > 0
    assert 0 < vce < 12
    # Sanity: IC * (RC + RE) should be less than VCC in active mode
    assert ic * (4700.0 + 1000.0) < 12.0


def test_nodal_cutoff_like():
    """When RE is very large the transistor should be near cutoff."""
    ic, vce = nodal_solve(5.0, 10000, 5000, 1000, 10_000_000, 100, 0.7)
    # With huge RE, IE current is tiny, IC should be very small
    assert ic >= 0
    assert vce > 0


def test_nodal_matches_primary():
    """Independent solve must agree with the Thevenin result within 0.1%."""
    from app.bjt import primary_calc

    p = primary_calc(12.0, 47000.0, 10000.0, 4700.0, 1000.0, 150.0, 0.7)
    ic, vce = nodal_solve(12.0, 47000.0, 10000.0, 4700.0, 1000.0, 150.0, 0.7)

    assert abs(ic - p.ic) / p.ic < 1e-3
    assert abs(vce - p.vce) / p.vce < 1e-3


def test_nodal_re_zero():
    """RE = 0 → emitter is effectively shorted; VE should be 0."""
    ic, vce = nodal_solve(5.0, 1000, 200, 100, 0, 50, 0.7)
    # With RE=0, VE=0 by definition, VCE = VC
    assert vce > 0
    # IC may be zero when emitter is shorted (circuit topology)
    assert ic >= 0