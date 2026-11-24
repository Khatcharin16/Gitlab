# Lab 04 — BJT CE Amplifier Simulator v1 — Design

**Course:** ENG29 2121 · **Date:** 2026-11-24 · **Status:** Awaiting approval
**Implementation plan:** `docs/superpowers/plans/2026-11-24-bjt-ce-amplifier-simulator-plan.md`
**Base repository:** `C:\Users\B6837006\Documents\GitHub\Gitlab` (Lab 03, branch `main`, clean working tree)

## Intent and why

Lab 03 produced a correct but purely analytical DC bias calculator. Lab 04 must turn it into a
*measurable* simulator: the student changes a resistor or the source, runs a real SPICE engine,
and sees numbers and plots that come from that run — with enough provenance (engine version, BJT
model, netlist, log, units) to prove the result is not a picture copied from a handout.

The pedagogical value is the separation of two truth sources: the Thévenin/beta approximation in
`app/bjt.py` / `app/independent.py` and the device-model-based `ngspice` result. They are allowed to
differ; they are not allowed to be silently merged or mislabelled.

## Goals

- Preserve every Lab 03 behaviour: Fixed / Emitter / Divider modes, unit parsing, validation,
  region warnings, the Divider nodal cross-check, existing tests and `/healthz`.
- Add **one** reference CE voltage-divider circuit simulated by real `ngspice`:
  DC operating point (`.op`), AC frequency response (`.ac`) and transient waveform (`.tran`).
- Expose component and source inputs with visible units; change an input and the plots change.
- Render **inline SVG** plots generated only from parsed simulation data, with labelled axes,
  units, legends and a clear "no data / error" state.
- Show run status, engine version, BJT model name, netlist preview and a log excerpt on the page.
- Record B1–B8 browser acceptance honestly in `docs/validation.md` and publish the repository.

## Non-goals

- Drag-and-drop editor, free-form circuit construction, AC/transient for all three bias modes.
- FET/MOSFET, writing a SPICE solver in Python, animated overlay on the schematic.
- Emitter bypass capacitor `C_E` (possible extension only), saturation/cutoff physics re-derived
  with approximations to replace SPICE.
- Deployment to external users, new UI framework, new Python plotting dependency.

## Anti-goals

- Hard-coded gain, illustrative Bode/waveform curves, or "success" status with stale results.
- Hiding `ngspice` errors, timeouts or empty output behind a good-looking UI.
- Mixing Analytical and SPICE values in one unlabelled table.
- Claiming "Playwright MCP PASS" when the tool was not configured or did not run.
- Editing numerical formulas in `app/bjt.py` while doing UI polish.

## Constraints (measured on 2026-11-24, not assumed)

| Item | Observed state |
| --- | --- |
| Repository | `C:\Users\B6837006\Documents\GitHub\Gitlab`, clean `## main...origin/main` |
| Python | `py` → 3.14.2 works; bare `python` is a broken Microsoft Store alias → use `py -m ...` |
| Dependencies | `requirements.txt` = `Flask==3.1.3`, `pytest==9.2.0`; no `.venv` yet |
| Git | not on PATH; `C:\Users\B6837006\Downloads\PortableGit\bin\git.exe` works |
| ngspice | installed 2026-11-24 from the official ngspice-47 Windows 7z into `C:\Users\B6837006\AppData\Local\Temp\opencode\ngspice-47\Spice64\bin`; **batch engine = `ngspice_con.exe`** (`ngspice.exe` is the GUI build and stays silent in batch); not on PATH yet |
| Starter Kit | **no** model/netlist/adapter found in the machine; BJT model still pending (Model gate) |
| Node / npx | not on PATH → `npx impeccable install` is not currently possible |
| Playwright MCP | no MCP config found; Lab 03 `docs/validation.md` already records it as NOT RUN |
| Existing assets | 23 pytest tests, A1–A5 evidence, `docs/superpowers/{specs,plans}` template from Lab 03 |
| Repo hygiene | leave unrelated root file `electrical.py` untouched |

## Approaches considered

