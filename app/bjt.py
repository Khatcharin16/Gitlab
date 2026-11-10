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
    """Current in human‑readable form with units."""
    if a >= 1e-3:
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