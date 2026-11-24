# ENG29 2121 — Lab 03 DC Bias + Lab 04 CE Amplifier Simulator

Flask web app for the DC operating point of a common-emitter BJT bias circuit.
Lab 03 extends the Lab 02 voltage-divider calculator with **Fixed Bias** and
**Emitter Bias** while keeping the original Divider result unchanged.
Lab 04 adds a separate ngspice-driven DC / AC / transient simulator at
`/simulate` without changing the Lab 03 routes or equations.

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

AI (OpenCode) also helped with the Lab 04 additions:

- designing the `/simulate` route and the ngspice adapter/ASCII raw parser,
- the injected model configuration and the no-fake-result error paths,
- the inline SVG Bode/waveform plots and the B1–B8 evidence notes.

The student's verification for Lab 04:

- confirmed the exact engine banner, batch flags and ASCII raw format from a real
  ngspice run (`docs/evidence/spice-sample/`),
- checked the netlist and `run.log` in `docs/evidence/ce-test-model/`,
- compared DC values after changing only RE and transient traces after changing
  only the source amplitude in the browser,
- confirmed `RE = 0` and engine/parse failures show errors without a chart,
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

From the repository root on Windows:

```powershell
py -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m app.app
```

Use `py` / the venv interpreter — the bare `python` command is a broken Microsoft
Store alias on this machine. On other platforms use `python3 -m venv .venv` and
the matching interpreter in `.venv/bin/`.

Open:

- <http://127.0.0.1:5000> — Lab 03 analytical DC bias calculator
- <http://127.0.0.1:5000/simulate> — Lab 04 real ngspice simulator

For a non-reloading server (used for browser acceptance):

```powershell
.venv\Scripts\python.exe -c "from app.app import app; app.run(host='127.0.0.1', port=5000, debug=False)"
```

## Lab 04 — ngspice setup

The simulator needs the **console** build `ngspice_con.exe`; the GUI `ngspice.exe`
produces no batch output. On this machine ngspice-47 (64-bit Windows 7z from the
official SourceForge release) lives at:

```text
C:\Users\B6837006\AppData\Local\Temp\opencode\ngspice-47\Spice64\bin\ngspice_con.exe
```

Set these before starting Flask, or add that `bin` folder to `PATH`:

```powershell
$env:NGSPICE_BIN = "...\ngspice-47\Spice64\bin\ngspice_con.exe"
$env:NGSPICE_MODEL_LINE = "<instructor .model line, one line>"
$env:NGSPICE_MODEL_SOURCE = "Instructor Starter Kit"
.venv\Scripts\python.exe -m app.app
```

`NGSPICE_MODEL_LINE` must be the instructor-verified `.model <name> NPN(...)`
line. It is **not hard-coded** in the app; without it the page shows a config
error and never invents a device. `NGSPICE_MODEL_SOURCE` is only a label shown
in the UI/provenance. Browser evidence in `docs/validation.md` used a
`TEST ONLY - not instructor verified` model, clearly labelled on the page.

The adapter writes each netlist into its own temporary directory and runs:

```text
<ngspice_con.exe> -b -o run.log -r run.raw circuit.cir
```

The ASCII `run.raw` is parsed directly; AC values are `real,imag` pairs and
transient values are real. `.tran` uses a positive TSTEP. No chart is drawn
unless ngspice exits 0 and its raw file parses successfully.

## Tests

```bash
.venv\Scripts\python.exe -m pytest tests/ -q
```

Expected: **51 passed** (23 Lab 03 + 28 Lab 04). Lab 04 adds adapter, parser,
plot and route tests; browser acceptance is recorded in
[`docs/validation.md`](docs/validation.md).

## Project layout

```text
app/
  app.py            Flask routes, unit parsing, Lab 03 context, /simulate
  bjt.py            Bias equations, mode dispatch, validation, warnings
  independent.py    Independent nodal solve (Divider cross-check)
  spice_engine.py   Lab 04: config, validation, netlist, ngspice run, ASCII parser
  plots.py          Lab 04: inline SVG Bode and waveform plots from parsed arrays
  templates/        index.html (Lab 03) and simulate.html (Lab 04)
  static/           Shared styles
tests/              51 pytest tests (23 Lab 03 + 28 Lab 04)
docs/validation.md  A1–A5 and B1–B8 acceptance evidence
docs/evidence/      Screenshots and real ngspice log/raw samples
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

## Lab 04 acceptance summary (test-only model)

| Case | Observed | Result |
| --- | --- | --- |
| B1 | Lab 03 values unchanged in all three modes | PASS |
| B2 | `.op` values, model and run status shown from real run | PASS (model gate open) |
| B3 | RE 1 → 2 kΩ changed IC 1.36 → 0.79 mA | PASS |
| B4 | AC Bode axes/units, 141 parsed points | PASS |
| B5 | `.tran` at 10 mV / 1 kHz, sampled inversion correlation −1.00 | PASS |
| B6 | Amplitude 10 → 50 mV changed Vin pp 0.020 → 0.100 V | PASS |
| B7 | RE = 0 → error, no plot, no Success state | PASS |
| B8 | 1296 × 841 desktop no overflow; 390 px phone NOT RUN | PARTIAL |

Full detail, engine version, model caveat and screenshots are in
[`docs/validation.md`](docs/validation.md).
