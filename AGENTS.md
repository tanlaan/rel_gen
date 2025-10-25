# Repository Guidelines

## Project Structure & Module Organization
- `puzzle_gen.py` houses all runtime logic, including the `generate` entry point and data models (`Fact`, `Seating`, `Puzzle`). Keep new helpers co-located and mark internal-only functions with a leading underscore.
- `__pycache__/` is transient; avoid committing interpreter artefacts. Add future modules beside `puzzle_gen.py`, and put unit tests under `tests/` once the directory exists.

## Build, Test, and Development Commands
- `python -m venv .venv && source .venv/bin/activate` creates an isolated environment; the project currently uses only the Python standard library, so no extra installs are required.
- `python -m puzzle_gen` is not wired up; work interactively instead: `python` → `from puzzle_gen import generate`.
- `python - <<'PY' ... PY` blocks are handy for quick manual checks; prefer deterministic seeds (`generate(6, 3, seed=42)`) when sharing output in reviews.

## Coding Style & Naming Conventions
- Follow PEP 8 with four-space indents and 100-character soft wraps. Functions and methods stay in `snake_case`; constants remain `UPPER_SNAKE_CASE`.
- Preserve typing across new code paths—public helpers should accept and return typed data structures and dataclasses where appropriate.
- Add targeted docstrings when behaviour is non-obvious; inline comments should explain reasoning, not syntax.

## Testing Guidelines
- Adopt `pytest` for future automated coverage, placing files at `tests/test_<area>.py`. Mirror generator scenarios with seeded randomness to keep assertions stable.
- When adding fixtures, prefer small graphs (≤8 people) that exercise both seating layouts and inverse relation handling.
- Run manual sanity checks after changes: instantiate `generate`, inspect `Puzzle.facts`, and confirm the DOT output renders via `dot -Tpng`.

## Commit & Pull Request Guidelines
- History is light (`init commit from gpt`), so establish the convention now: concise, imperative subject lines (≤50 chars) with optional body wrapping at 72 chars.
- Reference issue IDs or user stories in the body, and call out behavioural changes or new CLI flags explicitly.
- Pull requests should include a short summary, test evidence (commands + results), and screenshots or DOT snippets when visual output changes.
