"""Tests for the ngspice adapter (no engine required for these checks)."""

from __future__ import annotations

from pathlib import Path

import pytest

from app import spice_engine as se

SAMPLES = Path(__file__).resolve().parents[1] / "docs" / "evidence" / "spice-sample"

# Test-only identifier.  It is NOT the instructor model and is never used to
# produce a reported circuit result; it only exercises netlist generation.
TEST_MODEL_LINE = ".model QTEST NPN(IS=1e-14 BF=100)"

BASE_VALUES = {
    "vcc": 12.0,
    "r1": 100e3,
    "r2": 22e3,
    "rc": 2.2e3,
    "re": 1e3,
    "rl": 10e3,
    "cin": 10e-6,
    "cout": 10e-6,
    "amplitude": 10e-3,
    "frequency": 1e3,
    "beta": 100.0,
    "vbe": 0.70,
}


def test_validate_spice_inputs_accepts_baseline():
    ok, messages = se.validate_spice_inputs({**BASE_VALUES, "analysis": "dc"})
    assert ok, messages


def test_validate_spice_inputs_rejects_re_zero():
    ok, messages = se.validate_spice_inputs(
        {**BASE_VALUES, "analysis": "dc", "re": 0.0}
    )
    assert not ok
    assert any("RE" in message for message in messages)


def test_validate_spice_inputs_rejects_unknown_analysis():
    ok, messages = se.validate_spice_inputs(
        {**BASE_VALUES, "analysis": "sweep"}
    )
    assert not ok
    assert any("Unknown analysis" in message for message in messages)


def test_validate_spice_inputs_rejects_non_finite_source():
    ok, messages = se.validate_spice_inputs(
        {**BASE_VALUES, "analysis": "tran", "frequency": float("nan")}
    )
    assert not ok
    assert any("Frequency" in message for message in messages)


def test_ngspice_number_uses_engineering_suffixes():
    assert se.ngspice_number(100e3) == "100k"
    assert se.ngspice_number(10e-6) == "10u"
    assert se.ngspice_number(12.0) == "12"


def test_build_netlist_contains_dc_directive_and_injected_model():
    netlist = se.build_netlist("dc", BASE_VALUES, model_line=TEST_MODEL_LINE)
    assert ".op" in netlist
    assert TEST_MODEL_LINE in netlist
    assert "Q1 collector base emitter QTEST" in netlist
    assert "VCC vcc 0 DC 12" in netlist
    assert "Vs vs 0 AC 10m SIN(0 10m 1k)" in netlist
    assert netlist.rstrip().endswith(".end")


def test_build_netlist_ac_and_tran_directives_are_different():
    ac = se.build_netlist("ac", BASE_VALUES, model_line=TEST_MODEL_LINE)
    tran = se.build_netlist("tran", BASE_VALUES, model_line=TEST_MODEL_LINE)
    assert ".ac dec 20 1 10meg" in ac
    assert ".op" not in ac
    assert ".tran " in tran
    assert ".ac " not in tran


def test_build_netlist_requires_a_configured_model(monkeypatch):
    monkeypatch.delenv(se.MODEL_ENV, raising=False)
    with pytest.raises(se.SpiceConfigError):
        se.build_netlist("dc", BASE_VALUES)


def test_build_netlist_rejects_invalid_values():
    with pytest.raises(se.SpiceValidationError):
        se.build_netlist("dc", {**BASE_VALUES, "re": 0.0},
                         model_line=TEST_MODEL_LINE)


def test_parse_raw_reads_real_ascii_sections():
    sections = se.parse_raw((SAMPLES / "parser_fixture.raw").read_text(encoding="utf-8"))
    names = [section.plotname for section in sections]
    assert names == ["AC Analysis", "Operating Point", "Transient Analysis"]
    assert sections[0].flags == "complex"
    assert sections[1].flags == "real"


def test_parse_op_reads_operating_point_from_real_run():
    raw = (SAMPLES / "parser_fixture.raw").read_text(encoding="utf-8")
    result = se.parse_op(raw)
    assert result["units"]["ic"] == "A"
    assert result["vce"] == pytest.approx(result["vc"] - result["ve"])
    assert result["ic"] > 0  # -i(vcc) leaves the positive supply terminal
    assert result["vb"] == result["vb"]  # finite


def test_parse_ac_returns_frequency_gain_and_phase_from_real_run():
    raw = (SAMPLES / "parser_fixture.raw").read_text(encoding="utf-8")
    result = se.parse_ac(raw)
    assert len(result["frequency_hz"]) == len(result["gain_db"])
    assert len(result["gain_db"]) == len(result["phase_deg"])
    assert result["units"]["gain_db"] == "dB"
    assert all(value == value for value in result["gain_db"])


def test_parse_tran_returns_time_and_waveforms_from_real_run():
    raw = (SAMPLES / "parser_fixture.raw").read_text(encoding="utf-8")
    result = se.parse_tran(raw)
    assert len(result["time_ms"]) == len(result["vin"]) == len(result["vout"])
    assert result["time_ms"][0] == 0.0
    assert result["time_ms"][-1] > result["time_ms"][0]
    assert result["units"]["time_ms"] == "ms"


def test_ensure_success_rejects_failed_run():
    failed = se.SpiceRun(1, "", "", "Simulation interrupted due to error", "", "tmp")
    with pytest.raises(se.SpiceEngineError):
        se.ensure_success(failed)
