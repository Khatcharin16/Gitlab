"""Route tests for the Lab 04 simulator.  The adapter is stubbed at its boundary."""

from __future__ import annotations

from pathlib import Path

import pytest

import app.app as app_module
from app import spice_engine as se

SAMPLES = Path(__file__).resolve().parents[1] / "docs" / "evidence" / "spice-sample"
RAW = (SAMPLES / "parser_fixture.raw").read_text(encoding="utf-8")
MODEL_LINE = ".model QTEST NPN(IS=1e-14 BF=100)"  # test-only, not an instructor model


@pytest.fixture
def client():
    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as client:
        yield client


@pytest.fixture
def fake_engine(monkeypatch):
    """Patch only external boundaries; netlist/parser code stays real."""
    monkeypatch.setattr(se, "check_engine",
                        lambda: "** ngspice-47 : Circuit level simulation program")
    monkeypatch.setattr(se, "get_model_line", lambda: MODEL_LINE)
    monkeypatch.setattr(
        se, "run_ngspice",
        lambda analysis, netlist: se.SpiceRun(0, "", "", "run log", RAW, "tmp-fake-run"),
    )


BASE_FORM = {
    "analysis": "dc",
    "vcc": "12", "vcc_unit": "V",
    "r1": "100", "r1_unit": "k",
    "r2": "22", "r2_unit": "k",
    "rc": "2.2", "rc_unit": "k",
    "re": "1", "re_unit": "k",
    "rl": "10", "rl_unit": "k",
    "cin": "10", "cin_unit": "u",
    "cout": "10", "cout_unit": "u",
    "amplitude": "10", "amplitude_unit": "mV",
    "frequency": "1", "frequency_unit": "kHz",
    "beta": "100", "beta_unit": "-",
    "vbe": "0.70", "vbe_unit": "V",
}


def test_get_simulate_shows_status_but_no_results(client, fake_engine):
    resp = client.get("/simulate")
    assert resp.status_code == 200
    assert b"ngspice-47" in resp.data or b"yes" in resp.data
    assert b"SPICE results" in resp.data
    assert b"plot-svg" not in resp.data
    assert b"Run simulation" in resp.data


def test_post_dc_success_shows_spice_and_analytical_separately(client, fake_engine):
    resp = client.post("/simulate", data=BASE_FORM)
    assert resp.status_code == 200
    assert b"SPICE results" in resp.data
    assert b".op completed" in resp.data
    assert b"QTEST" in resp.data
    assert b"tmp-fake-run" in resp.data
    assert b"Analytical reference" in resp.data
    assert b"circuit.cir" in resp.data


def test_post_re_zero_is_rejected_without_stale_result(client, fake_engine):
    resp = client.post("/simulate", data={**BASE_FORM, "re": "0"})
    assert resp.status_code == 400
    assert b"RE" in resp.data
    assert b".op completed" not in resp.data
    assert b"plot-svg" not in resp.data


def test_engine_missing_is_an_error_not_success(client, monkeypatch, fake_engine):
    monkeypatch.setattr(se, "check_engine",
                        lambda: (_ for _ in ()).throw(
                            se.SpiceEngineError("ngspice not found")))
    resp = client.post("/simulate", data=BASE_FORM)
    assert resp.status_code == 502
    assert b"ngspice not found" in resp.data
    assert b"plot-svg" not in resp.data
    assert b".op completed" not in resp.data


def test_parse_failure_is_an_error_not_success(client, monkeypatch, fake_engine):
    monkeypatch.setattr(se, "parse_op",
                        lambda raw: (_ for _ in ()).throw(
                            se.SpiceParseError("incomplete raw file")))
    resp = client.post("/simulate", data=BASE_FORM)
    assert resp.status_code == 502
    assert b"incomplete raw file" in resp.data
    assert b"plot-svg" not in resp.data


def test_ac_post_renders_bode_svg_from_sample(client, fake_engine):
    resp = client.post("/simulate", data={**BASE_FORM, "analysis": "ac"})
    assert resp.status_code == 200
    assert b"Frequency (Hz, log scale)" in resp.data
    assert b"Gain" in resp.data and b"Phase" in resp.data
    assert b"plot-svg" in resp.data


def test_tran_post_renders_waveform_svg_from_sample(client, fake_engine):
    resp = client.post("/simulate", data={**BASE_FORM, "analysis": "tran"})
    assert resp.status_code == 200
    assert b"Time (ms)" in resp.data
    assert b"Vin = v(base) (V)" in resp.data and b"Vout = v(out) (V)" in resp.data
    assert b"plot-svg" in resp.data


def test_failed_post_after_success_does_not_keep_old_plot(client, fake_engine):
    assert b"plot-svg" in client.post(
        "/simulate", data={**BASE_FORM, "analysis": "ac"}).data
    failed = client.post("/simulate", data={**BASE_FORM, "analysis": "ac", "re": "0"})
    assert failed.status_code == 400
    assert b"plot-svg" not in failed.data


def test_lab04_panels_and_selected_mode_dispatch(client, fake_engine):
    """One submit runs only the selected analysis; the other cards stay empty."""
    resp = client.post("/simulate", data=BASE_FORM)
    assert resp.status_code == 200
    # Parameters, circuit reference, run control, plots and results now sit in
    # five clearly separated panels instead of three equal-weight cards.
    for heading in (b"Parameters", b"Circuit reference", b"Run control",
                    b"Simulation plots", b"Engineering results"):
        assert heading in resp.data
    assert b"Bode response" in resp.data
    assert b"Input / Output waveforms" in resp.data
    assert resp.data.count(b'class="plot-svg"') == 0  # DC has no time/frequency plot
    for label in (b"DC Operating Point", b"AC Frequency Response",
                  b"Transient Response"):
        assert label in resp.data
    assert b"Not run in this mode" in resp.data
    assert b"Success" in resp.data and b".op completed (1/1)" in resp.data

    ac = client.post("/simulate", data={**BASE_FORM, "analysis": "ac"})
    assert ac.data.count(b'class="plot-svg"') == 1
    assert b"Not run in this mode" in ac.data
    assert b"Success" in ac.data and b".ac dec 20 1 10meg completed (1/1)" in ac.data

    tran = client.post("/simulate", data={**BASE_FORM, "analysis": "tran"})
    assert tran.data.count(b'class="plot-svg"') == 1
    assert b"Time (ms)" in tran.data
