# Repository Guidelines

## Project Structure & Module Organization
- `puzzle_gen.py` houses all runtime logic, including the `generate` entry point and data models (`Fact`, `Seating`, `Puzzle`). Keep new helpers co-located and mark internal-only functions with a leading underscore.
- `__pycache__/` is transient; avoid committing interpreter artefacts. Add future modules beside `puzzle_gen.py`, and put unit tests under `tests/` once the directory exists. Medium and high difficulty modes may allocate sentinel seating slots (`EMPTY_n`) that should remain confined to the seating chart.

## Build, Test, and Development Commands
- `python -m venv .venv && source .venv/bin/activate` creates an isolated environment; the project currently uses only the Python standard library, so no extra installs are required.
- `python puzzle_gen.py [options]` runs the CLI; defaults to `--people 5 --length 2 --difficulty low` and prints JSON unless `--format text` is supplied. Add `--seed` for reproducible runs, and `--dense` for compact output (text sections collapse into single lines; JSON switches to minified form).
- `python - <<'PY' ... PY` blocks are handy for quick manual checks; prefer deterministic seeds (`generate(6, 3, seed=42)`) when sharing output in reviews.

## Coding Style & Naming Conventions
- Follow PEP 8 with four-space indents and 100-character soft wraps. Functions and methods stay in `snake_case`; constants remain `UPPER_SNAKE_CASE`.
- Preserve typing across new code paths—public helpers should accept and return typed data structures and dataclasses where appropriate.
- Add targeted docstrings when behaviour is non-obvious; inline comments should explain reasoning, not syntax.

## Testing Guidelines
- Adopt `pytest` for future automated coverage, placing files at `tests/test_<area>.py`. Mirror generator scenarios with seeded randomness to keep assertions stable.
- Create fixtures that validate genealogical, spatial, and difficulty-aware relation pools (e.g., `difficulty="medium"` includes `mentor_of`, `difficulty="high"` introduces `two_left_of` etc.).
- Run manual sanity checks after changes: instantiate `generate`, inspect `Puzzle.facts`, and confirm the DOT output renders via `dot -Tpng`.

## Commit & Pull Request Guidelines
- History is light (`init commit from gpt`), so establish the convention now: concise, imperative subject lines (≤50 chars) with optional body wrapping at 72 chars.
- Reference issue IDs or user stories in the body, and call out behavioural changes or new CLI flags explicitly.
- Pull requests should include a short summary, test evidence (commands + results), and screenshots or DOT snippets when visual output changes.

## Difficulty & Relation Profiles
- `difficulty` governs relation variety: `low` sticks with the original social/spatial set, `medium` adds symmetric social ties (`classmate_of`, `mentor_of`), and `high` layers in hierarchical roles (`manager_of`, `reports_to`, `rival_of`) plus longer-distance spatial hints (`two_left_of`, `clockwise_of`).
- `medium` and `high` also introduce empty chairs (`EMPTY_n`) into the seating map to create spacing constraints; always guard spatial helpers against these sentinels via `_is_empty`.
- `relation_profile` filters relation categories on top of difficulty. `auto` blends social + layout-aware spatial hints; `social` keeps conversational ties; `spatial` limits to seating-derived relations; `all` enables every relation unlocked by the chosen difficulty.
- Whenever you introduce new relations, update `RELATION_CATEGORY`, `INVERSE`, and canonical mapping tables, and ensure `_build_spatial_relation_map` or genealogical guards support them.
