# Lab 04 — BJT CE Amplifier Simulator v1 — Implementation Plan

> **For agentic workers:** If Superpowers is available in the session, use
> `superpowers:executing-plans` or `superpowers:subagent-driven-development` and execute this plan
> task by task. If it is not available, follow the same ordered steps manually and report a
> verification result after each task. Steps use checkbox (`- [ ]`) syntax.
> **Do not start Task 2 until the Task 0 engine gate passes.**

**Goal:** Extend the existing ENG29 2121 Lab 03 Flask BJT bias app into a minimal working CE
amplifier simulator that runs real `ngspice` DC / AC / transient analyses for one reference
voltage-divider circuit, displays parsed values and inline SVG plots with units and provenance,
and preserves all three analytical DC bias modes.

**Architecture:** Keep `app/app.py` GET/POST `/` and `app/bjt.py` / `app/independent.py` unchanged
in behaviour. Add a separate `POST /simulate` route, a new `app/spice_engine.py` adapter
(netlist → `subprocess.run` → parse), a new `app/plots.py` for inline SVG, and conditional sections
in the existing `app/templates/index.html`. No new Python plotting dependency.

**Tech stack:** Python 3.14.2 via `py`, Flask 3.1.3, pytest 9.2.0, external `ngspice_con.exe`
(ngspice-47 console build), inline SVG. Git executable:
`C:\Users\B6837006\Downloads\PortableGit\bin\git.exe` (`git` is not on PATH).
Engine binary: `C:\Users\B6837006\AppData\Local\Temp\opencode\ngspice-47\Spice64\bin\ngspice_con.exe`;
add that `bin` folder to PATH or set `NGSPICE_BIN` before running Flask. The sibling `ngspice.exe`
is the GUI build and produced no batch output in the spike.

**Spec:** `docs/superpowers/specs/2026-11-24-bjt-ce-amplifier-simulator-design.md`

---

## Global constraints

- Work inside `C:\Users\B6837006\Documents\GitHub\Gitlab`; branch `main`; leave `electrical.py` alone.
- Use `py -m ...` for Python; the bare `python` command is a broken Store alias.
- Use `ngspice_con.exe`, not the silent GUI `ngspice.exe`, for batch runs.
- Never use `shell=True`; netlist values are validated SI floats before entering a netlist string.
- No fabricated traces, no hard-coded "successful" numbers, no stale results on failure.
- Analytical results and SPICE results must carry separate labels.
- Playwright MCP is not configured: use OpenCode Browser and record `NOT RUN` in the report.
- `npx` / Node are not on PATH: Impeccable is optional; manual UI critique is the fallback.

---

## Task 0 — Environment baseline and engine gate (BLOCKING)

**Files:** `requirements.txt` (read only), `.venv/` (new, ignored by Git),
`docs/validation.md` (append only if blocked), `docs/evidence/spice-sample/` (new if spike passes).

- [x] **Step 1:** Created `.venv` and installed `requirements.txt` with the venv interpreter
  (Flask 3.1.3, pytest 9.2.0). The bare `python` alias was avoided.
- [x] **Step 2:** Baseline regression `py -m pytest tests/ -q` → **23 passed**.
- [x] **Step 3:** Flask smoke: `/`, `/?mode=fixed`, `/?mode=emitter`, `/healthz` → HTTP 200;
  Divider still shows `1.23 mA`, Fixed still shows `9.51 V`. (The background dev server was
  stopped by its 120 s shell timeout after the checks.)
- [x] **Step 4:** Downloaded the official ngspice-47 64-bit Windows 7z and extracted it to
  `C:\Users\B6837006\AppData\Local\Temp\opencode\ngspice-47`. `ngspice_con.exe -v` reports
  `ngspice-47, built Aug 11 2026`. The GUI `ngspice.exe` produced no output in batch and is not
  the engine to use. Not yet on PATH — add the `Spice64\bin` folder to PATH or set `NGSPICE_BIN`.
- [ ] **Step 5:** **BLOCKED.** No instructor Starter Kit / BJT model found in the machine. Ask the
  user or instructor for the model name and parameters; do not guess values and call them verified.
- [x] **Step 6:** Parser spike (simple RC circuit, since the CE model is pending):
  `ngspice_con.exe -b -o run.log -r run.raw circuit.cir` exits 0 and writes an **ASCII** raw file.
  AC section has `Flags: complex` with `real,imag` values; transient section has real values;
  both live in one raw file under separate `Title:` sections. `.tran 0 ...` is rejected — use a
  positive TSTEP such as `.tran 10u 2m 0 10u`. No `.control` block was needed.
