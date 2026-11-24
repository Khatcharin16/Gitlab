"""Flask web app for ENG29 2121 BJT Common-Emitter DC Bias calculator."""

from __future__ import annotations

import os
from pathlib import Path

from flask import Flask, render_template, request

from app import plots, spice_engine as se
from app.bjt import (
    BIAS_MODES,
    MODE_LABELS,
    compare_ic_vce,
    is_finite,
    solve_bias,
    validate_bias,
)
from app.independent import nodal_solve

app = Flask(__name__)
app.config["SECRET_KEY"] = "eng29-lab-secret"


# ---------------------------------------------------------------------------
# Units
# ---------------------------------------------------------------------------
# Each input maps its display unit to a multiplier into SI base units
# (volts for voltages, ohms for resistances, dimensionless for beta).
UNIT_MAP: dict[str, dict[str, float]] = {
    "vcc": {"V": 1.0, "mV": 1e-3},
    "r1": {"ohm": 1.0, "k": 1e3, "M": 1e6},
    "r2": {"ohm": 1.0, "k": 1e3, "M": 1e6},
    "rb": {"ohm": 1.0, "k": 1e3, "M": 1e6},
    "rc": {"ohm": 1.0, "k": 1e3, "M": 1e6},
    "re": {"ohm": 1.0, "k": 1e3, "M": 1e6},
    "beta": {"-": 1.0},
    "vbe": {"V": 1.0, "mV": 1e-3},
}

# Values shown when the page is first opened (in the displayed units).
DEFAULT_RAW: dict[str, str] = {
    "vcc": "12.0",
    "r1": "100",
    "r2": "22",
    "rb": "1",
    "rc": "2.2",
    "re": "1.0",
    "beta": "100",
    "vbe": "0.70",
}

DEFAULT_UNITS: dict[str, str] = {
    "vcc": "V",
    "r1": "k",
    "r2": "k",
    "rb": "M",
    "rc": "k",
    "re": "k",
    "beta": "-",
    "vbe": "V",
}

# Used when a POST omits a unit field (e.g. the pytest client): treat the
# number as already being in base units, so old-style requests keep working.
FALLBACK_UNITS: dict[str, str] = {
    "vcc": "V",
    "r1": "ohm",
    "r2": "ohm",
    "rb": "ohm",
    "rc": "ohm",
    "re": "ohm",
    "beta": "-",
    "vbe": "V",
}

# Extra fields for the Lab 04 CE amplifier.  Lab 03's UNIT_MAP/parse_form are
# intentionally untouched; the simulator parser layers these on top.
SPICE_UNIT_MAP: dict[str, dict[str, float]] = {
    "rl": {"ohm": 1.0, "k": 1e3, "M": 1e6},
    "cin": {"F": 1.0, "m": 1e-3, "u": 1e-6, "n": 1e-9, "p": 1e-12},
    "cout": {"F": 1.0, "m": 1e-3, "u": 1e-6, "n": 1e-9, "p": 1e-12},
    "amplitude": {"V": 1.0, "mV": 1e-3},
    "frequency": {"Hz": 1.0, "kHz": 1e3, "MHz": 1e6},
}

SPICE_DEFAULT_RAW: dict[str, str] = {
    "rl": "10",
    "cin": "10",
    "cout": "10",
    "amplitude": "10",
    "frequency": "1",
}

SPICE_DEFAULT_UNITS: dict[str, str] = {
    "rl": "k",
    "cin": "u",
    "cout": "u",
    "amplitude": "mV",
    "frequency": "kHz",
}

SPICE_FALLBACK_UNITS: dict[str, str] = {
    "rl": "ohm",
    "cin": "F",
    "cout": "F",
    "amplitude": "V",
    "frequency": "Hz",
}

ANALYSIS_LABELS = {"dc": "DC operating point (.op)",
                   "ac": "AC frequency response (.ac)",
                   "tran": "Transient waveforms (.tran)"}


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------
def fmt_current(a: float) -> str:
    """Auto-scale a current to mA / µA / nA (sign preserved)."""
    magnitude = abs(a)
    if magnitude >= 1e-3:
        return f"{a * 1e3:.2f} mA"
    if magnitude >= 1e-6:
        return f"{a * 1e6:.2f} µA"
    return f"{a * 1e9:.2f} nA"


