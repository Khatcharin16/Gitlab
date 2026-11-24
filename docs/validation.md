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

UI-polish commit: `8d244d4c9a07fcded70a41ee91f42c8068c43faa` ·
Repository: <https://github.com/Khatcharin16/Gitlab>

Date: 2026-11-24 (final handout-fidelity pass + Impeccable polish pass)

App: <http://127.0.0.1:5001> (Flask dev server, `.venv\Scripts\python.exe`, `debug=False`).

Method: **OpenCode Browser** (navigate, fresh snapshot, radio select/fill, real form submit,
snapshot/evaluate, compare with directly parsed ngspice arrays, screenshot). Port 5001 was
used because an older server process still held port 5000.  
Playwright MCP: **NOT RUN** — the tool is not configured in this repository. These results
are OpenCode Browser / manual verification and are **not** claimed as Playwright MCP results.  
Impeccable: **RUN (detector + manual polish)** — portable Node 22.23.5 was used to install
`impeccable` v4.10.0 into the git-ignored `.opencode/` folder. The bundled detector was run on
the rendered `/simulate` page at 1280×800 and 390×844 before and after the CSS changes. The
formal two-sub-agent critique workflow was **NOT RUN**; these are deterministic detector
results plus manual visual review, not a claimed full design critique.

## UI structure — five clearly separated panels

The handout's three conceptual blocks were refined into a two-region workspace so
that each kind of information has one obvious home. The left **setup** region holds
the two things you configure/reference; the right **output** region follows the
task order from running to reading:

1. **Parameters** (`01 · set up`) — editable `Vcc`, `RC`, `R1`, `R2`, `RE`, `RL`,
   source amplitude/frequency and collapsible coupling/analytical fields, with
   unit selectors (Ω/kΩ/MΩ, V/mV, Hz/kHz/MHz, pF/nF/µF/mF/F), **Run Simulation**
   and the visible `Running ngspice (…)` state.
2. **Circuit reference** (`visual aid`) — the handout's voltage-divider CE
   schematic and a compact fixture summary of the 12 V / 2.2 kΩ / 100 kΩ /
   22 kΩ / 1 kΩ / 10 kΩ / 10 mV · 1 kHz / 10 µF values. It is explicitly a visual
   aid, not a competing input step.
3. **Run control** (`02 · run`) — DC / AC / Transient radios, the contextual
   **Run …** button, the run banner, and engine/model readiness. Status and
   provenance of the engine sit next to the action that uses them.
4. **Simulation plots** (`03 · view`) — `Bode response` with `|Gain| (dB)`,
   `Phase (deg)`, `Frequency (Hz, log scale)`, the dashed `−3 dB from midband`
   reference, and `Input / Output waveforms` with `Time (ms)` and explicit
   `Vin = v(base)` / `Vout = v(out)` legends. Every point comes from parsed
   ngspice arrays; there are no fake traces.
5. **Engineering results** (`04 · measured values`) — a vertical list with one
   row per analysis. Each row has a clear heading, a `SPICE · <directive>` or
   `not run` chip, and an aligned metric grid when run; inactive rows stay
   compact instead of stretching to match the active one. Parsed sample tables
   sit in a collapsible `N parsed sample points · expand table` section, the
   Lab 3 analytical reference is a separately labelled callout, and netlist/log
   provenance remains below the list.

Desktop grid: a 400 px setup rail plus a flexible output region. At ≤1080 px the
workspace becomes one column in the same DOM/reading order: Parameters → Circuit
reference → Run control → Plots → Results. No formulas, netlist, parser or
validation rules changed in this layout pass.

The handout flowchart is now followed exactly: **one submit dispatches only the
selected analysis** (DC → `.op`, AC → `.ac`, Transient → `.tran`) in one real
ngspice batch. The other two result cards and both plot panels show `Not run in
this mode — select … and run again.` instead of stale or invented data. The
banner reports `Success — <directive> completed (1/1)` or
`Error — no results shown`; the DC card also labels the Lab 3 analytical value
as a separate, non-SPICE reference. During submission both Run buttons are
disabled with `aria-busy`, the status text names the selected analysis, and the
state is restored on `pageshow`.

## Impeccable detector + polish pass

`impeccable detect --json http://127.0.0.1:5001/simulate` was run at 1280×800 and 390×844.
The first scan found 8 desktop findings: low-contrast secondary text, three nested-card
instances, a long footer line, a straggler caption line and an unbalanced heading. All were
handled in `app/static/style.css` only — no formula, netlist, parser or route code changed.
A representative AC result page was then re-opened in OpenCode Browser: the real `.ac` run
still rendered (`Success — .ac dec 20 1 10meg completed (1/1)`, 1 SVG, 141 parsed points,
`−3 dB frequency 1.30961 Hz`) and no console errors were reported.

