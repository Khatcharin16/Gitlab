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
