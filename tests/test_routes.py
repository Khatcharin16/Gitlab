"""Tests for app.py — Flask routes, form handling, and error responses."""

from __future__ import annotations

import pytest

from app.app import app, validate_form


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_get_form(client):
    """GET / should render the form."""
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"BJT Common" in resp.data
    assert b"Calculate" in resp.data


def test_post_valid(client):
    """POST with valid inputs should show results."""
    resp = client.post("/", data=dict(
        vcc="12", r1="47000", r2="10000", rc="4700",
        re="1000", beta="150", vbe="0.7",
    ))
    assert resp.status_code == 200
    # Should contain results region and operating point
    assert b"active" in resp.data or b"Saturation" in resp.data


def test_post_invalid_vcc(client):
    """POST with VCC=0 should show validation errors."""
    resp = client.post("/", data=dict(
        vcc="0", r1="47000", r2="10000", rc="4700",
        re="1000", beta="150", vbe="0.7",
    ))
    assert resp.status_code == 200
    # Should re-render the form with error messages
    assert b"VCC must be greater than 0 V" in resp.data


def test_post_invalid_r1(client):
    """POST with R1=-1 should show validation errors."""
    resp = client.post("/", data=dict(
        vcc="12", r1="-1", r2="10000", rc="4700",
        re="1000", beta="150", vbe="0.7",
    ))
    assert resp.status_code == 200
    assert b"R1 must be greater than 0 ohm" in resp.data


def test_post_invalid_beta(client):
    """POST with beta=0 should show validation errors."""
    resp = client.post("/", data=dict(
        vcc="12", r1="47000", r2="10000", rc="4700",
        re="1000", beta="0", vbe="0.7",
    ))
    assert resp.status_code == 200
    assert b"beta must be between 1 and 2000" in resp.data


def test_post_invalid_vbe(client):
    """POST with VBE=1.5 should show validation errors."""
    resp = client.post("/", data=dict(
        vcc="12", r1="47000", r2="10000", rc="4700",
        re="1000", beta="150", vbe="1.5",
    ))
    assert resp.status_code == 200
    assert b"VBE must be 0.4-1.0 V" in resp.data


def test_validate_form_ok():
    """validate_form should return ok=True for valid inputs."""
    ok, msgs = validate_form(12.0, 47000.0, 10000.0, 4700.0, 1000.0, 150.0, 0.7)
    assert ok is True
    assert msgs == []


def test_validate_form_bad_vbe():
    """validate_form should reject VBE out of range."""
    ok, msgs = validate_form(12.0, 47000.0, 10000.0, 4700.0, 1000.0, 150.0, 2.0)
    assert ok is False
    assert any("VBE" in m for m in msgs)