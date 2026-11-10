"""Independent nodal DC solve for the CE voltage-divider bias circuit.

Solves the 6×6 system directly (Gaussian elimination with partial pivoting)
without using numpy.  Returns the same IC, VCE as the primary Thévenin calc
so they can be cross‑checked.

Unknowns: [VB, VE, VC, IB, IC, IE]
Equations (row-echelon form, solved by back-substitution):

  1) VB - VE                     = VBE
  2) IC - beta*IB                = 0
  3) IE - IB - IC                = 0
  4) -(1/R1 + 1/R2)*VB - IB      = -VCC/R1
  5) -(1/RC)*VC - IC             = -VCC/RC
  6) (1/RE)*VE - IE              = 0        (RE > 0; otherwise VE = 0)
"""


from __future__ import annotations

from typing import Tuple


def nodal_solve(vcc: float, r1: float, r2: float, rc: float, re: float,
                beta: float, vbe: float) -> Tuple[float, float]:
    """Return (IC, VCE) from the independent nodal solve.

    Uses only core Python — no numpy, no SciPy.
    """
    # ---- Build the 6×6 coefficient matrix A and RHS vector b ----
    # Rows correspond to equations [VB, VE, VC, IB, IC, IE]

    # Pre-compute conductances
    g1 = 1.0 / r1          # 1/R1
    g2 = 1.0 / r2          # 1/R2
    gc = 1.0 / rc          # 1/RC
    if re > 0:
        ge = 1.0 / re      # 1/RE
    else:
        ge = 0.0

    # Matrix A (6x6) — each row has 6 coefficients + 1 RHS
    A = [
        [ 1.0, -1.0,  0.0,  0.0,  0.0,  0.0],   # eq1: VB - VE = VBE
        [ 0.0,  0.0,  0.0,  1.0, -beta,  0.0],   # eq2: IC - beta*IB = 0
        [ 0.0,  0.0,  0.0, -1.0, -1.0,  1.0],   # eq3: IE - IB - IC = 0
        [-g1,  0.0,  0.0, -1.0,  0.0,  0.0],   # eq4: -g1*VB - IB = -VCC/R1
        [ 0.0,  0.0, -gc,  0.0, -1.0,  0.0],   # eq5: -gc*VC - IC = -VCC/RC
        [ 0.0,  ge,  0.0,  0.0,  0.0, -1.0],   # eq6: ge*VE - IE = 0
    ]

    # RHS vector b (6)
    b = [
        vbe,                     # eq1 RHS
        0.0,                     # eq2 RHS
        0.0,                     # eq3 RHS
        -vcc / r1,              # eq4 RHS
        -vcc / rc,              # eq5 RHS
        0.0,                     # eq6 RHS (always 0)
    ]

    # ---- Gaussian elimination with partial pivoting ----
    n = 6
    # Augmented matrix [A | b]
    aug = [[A[i][j] for j in range(n)] + [b[i]] for i in range(n)]

    for col in range(n):
        # Partial pivot: find row with max |aug[row][col]| below or at col
        max_row = col
        for row in range(col + 1, n):
            if abs(aug[row][col]) > abs(aug[max_row][col]):
                max_row = row
        aug[col], aug[max_row] = aug[max_row], aug[col]

        pivot = aug[col][col]
        if abs(pivot) < 1e-15:
            # Singular — fall back to primary-only mode
            return 0.0, vcc  # IC=0, VCE=VCC (cutoff)

        # Eliminate below
        for row in range(col + 1, n):
            factor = aug[row][col] / pivot
            for j in range(col, n + 1):
                aug[row][j] -= factor * aug[col][j]

    # ---- Back substitution ----
    x = [0.0] * n  # x = [VB, VE, VC, IB, IC, IE]
    for i in range(n - 1, -1, -1):
        s = aug[i][n]
        for j in range(i + 1, n):
            s -= aug[i][j] * x[j]
        x[i] = s / aug[i][i]

    vb, ve, vc, ib, ic, ie = x

    # Force negative zero to positive zero
    if ic == 0.0:
        ic = 0.0
    if vb == 0.0:
        vb = 0.0
    if ve == 0.0:
        ve = 0.0

    # If RE == 0 we shorted the emitter; VE should be 0
    if re == 0:
        ve = 0.0

    vce = vc - ve
    return ic, vce