def fmt_collector_current(a: float) -> str:
    """Show IC / IE in mA for the usual bias range, keeping small values clear."""
    if abs(a) >= 1e-4:
        return f"{a * 1e3:.2f} mA"
    return fmt_current(a)


def fmt_voltage(v: float, digits: int = 2) -> str:
    return f"{v:.{digits}f} V"


def fmt_resistor(v: float) -> str:
    """Human-readable resistance: 100 kΩ, 2.2 kΩ, 1.0 kΩ, 470 Ω."""
    if v >= 1e6:
        x, unit = v / 1e6, "MΩ"
    elif v >= 1e3:
        x, unit = v / 1e3, "kΩ"
    else:
        x, unit = v, "Ω"
    text = f"{x:.1f}" if x < 10 else f"{x:.0f}"
    return f"{text} {unit}"


# ---------------------------------------------------------------------------
# Form defaults and parsing
# ---------------------------------------------------------------------------
def default_values(mode: str = "divider") -> dict[str, float]:
    """Default circuit in SI base units for the selected mode."""
    values = {
        "vcc": 12.0,
        "r1": 100e3,
        "r2": 22e3,
        "rb": 1.0e6,
        "rc": 2.2e3,
        "re": 0.0 if mode == "fixed" else 1.0e3,
        "beta": 100.0,
        "vbe": 0.70,
    }
    return values


def default_form(mode: str = "divider") -> dict[str, str]:
    """Default form contents, including the *_unit keys."""
    form = dict(DEFAULT_RAW)
    if mode == "divider":
        form["re"] = "1.0"
    form.update({f"{key}_unit": unit for key, unit in DEFAULT_UNITS.items()})
    return form


def parse_mode(raw: str | None, default: str = "divider") -> str:
    """Return the requested mode, or ``default`` when it is missing."""
    if raw is None or not str(raw).strip():
        return default
    return str(raw).strip().lower()


def mode_label(mode: str) -> str:
    """Human-readable mode name, including unknown values."""
    return MODE_LABELS.get(mode, f"Unknown mode '{mode}'")


def parse_form(form) -> tuple[dict[str, float | None], dict[str, str]]:
    """Parse a submitted form into SI values and display values.

    Returns ``(values, display)`` where ``values`` holds floats (or ``None``
    for unparseable fields) in SI units and ``display`` holds the raw strings
    plus chosen units so the form can be re-rendered unchanged.
    """
    values: dict[str, float | None] = {}
    display: dict[str, str] = {}

    for key, units in UNIT_MAP.items():
        raw = (form.get(key) or "").strip()
        unit = form.get(f"{key}_unit", FALLBACK_UNITS[key])
        if unit not in units:
            unit = FALLBACK_UNITS[key]

        display[key] = raw
        display[f"{key}_unit"] = unit

        try:
            values[key] = float(raw) * units[unit]
        except (TypeError, ValueError):
            values[key] = None

    return values, display


def parse_spice_form(form) -> tuple[dict[str, float | None], dict[str, str]]:
    """Parse Lab 04 fields; reuse Lab 03's parser for the shared components."""
    values, display = parse_form(form)
    for key, units in SPICE_UNIT_MAP.items():
        raw = (form.get(key) or "").strip()
        unit = form.get(f"{key}_unit", SPICE_FALLBACK_UNITS[key])
        if unit not in units:
            unit = SPICE_FALLBACK_UNITS[key]
        display[key] = raw
        display[f"{key}_unit"] = unit
        try:
            values[key] = float(raw) * units[unit]
        except (TypeError, ValueError):
            values[key] = None
    return values, display


def default_spice_form() -> dict[str, str]:
    """Form contents for the reference CE circuit (10 mV, 1 kHz source)."""
    form = default_form("divider")
    form.update(SPICE_DEFAULT_RAW)
    form.update({f"{key}_unit": unit for key, unit in SPICE_DEFAULT_UNITS.items()})
    return form


def parse_analysis(raw: str | None) -> str:
    return str(raw or "").strip().lower()


