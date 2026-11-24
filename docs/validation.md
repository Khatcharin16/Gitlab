# Lab 03 — Browser Acceptance (A1–A5)

Date: 2026-11-17  
App: <http://127.0.0.1:5000> (Flask development server, Python 3.10.11)  
Method: **OpenCode built-in Browser** (navigate, snapshot, click mode tab, fill, click)  
Playwright MCP: **NOT RUN** — it is not configured in this repository. The lab
sheet allows OpenCode Browser or manual checking as the fallback.

Common inputs for A1–A5: VCC = 12 V, RC = 2.2 kΩ, β = 100, VBE = 0.70 V.  
Tolerance from the lab sheet: ±0.01 mA for IC and ±0.02 V for VCE.

## A1–A5 results

| Case | Mode and inputs | Expected (independently calculated) | Observed on page | Decision |
| --- | --- | --- | --- | --- |
| A1 | Divider; R1 = 100 kΩ, R2 = 22 kΩ, RE = 1 kΩ | IC = 1.2299 mA, VCE = 8.0522 V; must match Lab 02 | IC = **1.23 mA**, VCE = **8.05 V**, VB = 1.94 V, VE = 1.24 V, IB = 12.30 µA, region = Active | **PASS** |
| A2 | Fixed; RB = 1 MΩ (RE absent) | IC = 1.1300 mA, VCE = 9.5140 V | IC = **1.13 mA**, VCE = **9.51 V**, VB = 0.70 V, VE = 0.00 V, IB = 11.30 µA, region = Active | **PASS** |
| A3 | Emitter; RB = 1 MΩ, RE = 1 kΩ | IC = 1.0263 mA, VCE = 8.7054 V | IC = **1.03 mA**, VCE = **8.71 V**, VB = 1.74 V, VE = 1.04 V, IB = 10.26 µA, region = Active | **PASS** |
| A4 | Emitter; RB = 1 MΩ, change RE 1 kΩ → 2 kΩ | IC = 0.9401 mA, VCE = 8.0328 V; IC must be lower than A3 | IC = **0.94 mA**, VCE = **8.03 V**, VB = 2.60 V, VE = 1.90 V, IB = 9.40 µA, region = Active | **PASS** |
| A5 | Fixed; RB = 0 | Validation error for RB, not a result | Error box: “Validation errors — Fixed Bias:”, “RB must be greater than 0 ohm”; no results table; no status | **PASS** |

Screenshots for the default GET state of each mode are in
[`docs/evidence/`](evidence/): `A1-divider.png`, `A2-fixed.png`,
`A3-emitter.png`. A4 and A5 were verified from the live accessibility snapshot
text after submitting the form.

## Extra checks (not part of A1–A5)

| Check | Action | Observed | Decision |
| --- | --- | --- | --- |
| Mode warning, not cutoff/saturation solve | Fixed, RB = 100 kΩ | IC = 11.30 mA, VCE = −12.86 V; amber “Saturation model warning”; message says values are not clamped | **PASS** |
| Unknown mode never defaults to Divider | GET `/?mode=invalid` | HTTP 400, “Unknown bias mode 'invalid'”, “Mode: Unknown mode 'invalid'”, no results table | **PASS** |
| Per-mode validation | Divider with RB = −5 kΩ | Divider computes normally; RB is ignored because Divider does not use it | **PASS** |
| Per-mode validation | Fixed with RE = −5 kΩ | Fixed computes normally; RE is ignored because Fixed does not use it | **PASS** |
| Per-mode validation | Emitter with R1 = −5 kΩ | Emitter computes normally; R1 is ignored because Emitter does not use it | **PASS** |
| No stale results | Submit A5 after a successful A4 run | Result table disappears; only the mode-labelled error remains | **PASS** |
| Legacy regression | `python -m pytest tests/ -q` | **23 passed** | **PASS** |

## Notes

- A1 remains exactly the Lab 02 value: IC = 1.229858 mA → **1.23 mA**,
  VCE = 8.052155 V → **8.05 V**.
- The nodal cross-check (MATCH) is still shown for Divider only. Fixed and
  Emitter use their own base-loop equations and do not run the divider nodal
  solver.
