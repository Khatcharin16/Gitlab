# BJT Common-Emitter DC Bias Web App — Design

**Course:** ENG29 2121 · **Date:** 2026-11-10 · **Status:** Awaiting approval

## Intent and why

A short lab needs a working Flask app that computes the DC operating point of an
NPN BJT in a voltage-divider (common-emitter) bias circuit, shows the numbers
with units, refuses invalid inputs, warns when the transistor is not in the
active region, and cross-checks the answer with an independent calculation.

The value is pedagogical: the student can see the standard Thévenin/beta-model
result and a second, independently derived result agree, and can see immediately
when a chosen resistor set pushes the transistor into cutoff or saturation.

## Goals

- One page: enter `VCC, R1, R2, RC, RE, beta, VBE`, submit, see the operating point.
- Report `IB, IC, IE, VBE, VCE, VE, VB, VC, VBC` with units.
- Validate every input; re-render the form with clear messages and preserved values.
- Classify the region (active / cutoff / saturation) and warn near saturation.
- Compute the same point a second way (nodal analysis) and show the comparison.
- Separate engineering logic, Flask routes, templates, CSS, and tests.
- Run on localhost and be committed to GitHub today.

## Non-goals

AC analysis, transient analysis, load-line plots, schematic editor, FET/MOSFET,
databases, authentication, JavaScript frameworks, unit-selection dropdowns,
saved history, multi-page navigation.

## Anti-goals

- Returning numbers for invalid input instead of an error.
- An "independent" check that is the same formula written twice.
- Hiding the region or warnings below the fold or behind a click.

## Constraints

- Python 3.10.11, Flask, pytest; no numpy, no JavaScript.
- Windows host; git is installed but not on PATH (`C:\Users\B6837006\AppData\Local\Programs\Git\cmd\git.exe`).
- Remote `github.com/Khatcharin16/Gitlab.git`, branch `main`; push may require the
  user to authenticate.
- Repository root already contains an unrelated `electrical.py`; leave it alone.
- `README.md` currently contains committed merge-conflict markers; resolve it in
  the same commit and add run instructions.

## Approaches considered

| | Approach | Trade-off |
|---|---|---|
| A | Shockley equation + Newton–Raphson independent check | Real independent physics, but adds `Is`/`VT` assumptions and results differ by design |
| B | **Direct nodal linear solve (chosen)** | Different procedure, identical model, agreement within 0.1%; ~60 lines, no new assumptions |
| C | Fixed textbook/SPICE reference values | Tiny, but validates only one operating point |

**Chosen: B.** The lab asks for an independent engineering calculation, not a
device-physics model. A nodal solve builds and solves the 6×6 system directly
instead of reducing to a Thévenin source, so it catches algebra errors in the
primary path without introducing model mismatch the student would have to explain.

## Primary calculation (Thévenin / beta model)

```
VBB = VCC * R2 / (R1 + R2)
RB  = R1 * R2 / (R1 + R2)
IB  = (VBB - VBE) / (RB + (beta + 1) * RE)
IC  = beta * IB
IE  = (beta + 1) * IB
VE  = IE * RE
VC  = VCC - IC * RC
VCE = VC - VE
VB  = VE + VBE
VBC = VB - VC
```

### Region rules

1. **Cutoff** when `VBB <= VBE`: `IB = IC = IE = 0`, `VE = 0`, `VB = VBB`,
   `VC = VCC`, `VCE = VCC`. Warning: "Cutoff — no collector current."
2. **Saturation** when the active-model `VCE <= VCE_SAT` (`VCE_SAT = 0.2 V`):
   `IC = (VCC - VCE_SAT) / (RC + RE)`, `IE = IC + IB`, `VE = IE * RE`,
   `VC = VCC - IC * RC`, `VCE = VC - VE`. Warning: "Saturation — VCE clamped near 0.2 V."
3. **Near saturation** when active and `VCE < 1.0 V`: warning only, region stays active.
4. Otherwise **active**, no warning.

`RE = 0` is allowed; it skips the emitter term in the base equation and is
reported normally.

## Independent calculation (nodal solve)

Unknowns `[VB, VE, VC, IB, IC, IE]`, solved with Gaussian elimination and partial
pivoting (no numpy). Equations:

```
VB - VE                     = VBE
IC - beta*IB                = 0
IE - IB - IC                = 0
-(1/R1 + 1/R2)*VB - IB      = -VCC/R1
-(1/RC)*VC - IC             = -VCC/RC
(1/RE)*VE - IE              = 0        (RE > 0; otherwise VE = 0)
```

The comparison runs only in the **active** region, because cutoff and saturation
intentionally clamp the model. UI shows `IB, IC, VCE` from both methods with
absolute and percentage differences and a **MATCH** badge when the largest
relative difference is ≤ 0.1%.

## Validation

| Input | Rule |
|---|---|
| VCC | > 0 V |
| R1, R2, RC | > 0 Ω |
| RE | ≥ 0 Ω |
| beta | 1–2000 |
| VBE | 0.4–1.0 V |
| all | numeric, finite; no blank fields |

Invalid submissions return HTTP 400, re-render the form with the entered values,
and list each message next to its field. Non-numeric and non-finite values are
rejected before any division.

## UI sketch

```
BJT Common-Emitter DC Bias — ENG29 2121
VCC [12 V]  R1 [47000 Ω]  R2 [10000 Ω]
RC  [4700 Ω] RE [1000 Ω]  beta [150]
VBE [0.7 V]                       [Calculate]

Region: ACTIVE
IB 8.82 µA   IC 1.32 mA   IE 1.33 mA
VBE 0.700 V  VCE 4.45 V   VE 1.33 V
VB 2.03 V    VC 6.22 V    VBC -4.19 V

Independent check (nodal solve)
        Thévenin     Nodal      Δ
IC      1.3230 mA    1.3230 mA  0.000%   MATCH
VCE     4.4500 V     4.4500 V   0.000%
```

English labels with standard symbols and units. One CSS file, no JavaScript.

## File layout

```
app/app.py                      Flask routes, form parsing, error handling
app/bjt.py                      dataclasses, validation, primary calculation, region logic
app/independent.py              6x6 nodal solve, comparison result
app/templates/index.html        dashboard: inputs, SVG schematic, results
app/static/style.css            single stylesheet
tests/test_bjt.py               primary math, regions, validation
tests/test_independent.py       nodal vs Thévenin agreement
tests/test_routes.py            GET, valid POST, invalid POST, region messages
README.md                       conflict resolved + run instructions
docs/superpowers/specs/2026-11-10-bjt-ce-bias-design.md
```

## Decisions made

- Repo-root layout; `electrical.py` untouched.
- Resistors entered in Ω/kΩ/MΩ (converted to ohms internally), voltages in V/mV,
  currents auto-scaled (µA/mA).
- `VCE_SAT = 0.2 V` and near-saturation threshold `1.0 V` are constants.
- Comparison tolerance 0.1%, active region only.
- Default form values: VCC = 12 V, R1 = 100 kΩ, R2 = 22 kΩ, RC = 2.2 kΩ,
  RE = 1.0 kΩ, β = 100, VBE = 0.70 V.

## Left to the builder

Exact CSS, English copy for labels and messages, Gaussian elimination implementation
details, and the specific numeric fixtures used in tests.
