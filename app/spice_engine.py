"""Adapter for real ngspice runs (Lab 04).

This module owns the boundary between Flask and the external simulator:
validation -> netlist -> ``subprocess.run`` -> ASCII raw parsing.

The BJT model is deliberately *not* hard-coded here.  It must be supplied by
the instructor Starter Kit through ``NGSPICE_MODEL_LINE`` (or passed directly
to :func:`build_netlist`).  Without it, netlist creation raises
:class:`SpiceConfigError` instead of inventing device parameters.
"""

from __future__ import annotations

import math
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.bjt import is_finite

ANALYSIS_MODES = ("dc", "ac", "tran")

ENGINE_ENV = "NGSPICE_BIN"
MODEL_ENV = "NGSPICE_MODEL_LINE"
ENGINE_CANDIDATES = ("ngspice_con", "ngspice")


class SpiceError(Exception):
    """Base class for adapter errors."""


class SpiceConfigError(SpiceError):
    """Engine path or BJT model was not configured."""


class SpiceValidationError(SpiceError):
    """Form values failed SPICE-specific validation."""


class SpiceEngineError(SpiceError):
    """ngspice could not be started, timed out or exited unsuccessfully."""


class SpiceParseError(SpiceError):
    """Engine output was empty, incomplete or not parseable."""


@dataclass
class SpiceRun:
    """Files and process result from one batch run."""

    returncode: int
    stdout: str
    stderr: str
    log: str
    raw: str
    workdir: str


@dataclass
class RawSection:
    """One ``Title:`` block from an ASCII ``.raw`` file."""

    plotname: str
    flags: str
    variables: list[tuple[str, str]]
    points: list[list[complex | float]]


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
def resolve_engine() -> str:
    """Return the console ngspice executable path.

    ``NGSPICE_BIN`` wins so a machine without ngspice on PATH can still run.
    The GUI ``ngspice.exe`` must not be used for batch runs.
    """
    configured = os.environ.get(ENGINE_ENV, "").strip()
    if configured:
        path = Path(configured)
        if not path.is_file():
            raise SpiceConfigError(f"{ENGINE_ENV} is not a file: {configured}")
        return str(path)

    for name in ENGINE_CANDIDATES:
        found = shutil.which(name)
        if found:
            return found

    raise SpiceConfigError(
        "ngspice not found. Add the ngspice Spice64/bin folder to PATH or set "
        f"{ENGINE_ENV} to ngspice_con.exe."
    )