| Detector finding | Fix | Final scan |
| --- | --- | --- |
| Low contrast `#6a7f92` / `#7a8d9c` secondary text (4.0–4.1:1) | Replaced with `#4d6579` (6.1:1 on white, 5.9:1 on `#f9fcfd`) | Gone |
| Nested cards: `figure.schematic-figure`, `div.fixture-summary`, `div.plot-empty`, `div.status.warn`, `article.engine-block` | Removed box backgrounds/radius/tinted containers; used dividers, spacing and semantic text colour instead | `[]` at both viewports |
| Long `footer.goal > p` measure (~128 chars) | Added `max-width: 65ch` | Gone |
| Straggler caption / unbalanced heading | Added `text-wrap: pretty` to body copy and `text-wrap: balance` to headings | Gone |

Final detector output: `[]` at 1280×800 and `[]` at 390×844. Before/after visual evidence:
`docs/evidence/B8-handout-layout-desktop-1296.png` →
`docs/evidence/B8-impeccable-after-1280.png`, and
`docs/evidence/B8-handout-layout-mobile-390.png` →
`docs/evidence/B8-impeccable-after-390.png`.

## Layout clarity pass (final)

The page was then reorganised into the five panels described above. The mechanical
layout scan (`impeccable detect --scope layout` on the template and stylesheet,
plus rendered URL scans) and a real AC POST were repeated after the change:

| Check | Observed | Decision |
| --- | --- | --- |
| Rendered detector, desktop | `[]` at 1280×800 | **PASS** |
| Rendered detector, phone | `[]` at 390×844 | **PASS** |
| Desktop geometry (OpenCode Browser) | `innerWidth 1296`, no document overflow; setup rail **400 px**, output **809 px**; five headings in task order | **PASS** |
| Phone geometry (390 px iframe) | `innerWidth 390`, `clientWidth/scrollWidth 375`; one **347 px** column, engine and result grids collapse to one column; no page overflow | **PASS** |
| Real AC run after reorg | `Success — .ac dec 20 1 10meg completed (1/1)`, 141 points, `−3 dB frequency 1.30961 Hz`, 1 SVG, no console errors | **PASS** |
| Test suite after reorg | **54 passed**; one route test was renamed/updated to assert the five panel headings instead of the old three-card labels | **PASS** |

Evidence: `docs/evidence/B8-layout-1280.png`, `docs/evidence/B8-layout-390.png`,
`docs/evidence/B8-layout-desktop-result.jpg`. Source-scope Impeccable scanning still
warns that it cannot resolve the Jinja `url_for('static', …)` stylesheet link; the
rendered URL scans are the authoritative ones.

## Engineering-results readability pass (final)

The three result cards were replaced by a single vertical results list so that the
active analysis is obvious at a glance:

- `result-panel` macro renders `DC Operating Point`, `AC Frequency Response` and
  `Transient Response` consistently, with a `SPICE · .op/.ac/.tran` chip for the
  run row and `not run` for the others.
- Run values render as a definition-list metric grid (`VB 1.94 V`, `IC 1.26 mA`,
  `−3 dB frequency 1.30961 Hz`, `Vin peak-to-peak 19.92 mV`, …) instead of a
  label/value table. The grid uses `auto-fit, minmax(165px, 1fr)`, so it becomes
  one column at 390 px.
- AC and transient sample tables are collapsed behind a summary line; the DC
  analytical reference is a bordered callout explicitly marked `not SPICE`.
- Active rows measured about 268–298 px high; idle rows about 90 px. Previously
  all three cards stretched to 721 px because the transient sample table forced
  one common grid row height.
- A first detector run flagged low-contrast `#6a8296` index text and tiny
  `01/02/03` section labels. Both were removed rather than restyled: the visual
  chip plus heading hierarchy now carries the state. Final rendered detector:
  `[]` at 1280×800 and 390×844.

| Check | Observed | Decision |
| --- | --- | --- |
| DC run | `Success — .op completed (1/1)`, 5 metrics, analytical callout visible, 2 idle rows | **PASS** |
| AC run | `Success — .ac dec 20 1 10meg completed (1/1)`, 7 metrics, 6 parsed samples in a collapsed table, 1 SVG | **PASS** |
| Transient run | `Success — .tran 50u 5m 0 50u completed (1/1)`, 6 metrics, 6 parsed samples in a collapsed table, 19.92 mV / 34.86 mV, correlation −1.00 | **PASS** |
| Phone geometry | `innerWidth 390`, `clientWidth/scrollWidth 375`, results list one `313 px` column, no document overflow | **PASS** |
| Console/tests | No browser console errors; **54 passed** | **PASS** |

