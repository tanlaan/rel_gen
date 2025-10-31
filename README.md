# Relationship Puzzle Generator

`puzzle_gen.py` builds randomized social-and-seating logic puzzles that can be
solved from the generated facts. The tool emits both structured JSON and a
human-friendly text format, so you can feed the data into other programs or drop
the puzzle straight into docs, games, or interviews.

## Quick Start

```bash
python -m venv .venv && source .venv/bin/activate
python puzzle_gen.py --people 5 --length 3 --difficulty medium --format text --seed 42
```

Without flags the CLI defaults to JSON output for a low-difficulty puzzle with
five people and a minimum solution path length of two.

## CLI Options

- `--people <int>`: number of named participants (default `5`).
- `--length <int>`: minimum number of edges in the solution path (default `2`).
- `--seed <int>`: deterministic runs; also increments for `--count > 1`.
- `--seating-kind {linear,circular}`: force a table layout instead of random.
- `--relations {auto,social,spatial,all}`: relation profile overlay
  (`auto` mixes social and layout-aware spatial hints).
- `--difficulty {low,medium,high}`: unlocks broader relation pools and empty
  chairs (sentinel seats appear as `EMPTY_n` in medium/high).
- `--format {json,text}`: choose machine-readable JSON or colorized text.
- `--dense`: compact mode (JSON becomes minified, text collapses sections).
- `--output <dir>`: write numbered files like `puzzle_001.json` instead of
  printing to stdout (directory is created if needed).
- `--count <int>`: batch generation; seeds auto-increment when provided.

## Difficulty & Relation Profiles

Difficulty gates the catalog of social and spatial relations:

- **low**: classic family and neighbor ties.
- **medium**: adds symmetric social links (`classmate_of`, `mentor_of`, etc.) and
  introduces a single sentinel seat (`EMPTY_1`) in the seating chart.
- **high**: brings in hierarchy (`manager_of`, `reports_to`, `rival_of`) and
  longer-distance spatial facts (`two_left_of`, `clockwise_of`); multiple empty
  chairs may be inserted. Spatial helpers always ignore `EMPTY_n` slots.

The relation profile then filters the unlocked set:

- `auto`: combine social relations with those compatible with the seating kind.
- `social`: people-to-people relations only.
- `spatial`: positions drawn solely from the seating chart (requires ≥2 people).
- `all`: every relation made available by the chosen difficulty.

Whenever you extend the relation list, remember to update `RELATION_CATEGORY`,
`INVERSE`, canonical mappings, and the spatial map helpers inside
`puzzle_gen.py`.

## Output Formats

Every run returns a `Puzzle` dataclass with:

- `names`: ordered list of participants.
- `facts`: bidirectional `Fact` records (`id`, `subj`, `rel`, `obj`).
- `seating`: seating kind plus seat index → name mapping.
- `solution_path`: fact IDs that form the minimal solution chain.
- `dot`: Graphviz-friendly summary (one edge per canonical relation).
- `solution_summary`: readable recap of the solution edges.

Text output highlights social vs. spatial relations using ANSI colors; JSON skips
styling so it stays integration-friendly.

### Example

```bash
python puzzle_gen.py --people 4 --length 2 --seed 7 --format json --dense
```

```json
{
  "names": ["Chris", "Casey", "Cameron", "Robin"],
  "facts": [
    {"id": "f_itcu8w", "subj": "Casey", "rel": "child_of", "obj": "Robin"},
    {"id": "f_ucvbhu", "subj": "Robin", "rel": "parent_of", "obj": "Casey"},
    {"id": "f_el3gux", "subj": "Robin", "rel": "left_of", "obj": "Chris"},
    {"id": "f_ntcchy", "subj": "Chris", "rel": "right_of", "obj": "Robin"},
    ...
  ],
  "seating": {"kind": "linear", "seats": {"1": "Robin", "2": "Casey", "3": "Chris", "4": "Cameron"}},
  "solution_path": ["f_itcu8w", "f_el3gux", "f_nig2ck", "f_by1u5l"],
  "dot": "Cameron:friend_of -> Chris\n...",
  "solution_summary": [
    "Casey:child_of -> Robin",
    "Robin:left_of -> Chris",
    "Chris:neighbor_of -> Robin",
    "Robin:coworker_of -> Chris"
  ],
  "dense": true
}
```

The snippet above is truncated for brevity; the real output includes all facts.

## Programmatic Use

Import `generate` when you want puzzles in-memory:

```python
from puzzle_gen import generate

puzzle = generate(
    n_people=6,
    min_graph_len=3,
    seed=42,
    seating_kind="circular",
    relation_profile="auto",
    difficulty="high",
)
print(puzzle.solution_summary)
```

The function yields the same `Puzzle` dataclass the CLI serializes.

## Development Notes

- The project currently depends only on the Python standard library.
- Future unit tests should live under `tests/` and use `pytest` with seeded runs.
- Run ad-hoc checks with `python - <<'PY'` blocks and deterministic seeds so
  reviewers can reproduce results.
- DOT exports render via `dot -Tpng`, which is handy for visual validation.

Feel free to extend relation pools or add new CLI switches—just keep helper
functions inside `puzzle_gen.py` and follow the existing typing and naming
conventions.
