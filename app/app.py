"""Flask web app for ENG29 2121 BJT Common-Emitter DC Bias calculator."""

from __future__ import annotations

from flask import Flask, render_template, request, jsonify
from app.bjt import primary_calc, compare_ic_vce, is_finite
from app.independent import nodal_solve

app = Flask(__name__)
app.config["SECRET_KEY"] = "eng29-lab-secret"


# ---------------------------------------------------------------------------
# Helper: format numbers with units, auto‑scale
# ---------------------------------------------------------------------------
def fmt_cur(a: float) -> str:
    """Current in mA if ≥ 1 mA, else µA."""
    return f"{a*1e3:.2f} mA" if a >= 1e-3 else f"{a*1e6:.2f} µA"


def fmt_vol(v: float) -> str:
    return f"{v:.3f} V"


# ---------------------------------------------------------------------------
# Route: GET /  — show the form
# ---------------------------------------------------------------------------
@app.get("/")
def index():
    """Render the empty form (or keep previously entered values)."""
    return render_template(
        "index.html",
        result=None,
        form_values=dict(vcc="12", r1="47000", r2="10000", rc="4700", re="1000", beta="150", vbe="0.7"),
        error_messages=[],
    )


# ---------------------------------------------------------------------------
# Route: POST /  — compute and show results
# ---------------------------------------------------------------------------
@app.post("/")
def compute():
    """Accept the form, compute both methods, render results page."""
    # --- Pull & coerce form values ---
    try:
        vcc = float(request.form.get("vcc", ""))
    except ValueError:
        vcc = None
    try:
        r1 = float(request.form.get("r1", ""))
    except ValueError:
        r1 = None
    try:
        r2 = float(request.form.get("r2", ""))
    except ValueError:
        r2 = None
    try:
        rc = float(request.form.get("rc", ""))
    except ValueError:
        rc = None
    try:
        re = float(request.form.get("re", ""))
    except ValueError:
        re = None
    try:
        beta = float(request.form.get("beta", ""))
    except ValueError:
        beta = None
    try:
        vbe = float(request.form.get("vbe", ""))
    except ValueError:
        vbe = None

    # --- Defaults when fields are empty or bad ---
    if vcc is None:
        vcc = 12.0
    if r1 is None:
        r1 = 47000.0
    if r2 is None:
        r2 = 10000.0
    if rc is None:
        rc = 4700.0
    if re is None:
        re = 1000.0
    if beta is None:
        beta = 150.0
    if vbe is None:
        vbe = 0.7

    # --- Preserve entered values for the template ---
    # (override only the ones the user actually typed)
    form_values = dict(vcc=vcc, r1=r1, r2=r2, rc=rc, re=re, beta=beta, vbe=vbe)

    # --- Validation ---
    ok, v_msgs = validate_form(vcc, r1, r2, rc, re, beta, vbe)

    if not ok:
        # Re-render form with error messages and previously entered values
        return render_template(
            "index.html",
            result=None,
            form_values=form_values,
            error_messages=v_msgs,
        )

    # --- Primary (Thévenin) calculation ---
    primary = primary_calc(vcc, r1, r2, rc, re, beta, vbe)

    # --- Independent nodal solve (active region only) ---
    ic_node, vce_node = nodal_solve(vcc, r1, r2, rc, re, beta, vbe)

    # --- Comparison ---
    comparison = compare_ic_vce(primary.ic, primary.vce, ic_node, vce_node)

    # --- Build template context ---
    # Use comparison dict for the independent-check table;
    # its keys (ic_th, ic_node, ic_delta, vce_th, vce_node, vce_delta, match)
    # are the names the template expects.
    comparison = comparison  # keep for reference

    result = dict(
        ic_th=fmt_cur(primary.ic),
        ic_node=fmt_cur(ic_node),
        vce_th=fmt_vol(primary.vce),
        vce_node=fmt_vol(vce_node),
        region=primary.region,
        warning=primary.warning,
        ib=f"{primary.ib*1e6:.2f} µA",
        ic=fmt_cur(primary.ic),
        ie=f"{primary.ie*1e3:.2f} mA",
        vbe=fmt_vol(primary.vbe),
        vce=fmt_vol(primary.vce),
        ve=f"{primary.ve*1e3:.2f} mA" if primary.ve >= 1e-3 else f"{primary.ve*1e6:.2f} µA",
        vb=f"{primary.vb:.2f} V",
        vc=f"{primary.vc:.2f} V",
        vbc=f"{primary.vbc:.2f} V",
    )
    # Overlay comparison results (will overwrite keys above if overlap,
    # but they don't since comparison has ic_delta/vce_delta/match only)
    result.update(comparison)

    return render_template(
        "index.html",
        result=result,
        form_values=form_values,
        error_messages=None,
    )


# ---------------------------------------------------------------------------
# Validation helper
# ---------------------------------------------------------------------------
def validate_form(vcc: float, r1: float, r2: float, rc: float, re: float,
                  beta: float, vbe: float) -> tuple[bool, list[str]]:
    msgs: list[str] = []
    if not is_finite(vcc) or vcc <= 0:
        msgs.append("VCC must be greater than 0 V")
    if not is_finite(r1) or r1 <= 0:
        msgs.append("R1 must be greater than 0 ohm")
    if not is_finite(r2) or r2 <= 0:
        msgs.append("R2 must be greater than 0 ohm")
    if not is_finite(rc) or rc <= 0:
        msgs.append("RC must be greater than 0 ohm")
    if not is_finite(re) or re < 0:
        msgs.append("RE must be greater than or equal to 0 ohm")
    if not is_finite(beta) or beta < 1 or beta > 2000:
        msgs.append("beta must be between 1 and 2000")
    if not is_finite(vbe) or vbe < 0.4 or vbe > 1.0:
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