def build_circuit(mode: str, values: dict) -> dict[str, str]:
    """Labels shown next to the schematic (falls back to defaults)."""
    base = default_values(mode)
    v = {key: values[key] if values.get(key) is not None else base[key]
         for key in base}
    circuit = {
        "vcc": f"{v['vcc']:g} V",
        "rc": fmt_resistor(v["rc"]),
        "beta": f"{v['beta']:g}",
        "mode_label": mode_label(mode),
    }
    if mode == "divider":
        circuit["r1"] = fmt_resistor(v["r1"])
        circuit["r2"] = fmt_resistor(v["r2"])
    if mode in ("fixed", "emitter"):
        circuit["rb"] = fmt_resistor(v["rb"])
    if mode in ("divider", "emitter"):
        circuit["re"] = fmt_resistor(v["re"])
    return circuit


# ---------------------------------------------------------------------------
# Result model
# ---------------------------------------------------------------------------
def build_result(mode: str, values: dict) -> dict[str, str]:
    """Run the selected model and build the template's result context."""
    op = solve_bias(mode, values)

    comparison = None
    if mode == "divider" and op.region == "active":
        ic_node, vce_node = nodal_solve(
            values["vcc"], values["r1"], values["r2"], values["rc"],
            values["re"], values["beta"], values["vbe"],
        )
        comparison = compare_ic_vce(op.ic, op.vce, ic_node, vce_node)

    if op.region == "cutoff":
        status_class = "warn"
        status_title = "Cutoff model warning"
        status_text = op.warning or "The transistor would be cut off."
    elif op.region == "saturation":
        status_class = "warn"
        status_title = "Saturation model warning"
        status_text = op.warning or "The transistor would be saturated."
    else:
        status_class = "ok"
        status_title = "Active region approximation OK"
        status_text = (
            f"V<sub>CE</sub> = {op.vce:.2f} V &gt; 0.2 V "
            "(transistor in active region)"
        )

    result = {
        "vb": fmt_voltage(op.vb),
        "ve": fmt_voltage(op.ve),
        "vc": fmt_voltage(op.vc),
        "vce": fmt_voltage(op.vce),
        "ib": fmt_current(op.ib),
        "ic": fmt_collector_current(op.ic),
        "ie": fmt_collector_current(op.ie),
        "vbe": fmt_voltage(op.vbe),
        "vbc": fmt_voltage(op.vbc),
        "region": op.region,
        "mode": mode,
        "mode_label": mode_label(mode),
        "status_class": status_class,
        "status_title": status_title,
        "status_text": status_text,
        "show_check": comparison is not None,
    }
    if comparison is not None:
        result.update({
            "match": comparison["match"],
            "ic_delta": comparison["ic_delta"],
            "vce_delta": comparison["vce_delta"],
        })
    return result


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
def render_page(mode: str, form_values: dict, values: dict,
                result: dict | None, error_messages: list[str],
                status: int = 200):
    """Render the dashboard with mode-aware labels."""
    return render_template(
        "index.html",
        mode=mode,
        mode_label=mode_label(mode),
        result=result,
        form_values=form_values,
        circuit=build_circuit(mode, values),
        error_messages=error_messages,
    ), status


@app.get("/")
def index():
    """Show the default worked example for the requested mode."""
    mode = parse_mode(request.args.get("mode"))
    values = default_values(mode)
    if mode not in BIAS_MODES:
        message = (
            f"Unknown bias mode '{mode}'. Use divider, fixed, or emitter."
        )
        return render_page(mode, default_form("divider"), values, None,
                           [message], 400)
    return render_page(mode, default_form(mode), values,
                       build_result(mode, values), [])


@app.post("/")
def compute():
    """Accept the form, compute the selected model, render the dashboard."""
    mode = parse_mode(request.form.get("mode"))
    values, display = parse_form(request.form)

    if mode not in BIAS_MODES:
        message = (
            f"Unknown bias mode '{mode}'. Use divider, fixed, or emitter."
        )
        return render_page(mode, display, values, None, [message], 400)

    ok, messages = validate_bias(mode, values)
    if not ok:
        return render_page(mode, display, values, None, messages)

    return render_page(mode, display, values, build_result(mode, values), [])


# ---------------------------------------------------------------------------
# Lab 04 — real ngspice simulator (separate page; Lab 03 routes untouched)
# ---------------------------------------------------------------------------
def model_source() -> str:
    """Label the model's provenance (e.g. 'TEST ONLY - not instructor verified')."""
    return os.environ.get("NGSPICE_MODEL_SOURCE", "NGSPICE_MODEL_LINE").strip() \
        or "NGSPICE_MODEL_LINE"


