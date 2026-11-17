"""BJT voltage-divider bias engineering logic — no numpy, no SciPy."""

from __future__ import annotations


# Constants
VBE_SAT = 0.8          # B-E voltage when saturated (V)
VCE_SAT = 0.2          # C-E voltage when saturated (V)
VBE_DEFAULT = 0.7      # Forward B-E voltage (V)
VBE_MIN = 0.4
VBE_MAX = 1.0


class BjtResult:
    """Returned from the primary (Thévenin) calculation."""
    __slots__ = (
        "ib", "ic", "ie", "vbe", "vce", "ve", "vb", "vc", "vbc",
        "region", "warning", "valid",
    )

    def __init__(
        self,
        ib: float,
        ic: float,
        ie: float,
        vbe: float,
        vce: float,
        ve: float,
        vb: float,
        vc: float,
        vbc: float,
        region: str,
        warning: str | None,
        valid: bool,
    ):
        self.ib = ib
        self.ic = ic
        self.ie = ie
        self.vbe = vbe
        self.vce = vce
        self.ve = ve
        self.vb = vb
        self.vc = vc
        self.vbc = vbc
        self.region = region
        self.warning = warning
        self.valid = valid

    @property
    def current_ica(self) -> str:
        """Current in human‑readable form with units."""
        if self.ic >= 1e-3:
            return f"{self.ic*1e3:.2f} mA"
        return f"{self.ic*1e6:.2f} µA"

    @property
    def current_iba(self) -> str:
        if self.ib >= 1e-6:
            return f"{self.ib*1e6:.2f} µA"
        return f"{self.ib*1e3:.2f} mA"

    @property
    def voltage_v(self) -> str:
        return f"{self.vbe:.3f} V"

    @property
    def voltage_vce(self) -> str:
        return f"{self.vce:.2f} V"

    @property
    def voltage_vb(self) -> str:
        return f"{self.vb:.2f} V"

    @property
    def voltage_vc(self) -> str:
        return f"{self.vc:.2f} V"


def fmt_cur(a: float) -> str:
    """Current in human‑readable form with units (sign preserved)."""
    if abs(a) >= 1e-3:
        return f"{a*1e3:.2f} mA"
    return f"{a*1e6:.2f} µA"


def fmt_vol(v: float) -> str:
    return f"{v:.3f} V"


def is_finite(x: float) -> bool:
    """Check for NaN / Inf without importing math."""
    try:
        return x == x and abs(x) < 1e300
    except Exception:
        return False


def validate_inputs(vcc: float, r1: float, r2: float, rc: float, re: float,
                    beta: float, vbe: float) -> tuple[bool, list[str]]:
    """Return (ok, messages).  Empty messages → valid."""
    msgs: list[str] = []
    if not isinstance(vcc, (int, float)) or not is_finite(vcc) or vcc <= 0:
        msgs.append("VCC must be greater than 0 V")
    if not isinstance(r1, (int, float)) or not is_finite(r1) or r1 <= 0:
        msgs.append("R1 must be greater than 0 ohm")
    if not isinstance(r2, (int, float)) or not is_finite(r2) or r2 <= 0:
        msgs.append("R2 must be greater than 0 ohm")
    if not isinstance(rc, (int, float)) or not is_finite(rc) or rc <= 0:
        msgs.append("RC must be greater than 0 ohm")
    if not isinstance(re, (int, float)) or not is_finite(re) or re < 0:
        msgs.append("RE must be greater than or equal to 0 ohm")
    if not isinstance(beta, (int, float)) or not is_finite(beta) or beta < 1 or beta > 2000:
        msgs.append("beta must be between 1 and 2000")
    if not isinstance(vbe, (int, float)) or not is_finite(vbe) or vbe < VBE_MIN or vbe > VBE_MAX:
        msgs.append(f"VBE must be {VBE_MIN}-{VBE_MAX} V")
    return len(msgs) == 0, msgs