Evidence: `docs/evidence/B8-results-ac.jpg` and `docs/evidence/B8-results-tran.jpg`.
No formula, netlist, parser, validation or JS code changed in this pass.

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
- Collector current is measured with a zero-volt `VIC vcc rctop DC 0` source placed
  in series with `RC`; `parse_op()` reads `i(vic)` only. The earlier `-i(vcc)` value
  also contained the divider current and was corrected. The regenerated
  `parser_fixture.raw` contains the `i(vic)` column in its OP section.
- **BJT model gate is still OPEN.** No instructor Starter Kit was present on the machine.
  Browser runs used `NGSPICE_MODEL_LINE = .model QTEST NPN(IS=1e-14 BF=100)` with
  `NGSPICE_MODEL_SOURCE = TEST ONLY - not instructor verified`; the page displays both
  values. Those numbers exercise plumbing only and are **not** graded CE results. Replace
  the environment variable with the instructor `.model` line before using the app for
  graded work. No model parameters are hard-coded in application code.

## B1–B8 results

| Case | Method | Input | Expected/Reference | Observed | Evidence | Status |
| --- | --- | --- | --- | --- | --- | --- |
| B1 · Regression | OpenCode Browser navigate + snapshot on `/?mode=divider`, `fixed`, `emitter`; submit Lab 03 fixtures | VCC 12 V, RC 2.2 kΩ, β 100, VBE 0.70 V; Divider R1/R2/RE = 100 kΩ/22 kΩ/1 kΩ; Fixed RB = 1 MΩ; Emitter RB = 1 MΩ, RE = 1 kΩ | The original three analytical results and routes must be unchanged | Divider IC **1.23 mA**, VCE **8.05 V**; Fixed IC **1.13 mA**, VCE **9.51 V**; Emitter IC **1.03 mA**, VCE **8.71 V**; all forms render with the correct mode label | Browser snapshots + `docs/evidence/B1-lab3-regression.png`; 23 Lab 03 tests still pass | **PASS** |
| B2 · DC SPICE | Select DC, submit the real form, read the table and banner | Fixture values; RE = 1 kΩ; test model injected through `NGSPICE_MODEL_LINE` | VB/VE/VC/VCE/IC from parsed real `.op`, Model and Run Status visible; no analytical value masquerading as SPICE | `Success — .op completed (1/1)`, exit 0, run id `lab04-dc-hja8yg6_`; VB **1.94 V**, VE **1.28 V**, VC **9.22 V**, VCE **7.95 V**, IC **1.26 mA** (from `i(vic)`); model `QTEST`, source `TEST ONLY - not instructor verified`; Lab 3 reference shown separately as IC 1.23 mA / VCE 8.05 V | Browser evaluate + response HTML; `docs/evidence/ce-test-model/` logs/raw; regenerated `parser_fixture.raw` has `i(vic)` | **PASS (mechanism), model gate open** |
| B3 · Change RE | Change only the RE field and rerun DC | RE 1 kΩ → 2 kΩ, all other fixture values unchanged | Operating point changes; no old values, old run id or stale plot remains | IC **1.26 → 0.69 mA**, VCE **7.95 → 9.09 V**, new run id; AC/DC/Transient cards not selected show `Not run in this mode`; analytical row also updates | Before/after browser evaluations; route test covers no stale result | **PASS** |
| B4 · AC | Select AC, submit, inspect SVG, sample table and provenance | 1 Hz–10 MHz sweep, 20 points/decade; 10 mV · 1 kHz source | Frequency, gain dB and phase deg with units from real `.ac`; −3 dB defined against midband maximum | **141** points, **1 Hz–10 MHz**, gain **0.54 to 4.86 dB**, midband reference **4.86 dB**, target **1.86 dB**, −3 dB frequency **1.31 Hz**, phase at first point **−127.5 deg**; SVG has 2 polylines of 141 parsed points and a dashed midband reference line | Browser evaluate, run id `lab04-ac-vppaoowp`, `docs/evidence/B4-ac-bode.png`, engine raw/log | **PASS** |
| B5 · Transient | Select Transient, submit, inspect waveform and result table | 10 mV peak, 1 kHz, 0–5 ms window, `Vin = v(base)`, `Vout = v(out)` | Vin/Vout vs time with voltage and time units; CE inversion visible from real samples | **108** points, **0.000–5.000 ms**, Vin pp **19.92 mV**, Vout pp **34.86 mV**, phase **inverted (~180°), correlation −1.00**; axes `Time (ms)` and node-labelled voltage legend. The traces are drawn as each node's AC component about its own mean (mV), so the ~20/35 mV sine is readable instead of being flattened by the ~1.3 V / 9.2 V DC levels; absolute values remain in the table | Browser evaluate, run id `lab04-tran-txhpwwzd`, `docs/evidence/B5-transient.png`, corrected-view `docs/evidence/B5-transient-ac-view.jpg`, parsed `.tran` raw | **PASS** |
| B6 · Change source | Change both amplitude and frequency, rerun Transient | Amplitude 10 → 20 mV and frequency 1 → 2 kHz | Waveform, time window and measured values change; not a hard-coded trace | Fixture summary becomes `20 mV · 2 kHz`; time window **0.000–2.500 ms**, Vin pp **39.84 mV**, Vout pp **69.72 mV**; SVG coordinates and run id change | Before/after browser evaluations; new run id `lab04-tran-jthrkcc4`; `docs/evidence/B6-change-source.png` | **PASS** |
| B7 · Invalid / fail | Set RE = 0 and submit; also test engine/parse exception paths in route tests | RE = 0 Ω; simulated `SpiceEngineError` and `SpiceParseError` | Error shown, no Success state, no stale plot or results | Banner `Error — no results shown` with `RE must be > 0 and <= 1e+07`; `plot-svg` count **0**, no `Success —`, HTTP 400. Exception paths render HTTP 502 with an error and no chart | Browser evaluate + `tests/test_simulate_routes.py`; `docs/evidence/B7-invalid-re.png` | **PASS** |
| B8 · UI | Open the page in real 1296 px and 390 px CSS iframe viewports, switch mode and run | Readable, separated panels: Parameters, Circuit reference, Run control, Plots, Results; no clipped critical content | **Desktop**: `innerWidth 1296`, no document overflow, two-column workspace `400px + 809px`, five headings in task order, AC SVG renders. **Phone**: `innerWidth 390`, `clientWidth/scrollWidth 375`, one `347px` column with the same DOM order, engine/result grids collapse to one column, plots keep their horizontal scroller | `docs/evidence/desktop-viewport-check.html`, `mobile-viewport-check.html`, `B8-handout-layout-desktop-1296.png`, `B8-handout-layout-mobile-390.png`, `B8-impeccable-after-1280.png`, `B8-impeccable-after-390.png`, final `B8-layout-1280.png`, `B8-layout-390.png`, `B8-layout-desktop-result.jpg`, `B8-results-ac.jpg`, `B8-results-tran.jpg` | **PASS** |

