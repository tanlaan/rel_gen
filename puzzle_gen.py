
import argparse
import json
import random
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Set, Tuple

FIRST_NAMES = [
    "Alex", "Sam", "Jordan", "Taylor", "Casey", "Riley", "Avery", "Morgan", "Quinn", "Reese",
    "Chris", "Jamie", "Cameron", "Drew", "Logan", "Devon", "Shawn", "Dana", "Frankie", "Jesse",
    "Robin", "Kelly", "Leslie", "Skyler", "Rowan", "Sawyer", "Parker", "Elliot", "Harley", "Remy"
]

COMMON_RELATIONS = [
    "parent_of", "child_of", "sibling_of", "cousin_of", "spouse_of",
    "friend_of", "coworker_of", "neighbor_of",
]

LINEAR_RELATIONS = ["left_of", "right_of", "next_to"]

CIRCULAR_RELATIONS = ["left_of", "right_of", "next_to", "across_from"]

RELATION_SETS = {
    "common": COMMON_RELATIONS,
    "linear": LINEAR_RELATIONS,
    "circular": CIRCULAR_RELATIONS,
}

VALID_SEATING_KINDS = ("linear", "circular")
DEFAULT_RELATION_PROFILE = "auto"
VALID_RELATION_PROFILES = ("auto", "social", "spatial", "all")

RELATION_CATEGORY = {rel: "social" for rel in COMMON_RELATIONS}
for rel in set(LINEAR_RELATIONS + CIRCULAR_RELATIONS):
    RELATION_CATEGORY.setdefault(rel, "spatial")

ANSI_COLORS = {
    "social": "\033[34m",   # blue
    "spatial": "\033[33m",  # yellow
}
ANSI_RESET = "\033[0m"

SPATIAL_RELATIONS = set(LINEAR_RELATIONS) | {"across_from"}

CANONICAL_RELATIONS = {
    "parent_of": ("parent_of", False),
    "child_of": ("parent_of", True),
    "left_of": ("left_of", False),
    "right_of": ("left_of", True),
}


