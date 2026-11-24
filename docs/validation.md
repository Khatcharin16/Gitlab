# Lab 03 — Browser Acceptance (A1–A5)

Date: 2026-11-17  
App: <http://127.0.0.1:5000> (Flask development server, Python 3.10.11)  
Method: **OpenCode built-in Browser** (navigate, snapshot, click mode tab, fill, click) for A1–A5.  
Playwright MCP was not installed on 2026-11-17. It was installed on 2026-11-24 and the Lab 03
regression was then re-checked with it (see B1 in the Lab 04 section and
`docs/evidence/tooling-playwright/B1-lab03.png`).

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

App: <http://127.0.0.1:5002> for the final Playwright MCP pass (Flask dev server,
`.venv\Scripts\python.exe`, `debug=False`, **no `NGSPICE_BIN`** — the engine is resolved from
`PATH`). Earlier passes used port 5001 because an older server process still held port 5000.

Method: **Playwright MCP** (*@playwright/mcp* 0.0.86, Microsoft Edge channel, headless) driving
the real form: navigate, evaluate/select, click submit, wait for the run banner, snapshot, and
screenshot. Earlier passes used OpenCode Browser and are kept in the file history; B1–B8 below
were re-run with Playwright MCP on 2026-11-24.  

Impeccable: **RUN (detector + manual polish)** — portable Node 22.23.5 was used to install
`impeccable` v4.10.0 into the git-ignored `.opencode/` folder. The bundled detector was run on
the rendered `/simulate` page at 1280×800 and 390×844 before and after the CSS changes; the final
output was `[]` at both viewports. The formal two-sub-agent critique workflow was **NOT RUN**;
these are deterministic detector results plus manual visual review, not a claimed full design
critique.

## Toolchain check (handout “04 / Setup & Starter”)

Run on 2026-11-24 before the final acceptance pass. Everything the handout lists was checked;
the two missing pieces were installed, not assumed.

| Tool | Check | Result |
| --- | --- | --- |
| Git + GitHub | `git status --short --branch`, `git remote -v` | `main...origin/main`, clean tree; `origin` = `https://github.com/Khatcharin16/Gitlab.git` — **PASS** |
| Python + Flask | `.venv\Scripts\python.exe --version`, `GET /simulate` | Python **3.12.7**, Flask server returns **200** — **PASS** |
| ngspice | `ngspice_con --version` from a **fresh-login PATH** (machine + user PATH, no `NGSPICE_BIN`) | **ngspice-47** found at `%LOCALAPPDATA%\Programs\ngspice-47\Spice64\bin`; a real DC run succeeded on the PATH-only server (`Success — .op completed (1/1)`, `lab04-dc-1rsj5oto`) — **PASS** |
| Node.js (needed by Playwright MCP) | `node --version`, `npm --version` | Was **missing** → installed portable Node **22.23.5** to `%LOCALAPPDATA%\Programs\node` and added it to the user PATH — **INSTALLED** |
| Playwright MCP | `opencode mcp list`, then navigate + snapshot + screenshot in a real browser | Was **NOT RUN** (not configured) → installed *@playwright/mcp* 0.0.86, registered as a local MCP server (Edge channel), connection **connected**; navigate/snapshot/screenshot all worked — **PASS** |
| Impeccable | `impeccable detect --json … --viewport 1280x800` / `390x844` | Project skill loads; detector returns `[]` at both viewports — **PASS** |
| Superpowers (OpenCode skill set) | `opencode.json` → `plugins`, plugin load log, skill list | Was **missing** → installed *superpowers* **7.0.2** from `obra/superpowers`, plugin loaded (`msg="loading plugin"`), **15 skills** registered (brainstorming, writing-plans, test-driven-development, systematic-debugging, …) — **INSTALLED** |

Install locations (not committed; machine-level): `%LOCALAPPDATA%\Programs\ngspice-47`,
`%LOCALAPPDATA%\Programs\node`, `%LOCALAPPDATA%\Programs\node\node_modules\@playwright\mcp`,
`%USERPROFILE%\.config\opencode\node_modules\superpowers`.

**Model fallback (final pass).** The Instructor Starter Kit `.model` file was not present on
this machine. To keep the app runnable without inventing parameters, the adapter resolves the
model in this order: `NGSPICE_MODEL_LINE` → `NGSPICE_MODEL_FILE` → the bundled, cited
`models/2N3904_onsemi.model` (onsemi 2N3904, MODPEX header). The bundled model is labelled
`Bundled vendor model (onsemi 2N3904) — NOT instructor verified` in the UI and in every result
provenance block. B2–B8 below were re-run with that bundled model on 2026-11-24. The instructor
model still overrides it with one environment variable; the gate is **OPEN** until that file is
supplied.