- A5 is checked in the browser with the visible Fixed form; the required RB
  field stays required in HTML and the server also rejects RB ≤ 0.
- Mode switching uses three server-side tabs (Voltage Divider / Fixed /
  Emitter). Clicking a tab reloads the form immediately; there is no separate
  “load form” button and no JavaScript.

---

# Lab 04 — Browser Acceptance (B1–B8)

Date: 2026-11-24  
App: <http://127.0.0.1:5000> (Flask dev server, `.venv\Scripts\python.exe`, `debug=False`)  
Method: **OpenCode Browser** (navigate, snapshot/find, fill, radio check, Enter submit,
snapshot/evaluate, screenshot).  
Playwright MCP: **NOT RUN** — not configured in this repository.  
Impeccable: **NOT RUN** — `npx`/Node unavailable.

## Engine and model provenance

- Engine: `ngspice_con.exe` from the official ngspice-47 64-bit Windows 7z, extracted to
  `C:\Users\B6837006\AppData\Local\Temp\opencode\ngspice-47\Spice64\bin`.
  `winget search ngspice` found no package, so the archive was downloaded from the
  project's SourceForge release. The sibling `ngspice.exe` is a GUI build and produced no
  batch output; only `ngspice_con.exe` is used.
- Version banner observed: `** ngspice-47 : Circuit level simulation program`, compiled
  with KLU Direct Linear Solver, creation date `Aug 11 2026 13:55:25`.
- Batch command: `<ngspice_con.exe> -b -o run.log -r run.raw circuit.cir` in a fresh
  `tempfile.mkdtemp()` directory, `timeout=30`, `shell=False`.
- Output format: **ASCII `.raw`**, split by `Title:` sections. AC is `Flags: complex`
  with `real,imag` values; transient is `Flags: real`. `.tran` requires a positive
  TSTEP (`.tran 10u 5m 0 10u`); `.tran 0 ...` was rejected in the spike.
- **BJT model gate is still OPEN.** No instructor Starter Kit was present on the machine.
  Browser runs used `NGSPICE_MODEL_LINE = .model QTEST NPN(IS=1e-14 BF=100)` with
  `NGSPICE_MODEL_SOURCE = TEST ONLY - not instructor verified`; the page displays both
  values. Those numbers exercise plumbing only and are **not** graded CE results. Replace
  the environment variable with the instructor `.model` line before using the app for
  graded work. No model parameters are hard-coded in application code.

## B1–B8 results