| Area | Option | Trade-off |
| --- | --- | --- |
| Engine | **Install/locate ngspice + run a short batch spike before writing the parser (chosen)** | Only way to satisfy the real-simulation DoD; needs internet/PATH and will stop the lab if unavailable |
| Engine | Use instructor Starter Kit only | Best fidelity when supplied, but none is present in the machine today |
| Engine | Python stub that returns plausible numbers | Fast, but violates the handout; rejected |
| Architecture | **New `/simulate` route + `app/spice_engine.py` adapter (chosen)** | Lab 03 `/` route stays untouched, so B1 regression is structurally safe |
| Architecture | Overload the existing `/` POST with an `analysis` flag | Fewer files, but risks breaking the 23 Lab 03 tests and per-mode validation |
| Charts | **Inline SVG built from parsed arrays (chosen)** | No new dependency, provenance is traceable, matches the no-JS style of Lab 03 |
| Charts | Chart.js / Plotly CDN | Interactive, but adds a dependency and a new failure path to verify |
| Charts | Matplotlib PNG | Simple, but numpy/matplotlib installation on Python 3.14 is an extra risk |
| Browser test | **OpenCode Browser with explicit `Playwright MCP: NOT RUN` (chosen)** | Real browser evidence today; honest about the missing tool per handout §09 |
| Browser test | Wait for Playwright MCP | Blocked; would produce no acceptance evidence |

**Chosen:** install/locate ngspice first, lock the parser format with a spike, then extend the Lab 03
app through a separate SPICE route and adapter, render inline SVG, and verify with the browser tool
that is actually available.

## Decision gates (hard stops)

1. **Engine gate.** If `ngspice --version` cannot be made to work, stop before Task 2 and record a
   P0 blocker in `docs/validation.md`. Never show a graph or Success state without a real run.
2. **Model gate.** The BJT model name/parameters must come from the instructor Starter Kit. If the
   kit is unavailable, ask the instructor/user; do not invent model values and call them verified.
3. **Parser-format gate — PASSED with ASCII raw.** The Task 0 spike proved
   `ngspice_con.exe -b -o run.log -r run.raw circuit.cir` writes an **ASCII raw file** with
   `Plotname`, `Flags`, `No. Variables`, `No. Points`, `Variables:` and `Values:` sections.
   AC values are `real,imag` pairs; transient values are real; multiple analyses produce multiple
   `Title:` sections in one raw file. No `.control` block or binary parser is needed. Real samples
   are stored in `docs/evidence/spice-sample/`. Note `.tran` needs `TSTEP > 0`
   (e.g. `.tran 10u 2m 0 10u`); `.tran 0 ...` is rejected.
4. **Browser-tool gate.** If Playwright MCP remains unconfigured, B1–B8 are executed with OpenCode
   Browser and the report says so explicitly.

## Data flow

```
Browser form (/simulate)
  → app.py: validate SI values + source + analysis mode
  → app/spice_engine.py: build_netlist() → subprocess.run([...], cwd=tempdir, timeout=...)
  → ngspice_con.exe (.op / .ac / .tran) → run.log + ASCII run.raw
  → parse_*() → arrays/dict with units
  → Jinja results panel + inline SVG
  → Browser acceptance (OpenCode Browser) + docs/validation.md

app/bjt.py + app/independent.py ──(DC only, labelled "Analytical reference")──┘
```

Configuration is injected, never hard-coded: `NGSPICE_BIN` points at the console executable when
it is not on PATH, and `NGSPICE_MODEL_LINE` holds the single instructor `.model ... NPN(...)`
line. Missing configuration raises an error instead of producing a result.

## Reference circuit contract

One fixed topology, no editor. Nodes: `vcc`, `base`, `emitter`, `collector`, `out`, `vs`, `0`.

| Element | Connection | Baseline |
| --- | --- | --- |
| VCC | `vcc` → `0`, DC source | 12 V |
| R1 / R2 | `vcc`–`base` / `base`–`0` | 100 kΩ / 22 kΩ |
| RC / RE | `vcc`–`collector` / `emitter`–`0` | 2.2 kΩ / 1 kΩ |
| RL | `out`–`0` | 10 kΩ |
| Cin / Cout | `vs`–`base` / `collector`–`out` | 10 µF / 10 µF |
| Q1 | `collector base emitter`, NPN model `MODEL_NAME` | from Starter Kit |
| Vs | `vs` → `0`, `SIN(0 amplitude frequency)` + `AC amplitude` | 10 mV peak, 1 kHz |