### Starter Kit search log (2026-11-24)

A full local search was run before adopting the fallback. Search result: **not present on this
machine**. The handout itself gates the kit on distribution ("รับ Instructor-verified Starter Kit
สำหรับการเรียก ngspice — ถ้าผู้สอนแจก"), so absence is expected until the instructor hands it out.

| Location searched | Method | Result |
| --- | --- | --- |
| `Downloads`, `Desktop`, `Documents`, `OneDrive`, whole `C:` and `D:` | name filter for `*.model *.mod *.lib *.cir *.sp *.net *.spice *.inc`, plus `starter / 2n3904 / q2n / bjt / spice / lab04 / eng29` | Only the repo's own `models/2N3904_onsemi.model` and the repo's generated evidence netlists |
| Handout HTML | decoded text, `<a href>`/`src` list, base64 payloads, every "Starter Kit" mention | No embedded model, no attachment, no download link; only a description of the kit and the `spice_engine.py` starter layout |
| All 9 archives (`*.zip`); `*.7z` | archive entry listing for model/netlist members | Only `lab3-main.zip` (this repo's own earlier code) and unrelated Photoshop/CP210x archives |
| Starter layout signature (`dc_bias.py`, `transistor-simulator/`, `app.js`) | recursive filename search across both drives | 0 hits |
| Git history, all branches (`main`, `lab03-*`, `feature/input-validation`) | `git log --all --name-only`, deleted-file filter | No model or netlist file was ever committed and then removed |
| Recycle bins (`C:\$Recycle.Bin`, `D:\$RECYCLE.BIN`) | name filter | Nothing matching |
| Agent/session storage and local logs | text scan for a `.model <name> NPN(` card | 0 hits |
| GitHub account `Khatcharin16` | REST API repo list | Only `Gitlab` (this project); no starter-kit repo |

Unrelated SPICE models that do exist on disk (ngspice-47 examples: `PN2222.mod`, `qnva.mod`,
`Infineon_VBIC.lib`, OSDI/PSP MOSFET cards) were **not** used — none is the instructor device and
using one would be an invented substitute.

To close the gate, the instructor must supply the `.model` line or file; see README
"BJT model (instructor Starter Kit)". After it arrives, set `NGSPICE_MODEL_LINE` (+
`NGSPICE_MODEL_SOURCE="Instructor Starter Kit"`) or `NGSPICE_MODEL_FILE` and rerun B2–B6.

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
No formula, netlist, parser, validation or JS code changed in this pass. The numeric examples
in this subsection were captured with the earlier `QTEST` plumbing model; the final
bundled-model rerun values are the B2–B6 rows above.

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
  The final browser runs used the bundled `models/2N3904_onsemi.model` (onsemi 2N3904,
  MODPEX-generated, downloaded from onsemi on 2026-11-24). It is a real, cited vendor model,
  not a guessed one, but it is **not** the instructor model; the page labels it
  `Bundled vendor model (onsemi 2N3904) — NOT instructor verified` and shows an `unverified`
  badge plus a “Not the Instructor Starter Kit model” warning. Those numbers exercise the
  complete netlist/run/parse path and are **not** graded CE results. Set
  `NGSPICE_MODEL_LINE` (or `NGSPICE_MODEL_FILE`) to the instructor `.model` line to override
  it; no model parameters are hard-coded in application code. The earlier `QTEST`
  (`IS=1e-14 BF=100`) artifacts remain under `docs/evidence/ce-test-model/` for history.

## B1–B8 results

| Case | Method | Input | Expected/Reference | Observed | Evidence | Status |
| --- | --- | --- | --- | --- | --- | --- |
| B1 · Regression | OpenCode Browser navigate + snapshot on `/?mode=divider`, `fixed`, `emitter`; submit Lab 03 fixtures | VCC 12 V, RC 2.2 kΩ, β 100, VBE 0.70 V; Divider R1/R2/RE = 100 kΩ/22 kΩ/1 kΩ; Fixed RB = 1 MΩ; Emitter RB = 1 MΩ, RE = 1 kΩ | The original three analytical results and routes must be unchanged | Divider IC **1.23 mA**, VCE **8.05 V**; Fixed IC **1.13 mA**, VCE **9.51 V**; Emitter IC **1.03 mA**, VCE **8.71 V**; all forms render with the correct mode label | Browser snapshots + `docs/evidence/B1-lab3-regression.png`; 23 Lab 03 tests still pass | **PASS** |
| B2 · DC SPICE | Select DC, submit the real form, read the table and banner | Fixture values; RE = 1 kΩ; bundled onsemi 2N3904 model (no env override) | VB/VE/VC/VCE/IC from parsed real `.op`, Model and Run Status visible; no analytical value masquerading as SPICE | `Success — .op completed (1/1)`, exit 0, run id `lab04-dc-vy3r3d3s`; VB **1.97 V**, VE **1.34 V**, VC **9.08 V**, VCE **7.75 V**, IC **1.33 mA** (from `i(vic)`); model `Q2n3904`, source `Bundled vendor model (onsemi 2N3904) — NOT instructor verified`; Lab 3 reference shown separately as IC 1.23 mA / VCE 8.05 V | Browser evaluate + response HTML; `docs/evidence/B2-dc-spice.png`; `docs/evidence/ce-vendor-model/dc-*` logs/raw | **PASS (mechanism), model gate open** |
| B3 · Change RE | Change only the RE field and rerun DC | RE 1 kΩ → 2 kΩ, all other fixture values unchanged | Operating point changes; no old values, old run id or stale plot remains | IC **1.33 → 0.71 mA**, VCE **7.75 → 8.99 V**, new run id `lab04-dc-6409572x`; AC/DC/Transient cards not selected show `Not run in this mode`; analytical row also updates | Before/after browser evaluations; `docs/evidence/B3-change-re.png`; route test covers no stale result | **PASS** |
| B4 · AC | Select AC, submit, inspect SVG, sample table and provenance | 1 Hz–10 MHz sweep, 20 points/decade; 10 mV · 1 kHz source | Frequency, gain dB and phase deg with units from real `.ac`; −3 dB defined against midband maximum | **141** points, **1 Hz–10 MHz**, gain **0.48 to 4.80 dB**, midband reference **4.80 dB**, target **1.80 dB**, −3 dB frequency **1.30964 Hz**, phase at first point **−127.5 deg**; SVG has 2 polylines of 141 parsed points and a dashed midband reference line | Browser evaluate, run id `lab04-ac-v0ofwpp4`, `docs/evidence/B4-ac-bode.png`, `docs/evidence/ce-vendor-model/ac-*` logs/raw | **PASS** |
| B5 · Transient | Select Transient, submit, inspect waveform and result table | 10 mV peak, 1 kHz, 0–5 ms window, `Vin = v(base)`, `Vout = v(out)` | Vin/Vout vs time with voltage and time units; CE inversion visible from real samples | **108** points, **0.000–5.000 ms**, Vin pp **19.92 mV**, Vout pp **34.60 mV**, phase **inverted (~180°), correlation −1.00**; axes `Time (ms)` and node-labelled voltage legend. The traces are drawn as each node's AC component about its own mean (mV), so the ~20/35 mV sine is readable instead of being flattened by the ~1.3 V / 9.1 V DC levels; absolute values remain in the table | Browser evaluate, run id `lab04-tran-yor0ml6g`, `docs/evidence/B5-transient.png`, `docs/evidence/ce-vendor-model/tran-*` logs/raw | **PASS** |
| B6 · Change source | Change both amplitude and frequency, rerun Transient | Amplitude 10 → 20 mV and frequency 1 → 2 kHz | Waveform, time window and measured values change; not a hard-coded trace | Fixture summary becomes `20 mV · 2 kHz`; time window **0.000–2.500 ms**, Vin pp **39.84 mV**, Vout pp **69.21 mV**; SVG coordinates and run id change | Before/after browser evaluations; new run id `lab04-tran-38832zf7`; `docs/evidence/B6-change-source.png`; `docs/evidence/ce-vendor-model/tran-20mv-2khz-*` | **PASS** |
| B7 · Invalid / fail | Set RE = 0 and submit; also test engine/parse exception paths in route tests | RE = 0 Ω; simulated `SpiceEngineError` and `SpiceParseError` | Error shown, no Success state, no stale plot or results | Banner `Error — no results shown` with `RE must be > 0 and <= 1e+07`; `plot-svg` count **0**, no `Success —`, HTTP 400. Exception paths render HTTP 502 with an error and no chart | Browser evaluate + `tests/test_simulate_routes.py`; `docs/evidence/B7-invalid-re.png` | **PASS** |
| B8 · UI | Open the page in real 1296 px and 390 px CSS iframe viewports, switch mode and run | Readable, separated panels: Parameters, Circuit reference, Run control, Plots, Results; no clipped critical content | **Desktop**: `innerWidth 1296`, `scrollWidth 1281`, no document overflow, two-column workspace, five headings in task order, real AC SVG and the `unverified` model badge render (`lab04-ac-e9iritcr`). **Phone**: `iframeWidth 390`, `clientWidth/scrollWidth 375`, one-column stack with the same DOM order, engine/result grids collapse to one column, plots keep their horizontal scroller | `docs/evidence/desktop-viewport-check.html`, `mobile-viewport-check.html`, `B8-handout-layout-desktop-1296.png`, `B8-handout-layout-mobile-390.png`, `B8-impeccable-after-1280.png`, `B8-impeccable-after-390.png`, final `B8-layout-1280.png`, `B8-layout-390.png`, `B8-layout-desktop-result.jpg`, `B8-results-ac.jpg`, `B8-results-tran.jpg` | **PASS** |

Phone and desktop verification used real CSS layout viewports in Chromium iframes because
OpenCode Browser has no device-emulation control. It is **not** Playwright MCP device
emulation; that tool remains NOT RUN. On the phone viewport the plot panel has its own
horizontal scroller and swipe hint: the SVG keeps a 560 px drawing width for readable
axes and labels instead of being crushed into 299 px; page `scrollWidth` remains 375 px,
so no page-level critical content is clipped. Final layout screenshots:
`docs/evidence/B8-layout-1280.png` and `docs/evidence/B8-layout-390.png`;
real result pages are in `docs/evidence/B8-layout-desktop-result.jpg`,
`docs/evidence/B8-results-ac.jpg` and `docs/evidence/B8-results-tran.jpg`.

Current screenshots for B2–B7 are `docs/evidence/B2-dc-spice.png`, `B3-change-re.png`,
`B4-ac-bode.png`, `B5-transient.png`, `B6-change-source.png` and `B7-invalid-re.png`, all
regenerated with the bundled onsemi model. Real engine artifacts for that model are in
`docs/evidence/ce-vendor-model/` (`dc`, `dc-re2k`, `ac`, `ac-20mv`, `tran`, `tran-20mv-2khz`
with `-circuit.cir`, `-run.log`, `-run.raw`), and parser fixtures with the same node names are
in `docs/evidence/spice-sample/`. The earlier `QTEST` plumbing artifacts remain in
`docs/evidence/ce-test-model/` for history; they are not the reported B2–B6 results.

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
| Full suite after bundled vendor model | `.venv\Scripts\python.exe -m pytest tests/ -q` | **58 passed** (23 Lab 03 + 35 Lab 04); adds `resolve_model` precedence, continuation-line joining, missing-file and no-source fallback tests | **PASS** |
| Browser rerun with bundled model | real OpenCode Browser POSTs for DC, RE = 2 kΩ, AC, Transient, 20 mV / 2 kHz and `RE = 0` | `lab04-dc-vy3r3d3s`, `lab04-dc-6409572x`, `lab04-ac-v0ofwpp4`, `lab04-tran-yor0ml6g`, `lab04-tran-38832zf7`; all success runs exited 0, `RE = 0` showed `Error — no results shown`; console error list empty | **PASS** |
| Playwright MCP rerun (B1–B8) | installed *@playwright/mcp* 0.0.86; drove the real form on the PATH-only server at `127.0.0.1:5002` (Edge, headless) | DC `lab04-dc-1rsj5oto`, RE = 2 kΩ `lab04-dc-kypyv0r4`, AC `lab04-ac-qnupv3e6`, Transient `lab04-tran-8mjz3c9u`, 20 mV / 2 kHz `lab04-tran-mj_x9z2g`, layout AC `lab04-ac-l7zdh2mc`; every banner showed `ngspice exit 0`; `RE = 0` showed `Error — no results shown` with 0 plots; console error count **0** since navigation; screenshots in `docs/evidence/tooling-playwright/` and the rubric pack `docs/evidence/submission/` | **PASS** |
| Playwright MCP connectivity | `opencode mcp list` then navigate / snapshot / screenshot on the running app | `○ playwright pending` immediately after config reload, then tool calls succeeded and returns `### Page URL` + snapshot + saved PNG | **PASS** |
| Impeccable detector after bundled model | `impeccable detect --json http://127.0.0.1:5001/simulate --viewport 1280x800` and `390x844` | `[]` at both viewports with the new `unverified` badge/warning visible | **PASS** |
| Impeccable detector after polish | `impeccable detect --json http://127.0.0.1:5001/simulate --viewport 1280x800` and `390x844` | `[]` at both viewports; result-page AC run still succeeded with 1 parsed SVG and no console errors | **PASS** |
| Formal Impeccable dual-agent critique | Not attempted | Detector + manual polish only; no two-sub-agent design critique is claimed | **NOT RUN** |
| Engine failure path | route test monkeypatch raising `SpiceEngineError` | HTTP 502, error text visible, no plot, no success banner | **PASS** |
| Parse failure path | route test monkeypatch raising `SpiceParseError` | HTTP 502, error text visible, no plot, no success banner | **PASS** |
| No stale result after a failure | successful AC POST then `RE = 0` POST in the same client | SVG disappears, error remains | **PASS** |
| Model resolution | route test patches `resolve_model` with `QTEST`; unit tests cover env-line, file, bundled and missing-source precedence | Env override wins; the bundled onsemi model is read from `models/` and labelled unverified; a missing source raises instead of guessing | **PASS** |
| `RE >= 0` Lab 03 vs `RE > 0` SPICE | unit tests on both validators | Divider still accepts 0 Ω; SPICE rejects it | **PASS** |
| Illustrative layout vs real data | route test counts `plot-svg` elements after each selected mode and browser checks SVG point labels | DC renders 0 plots, AC renders 1 Bode SVG, Transient renders 1 waveform SVG; every point is generated from parsed ngspice arrays | **PASS** |
| Selected-mode dispatch | browser set AC/Transient radios outside the form and submitted; page evaluate immediately after submit | Running text became `Running ngspice (Transient .tran) — please wait…`; both buttons disabled with `aria-busy`, both result regions `aria-busy`; buttons restored on page load | **PASS** |
| No JavaScript console errors | Playwright MCP console error level after a fresh navigation to `/simulate` | **0 errors** since navigation (favicon 404 removed by adding `<link rel="icon" href="data:,">`); the only HTTP 400 in the historical log is the intentional B7 invalid-input POST | **PASS** |
| Parser fixture regeneration | real ngspice-47 batch run of `parser_fixture.cir`, then parser unit test | OP section has `i(vic)`; IC is positive and comes from the collector branch only | **PASS** |

## Limitations

- The bundled BJT parameters are a cited onsemi vendor model, but they are **not** the
  Instructor Starter Kit model; no instructor-verified DC/AC/transient values can be claimed
  until that `.model` line is supplied. Every browser number above is a real-solver mechanism
  check, not a graded amplifier result. Swapping in the instructor model needs only
  `NGSPICE_MODEL_LINE` or `NGSPICE_MODEL_FILE`; rerun B2–B6 afterwards.
- The −3 dB reference is defined as `max(gain_db) − 3 dB`, matching the handout's midband
  reference idea. For the bundled onsemi model it is 1.80 dB and the interpolated crossing is
  1.30964 Hz; when no crossing exists the page says `not determined in sweep range` rather
  than inventing one. This value will change with the instructor model.
- Only the selected analysis runs per submit. This follows the handout flowchart; the other
  result cards deliberately say `Not run in this mode` instead of filling old values.
- On the 390 px CSS viewport the plot is horizontally scrollable inside its panel. This is a
  legibility choice; the page itself has no horizontal overflow.
- Playwright MCP was **installed and used** for the final B1–B8 pass (2026-11-24). It ran with
  the Microsoft Edge channel in headless mode because the machine has no downloaded Chromium
  bundle. B8 therefore measures the real browser at a resized 1280×800 and 390×844 window
  (`innerWidth`/`scrollWidth` recorded), not a device-emulation profile; mobile network and
  touch behaviour are still **NOT RUN**.
- Impeccable was run as a deterministic detector + manual polish pass after portable Node
  made the CLI available. The formal two-sub-agent critique workflow remains NOT RUN, so no
  full heuristic-scored critique is claimed. The detector was clean at both target viewports
  after the CSS-only fixes; the bundled-vendor-model caveat above is unchanged.
- All `run.log` excerpts and raw files listed above were produced by ngspice-47 in batch
  mode; no trace was generated from constants or hand-drawn points.