def _build_spatial_relation_map(seating: "Seating") -> Dict[Tuple[str, str], Set[str]]:
    seats = seating.seats
    if not seats:
        return {}

    ordered = [name for _, name in sorted(seats.items())]
    positions = {name: idx for idx, name in enumerate(ordered)}
    relation_map: Dict[Tuple[str, str], Set[str]] = {}

    if seating.kind == "linear":
        for subj in ordered:
            for obj in ordered:
                if subj == obj:
                    continue
                idx_subj = positions[subj]
                idx_obj = positions[obj]
                if idx_subj < idx_obj:
                    relation_map.setdefault((subj, obj), set()).add("left_of")
                if idx_subj > idx_obj:
                    relation_map.setdefault((subj, obj), set()).add("right_of")
                if abs(idx_subj - idx_obj) == 1:
                    relation_map.setdefault((subj, obj), set()).add("next_to")
        return relation_map

    # circular seating
    n = len(ordered)
    for obj in ordered:
        idx_obj = positions[obj]
        left_name = ordered[(idx_obj - 1) % n]
        right_name = ordered[(idx_obj + 1) % n]
        for subj, rel in ((left_name, "left_of"), (right_name, "right_of")):
            relation_map.setdefault((subj, obj), set()).add(rel)
            relation_map.setdefault((subj, obj), set()).add("next_to")
        if n % 2 == 0:
            across_name = ordered[(idx_obj + n // 2) % n]
            if across_name != obj:
                relation_map.setdefault((across_name, obj), set()).add("across_from")

    return relation_map


def _relation_family_type(rel: str) -> Optional[str]:
    if rel in ("parent_of", "child_of"):
        return "parent_child"
    if rel == "sibling_of":
        return "sibling"
    if rel == "cousin_of":
        return "cousin"
    if rel == "spouse_of":
        return "spouse"
    return None


def _register_family_relation(
    pair_state: Dict[frozenset, str], subj: str, rel: str, obj: str
) -> None:
    family_type = _relation_family_type(rel)
    if family_type is None:
        return
    if subj == obj:
        return
    key = frozenset((subj, obj))
    pair_state[key] = family_type


def _valid_relations_between(
    subj: str,
    obj: str,
    relations: List[str],
    spatial_map: Dict[Tuple[str, str], Set[str]],
    pair_state: Dict[frozenset, str],
) -> List[str]:
    allowed_spatial = spatial_map.get((subj, obj))
    valid: List[str] = []
    pair_key = frozenset((subj, obj))
    existing_family = pair_state.get(pair_key)
    for rel in relations:
        family_type = _relation_family_type(rel)
        if subj == obj and family_type is not None:
            continue
        if existing_family and family_type and existing_family != family_type:
            continue
        if rel in SPATIAL_RELATIONS:
            if allowed_spatial and rel in allowed_spatial:
                valid.append(rel)
        else:
            valid.append(rel)
    return valid


def _pick_next_relation(
    current: str,
    names: List[str],
    relations: List[str],
    spatial_map: Dict[Tuple[str, str], Set[str]],
    pair_state: Dict[frozenset, str],
) -> Tuple[str, str]:
    candidates = names[:]
    random.shuffle(candidates)
    viable: List[Tuple[str, List[str]]] = []
    for name in candidates:
        if len(names) > 1 and name == current:
            continue
        valid = _valid_relations_between(current, name, relations, spatial_map, pair_state)
        if valid:
            viable.append((name, valid))
    if viable:
        next_name, valid = random.choice(viable)
        return next_name, random.choice(valid)

    valid_self = _valid_relations_between(current, current, relations, spatial_map, pair_state)
    if valid_self:
        return current, random.choice(valid_self)

    raise ValueError("Unable to find a valid relation for path construction.")


def _pick_relation_pair(
    names: List[str],
    relations: List[str],
    spatial_map: Dict[Tuple[str, str], Set[str]],
    pair_state: Dict[frozenset, str],
) -> Tuple[str, str, str]:
    viable: List[Tuple[str, str, List[str]]] = []
    for subj in names:
        for obj in names:
            if len(names) > 1 and subj == obj:
                continue
            valid = _valid_relations_between(subj, obj, relations, spatial_map, pair_state)
            if valid:
                viable.append((subj, obj, valid))

    if not viable:
        raise ValueError("Unable to identify any valid relation pair.")

    subj, obj, valid = random.choice(viable)
    return subj, obj, random.choice(valid)


def _relation_pool(seating_kind: str, relation_profile: Optional[str]) -> List[str]:
    """Select relations compatible with the seating layout and requested profile."""
    if seating_kind not in VALID_SEATING_KINDS:
        raise ValueError(f"Unsupported seating kind: {seating_kind}")

    profile = (relation_profile or DEFAULT_RELATION_PROFILE).lower()
    if profile == "auto":
        groups = ("common", seating_kind)
    elif profile == "social":
        groups = ("common",)
    elif profile == "spatial":
        groups = (seating_kind,)
    elif profile == "all":
        groups = ("common", "linear", "circular")
    else:
        raise ValueError(f"Unsupported relation profile: {relation_profile}")

    deduped: List[str] = []
    seen = set()
    for group in groups:
        for rel in RELATION_SETS[group]:
            if rel in seen:
                continue
            seen.add(rel)
            deduped.append(rel)
    return deduped


def _candidate_edges(
    names: List[str],
    relations: List[str],
    spatial_map: Dict[Tuple[str, str], Set[str]],
) -> List[Tuple[str, str, str]]:
    pair_state: Dict[frozenset, str] = {}
    seen = set()
    valid_edges: List[Tuple[str, str, str]] = []
    for subj in names:
        for obj in names:
            if len(names) > 1 and subj == obj and any(r in SPATIAL_RELATIONS for r in relations):
                continue
            valids = _valid_relations_between(subj, obj, relations, spatial_map, pair_state)
            for rel in valids:
                key = (subj, rel, obj)
                if key in seen:
                    continue
                seen.add(key)
                valid_edges.append(key)
            for rel in valids:
                _register_family_relation(pair_state, subj, rel, obj)
    return valid_edges

INVERSE = {
    "parent_of": "child_of",
    "child_of": "parent_of",
    "sibling_of": "sibling_of",
    "cousin_of": "cousin_of",
    "spouse_of": "spouse_of",
    "friend_of": "friend_of",
    "coworker_of": "coworker_of",
    "neighbor_of": "neighbor_of",
    "left_of": "right_of",
    "right_of": "left_of",
    "next_to": "next_to",
    "across_from": "across_from",
}

def _rand_id(prefix: str, k: int = 6) -> str:
    import string
    return f"{prefix}_" + "".join(random.choices(string.ascii_lowercase + string.digits, k=k))

def _make_names(n: int, allow_duplicates: bool = True) -> List[str]:
    if allow_duplicates:
        return [random.choice(FIRST_NAMES) for _ in range(n)]
    chosen = random.sample(FIRST_NAMES, k=min(n, len(FIRST_NAMES)))
    if n > len(FIRST_NAMES):
        for i in range(len(FIRST_NAMES), n):
            chosen.append(f"Name{i-len(FIRST_NAMES)+1}")
    return chosen

@dataclass(frozen=True)
class Fact:
    id: str
    subj: str
    rel: str
    obj: str

@dataclass
class Seating:
    kind: str
    seats: Dict[int, str]

@dataclass
class Puzzle:
    names: List[str]
    facts: List[Fact]
    seating: Seating
    solution_path: List[str]
    dot: str
    solution_summary: List[str]

def _emit_fact(a: str, rel: str, b: str) -> Fact:
    return Fact(id=_rand_id("f"), subj=a, rel=rel, obj=b)

def _add_bidirectional_facts(a: str, rel: str, b: str) -> List[Fact]:
    fwd = _emit_fact(a, rel, b)
    inv = INVERSE.get(rel, None)
    if inv is None:
        return [fwd]
    back = _emit_fact(b, inv, a)
    return [fwd, back]

def _graph_to_dot(facts: List[Fact]) -> str:
    dedup = {}
    for fact in facts:
        rel, swap = CANONICAL_RELATIONS.get(fact.rel, (fact.rel, False))
        subj, obj = (fact.obj, fact.subj) if swap else (fact.subj, fact.obj)
        inverse = INVERSE.get(rel)
        if inverse == rel and subj > obj:
            subj, obj = obj, subj
        key = (subj, rel, obj)
        dedup[key] = f"{subj}:{rel} -> {obj}"

    lines = [value for _, value in sorted(dedup.items(), key=lambda item: item[0])]
    return "\n".join(lines)


def _colorize_relation_line(line: str) -> str:
    try:
        subj, rest = line.split(":", 1)
        rel, obj = rest.split(" -> ", 1)
    except ValueError:
        return line
    category = RELATION_CATEGORY.get(rel)
    color = ANSI_COLORS.get(category)
    if color:
        rel = f"{color}{rel}{ANSI_RESET}"
    return f"{subj}:{rel} -> {obj}"

def _build_path(
    names: List[str],
    min_len: int,
    relations: List[str],
    spatial_map: Dict[Tuple[str, str], Set[str]],
    pair_state: Dict[frozenset, str],
) -> Tuple[List[Fact], List[str]]:
    L = max(min_len, 1) + random.randint(0, 2)
    path_facts: List[Fact] = []
    path_ids: List[str] = []

    current = random.choice(names)
    for _ in range(L):
        next_name, rel = _pick_next_relation(current, names, relations, spatial_map, pair_state)
        pair = _add_bidirectional_facts(current, rel, next_name)
        path_facts.extend(pair)
        path_ids.append(pair[0].id)
        _register_family_relation(pair_state, current, rel, next_name)
        current = next_name

    return path_facts, path_ids

def _dedupe_facts(facts: List[Fact]) -> List[Fact]:
    seen = set()
    out = []
    for f in facts:
        key = (f.subj, f.rel, f.obj)
        if key in seen:
            continue
        seen.add(key)
        out.append(f)
    return out

def generate(
    n_people: int,
    min_graph_len: int,
    seed: Optional[int] = None,
    *,
    seating_kind: Optional[str] = None,
    relation_profile: Optional[str] = None
) -> Puzzle:
    if seed is not None:
        random.seed(seed)

    names = _make_names(n_people, allow_duplicates=False)

    # Seating
    if seating_kind is None:
        kind = random.choice(VALID_SEATING_KINDS)
    else:
        kind = seating_kind.lower()
        if kind not in VALID_SEATING_KINDS:
            raise ValueError(f"Unsupported seating kind: {seating_kind}")

    order = names[:]
    random.shuffle(order)
    seats = {i + 1: order[i] for i in range(len(order))}
    seating = Seating(kind=kind, seats=seats)

    relations = _relation_pool(kind, relation_profile)
    if relations and all(rel in SPATIAL_RELATIONS for rel in relations) and len(names) < 2:
        raise ValueError("Spatial relations require at least two people.")
    spatial_map = _build_spatial_relation_map(seating)
    candidate_edges = _candidate_edges(names, relations, spatial_map)
    max_path = len(candidate_edges)
    if max_path == 0:
        raise ValueError("No valid relations can be formed with the current configuration.")
    if min_graph_len > max_path:
        raise ValueError(
            f"Requested path length {min_graph_len} exceeds available unique relations ({max_path})."
        )
    pair_state: Dict[frozenset, str] = {}

    # Path + extra facts
    path_facts, path_ids = _build_path(names, min_graph_len, relations, spatial_map, pair_state)

    extra_facts: List[Fact] = []
    extra_edges = random.randint(max(0, n_people - 2), n_people + 2)
    for _ in range(extra_edges):
        try:
            a, b, rel = _pick_relation_pair(names, relations, spatial_map, pair_state)
        except ValueError:
            break
        extra_facts.extend(_add_bidirectional_facts(a, rel, b))
        _register_family_relation(pair_state, a, rel, b)

    all_facts = _dedupe_facts(path_facts + extra_facts)
    dot = _graph_to_dot(all_facts)
    id_to_fact = {fact.id: fact for fact in all_facts}
    solution_summary = []
    for fact_id in path_ids:
        fact = id_to_fact.get(fact_id)
        if fact is None:
            continue
        solution_summary.append(f"{fact.subj}:{fact.rel} -> {fact.obj}")

    return Puzzle(
        names=names,
        facts=all_facts,
        seating=seating,
        solution_path=path_ids,
        dot=dot,
        solution_summary=solution_summary,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a relationship puzzle.")
    parser.add_argument(
        "--people",
        type=int,
        default=5,
        help="Number of people to include (default: 5).",
    )
    parser.add_argument(
        "--length",
        type=int,
        default=2,
        help="Minimum graph length for the solution path (default: 2).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducible output.",
    )
    parser.add_argument(
        "--seating-kind",
        choices=VALID_SEATING_KINDS,
        help=f"Force a seating layout ({', '.join(VALID_SEATING_KINDS)}).",
    )
    parser.add_argument(
        "--relations",
        choices=VALID_RELATION_PROFILES,
        help="Select relation profile (auto, social, spatial, all).",
    )
    parser.add_argument(
        "--format",
        choices=("json", "text"),
        default="json",
        help="Output format (default: json).",
    )
    args = parser.parse_args()

    puzzle = generate(
        args.people,
        args.length,
        seed=args.seed,
        seating_kind=args.seating_kind,
        relation_profile=args.relations,
    )

    if args.format == "json":
        print(json.dumps(asdict(puzzle), indent=2))
        return

    print(f"Seating ({puzzle.seating.kind}):")
    for pos, name in sorted(puzzle.seating.seats.items()):
        print(f"  {pos}: {name}")

    print("\nFacts:")
    for fact in puzzle.facts:
        print(f"  {fact.id}: {fact.subj} {fact.rel} {fact.obj}")

    if puzzle.dot:
        print("\nRelations:")
        for line in puzzle.dot.splitlines():
            print(f"  {_colorize_relation_line(line)}")

    print("\nSolution path IDs:")
    print("  " + ", ".join(puzzle.solution_path))

    if puzzle.solution_summary:
        print("\nSolution summary:")
        for line in puzzle.solution_summary:
            print(f"  {_colorize_relation_line(line)}")


if __name__ == "__main__":
    main()