def primary_calc(vcc: float, r1: float, r2: float, rc: float, re: float,
                 beta: float, vbe: float) -> BjtResult:
    """Thévenin / beta‑model DC bias calculation.

    Returns a BjtResult with region classification and validation.
    """
    ok, msgs = validate_inputs(vcc, r1, r2, rc, re, beta, vbe)
    if not ok:
        return BjtResult(0.0, 0.0, 0.0, vbe, 0.0, 0.0, 0.0, vcc, vcc - 0.0,
                         "cutoff", None, False)

    # --- Thévenin reduction ---
    vbb = vcc * r2 / (r1 + r2)
    rb  = r1 * r2 / (r1 + r2)

    # --- Base current (assume active) ---
    ib = (vbb - vbe) / (rb + (beta + 1) * re)

    # --- If VBB ≤ VBE we are in cutoff ---
    if vbb <= vbe:
        ib = 0.0

    ic = beta * ib
    ie = (beta + 1) * ib

    ve = ie * re if re > 0 else 0.0
    vc = vcc - ic * rc
    vb = ve + vbe
    vce = vc - ve

    # --- Region classification ---
    region = "active"
    warning: str | None = None

    if ib == 0.0:
        region = "cutoff"
        warning = "Cutoff — no collector current."
    elif vce <= VCE_SAT:
        # Saturation clamping
        ic = (vcc - VCE_SAT) / (rc + re) if (rc + re) > 0 else 0.0
        ib = ic / beta if beta > 0 else 0.0
        ie = ib + ic
        ve = ie * re if re > 0 else 0.0
        vc = vcc - ic * rc
        vce = vc - ve
        vb = ve + vbe
        vbc = vb - vc
        region = "saturation"
        warning = "Saturation — VCE clamped near 0.2 V."
    elif vce < 1.0:
        # Near saturation warning only
        warning = "Near saturation — VCE < 1 V, check design."

    # Build result
    vbc = vb - vc
    return BjtResult(ib, ic, ie, vbe, vce, ve, vb, vc, vbc,
                     region, warning, True)


# ---------------------------------------------------------------------------
# Lab 03 — selectable bias modes
# ---------------------------------------------------------------------------
# Divider is the original Lab 02 circuit.  Fixed and Emitter are added here
# without touching primary_calc(), so the existing 23 tests and the Lab 02
# result stay exactly as they were.

BIAS_MODES = ("divider", "fixed", "emitter")

MODE_LABELS: dict[str, str] = {
    "divider": "Voltage Divider Bias",
    "fixed": "Fixed Bias",
    "emitter": "Emitter Bias",
}


def _valid_number(value) -> bool:
    return isinstance(value, (int, float)) and is_finite(value)


def validate_bias(mode: str, values: dict) -> tuple[bool, list[str]]:
    """Validate only the fields used by ``mode``.

    Returns ``(ok, messages)``.  An unknown mode is always an error; it never
    falls back to the divider equations.
    """
    if mode not in BIAS_MODES:
        return False, [
            f"Unknown bias mode '{mode}'. Use divider, fixed, or emitter."
        ]

    msgs: list[str] = []

    vcc = values.get("vcc")
    if not _valid_number(vcc):
        msgs.append("VCC must be a valid number")
    elif vcc <= 0:
        msgs.append("VCC must be greater than 0 V")

    rc = values.get("rc")
    if not _valid_number(rc):
        msgs.append("RC must be a valid number")
    elif rc <= 0:
        msgs.append("RC must be greater than 0 ohm")

    if mode in ("fixed", "emitter"):
        rb = values.get("rb")
        if not _valid_number(rb):
            msgs.append("RB must be a valid number")
        elif rb <= 0:
            msgs.append("RB must be greater than 0 ohm")

    if mode == "divider":
        r1 = values.get("r1")
        if not _valid_number(r1):
            msgs.append("R1 must be a valid number")
        elif r1 <= 0:
            msgs.append("R1 must be greater than 0 ohm")

        r2 = values.get("r2")
        if not _valid_number(r2):
            msgs.append("R2 must be a valid number")
        elif r2 <= 0:
            msgs.append("R2 must be greater than 0 ohm")

    if mode in ("divider", "emitter"):
        re = values.get("re")
        if not _valid_number(re):
            msgs.append("RE must be a valid number")
        elif re < 0:
            msgs.append("RE must be greater than or equal to 0 ohm")

    beta = values.get("beta")
    if not _valid_number(beta):
        msgs.append("beta must be a valid number")
    elif beta < 1 or beta > 2000:
        msgs.append("beta must be between 1 and 2000")

    vbe = values.get("vbe")
    if not _valid_number(vbe):
        msgs.append("VBE must be a valid number")
    elif vbe < VBE_MIN or vbe > VBE_MAX:
        msgs.append(f"VBE must be {VBE_MIN}-{VBE_MAX} V")

    return len(msgs) == 0, msgs