def spice_status() -> dict[str, str]:
    """Report readiness from configuration without ever inventing a result."""
    info = {
        "engine_ready": "no", "engine": "not configured",
        "model_ready": "no", "model": "not configured", "message": "",
        "model_source": model_source(),
    }
    try:
        banner = se.check_engine()
        info["engine_ready"] = "yes"
        info["engine"] = next(
            (line.strip() for line in banner.splitlines() if "ngspice-" in line.lower()),
            banner.splitlines()[0].strip() if banner.splitlines() else "ngspice",
        )
    except se.SpiceError as exc:
        info["message"] = f"Engine: {exc}"
    try:
        info["model"] = se.model_name_from_line(se.get_model_line())
        info["model_ready"] = "yes"
    except se.SpiceError as exc:
        info["message"] = f"{info['message']} Model: {exc}".strip()
    return info


def render_simulate(analysis: str, form_values: dict, result: dict | None,
                    all_results: dict[str, dict] | None,
                    plot_by_mode: dict[str, str] | None,
                    error_messages: list[str],
                    status: int = 200):
    """Render the simulator page.  Failures never receive a result or plot."""
    return render_template(
        "simulate.html",
        analysis=analysis,
        analysis_label=ANALYSIS_LABELS.get(analysis, f"Unknown '{analysis}'"),
        form_values=form_values,
        result=result,
        results=all_results,
        plots=plot_by_mode,
        error_messages=error_messages,
        status=spice_status(),
    ), status


def _analyse(analysis: str, banner: str, model_line: str, values: dict) -> tuple[dict, str]:
    """Execute one real batch run and build the template context from it."""
    netlist = se.build_netlist(analysis, values, model_line=model_line)
    run = se.run_ngspice(analysis, netlist)
    se.ensure_success(run)

    directive = next(
        (line.strip() for line in netlist.splitlines()
         if line.startswith(".") and not line.lower().startswith((".model", ".end"))),
        "none",
    )
    provenance = {
        "engine": next(
            (line.strip() for line in banner.splitlines() if "ngspice-" in line.lower()),
            "ngspice",
        ),
        "model_name": se.model_name_from_line(model_line),
        "model_line": model_line,
        "model_source": model_source(),
        "directive": directive,
        "run_id": Path(run.workdir).name,
        "workdir": run.workdir,
        "returncode": run.returncode,
        "raw_bytes": len(run.raw),
        "netlist": netlist,
        "log_excerpt": "\n".join(run.log.splitlines()[-25:]),
    }
    rows: list[dict[str, str]] = []
    analytical: dict[str, str] | None = None
    plot = ""

    if analysis == "dc":
        dc = se.parse_op(run.raw)
        rows = [
            {"label": "V<sub>B</sub>", "value": fmt_voltage(dc["vb"])},
            {"label": "V<sub>E</sub>", "value": fmt_voltage(dc["ve"])},
            {"label": "V<sub>C</sub>", "value": fmt_voltage(dc["vc"])},
            {"label": "V<sub>CE</sub>", "value": fmt_voltage(dc["vce"])},
            {"label": "I<sub>C</sub>", "value": fmt_collector_current(dc["ic"])},
        ]
        op = solve_bias("divider", values)
        analytical = {
            "ic": fmt_collector_current(op.ic),
            "vce": fmt_voltage(op.vce),
            "note": "Lab 3 Thévenin approximation — separate model, not SPICE",
        }
    elif analysis == "ac":
        ac = se.parse_ac(run.raw)
        crossing = plots.minus_three_db(ac["frequency_hz"], ac["gain_db"])
        rows = [
            {"label": "Sweep points", "value": str(len(ac["frequency_hz"]))},
            {"label": "Frequency range", "value": (
                f"{ac['frequency_hz'][0]:.3g}–{ac['frequency_hz'][-1]:.3g} Hz")},
            {"label": "Gain range", "value": (
                f"{min(ac['gain_db']):.2f} to {max(ac['gain_db']):.2f} dB")},
            {"label": "Gain at first point", "value": (
                f"{ac['gain_db'][0]:.2f} dB")},
            {"label": "Phase at first point", "value": (
                f"{ac['phase_deg'][0]:.1f} deg")},
            {"label": "−3 dB frequency", "value": (
                f"{crossing:.0f} Hz" if crossing is not None
                else "not determined in sweep range")},
        ]
        plot = plots.bode_svg(ac["frequency_hz"], ac["gain_db"], ac["phase_deg"])
    else:
        tran = se.parse_tran(run.raw)
        rows = [
            {"label": "Sample points", "value": str(len(tran["time_ms"]))},
            {"label": "Time window", "value": (
                f"{tran['time_ms'][0]:.3f}–{tran['time_ms'][-1]:.3f} ms")},
            {"label": "V<sub>in</sub> peak-to-peak", "value": (
                f"{max(tran['vin']) - min(tran['vin']):.3f} V")},
            {"label": "V<sub>out</sub> peak-to-peak", "value": (
                f"{max(tran['vout']) - min(tran['vout']):.3f} V")},
            {"label": "Phase (from samples)", "value": (
                plots.phase_relation(tran["vin"], tran["vout"]))},
        ]
        plot = plots.waveform_svg(tran["time_ms"], tran["vin"], tran["vout"])

    result = {
        "analysis": analysis,
        "analysis_label": ANALYSIS_LABELS[analysis],
        "rows": rows,
        "analytical": analytical,
        "provenance": provenance,
    }
    return result, plot