- [x] **Step 7:** Recorded exact engine version, command flags and chosen ASCII-raw format in the
  spec; saved real samples in `docs/evidence/spice-sample/` (`test.cir`, `run.log`, `run.raw`,
  `ac_tran.cir`, `ac_tran.log`, `ac_tran.raw`). Model source is still the pending item.
- [ ] **Step 8:** `git status` currently shows only the new spec/plan docs and the sample evidence;
  no application code was changed. `.venv/` is ignored.

**Gate result:** engine gate **PASS**, parser-format gate **PASS**, baseline regression **PASS**.
**Model gate still BLOCKED for reported CE results.** Per user instruction, Task 1 foundation was
built with model injection via `NGSPICE_MODEL_LINE`; no guessed device parameters are stored in the
repo. Real CE runs and validation numbers remain on hold until the instructor model is supplied.

---

## Task 1 — SPICE adapter foundation (no UI yet)

**Files:** create `app/spice_engine.py`, `tests/test_spice_engine.py`; modify nothing else.

**Interfaces:** consumes validated SI values from `app.py`; produces netlist text, run status and
parsed arrays for Tasks 2–4.

- [x] **Step 1:** Created `app/spice_engine.py` with `ANALYSIS_MODES`, resolved engine from
  `NGSPICE_BIN` / PATH, and `get_model_line()` reading `NGSPICE_MODEL_LINE`. No model parameters
  are hard-coded; missing configuration raises `SpiceConfigError`. The model name is extracted
  from the line and used by `Q1`, so an instructor model can be dropped in unchanged.
- [x] **Step 2:** `check_engine()` resolves the console exe and calls `<exe> -v`; verified against
  ngspice-47 (`** ngspice-47 : Circuit level simulation program`).
- [x] **Step 3:** `validate_spice_inputs()` enforces finite inputs, VCC 1–24 V, resistors
  1 Ω–10 MΩ, **RE > 0**, RL, Cin/Cout, amplitude 1 µV–1 V, frequency 10 Hz–1 MHz, and analysis in
  `ANALYSIS_MODES`.
- [x] **Step 4:** `build_netlist()` emits the fixed node topology with SI suffix formatting
  (`100k`, `10u`, `1k`), `.op` / `.ac dec 20 1 10meg` / `.tran` with positive TSTEP, and a
  configured `.model` line.
- [x] **Step 5:** `run_ngspice()` uses a fresh `tempfile.mkdtemp()`, `subprocess.run([...])` with
  `cwd`, `timeout=30` and captured output; no `shell=True`, no GUI executable.
- [x] **Step 6:** ASCII raw parser implemented: `parse_raw()` splits `Title:` sections, reads
  complex/real values, and `parse_op()` / `parse_ac()` / `parse_tran()` return dicts with units.
- [x] **Step 7:** Added `tests/test_spice_engine.py` (14 tests) using the real
  `docs/evidence/spice-sample/parser_fixture.raw` produced by ngspice; covers validation, netlist,
  missing-model config and all three parsers.
- [x] **Step 8:** `py -m pytest tests/ -q` → **37 passed** (23 original + 14 new).
- [x] **Step 9 (extra):** Pipeline smoke with a clearly **test-only** model line ran all three
  analyses end to end through the real console engine (exit 0, 141 AC points, 108 transient
  points). These numbers are plumbing evidence only and must not be reported as CE results.

---

## Task 2 — DC `.op` integration and provenance panel

**Status: DONE.** Implemented on a separate `app/templates/simulate.html` page so the
Lab 03 `index.html` and its routes are completely untouched. `app/bjt.py` equations unchanged.

- [ ] **Step 1:** Add `POST /simulate` accepting `analysis=dc`; parse fields with the existing
  `parse_form()`/`UNIT_MAP`, run `validate_spice_inputs()`, return HTTP 400 with no result on error.
- [ ] **Step 2:** Call `check_engine()` then `run_ngspice()`; on missing engine, non-zero exit,
  timeout or empty output, return HTTP 502 with an error panel and **no chart/result table**.
- [ ] **Step 3:** Parse VB, VE, VC, VCE and IC; determine IC direction from the netlist's current
  probe and document the sign convention in the panel.
- [ ] **Step 4:** Render values with units plus a provenance block: engine version, model name,
  directive, run id/workdir, netlist `<details>` preview and log excerpt.
- [ ] **Step 5:** Show the Lab 03 Analytical value in a separately labelled row (badge
  "Analytical reference") next to the SPICE value; do not merge or overwrite either.
