# AGENTS.md

## Project status

Greenfield repo: no source code, README, package manifest, git history, or CI exists yet — only `.venv/`. Verify claims against actual files before assuming any structure below has been implemented.

## Environment (verified)

- Python environment: `.venv/` created from Miniconda Python **3.13.12** (not a system Python).
  - Activate: `source .venv/bin/activate`
  - The venv is not reproducible from a lockfile — there is **no** `requirements.txt`, `pyproject.toml`, or `uv.lock`. Installed packages exist only inside `.venv`.
- Intended stack (inferred from installed packages, not yet used in code):
  - **Streamlit** 1.65 (UI, `streamlit` CLI in `.venv/bin`)
  - **Starlette** + **uvicorn** (ASGI backend; note: `fastapi` is *not* installed)
  - Data: `pandas` 3.0, `numpy`, `pyarrow`; tests: `pytest` 9
- Commands so far:
  - Run tests: `pytest` (no tests or pytest config exist yet)
  - Run UI: `streamlit run <app.py>` (no entrypoint exists yet)
  - Run server: `uvicorn <module>:app` (no app exists yet)

# Working rules

- Always make a plan before changing any code.
- Pure logic goes in `logic.py`, UI goes in `app.py`. Never mix them.
- Every new function in `logic.py` must have a test in `test_logic.py`.
- After every change, run `pytest` and fix until all tests pass.
- Use `zoneinfo` for time zones. The only extra libraries allowed are `streamlit` and `pytest`.

## Conventions to establish when writing the first code

- Add a `pyproject.toml` (or `requirements.txt`) pinning what's in `.venv` so the environment is reproducible; until then, don't delete or rebuild `.venv` casually — it's the only record of dependencies.
- Keep generated/runtime artifacts (`.venv/`, `__pycache__/`, Streamlit's `.streamlit/` secrets) out of version control when git is initialized.