Phone and desktop verification used real CSS layout viewports in Chromium iframes because
OpenCode Browser has no device-emulation control. It is **not** Playwright MCP device
emulation; that tool remains NOT RUN. On the phone viewport the plot panel has its own
horizontal scroller and swipe hint: the SVG keeps a 560 px drawing width for readable
axes and labels instead of being crushed into 299 px; page `scrollWidth` remains 375 px,
so no page-level critical content is clipped. Final layout screenshots:
`docs/evidence/B8-layout-1280.png` and `docs/evidence/B8-layout-390.png`;
real result pages are in `docs/evidence/B8-layout-desktop-result.jpg`,
`docs/evidence/B8-results-ac.jpg` and `docs/evidence/B8-results-tran.jpg`.

Earlier screenshots: `docs/evidence/B1-lab3-regression.png`, `B2-dc-spice.png`,
`B3-change-re.png`, `B4-ac-bode.png`, `B5-transient.png`, `B6-change-source.png`,
`B7-invalid-re.png`. Real engine artifacts for the test model are in
`docs/evidence/ce-test-model/` (`dc/ac/tran-circuit.cir`, `-run.log`, `-run.raw`), and
parser fixtures with the same node names are in `docs/evidence/spice-sample/`.

## Lab 04 checks beyond B1–B8