def _run_spice(analysis: str, values: dict) -> tuple[dict, dict[str, dict], dict[str, str]]:
    """Run all three real analyses so both plots and all result cards are real."""
    banner = se.check_engine()
    model_line = se.get_model_line()
    results: dict[str, dict] = {}
    plot_by_mode: dict[str, str] = {}
    for mode in ("dc", "ac", "tran"):
        results[mode], plot_by_mode[mode] = _analyse(mode, banner, model_line, values)
    return results[analysis], results, plot_by_mode


@app.get("/simulate")
def simulate_page():
    """Show the CE amplifier form with engine/model status, but no results."""
    return render_simulate("dc", default_spice_form(), None, None, None, [])


@app.post("/simulate")
def simulate_run():
    """Validate, run ngspice, render real results — or a clean error panel."""
    analysis = parse_analysis(request.form.get("analysis"))
    values, display = parse_spice_form(request.form)

    if analysis not in se.ANALYSIS_MODES:
        return render_simulate(
            analysis, display, None, None, None,
            [f"Unknown analysis '{analysis}'. Use dc, ac, or tran."], 400,
        )

    ok, messages = se.validate_spice_inputs({**values, "analysis": analysis})
    if not ok:
        return render_simulate(analysis, display, None, None, None, messages, 400)

    try:
        selected, results, plot_by_mode = _run_spice(analysis, values)
    except se.SpiceValidationError as exc:
        return render_simulate(analysis, display, None, None, None, [str(exc)], 400)
    except se.SpiceError as exc:
        return render_simulate(analysis, display, None, None, None, [str(exc)], 502)

    return render_simulate(analysis, display, selected, results, plot_by_mode, [])


# ---------------------------------------------------------------------------
# Validation helper
# ---------------------------------------------------------------------------
def _valid_number(value) -> bool:
    return value is not None and is_finite(value)


def validate_form(vcc, r1, r2, rc, re, beta, vbe) -> tuple[bool, list[str]]:
    """Validate SI values. Returns (ok, messages)."""
    msgs: list[str] = []

    if not _valid_number(vcc):
        msgs.append("VCC must be a valid number")
    elif vcc <= 0:
        msgs.append("VCC must be greater than 0 V")

    if not _valid_number(r1):
        msgs.append("R1 must be a valid number")
    elif r1 <= 0:
        msgs.append("R1 must be greater than 0 ohm")

    if not _valid_number(r2):
        msgs.append("R2 must be a valid number")
    elif r2 <= 0:
        msgs.append("R2 must be greater than 0 ohm")

    if not _valid_number(rc):
        msgs.append("RC must be a valid number")
    elif rc <= 0:
        msgs.append("RC must be greater than 0 ohm")

    if not _valid_number(re):
        msgs.append("RE must be a valid number")
    elif re < 0:
        msgs.append("RE must be greater than or equal to 0 ohm")

    if not _valid_number(beta):
        msgs.append("beta must be a valid number")
    elif beta < 1 or beta > 2000:
        msgs.append("beta must be between 1 and 2000")

    if not _valid_number(vbe):
        msgs.append("VBE must be a valid number")
    elif vbe < 0.4 or vbe > 1.0:
        msgs.append("VBE must be 0.4-1.0 V")

    return len(msgs) == 0, msgs


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/healthz")
def health():
    return "ok", 200


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
