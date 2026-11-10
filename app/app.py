"""Flask web app for ENG29 2121 BJT Common-Emitter DC Bias calculator."""

from __future__ import annotations

from flask import Flask, render_template, request

from app.bjt import primary_calc, compare_ic_vce, is_finite
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
    "rc": "2.2",
    "re": "1.0",
    "beta": "100",
    "vbe": "0.70",
}

DEFAULT_UNITS: dict[str, str] = {
    "vcc": "V",
    "r1": "k",
    "r2": "k",
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
    "rc": "ohm",
    "re": "ohm",
    "beta": "-",
    "vbe": "V",
}


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------
def fmt_current(a: float) -> str:
    """Auto-scale a current to mA / µA / nA."""
    if a >= 1e-3:
        return f"{a * 1e3:.2f} mA"
    if a >= 1e-6:
        return f"{a * 1e6:.2f} µA"
    return f"{a * 1e9:.2f} nA"


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
def default_values() -> dict[str, float]:
    """Default circuit in SI base units."""
    return {
        "vcc": 12.0,
        "r1": 100e3,
        "r2": 22e3,
        "rc": 2.2e3,
        "re": 1.0e3,
        "beta": 100.0,
        "vbe": 0.70,
    }


def default_form() -> dict[str, str]:
    """Default form contents, including the *_unit keys."""
    form = dict(DEFAULT_RAW)
    form.update({f"{key}_unit": unit for key, unit in DEFAULT_UNITS.items()})
    return form


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


def build_circuit(values: dict) -> dict[str, str]:
    """Labels shown next to the schematic (falls back to defaults)."""
    base = default_values()
    v = {key: values[key] if values.get(key) is not None else base[key]
         for key in base}
    return {
        "vcc": f"{v['vcc']:g} V",
        "r1": fmt_resistor(v["r1"]),
        "r2": fmt_resistor(v["r2"]),
        "rc": fmt_resistor(v["rc"]),
        "re": fmt_resistor(v["re"]),
        "beta": f"{v['beta']:g}",
    }


# ---------------------------------------------------------------------------
# Result model
# ---------------------------------------------------------------------------
def build_result(values: dict) -> dict[str, str]:
    """Run both calculations and build the template's result context."""
    primary = primary_calc(
        values["vcc"], values["r1"], values["r2"], values["rc"],
        values["re"], values["beta"], values["vbe"],
    )
    ic_node, vce_node = nodal_solve(
        values["vcc"], values["r1"], values["r2"], values["rc"],
        values["re"], values["beta"], values["vbe"],
    )
    comparison = compare_ic_vce(primary.ic, primary.vce, ic_node, vce_node)

    if primary.region == "cutoff":
        status_class = "bad"
        status_title = "Cutoff region"
        status_text = (
            "V<sub>BB</sub> ≤ V<sub>BE</sub> — no collector current flows."
        )
    elif primary.region == "saturation":
        status_class = "bad"
        status_title = "Saturation region"
        status_text = (
            "V<sub>CE</sub> is clamped near 0.2 V — transistor is fully on."
        )
    elif primary.warning:
        status_class = "warn"
        status_title = "Near saturation warning"
        status_text = (
            f"V<sub>CE</sub> = {primary.vce:.2f} V &lt; 1.0 V — check the design."
        )
    else:
        status_class = "ok"
        status_title = "Active region approximation OK"
        status_text = (
            f"V<sub>CE</sub> = {primary.vce:.2f} V &gt; 0.2 V "
            "(transistor in active region)"
        )

    return {
        "vb": fmt_voltage(primary.vb),
        "ve": fmt_voltage(primary.ve),
        "vc": fmt_voltage(primary.vc),
        "vce": fmt_voltage(primary.vce),
        "ib": fmt_current(primary.ib),
        "ic": fmt_current(primary.ic),
        "ie": fmt_current(primary.ie),
        "vbe": fmt_voltage(primary.vbe),
        "vbc": fmt_voltage(primary.vbc),
        "region": primary.region,
        "status_class": status_class,
        "status_title": status_title,
        "status_text": status_text,
        "match": comparison["match"],
        "ic_delta": comparison["ic_delta"],
        "vce_delta": comparison["vce_delta"],
        "show_check": primary.region == "active",
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/")
def index():
    """Show the dashboard with the default worked example."""
    values = default_values()
    return render_template(
        "index.html",
        result=build_result(values),
        form_values=default_form(),
        circuit=build_circuit(values),
        error_messages=[],
    )


@app.post("/")
def compute():
    """Accept the form, compute both methods, render the dashboard."""
    values, display = parse_form(request.form)
    circuit = build_circuit(values)

    ok, messages = validate_form(
        values["vcc"], values["r1"], values["r2"], values["rc"],
        values["re"], values["beta"], values["vbe"],
    )
    if not ok:
        return render_template(
            "index.html",
            result=None,
            form_values=display,
            circuit=circuit,
            error_messages=messages,
        )

    return render_template(
        "index.html",
        result=build_result(values),
        form_values=display,
        circuit=circuit,
        error_messages=[],
    )


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