| Check | Method | Observed | Decision |
| --- | --- | --- | --- |
| Baseline regression | `.venv\Scripts\python.exe -m pytest tests/ -q` before any app change | **23 passed** | **PASS** |
| Full suite after implementation | same command | **51 passed** (23 Lab 03 + 28 Lab 04) | **PASS** |
| Full suite after handout-layout redesign | same command | **52 passed** (23 Lab 03 + 29 Lab 04) | **PASS** |
| Full suite after final fidelity pass | same command | **53 passed** (23 Lab 03 + 30 Lab 04); includes VIC/IC extraction, selected-mode dispatch, midband −3 dB logic, status/legend/sample-table assertions | **PASS** |
| Full suite after Impeccable CSS polish | same command | **53 passed**; only `app/static/style.css` changed, so analytical and SPICE behavior is unchanged | **PASS** |
| Full suite after transient AC-view fix | same command | **54 passed** (23 Lab 03 + 31 Lab 04); new test proves a 10–20 mV ripple on a large DC offset spans >80 px in the SVG instead of being visually flat | **PASS** |
| Transient AC-view browser recheck | real `.tran` POST in OpenCode Browser after restart | `Success — .tran 50u 5m 0 50u completed (1/1)`, 2 polylines with y-spans **132 px** (Vin) and **232 px** (Vout), SVG note `AC view: trace − own mean (mV)`, no console errors | **PASS** |
| Full suite after layout clarity pass | same command | **54 passed**; one route test renamed to assert five separated panels instead of the old three handout labels | **PASS** |
| Impeccable detector after polish | `impeccable detect --json http://127.0.0.1:5001/simulate --viewport 1280x800` and `390x844` | `[]` at both viewports; result-page AC run still succeeded with 1 parsed SVG and no console errors | **PASS** |
| Formal Impeccable dual-agent critique | Not attempted | Detector + manual polish only; no two-sub-agent design critique is claimed | **NOT RUN** |
| Engine failure path | route test monkeypatch raising `SpiceEngineError` | HTTP 502, error text visible, no plot, no success banner | **PASS** |
| Parse failure path | route test monkeypatch raising `SpiceParseError` | HTTP 502, error text visible, no plot, no success banner | **PASS** |
| No stale result after a failure | successful AC POST then `RE = 0` POST in the same client | SVG disappears, error remains | **PASS** |
| Injected model | route test with `QTEST` and unit tests with `QTEST` | Netlist and page show `QTEST`; no engineer model is stored in source | **PASS** |
| `RE >= 0` Lab 03 vs `RE > 0` SPICE | unit tests on both validators | Divider still accepts 0 Ω; SPICE rejects it | **PASS** |
| Illustrative layout vs real data | route test counts `plot-svg` elements after each selected mode and browser checks SVG point labels | DC renders 0 plots, AC renders 1 Bode SVG, Transient renders 1 waveform SVG; every point is generated from parsed ngspice arrays | **PASS** |
| Selected-mode dispatch | browser set AC/Transient radios outside the form and submitted; page evaluate immediately after submit | Running text became `Running ngspice (Transient .tran) — please wait…`; both buttons disabled with `aria-busy`, both result regions `aria-busy`; buttons restored on page load | **PASS** |
| No JavaScript console errors | OpenCode Browser console error level after final AC/Transient runs | Empty error list | **PASS** |
| Parser fixture regeneration | real ngspice-47 batch run of `parser_fixture.cir`, then parser unit test | OP section has `i(vic)`; IC is positive and comes from the collector branch only | **PASS** |

## Limitations

- The BJT parameters are test-only; no instructor-verified DC/AC/transient values can be
  claimed until the Starter Kit `.model` line is supplied. Every browser number above is a
  mechanism check, not a graded amplifier result.
- The −3 dB reference is defined as `max(gain_db) − 3 dB`, matching the handout's midband
  reference idea. For the test model it is 1.86 dB and the interpolated crossing is
  1.31 Hz; when no crossing exists the page says `not determined in sweep range` rather
  than inventing one. This value would change with the instructor model.
- Only the selected analysis runs per submit. This follows the handout flowchart; the other
  result cards deliberately say `Not run in this mode` instead of filling old values.
- On the 390 px CSS viewport the plot is horizontally scrollable inside its panel. This is a
  legibility choice; the page itself has no horizontal overflow.
- Playwright MCP device emulation remains NOT RUN; B8 used real 1296 px and 390 px CSS
  iframe layout viewports instead, as recorded above.
- Impeccable was run as a deterministic detector + manual polish pass after portable Node
  made the CLI available. The formal two-sub-agent critique workflow remains NOT RUN, so no
  full heuristic-scored critique is claimed. The detector was clean at both target viewports
  after the CSS-only fixes; the test-only BJT model caveat above is unchanged.
- All `run.log` excerpts and raw files listed above were produced by ngspice-47 in batch
  mode; no trace was generated from constants or hand-drawn points.
