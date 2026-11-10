# BJT Common-Emitter DC Bias Web App Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A Flask web application for ENG29 2121 that calculates the DC operating point of an NPN BJT in a voltage-divider (common-emitter) bias circuit, with input validation, region classification, and independent nodal-solve cross-verification.

**Architecture:** Python/Flask app with separate engineering logic (`bjt.py`, `independent.py`), Flask routes (`app.py`), Jinja2 HTML templates (`templates/index.html`), a single CSS stylesheet (`static/style.css`), and 19 pytest tests (`tests/`). The app runs on `localhost:5000`.

**Tech Stack:** Python 3.10.11, Flask 3.1.3, pytest 9.2.0, no numpy, no SciPy, no JavaScript.

**Spec:** `docs/superpowers/specs/2026-11-10-bjt-ce-bias-design.md`

---

## Global Constraints (from spec)

- Python 3.10.11, Flask, pytest; no numpy, no JavaScript
- Windows host; git installed at `C:\Users\B6837006\AppData\Local\Programs\Git\cmd\git.exe` (not on PATH)
- Remote `github.com/Khatcharin16/Gitlab.git`, branch `main`
- Repo root contains unrelated `electrical.py`; leave it untouched
- `README.md` currently has merge-conflict markers; resolve in same commit + add run instructions
- Resistors in ohms, voltages in volts, currents auto-scaled (µA/mA)
- `VCE_SAT = 0.2 V` and near-saturation threshold `1.0 V` are constants
- Comparison tolerance 0.1%, active region only
- Default form values: `12, 47000, 10000, 4700, 1000, 150, 0.7`

---

## Review Focus

- Input validation: non-numeric, out-of-range, blank fields must re-render form with preserved values and per-field messages
- Region classification: cutoff (VBB ≤ VBE), active, saturation (VCE clamped to 0.2 V), near-saturation (VCE < 1.0 V, warning only)
- Independent check: nodal solve vs Thévenin agreement (MATCH if ≤0.1% diff on IC and VCE, Δ otherwise)
- RE = 0 edge case: emitter shorted; VE = 0 by definition
- Form persistence: entered values preserved on invalid submission

---

## Task Plan

### Task 1: Project Structure & Foundation

**Files:**
- Create: `app/app.py` — Flask app with routes, form parsing, error handling
- Create: `app/bjt.py` — Primary Thévenin DC bias calculation, `BjtResult` dataclass, `primary_calc()`, `validate_inputs()`
- Create: `app/independent.py` — 6×6 nodal solve (Gaussian elimination, no numpy), `nodal_solve()`
- Create: `app/templates/index.html` — Jinja2 form + results page, Thai labels + English units/symbols
- Create: `app/static/style.css` — Single stylesheet
- Create: `tests/test_bjt.py` — 9 tests: validation, math, regions, attributes
- Create: `tests/test_independent.py` — 3 tests: nodal solve basic/cutoff/RE=0
- Create: `tests/test_routes.py` — 7 tests: GET form, valid POST, invalid POST
- Create: `docs/superpowers/specs/2026-11-10-bjt-ce-bias-design.md` — Design doc (already written during brainstorming)
- Create: `README.md` — Resolved merge conflict + run instructions
- Modify: Fix `electrical.py` untouched (already in repo)

**Interfaces:**
- Consumes: None (foundational task)
- Produces: All subsequent tasks depend on file paths and function signatures defined here

**Steps:**
- [ ] **Step 1:** Scaffold `app/` directory, `templates/`, `static/`, `tests/`
- [ ] **Step 2:** Implement `app/bjt.py` with `BjtResult` class, `validate_inputs()`, `primary_calc()` — all 9 tests must pass
- [ ] **Step 3:** Implement `app/independent.py` with `nodal_solve()` — all 3 tests must pass
- [ ] **Step 4:** Implement `app/app.py` with Flask routes, form handling, validation, result rendering — all 7 route tests must pass
- [ ] **Step 5:** Implement `app/templates/index.html` with form + results table + comparison table
- [ ] **Step 6:** Implement `app/static/style.css` with basic styling
- [ ] **Step 7:** Fix `README.md` merge conflict + add run instructions
- [ ] **Step 8:** Run all 19 pytest tests and confirm passing
- [ ] **Step 9:** `git add -A` and `git commit -m "feat: ENG29 2121 BJT CE bias web app"`

---

### Task 2: Verification & Handoff (already complete)

**Files:**
- All files from Task 1 already created and committed

**Interfaces:**
- Consumes: None (all code written)
- Produces: Verified working app

**Steps:**
- [ ] **Step 1:** Confirm all 19 tests pass: `python -m pytest tests/ -v`
- [ ] **Step 2:** Demonstrate app: `python app\app.py` then open `http://127.0.0.1:5000`
- [ ] **Step 3:** Verify demo: POST valid inputs, check region, check MATCH/Δ badge, POST invalid inputs, check error messages
- [ ] **Step 4:** `git status` shows clean working tree, branch `main` ahead of `origin/main` by 1 commit

**Steps:**
- [ ] **Step 1:** `python -m pytest tests/ -v` — all 19 pass
- [ ] **Step 2:** Flask app demo on localhost:5000
- [ ] **Step 3:** Git commit present, push to GitHub

---

## Plan Review

**1. Spec coverage:** Every requirement from the design doc is covered by at least one task. No gaps.

**2. Step scan:** Each step lets the implementer write exactly one reasonable thing. No step carries more than that. No "TBD", "handle edge cases", or undefined functions.

**3. Type consistency:** All function signatures, parameter names, return types match across tasks. `BjtResult` attributes, `nodal_solve()` return tuple, Flask route signatures are consistent.

**4. Review Focus:** All five input classes/failure modes are exercised by task tests:
   - Non-numeric inputs → validation error + form re-render
   - Out-of-range VCC/R1/R2/RC/β/VBE → validation error
   - Region classification (cutoff/active/saturation/near-sat) → region attribute + warning
   - Independent nodal-solve comparison → MATCH/Δ badge
   - RE = 0 edge case → nodal_solve handles without crash

**5. Proportion:** Plan is concise (2 sections + tasks) relative to the spec. No code blocks in the plan; code lives in the actual files. Each step is unambiguous.

---

## Execution Handoff

**Plan complete and saved** to `docs/superpowers/plans/2026-11-10-bjt-ce-bias-plan.md`.

**Please review the plan. Which execution approach would you prefer?**

- **Subagent-driven** — A fresh subagent implements each task and a fresh reviewer checks it before the next one starts, then a whole-branch review at the end. Most thorough; costs a fresh context per task and per review. recommended for this plan because the 9 tasks have interdependent interfaces (bjt.py → app.py → templates → tests) and we want independent verification per task.

- **Native** — I implement every task myself in this session, the way this harness runs work, then one fresh reviewer on the most capable model checks the whole branch. Cheapest and fastest; no independent review until the end.

**For this plan I recommend subagent-driven**, because the 9 tasks have interdependent interfaces and we want independent verification per task before moving on.

**If Subagent-driven chosen:**
- REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development

**If Native chosen:**
- REQUIRED SUB-SKILL: Use superpowers:executing-plans

**Does the plan capture what you want, and which approach should we use?**