- [ ] **Step 6:** Add route tests with a monkeypatched adapter covering: success, engine missing,
  parse failure and invalid `RE = 0`; assert no stale values/chart survive a failure.
- [ ] **Step 7:** Run all tests and a real browser POST; confirm B2 and B3 behaviour by changing
  RE only and observing different numbers.

---

## Task 3 — AC `.ac` frequency response + inline SVG Bode plot

**Status: DONE.** `app/plots.py` renders both panels from parsed arrays; tests prove the SVG
changes when the arrays change.

**Files:** create `app/plots.py`; modify `app/app.py`, `app/templates/index.html`,
`tests/test_spice_engine.py` (parser cases).

- [ ] **Step 1:** Extend `/simulate` for `analysis=ac`; validate source amplitude/frequency before
  building the netlist; use `.ac dec 20 1 10meg` from the Task 1 builder.
- [ ] **Step 2:** Parse frequency, magnitude and phase. Define `Vin = v(base)` and `Vout = v(out)`;
  compute gain as the complex ratio so the measurement point is unambiguous.
- [ ] **Step 3:** Implement `bode_svg(frequency, gain_db, phase_deg)` in `app/plots.py` returning a
  safe inline SVG string with labelled axes (Hz, dB, deg), grid, and two panels (magnitude/phase).
  Escape all text; never interpolate raw form strings into SVG markup.
- [ ] **Step 4:** Find the −3 dB crossing only if it exists in the sweep; otherwise display
  "not determined in sweep range".
- [ ] **Step 5:** Render the chart only from parsed arrays; assert in a test that the SVG contains
  axis labels and at least one data point from the captured sample.
- [ ] **Step 6:** Run a real AC simulation and verify B4: axes, units, values and provenance match
  the engine output, not a source-code constant.

---

## Task 4 — Transient `.tran` waveforms + inline SVG overlay

**Status: DONE.** Phase is computed from the sampled Vin/Vout correlation, not assumed from theory.
Browser evidence is still pending; it is recorded honestly in `docs/validation.md`.

**Files:** modify `app/plots.py`, `app/app.py`, `app/templates/index.html`, tests.

- [ ] **Step 1:** Extend `/simulate` for `analysis=tran`; derive the `.tran` stop/step from the
  validated source frequency (5 periods minimum, bounded maximum).
- [ ] **Step 2:** Parse time, `Vin = v(base)` and `Vout = v(out)` arrays with units (s → ms, V).
- [ ] **Step 3:** Implement `waveform_svg(time_ms, vin, vout)` with two distinguishable traces,
  time axis (ms), voltage axis (V), legend and a readable size on mobile.
- [ ] **Step 4:** Detect phase inversion from the sampled data (e.g. sign/correlation over the
  last periods) and print the result with the method used; do not assume inversion from theory alone.
- [ ] **Step 5:** Verify B5 at 10 mV / 1 kHz and B6 after changing amplitude or frequency; capture
  before/after screenshots and confirm the traces really change.
- [ ] **Step 6:** Run the full test suite again.

---

## Task 5 — UI refinement and honest tool reporting

**Status: DONE.** Impeccable **RUN as detector + manual polish** after portable Node was
installed; the formal two-sub-agent `critique → polish → audit` workflow remains **NOT RUN**.
Added grouped inputs, analysis radios, visible engine/model status, separate
SPICE/Analytical sections, readable SVG legends, provenance `<details>` and responsive rules.
The final detector scan is `[]` at 1280×800 and 390×844. No numerical code was changed in
this task; `app/bjt.py` remains untouched.

- [x] **Step 1:** With portable `npx` available, installed Impeccable v4.10.0 into the
  git-ignored `.opencode/` folder and ran `detect --json` on the rendered page before and after
  CSS changes. Full critique sub-agents were not run; this is reported honestly.
- [x] **Step 2:** Prioritised grouped inputs, readable plots/legends, visible status and provenance,
  error states, and responsive layout; kept circuit/plot clarity above decoration.
- [x] **Step 3:** Inspected at ~1280 px and ~390 px; captured before/after screenshots under
  `docs/evidence/` (`B8-impeccable-after-1280.png`, `B8-impeccable-after-390.png`).
- [x] **Step 4:** Confirmed only `app/static/style.css` changed in this polish task
  (`git diff` review), then ran the tests: **53 passed**.

