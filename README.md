# ENG29 2121 — Lab 03: BJT DC Bias Web App

Flask web app for the DC operating point of a common-emitter BJT bias circuit.
Lab 03 extends the Lab 02 voltage-divider calculator with **Fixed Bias** and
**Emitter Bias** while keeping the original Divider result unchanged.

- Repository: <https://github.com/Khatcharin16/Gitlab>
- Lab 03 commits: `96857921949ed7b664054d0fc906f2dd27dcab76` (tabbed mode UI),
  `0bf0ba5df837b04a4f6f9e0e2b8959eaca2430e4` (Fixed + Emitter modes)
- Browser acceptance evidence: [`docs/validation.md`](docs/validation.md)

## Bias modes

| Mode | Resistors used | Base-current equation |
| --- | --- | --- |
| Voltage Divider (`divider`, default) | R1, R2, RE | IB = (VTH − VBE) / [RTH + (β + 1)RE] |
| Fixed (`fixed`) | RB | IB = (VCC − VBE) / RB |
| Emitter (`emitter`) | RB, RE | IB = (VCC − VBE) / [RB + (β + 1)RE] |

All modes share VCC, RC, β, and VBE. Then:

- IC = β·IB, IE = (β + 1)·IB
- VE = IE·RE (VE = 0 V for Fixed)
- VB = VE + VBE
- VC = VCC − IC·RC
- VCE = VC − VE

The form also supports Ω / kΩ / MΩ and V / mV units.

## Behaviour

- Mode tabs link to `/?mode=divider`, `/?mode=fixed`, or `/?mode=emitter`.
  Clicking a tab immediately re-renders the form and schematic on the server.
  No JavaScript is used, and there is no separate "load form" button.
- Validation only checks the fields used by the selected mode. For example,
  an invalid RB is ignored in Divider mode, and RE is not required in Fixed mode.
- An unknown mode is an error and never falls back to Divider.
- If the inputs are valid but IB ≤ 0 or VCE ≤ 0.2 V, the app shows the
  calculated values with a **warning**; it does not clamp or solve
  Cutoff/Saturation. This is the Lab 03 model required by the lab sheet.
- A failed calculation shows no result table, so stale results from an earlier
  run cannot appear.
- Divider mode keeps the Lab 02 Thévenin result and the independent nodal
  cross-check. Fixed and Emitter modes do not run the divider-only nodal check.

## AI assistance and verification

AI (OpenCode) helped with the Lab 03 additions:

- drafting the Fixed and Emitter bias equations and the `solve_bias()` dispatch,
- the server-side mode tabs and the mode-aware form/schematic,
- the unit-aware form parsing (Ω/kΩ/MΩ, V/mV),
- the pytest scaffolding and the A1–A5 acceptance notes.

The student's verification:

- recomputed A1–A4 by hand from the base-loop equations (see below),
- confirmed Divider still returns the Lab 02 values
  (IC = 1.229858 mA, VCE = 8.052155 V),
- ran the browser cases A1–A5 and recorded the evidence in
  [`docs/validation.md`](docs/validation.md) and [`docs/evidence/`](docs/evidence/),
- checked invalid inputs (A5), per-mode validation, unknown mode, and
  no stale results,
- reviewed `git diff` and `git diff --staged` before committing.

Code locations:

- **Mode selection:** `app/bjt.py` — `solve_bias()` dispatches to
  `divider_bias()`, `fixed_bias()`, and `emitter_bias()`; `BIAS_MODES`
  lists the allowed modes. `app/app.py` — `parse_mode()` reads the mode
  from the query string or form.
- **Unit conversion:** `app/app.py` — `UNIT_MAP` defines the multipliers
  and `parse_form()` applies them
  (`values[key] = float(raw) * units[unit]`).

### Independent reference for the new modes

Common values: VCC = 12 V, RC = 2.2 kΩ, β = 100, VBE = 0.70 V.

Fixed bias (A2, RB = 1 MΩ):

```text
IB  = (VCC − VBE) / RB = (12 − 0.7) V / 1,000,000 Ω = 11.30 µA
IC  = β · IB = 100 × 11.30 µA = 1.130 mA
VCE = VCC − IC · RC = 12 V − (1.130 mA × 2.2 kΩ) = 9.514 V
VE  = 0 V, VB = VBE = 0.70 V
```

Emitter bias (A3, RB = 1 MΩ, RE = 1 kΩ):

```text
IB  = (VCC − VBE) / [RB + (β + 1)RE]
    = (12 − 0.7) V / [1,000,000 + 101 × 1,000] Ω = 10.263 µA
IC  = β · IB = 1.0263 mA
IE  = (β + 1) · IB = 1.0366 mA
VE  = IE · RE = 1.0366 V
VC  = VCC − IC · RC = 9.742 V
VCE = VC − VE = 8.705 V
```

## Run the app

From the repository root, using Python 3.10+:

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# macOS / Linux
# source .venv/bin/activate

python -m pip install -r requirements.txt
python -m app.app
```

Then open <http://127.0.0.1:5000>.

The lab-sheet style command also works:

```bash
python -m flask --app app.app run
```

## Tests

```bash
python -m pytest tests/ -q
```

Expected: **23 passed**. Lab 03 adds manual formula checks and browser
acceptance checks instead of new unittest/Playwright scripts, as required by
the lab sheet.

## Project layout

```text
app/
  app.py            Flask routes, unit parsing, form/result context
  bjt.py            Bias equations, mode dispatch, validation, warnings
  independent.py    Independent nodal solve (Divider cross-check)
  templates/        Jinja dashboard (form, schematic, results)
  static/           Dashboard styles
tests/              23 existing pytest tests (Lab 02 behaviour preserved)
docs/validation.md  A1–A5 and extra acceptance evidence
```

## Lab 03 acceptance summary

| Case | Mode | Observed IC | Observed VCE | Result |
| --- | --- | --- | --- | --- |
| A1 | Divider, R1 = 100 kΩ, R2 = 22 kΩ, RE = 1 kΩ | 1.23 mA | 8.05 V | PASS |
| A2 | Fixed, RB = 1 MΩ | 1.13 mA | 9.51 V | PASS |
| A3 | Emitter, RB = 1 MΩ, RE = 1 kΩ | 1.03 mA | 8.71 V | PASS |
| A4 | Emitter, RB = 1 MΩ, RE = 2 kΩ | 0.94 mA | 8.03 V | PASS |
| A5 | Fixed, RB = 0 | validation error | — | PASS |

Common values: VCC = 12 V, RC = 2.2 kΩ, β = 100, VBE = 0.70 V.
