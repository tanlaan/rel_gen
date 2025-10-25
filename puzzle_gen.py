
import argparse
import json
import random
from dataclasses import dataclass, asdict
from typing import List, Dict, Tuple, Optional

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
    lines = ["digraph G {", '  rankdir=LR;']
    nodes = sorted(set([f.subj for f in facts] + [f.obj for f in facts]))
    for n in nodes:
        lines.append(f'  "{n}";')
    for f in facts:
        lines.append(f'  "{f.subj}" -> "{f.obj}" [label="{f.rel}"];')
    lines.append("}")
    return "\n".join(lines)

def _build_path(names: List[str], min_len: int, relations: List[str]) -> Tuple[List[Fact], List[str]]:
    L = max(min_len, 1) + random.randint(0, 2)
    path_facts: List[Fact] = []
    path_ids: List[str] = []

    current = random.choice(names)
    for _ in range(L):
        next_name = random.choice([n for n in names if n != current] or [current])
        rel = random.choice(relations)
        pair = _add_bidirectional_facts(current, rel, next_name)
        path_facts.extend(pair)
        path_ids.append(pair[0].id)
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

    names = _make_names(n_people, allow_duplicates=True)

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

    # Path + extra facts
    path_facts, path_ids = _build_path(names, min_graph_len, relations)

    extra_facts: List[Fact] = []
    extra_edges = random.randint(max(0, n_people - 2), n_people + 2)
    for _ in range(extra_edges):
        if len(names) >= 2:
            a, b = random.sample(names, 2)
        else:
            a = b = names[0]
        rel = random.choice(relations)
        extra_facts.extend(_add_bidirectional_facts(a, rel, b))

    all_facts = _dedupe_facts(path_facts + extra_facts)
    dot = _graph_to_dot(all_facts)

    return Puzzle(
        names=names,
        facts=all_facts,
        seating=seating,
        solution_path=path_ids,
        dot=dot
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

    print("\nSolution path IDs:")
    print("  " + ", ".join(puzzle.solution_path))


if __name__ == "__main__":
    main()
