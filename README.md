# Borderless Meeting Planner

Find a time window where every selected city is inside working hours (09:00–17:00 local time) over the next 7 days. Built with Python, Streamlit, and pytest.

<!-- Screenshot placeholder: sidebar city multiselect, metrics, live clocks, and the
     24-hour view (blue = working hours, green = overlap, gray = outside). -->

## Features

- **Add / remove cities** from a curated list of 36 cities (sidebar, `2 of 36 cities selected`).
- **Metrics**: number of cities and total **overlapping hours in the next 7 days** (e.g. `7.0 h`).
- **Live local clocks** per city with weekday, date, and UTC-offset badge (`↑ Monday 2026-10-13 · UTC+1`).
- **24-hour view per city** — one row of hour cells `00`–`23`:
  - blue = inside working hours, green = all selected cities working (overlap), gray = outside.
- **Warning** when no overlap exists at all (e.g. Tokyo + London): *"No overlapping window in the next 7 days…"*.

## Quick start

Requires Python 3.13.

```bash
python -m venv .venv
source .venv/bin/activate
pip install streamlit pytest

streamlit run app.py
```

The app opens in your browser with London and Bali preselected — try adding or removing cities from the sidebar and watch the overlap stat and the green cells update.

## Tests

```bash
pytest
```

- `test_logic.py` — acceptance tests for all computation, pinned to a fixed `now` so results are deterministic (e.g. London+Bali → `7.0 h`, London+Sydney → `0.0 h`).
- `test_app.py` — UI smoke tests using Streamlit's built-in `AppTest` (no extra dependencies).

Run a single test with `pytest test_logic.py::test_london_bali -q`.

## Project layout

| File | Purpose |
|---|---|
| `app.py` | Streamlit UI — display only, reads the clock and delegates all computation |
| `logic.py` | Pure logic — overlap scan, local times, cell states; no Streamlit imports |
| `test_logic.py` / `test_app.py` | pytest suites for logic and UI |
| `SPEC.md` | Full specification: features, data structures, acceptance criteria |

## How overlap is computed

- Working hours are **local, start-inclusive, end-exclusive**: `[09:00, 17:00)`.
- The horizon is **rolling**: `[now, now + 7 days)`, scanned in **1-minute steps**.
- A minute counts only if **every** selected city is inside working hours at that instant; consecutive good minutes are merged into windows.
- All conversions use the stdlib `zoneinfo` (DST-safe) — no fixed offsets, no third-party time-zone libraries.

See [SPEC.md](SPEC.md) for the full specification and the worked example test cases.

## Rules of the codebase

- Plan before changing code; pure logic stays in `logic.py`, UI in `app.py` — never mixed.
- Every new function in `logic.py` must have a test in `test_logic.py`.
- After every change, run `pytest` and fix until all tests pass.
- Only extra libraries allowed: `streamlit` and `pytest` (time zones via `zoneinfo`).