| Case | Action | Expected | Observed on page | Decision |
| --- | --- | --- | --- | --- |
| B1 · Regression | Open `/?mode=divider`, `fixed`, `emitter` | Lab 03 values unchanged and mode switching works | Divider IC **1.23 mA**, VCE **8.05 V**; Fixed VC **9.51 V**, IC **1.13 mA**; Emitter IC **1.03 mA**, VCE **8.71 V**; all three forms rendered | **PASS** |
| B2 · DC SPICE | RE = 1 kΩ, DC `.op` run | VB/VE/VC/VCE/IC from ngspice, model and run status visible | `ngspice run completed`, exit 0, run id `lab04-dc-1ulpv80w`; VB **1.94 V**, VE **1.28 V**, VC **9.22 V**, VCE **7.95 V**, IC **1.36 mA**; model `QTEST` with source label `TEST ONLY`; separate Analytical row IC 1.23 mA / VCE 8.05 V | **PASS (mechanism), model gate open** |
| B3 · Change RE | Change only RE 1 kΩ → 2 kΩ, rerun DC | Operating point changes, no stale values | IC **1.36 → 0.79 mA**, VCE **7.95 → 9.09 V**, VC **9.22 → 10.48 V**; new run id `lab04-dc-3pszazr8`; Analytical row also changed 1.23 → 0.67 mA | **PASS** |
| B4 · AC | Select AC, rerun with 1 kHz / 10 mV source | Bode axes, gain dB and phase deg from the real run | 141 sweep points, **1–1e7 Hz**, gain **0.54 to 4.86 dB**, phase at first point **−127.5 deg**; SVG has 2 polylines of 141 points and labels `|Gain| (dB)`, `Phase (deg)`, `Frequency (Hz, log scale)`; run id `lab04-ac-xkzi6lb0`; −3 dB shown as `not determined in sweep range` | **PASS** |
| B5 · Transient | Select `.tran`, 10 mV peak / 1 kHz | Vin/Vout vs time with units; phase direction from samples | 108 points, **0.000–5.000 ms**, Vin pp **0.020 V**, Vout pp **0.035 V**; phase from sampled correlation **inverted (~180°), correlation −1.00**; SVG labels `Time (ms)`, `Vin (V)`, `Vout (V)`; run id `lab04-tran-i8zhvdxl` | **PASS** |
| B6 · Change source | Change amplitude 10 mV → 50 mV, rerun `.tran` | Waveform and measured values change, not hard-coded | Vin pp **0.020 → 0.100 V**, Vout pp **0.035 → 0.174 V**; first SVG polyline begins `64.0,54.3 …` before and `64.0,58.7 …` after; new run id `lab04-tran-x1nt6pwq` | **PASS** |
| B7 · Invalid / fail | Set RE = 0 and submit | Error, no success state, no stale graph | Error box: `Run failed — no results shown: RE must be > 0 and <= 1e+07`; `plot-svg` count **0**; `ngspice run completed` **absent**; HTTP 400 | **PASS** |
| B8 · UI | Inspect simulator at desktop viewport | Readable controls, plots, no clipped content | At **1296 × 841**: grid columns `477.8px 729.2px`, `scrollWidth 1281` (no horizontal overflow), submit button visible; CSS has `@media (max-width:1040px)` and `(max-width:520px)` rules | **PARTIAL — desktop PASS, phone NOT RUN** |

B8 phone viewport is **NOT RUN** because the available OpenCode Browser toolset has no
viewport/device-emulation control; the responsive rules exist in `app/static/style.css` but
were not browser-verified at 390 px. Do not treat this as a PASS.

Screenshots: `docs/evidence/B1-lab3-regression.png`, `B2-dc-spice.png`,
`B3-change-re.png`, `B4-ac-bode.png`, `B5-transient.png`, `B6-change-source.png`,
`B7-invalid-re.png`. Real engine artifacts for the test model are in
`docs/evidence/ce-test-model/` (`dc/ac/tran-circuit.cir`, `-run.log`, `-run.raw`), and
parser fixtures with the same node names are in `docs/evidence/spice-sample/`.

## Lab 04 checks beyond B1–B8

| Check | Method | Observed | Decision |
| --- | --- | --- | --- |
| Baseline regression | `.venv\Scripts\python.exe -m pytest tests/ -q` before any app change | **23 passed** | **PASS** |
| Full suite after implementation | same command | **51 passed** (23 Lab 03 + 28 Lab 04) | **PASS** |
| Engine failure path | route test monkeypatch raising `SpiceEngineError` | HTTP 502, error text visible, no plot, no success banner | **PASS** |
| Parse failure path | route test monkeypatch raising `SpiceParseError` | HTTP 502, error text visible, no plot, no success banner | **PASS** |
| No stale result after a failure | successful AC POST then `RE = 0` POST in the same client | SVG disappears, error remains | **PASS** |
| Injected model | route test with `QTEST` and unit tests with `QTEST` | Netlist and page show `QTEST`; no engineer model is stored in source | **PASS** |
| `RE >= 0` Lab 03 vs `RE > 0` SPICE | unit tests on both validators | Divider still accepts 0 Ω; SPICE rejects it | **PASS** |

## Limitations

- The BJT parameters are test-only; no instructor-verified DC/AC/transient values can be
  claimed until the Starter Kit model is supplied.
- The −3 dB crossing was outside the simulated sweep for the test model and is reported as
  `not determined in sweep range`, not guessed.
- B8 mobile viewport and Playwright MCP remain NOT RUN as recorded above.
- All `run.log` excerpts and raw files listed above were produced by ngspice-47 in batch
  mode; no trace was generated from constants or hand-drawn points.