def check_engine() -> str:
    """Run ``<engine> -v`` and return the version banner."""
    exe = resolve_engine()
    try:
        proc = subprocess.run(
            [exe, "-v"], capture_output=True, text=True, timeout=10, check=False
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise SpiceEngineError(f"Could not start ngspice: {exc}") from exc

    banner = "\n".join(part for part in (proc.stdout, proc.stderr) if part).strip()
    if proc.returncode != 0 or "ngspice" not in banner.lower():
        raise SpiceEngineError(
            f"ngspice version check failed (exit {proc.returncode}): {banner[:400]}"
        )
    return banner


def model_name_from_line(model_line: str) -> str:
    """Extract the model identifier from an instructor ``.model`` line."""
    match = re.match(r"^\s*\.model\s+(\S+)", model_line, re.IGNORECASE)
    if not match:
        raise SpiceConfigError(
            "Model line must start with '.model <name> NPN(...)'."
        )
    return match.group(1)


def get_model_line() -> str:
    """Return the instructor model line from configuration.

    Raises instead of guessing parameters when the Starter Kit has not been
    supplied.
    """
    line = os.environ.get(MODEL_ENV, "").strip()
    if not line:
        raise SpiceConfigError(
            "BJT model is not configured. Set NGSPICE_MODEL_LINE to the "
            "instructor-verified '.model ... NPN(...)' line."
        )
    if "\n" in line or not line.lower().startswith(".model"):
        raise SpiceConfigError(
            "NGSPICE_MODEL_LINE must be exactly one '.model ...' line."
        )
    model_name_from_line(line)
    return line


# ---------------------------------------------------------------------------
# Validation and netlist generation
# ---------------------------------------------------------------------------
def _number(values: dict[str, Any], key: str, label: str,
            messages: list[str]) -> float | None:
    value = values.get(key)
    if not isinstance(value, (int, float)) or not is_finite(value):
        messages.append(f"{label} must be a valid number")
        return None
    return float(value)


def _bounded(value: float | None, label: str, messages: list[str],
             *, low: float, high: float, inclusive_low: bool = True) -> None:
    if value is None:
        return
    too_low = value < low if inclusive_low else value <= low
    if too_low or value > high:
        relation = ">=" if inclusive_low else ">"
        messages.append(f"{label} must be {relation} {low:g} and <= {high:g}")


def validate_spice_inputs(values: dict[str, Any]) -> tuple[bool, list[str]]:
    """Validate SI values before they are allowed into a netlist.

    The SPICE path requires ``RE > 0`` so an emitter short has a deterministic
    error; the Lab 03 analytical Divider path keeps its own ``RE >= 0`` rule.
    """
    messages: list[str] = []

    analysis = values.get("analysis")
    if analysis not in ANALYSIS_MODES:
        messages.append(
            f"Unknown analysis '{analysis}'. Use dc, ac, or tran."
        )

    vcc = _number(values, "vcc", "VCC", messages)
    r1 = _number(values, "r1", "R1", messages)
    r2 = _number(values, "r2", "R2", messages)
    rc = _number(values, "rc", "RC", messages)
    re = _number(values, "re", "RE", messages)
    rl = _number(values, "rl", "RL", messages)
    cin = _number(values, "cin", "Cin", messages)
    cout = _number(values, "cout", "Cout", messages)
    amplitude = _number(values, "amplitude", "Amplitude", messages)
    frequency = _number(values, "frequency", "Frequency", messages)

    _bounded(vcc, "VCC", messages, low=1.0, high=24.0)
    for label, value in (("R1", r1), ("R2", r2), ("RC", rc), ("RL", rl)):
        _bounded(value, label, messages, low=1.0, high=10e6)
    _bounded(re, "RE", messages, low=0.0, high=10e6, inclusive_low=False)
    for label, value in (("Cin", cin), ("Cout", cout)):
        _bounded(value, label, messages, low=1e-12, high=1e-3)
    _bounded(amplitude, "Amplitude", messages, low=1e-6, high=1.0)
    _bounded(frequency, "Frequency", messages, low=10.0, high=1e6)

    # beta / VBE are used only for the analytical comparison row.
    if "beta" in values:
        beta = _number(values, "beta", "beta", messages)
        _bounded(beta, "beta", messages, low=1.0, high=2000.0)
    if "vbe" in values:
        vbe = _number(values, "vbe", "VBE", messages)
        _bounded(vbe, "VBE", messages, low=0.4, high=1.0)

    return not messages, messages


_SPICE_SUFFIXES = (
    (1e9, "g"),
    (1e6, "meg"),
    (1e3, "k"),
    (1.0, ""),
    (1e-3, "m"),
    (1e-6, "u"),
    (1e-9, "n"),
    (1e-12, "p"),
)


def ngspice_number(value: float) -> str:
    """Format a validated SI float with a SPICE engineering suffix."""
    if not is_finite(value):
        raise SpiceValidationError("Cannot format a non-finite number")
    for factor, suffix in _SPICE_SUFFIXES:
        if abs(value) >= factor or factor == 1e-12:
            scaled = value / factor
            return f"{scaled:.6g}{suffix}"
    raise SpiceValidationError(f"Number out of range: {value}")


def build_netlist(analysis: str, values: dict[str, Any],
                  model_line: str | None = None) -> str:
    """Build the single reference CE voltage-divider netlist.

    Node names are fixed: ``vcc``, ``base``, ``emitter``, ``collector``,
    ``out``, ``vs`` and ground ``0``.  ``Vin`` is measured at ``base`` (after
    ``Cin``) and ``Vout`` at ``out`` (across ``RL``).
    """
    source = dict(values)
    source["analysis"] = analysis
    ok, messages = validate_spice_inputs(source)
    if not ok:
        raise SpiceValidationError("; ".join(messages))

    model = model_line.strip() if model_line is not None else get_model_line()
    model_name = model_name_from_line(model)

    vin_peak = float(source["amplitude"])
    frequency_hz = float(source["frequency"])
    stop_s = 5.0 / frequency_hz
    step_s = stop_s / 100.0

    lines = [
        "* Lab04 CE voltage-divider reference (real ngspice run)",
        f"VCC vcc 0 DC {ngspice_number(float(source['vcc']))}",
        f"R1 vcc base {ngspice_number(float(source['r1']))}",
        f"R2 base 0 {ngspice_number(float(source['r2']))}",
        f"RC vcc collector {ngspice_number(float(source['rc']))}",
        f"RE emitter 0 {ngspice_number(float(source['re']))}",
        f"Cin vs base {ngspice_number(float(source['cin']))}",
        f"Cout collector out {ngspice_number(float(source['cout']))}",
        f"RL out 0 {ngspice_number(float(source['rl']))}",
        f"Q1 collector base emitter {model_name}",
        model,
        (
            f"Vs vs 0 AC {ngspice_number(vin_peak)} "
            f"SIN(0 {ngspice_number(vin_peak)} {ngspice_number(frequency_hz)})"
        ),
    ]

    if analysis == "dc":
        lines.append(".op")
    elif analysis == "ac":
        lines.append(".ac dec 20 1 10meg")
    elif analysis == "tran":
        lines.append(
            f".tran {ngspice_number(step_s)} {ngspice_number(stop_s)} "
            f"0 {ngspice_number(step_s)}"
        )
    else:  # guarded by validate_spice_inputs, kept for safety
        raise SpiceValidationError(f"Unknown analysis '{analysis}'")

    lines.append(".end")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Running and reading results
# ---------------------------------------------------------------------------
def run_ngspice(analysis: str, netlist: str, *, engine: str | None = None,
                timeout: int = 30) -> SpiceRun:
    """Run one batch simulation in its own temporary working directory."""
    exe = engine or resolve_engine()
    workdir = tempfile.mkdtemp(prefix=f"lab04-{analysis}-")
    circuit = Path(workdir) / "circuit.cir"
    circuit.write_text(netlist, encoding="utf-8")

    try:
        proc = subprocess.run(
            [exe, "-b", "-o", "run.log", "-r", "run.raw", circuit.name],
            cwd=workdir,
            timeout=timeout,
            capture_output=True,
            text=True,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise SpiceEngineError(
            f"ngspice timed out after {timeout}s in {workdir}"
        ) from exc
    except OSError as exc:
        raise SpiceEngineError(f"Could not start ngspice: {exc}") from exc

    log_path = Path(workdir) / "run.log"
    raw_path = Path(workdir) / "run.raw"
    return SpiceRun(
        returncode=proc.returncode,
        stdout=proc.stdout or "",
        stderr=proc.stderr or "",
        log=log_path.read_text(encoding="utf-8", errors="replace")
        if log_path.is_file() else "",
        raw=raw_path.read_text(encoding="utf-8", errors="replace")
        if raw_path.is_file() else "",
        workdir=workdir,
    )


def ensure_success(run: SpiceRun) -> None:
    """Reject failed or empty runs so no stale result can look successful."""
    if run.returncode != 0:
        raise SpiceEngineError(
            f"ngspice exited with {run.returncode}: {run.log[:400]}"
        )
    if not run.raw.strip():
        raise SpiceParseError("ngspice produced an empty raw file")
    if "Simulation interrupted due to error" in run.log:
        raise SpiceEngineError(f"ngspice reported a simulation error: {run.log[:400]}")


def _split_raw_blocks(raw_text: str) -> list[list[str]]:
    blocks: list[list[str]] = []
    current: list[str] = []
    for line in raw_text.splitlines():
        if line.strip().startswith("Title:"):
            if current:
                blocks.append(current)
            current = [line]
        elif current:
            current.append(line)
    if current:
        blocks.append(current)
    return blocks


def parse_raw(raw_text: str) -> list[RawSection]:
    """Parse ngspice's ASCII ``.raw`` output (no binary reader needed)."""
    sections: list[RawSection] = []
    for block in _split_raw_blocks(raw_text):
        meta: dict[str, str] = {}
        variables: list[tuple[str, str]] = []
        state = "meta"
        body_start = len(block)

        for index, raw_line in enumerate(block):
            stripped = raw_line.strip()
            if not stripped:
                continue
            if state == "meta":
                if not raw_line.startswith("\t") and ":" in stripped:
                    key, value = stripped.split(":", 1)
                    key, value = key.strip(), value.strip()
                    meta[key] = value
                    if key == "Variables":
                        state = "variables"
                    elif key == "Values":
                        state = "values"
                        body_start = index + 1
                continue
            if state == "variables":
                if stripped.startswith("Values:"):
                    state = "values"
                    body_start = index + 1
                    continue
                parts = [p.strip() for p in stripped.split("\t") if p.strip()]
                if len(parts) >= 3:
                    variables.append((parts[1], parts[2]))

        plotname = meta.get("Plotname", "")
        flags = meta.get("Flags", "")
        try:
            count = int(meta.get("No. Points", "").strip())
            nvars = int(meta.get("No. Variables", "").strip())
        except ValueError as exc:
            raise SpiceParseError(
                f"Bad raw header for '{plotname}': "
                f"{meta.get('No. Points')!r}, {meta.get('No. Variables')!r}"
            ) from exc

        complex_values = "complex" in flags.lower()
        collected: list[complex | float] = []
        for raw_line in block[body_start:]:
            for token in raw_line.split("\t"):
                token = token.strip()
                if not token or token.isdigit():  # skip point index
                    continue
                if complex_values:
                    if "," in token:
                        real, imag = token.split(",", 1)
                        value: complex | float = complex(float(real), float(imag))
                    else:
                        value = complex(float(token), 0.0)
                else:
                    value = float(token)
                collected.append(value)

        expected = count * nvars
        if len(collected) != expected:
            raise SpiceParseError(
                f"'{plotname}': expected {expected} values, got {len(collected)}"
            )
        points = [collected[i:i + nvars] for i in range(0, expected, nvars)]
        sections.append(
            RawSection(plotname=plotname, flags=flags, variables=variables,
                       points=points)
        )

    if not sections:
        raise SpiceParseError("No sections found in raw file")
    return sections


def _section(sections: list[RawSection], needle: str) -> RawSection:
    for section in sections:
        if needle.lower() in section.plotname.lower():
            return section
    raise SpiceParseError(f"No '{needle}' section in raw output")


def _column(section: RawSection, name: str) -> list[complex | float]:
    wanted = name.lower().replace(" ", "")
    for column, (variable_name, _kind) in enumerate(section.variables):
        if variable_name.lower().replace(" ", "") == wanted:
            return [point[column] for point in section.points]
    raise SpiceParseError(
        f"Variable '{name}' not in {section.plotname}: "
        f"{[name for name, _ in section.variables]}"
    )


def parse_op(raw_text: str) -> dict[str, float]:
    """Return VB, VE, VC, VCE and IC from an ``.op`` run."""
    section = _section(parse_raw(raw_text), "Operating Point")
    if not section.points:
        raise SpiceParseError("Operating Point section has no data")

    def voltage(node: str) -> float:
        values = _column(section, f"v({node})")
        return float(values[0].real if isinstance(values[0], complex) else values[0])

    vb = voltage("base")
    ve = voltage("emitter")
    vc = voltage("collector")
    # IC leaves the VCC source's positive terminal, so i(vcc) is negative.
    ic = -float(_column(section, "i(vcc)")[0].real)
    return {
        "vb": vb, "ve": ve, "vc": vc, "vce": vc - ve, "ic": ic,
        "units": {"vb": "V", "ve": "V", "vc": "V", "vce": "V", "ic": "A"},
    }


def parse_ac(raw_text: str) -> dict[str, list[float]]:
    """Return frequency, gain (dB) and phase (deg) from an ``.ac`` run."""
    section = _section(parse_raw(raw_text), "AC Analysis")
    frequencies = [float(v.real) for v in _column(section, "frequency")]
    vin = _column(section, "v(base)")
    vout = _column(section, "v(out)")

    gain_db: list[float] = []
    phase_deg: list[float] = []
    vin_mag: list[float] = []
    vout_mag: list[float] = []
    for source, load in zip(vin, vout):
        s = complex(source) if isinstance(source, complex) else complex(float(source), 0.0)
        o = complex(load) if isinstance(load, complex) else complex(float(load), 0.0)
        if abs(s) < 1e-15:
            raise SpiceParseError("AC input at v(base) is zero; gain is undefined")
        ratio = o / s
        gain_db.append(20.0 * math.log10(abs(ratio)))
        phase_deg.append(math.degrees(math.atan2(ratio.imag, ratio.real)))
        vin_mag.append(abs(s))
        vout_mag.append(abs(o))

    return {
        "frequency_hz": frequencies,
        "gain_db": gain_db,
        "phase_deg": phase_deg,
        "vin_mag": vin_mag,
        "vout_mag": vout_mag,
        "units": {
            "frequency_hz": "Hz", "gain_db": "dB", "phase_deg": "deg",
            "vin_mag": "V", "vout_mag": "V",
        },
    }


def parse_tran(raw_text: str) -> dict[str, list[float]]:
    """Return time, Vin and Vout arrays from a ``.tran`` run."""
    section = _section(parse_raw(raw_text), "Transient Analysis")
    time = [float(v.real if isinstance(v, complex) else v)
            for v in _column(section, "time")]
    vin = [float(v.real if isinstance(v, complex) else v)
           for v in _column(section, "v(base)")]
    vout = [float(v.real if isinstance(v, complex) else v)
            for v in _column(section, "v(out)")]
    return {
        "time_s": time,
        "time_ms": [t * 1e3 for t in time],
        "vin": vin,
        "vout": vout,
        "units": {"time_s": "s", "time_ms": "ms", "vin": "V", "vout": "V"},
    }