def _base_point(vbb: float, rb: float, vcc: float, rc: float, re: float,
                beta: float, vbe: float) -> BjtResult:
    """Solve the forward-active base loop, then report (never clamp) region.

    Lab 03 uses a warn-only model: if IB <= 0 or VCE <= 0.2 V the calculated
    values are still shown, with a warning instead of a cutoff/saturation
    solution.
    """
    ib = (vbb - vbe) / (rb + (beta + 1) * re)
    ic = beta * ib
    ie = (beta + 1) * ib

    ve = ie * re
    vc = vcc - ic * rc
    vb = ve + vbe
    vce = vc - ve
    vbc = vb - vc

    if ib <= 0:
        region = "cutoff"
        warning = (
            f"Model warning — I_B = {fmt_cur(ib)} ≤ 0: "
            "the transistor would be cut off. Values are not clamped."
        )
    elif vce <= VCE_SAT:
        region = "saturation"
        warning = (
            f"Model warning — V_CE = {vce:.2f} V ≤ {VCE_SAT} V: "
            "the transistor would be saturated. Values are not clamped."
        )
    else:
        region = "active"
        warning = None

    return BjtResult(ib, ic, ie, vbe, vce, ve, vb, vc, vbc,
                     region, warning, True)


def divider_bias(values: dict) -> BjtResult:
    """Voltage-divider bias: VBB and RTH from R1/R2, then the shared loop."""
    vcc = values["vcc"]
    r1 = values["r1"]
    r2 = values["r2"]
    vbb = vcc * r2 / (r1 + r2)
    rb = r1 * r2 / (r1 + r2)
    return _base_point(vbb, rb, vcc, values["rc"], values["re"],
                       values["beta"], values["vbe"])


def fixed_bias(values: dict) -> BjtResult:
    """Fixed bias: RB from VCC to base, no emitter resistor."""
    return _base_point(values["vcc"], values["rb"], values["vcc"],
                       values["rc"], 0.0, values["beta"], values["vbe"])


def emitter_bias(values: dict) -> BjtResult:
    """Emitter bias: RB from VCC to base plus RE in the emitter leg."""
    return _base_point(values["vcc"], values["rb"], values["vcc"],
                       values["rc"], values["re"], values["beta"],
                       values["vbe"])


def solve_bias(mode: str, values: dict) -> BjtResult:
    """Dispatch to the selected bias model.

    Call ``validate_bias`` first.  Raises ``ValueError`` for an unknown mode
    instead of silently choosing divider.
    """
    if mode == "divider":
        return divider_bias(values)
    if mode == "fixed":
        return fixed_bias(values)
    if mode == "emitter":
        return emitter_bias(values)
    raise ValueError(f"Unknown bias mode: {mode!r}")


def compare_ic_vce(ic_th: float, vce_th: float,
                   ic_node: float, vce_node: float) -> dict:
    """Compare primary vs nodal results.

    Returns a dict with formatted strings and a MATCH badge.
    """
    ic_rel = abs(ic_th - ic_node) / max(ic_node, 1e-15) * 100.0
    vce_rel = abs(vce_th - vce_node) / max(vce_node, 1e-15) * 100.0
    match = ic_rel <= 0.1 and vce_rel <= 0.1
    return {
        "ic_th": f"{ic_th*1e3:.4f} mA",
        "ic_node": f"{ic_node*1e3:.4f} mA",
        "ic_delta": f"{ic_rel:.3f} %",
        "vce_th": f"{vce_th:.4f} V",
        "vce_node": f"{vce_node:.4f} V",
        "vce_delta": f"{vce_rel:.3f} %",
        "match": "MATCH" if match else "Δ",
    }