**Follow-up layout clarity pass:** the handout's three conceptual blocks were split into
five clearly separated panels — Parameters, Circuit reference, Run control, Plots and
Engineering results — in a two-region workspace. Only `app/templates/simulate.html`,
`app/static/style.css` and the panel-heading assertions in one route test changed; no
formula, netlist, parser or validation code was touched. Desktop grid is 400 px + flexible
output; the 390 px viewport keeps the same DOM/visual order in one column. Tests: **54
passed**; rendered Impeccable detector: `[]` at 1280×800 and 390×844; real AC POST still
succeeded with 141 points and no console errors.

**Follow-up engineering-results pass:** the three equal-width cards became one vertical
list with `SPICE · .op/.ac/.tran` or `not run` chips, aligned definition-list metric grids
and collapsed sample tables. Idle analyses stay ~90 px instead of stretching to the
active row; active rows measured 268–298 px. A detector pass flagged numbered `01/02/03`
labels and low-contrast idle index text, so both were removed rather than restyled. Final
rendered detector remained `[]` at both viewports; DC, AC and transient browser runs all
succeeded without console errors; tests remained **54 passed**. No formula, netlist,
parser, validation or JS code changed.

---

## Task 6 — Browser acceptance B1–B8

**Status: DONE.** B1–B7 PASS (B2 explicitly marked "mechanism PASS, model gate open");
B8 PASS at desktop 1296 px and at a real 390 px CSS viewport created with an iframe,
because OpenCode Browser has no device-emulation control. Playwright MCP: NOT RUN (not
configured). Evidence and screenshots are in `docs/validation.md` and `docs/evidence/`.

- [ ] **Step 1:** Navigate → snapshot → fill/select → submit → snapshot → read values → compare →
  screenshot for each case B1–B8 using OpenCode Browser.
- [ ] **Step 2:** Record expected, observed, units, method and PASS/FAIL/NOT RUN for every case;
  explicitly write `Playwright MCP: NOT RUN (not configured); OpenCode Browser used instead`.
- [ ] **Step 3:** For B4/B5/B6 prove the plotted numbers came from a real run by quoting the
  engine log/sample and comparing before/after parameter changes.
- [ ] **Step 4:** For B7 submit `RE = 0` and confirm an error with no stale graph.
- [ ] **Step 5:** Note ngspice version, BJT model source, limitations and anything not tested.
- [ ] **Step 6:** Do not edit code until the first findings have been reported.

---

## Task 7 — Documentation and publication

**Status:** README, validation notes, spec and plan are written. Commit created:
`734f3e3a65532c58ee9cadf6874cf8aa9b1fa45f` — "Add Lab 04 BJT CE amplifier simulator with
real ngspice runs" (39 files). Push to `origin/main` was attempted with PortableGit; its
outcome is recorded in the final report.

- [ ] **Step 1:** Update README: `py` vs `python`, venv creation, ngspice installation/PATH,
  Starter model source, `py -m app.app`, `py -m pytest tests/ -q`, known tool limitations.
- [ ] **Step 2:** Add the 3–5 line AI-assistance note: what AI created/edited and what the student
  personally checked (formulas, units, ngspice log, browser evidence).
- [ ] **Step 3:** Ensure no `.venv/`, secrets or oversized run artefacts are staged; keep only
  small, reproducible evidence samples.
- [ ] **Step 4:** `git status`, `git diff`, `git diff --staged` review with the PortableGit executable.
- [ ] **Step 5:** Commit Lab 4 with a clear message; push if credentials are available, otherwise
  report the commit SHA and the exact push blocker honestly.

---

## Review focus

- **Safety:** every new route rejects invalid input before touching ngspice; no `shell=True`;
  bounded timeout and workdir per run.
- **Truth:** graph data originates from a parsed engine file/log captured in Task 0; no constants
  masquerading as simulation results.
- **Regression:** the three Lab 03 bias modes and all 23 original tests remain intact.
- **Units/provenance:** axes, legends, status, engine version and model source visible on the page.
- **Honesty:** missing tools recorded as NOT RUN; engine failure never rendered as success.

## Definition of done

- [ ] `py -m pytest tests/ -q` passes (original 23 + new checks).
- [ ] A real browser run can execute DC, AC and Transient for the reference CE circuit.
- [ ] Changing RE, amplitude or frequency visibly changes the real results.
- [ ] `RE = 0` and engine-failure paths show an error, not an old chart with Success.
- [ ] `docs/validation.md` contains B1–B8 with truthful statuses and evidence.
- [ ] README reproduces the environment; `git status` clean after the final commit.

## Stop rules

If ngspice or the Starter model cannot be obtained, stop at Task 0, report the blocker, and do not
produce fake plots. If time runs short, reduce UI polish before reducing real simulation or browser
acceptance. If a browser tool did not execute, mark it NOT RUN — never claim a PASS.