The netlist builder receives already-validated SI values and emits units ngspice understands
(`k`, `meg`, `u`, `m`). `MODEL_NAME` is a configured identifier, never arbitrary form text.

## Analysis modes and outputs

| Mode | Directive | Measurement definition | Displayed result |
| --- | --- | --- | --- |
| DC | `.op` | Coupling capacitors are open at DC; read `v(base)`, `v(emitter)`, `v(collector)` and `-i(vcc)` | VB, VE, VC, VCE, IC with units + region/status + model name |
| AC | `.ac dec 20 1 10meg` | `Vin = v(base)` (node after `Cin`), `Vout = v(out)`; gain = `Vout/Vin` | frequency (Hz), magnitude (V/V and/or dB), phase (deg), −3 dB point only if present in sweep |
| Transient | `.tran` window = max(5 source periods, 1 ms), capped by a validated upper bound | `Vin = v(base)`, `Vout = v(out)` vs time | time (ms), Vin/Vout (V), phase-inversion check from sampled data |

If the sweep has no −3 dB crossing, display **"not determined in sweep range"** rather than a
fabricated cutoff frequency.

## Validation rules (extend, do not replace, Lab 03 validation)

- Reuse `UNIT_MAP`, `parse_form()`, `parse_mode()` and `validate_bias()` for the existing fields.
- `analysis` must be one of `dc`, `ac`, `tran`; unknown values are an error, never a default.
- New fields must be finite and positive: `RL`, `Cin`, `Cout`, amplitude, frequency.
- Frequency bounds: 10 Hz – 1 MHz; amplitude: 1 µV – 1 V; VCC: 1–24 V; resistors: 1 Ω – 10 MΩ.
- **SPICE path requires `RE > 0 Ω`** so B7 (`RE = 0`) has a deterministic error; the Lab 03
  analytical Divider path keeps its existing `RE >= 0` behaviour.
- The BJT model is selected from a configured whitelist/Starter value, not typed into the form.
- Duration/step limits come from validated frequency, so no request can create an unbounded run.

## Provenance and error handling

Every successful result panel must show: engine + version, model name and parameters source,
analysis directive, run id/temp directory name, netlist preview (collapsible), and a log excerpt.
Every failure must show: clear error text, HTTP 400 for invalid input / 502 for engine failures,
**no result table and no chart**, and must not reuse a previous run's data.

Required error paths: engine missing, netlist write failure, non-zero exit, timeout, empty/partial
output, unparsable numbers, and invalid form input.

## UI requirements

- Keep the three Lab 03 bias tabs and their server-side rendering exactly as they are.
- Add an analysis selector (DC / AC / Transient) and source controls with visible units.
- Results area: labelled engineering values, SPICE vs Analytical badges, status chip, SVG plots.
- SVG axes must carry units; legends must say `Vin` / `Vout`; the layout must remain readable at
  ~1280 px desktop and ~390 px mobile without clipping buttons or plots.
- Impeccable may critique/polish UI files only; if `npx` is unavailable, do a manual critique with
  before/after screenshots and state the tool was not run.

## Acceptance mapping

| Case | Handout expectation | Evidence |
| --- | --- | --- |
| B1 | Lab 03 A1–A5 still work | values read from page + 23 tests |
| B2 | `.op` values from ngspice with model + status | page values + ngspice log |
| B3 | changing RE changes results | before/after values |
| B4 | Bode axes/units from real run | SVG + engine output |
| B5 | transient Vin/Vout with time axis and inversion | screenshot + sampled data summary |
| B6 | changing amplitude/frequency changes waveform | before/after screenshots |
| B7 | `RE = 0` fails cleanly | visible error, no stale chart |
| B8 | desktop/mobile readable | two screenshots |

`docs/validation.md` must also state the ngspice version, BJT model source, the `NOT RUN` tools,
and any limitation honestly.
