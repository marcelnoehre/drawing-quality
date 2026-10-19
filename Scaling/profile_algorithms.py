"""How long does each algorithm take, and does it give the same drawing twice?

*Determinism.* Consistency is a Kendall correlation between two drawings of the
same concepts in two scales. It means little until it is known how much an
algorithm moves things when simply run again on the *same* input; an algorithm
that is deterministic moves nothing. Each algorithm is run three times on the same
context and the coordinates are compared exactly.

*Timing.* Each algorithm is timed over a ladder of lattice sizes.

    python profile_algorithms.py                    # the full ladder, writes algorithm_timing.csv
    python profile_algorithms.py --runs 1           # timing only, no determinism check
    python profile_algorithms.py --algorithm fdp

Output: `algorithm_timing.csv`, one row per (algorithm, scale, run). (`profile.csv`
is the ranking's profile of failures, a different file.)
"""

from __future__ import annotations

import argparse
import csv
import shutil
import sys
import time
from pathlib import Path
from xml.etree.ElementTree import parse as parse_xml

from node_extents import ALGORITHMS, HERE, load_generator

GRAPHML_NS = "{http://graphml.graphdrawing.org/xmlns}"

# A ladder across the range we actually intend to draw. The sizes are the concept
# counts recorded in the manifests.
LADDER = [
    ("instruments", "instruments_practice", 46),
    ("olympics", "olympics_structure_format", 139),
    ("instruments", "instruments_capability_practice_making", 319),
    ("instruments", "instruments", 576),
]


def draw_once(algorithm: str, cxt_path: Path, out_root: Path) -> tuple[float, Path]:
    """Run one generator once into a scratch directory; return its runtime and file."""
    module = load_generator(algorithm)
    module.GRAPHML_ROOT = out_root / "graphml" / algorithm
    module.DRAWINGS_ROOT = out_root / "drawings" / algorithm
    target = module.GRAPHML_ROOT / "profile" / f"{module.slug(cxt_path.stem)}.graphml"
    target.unlink(missing_ok=True)

    started = time.perf_counter()
    module.generate("profile", cxt_path.resolve())
    elapsed = time.perf_counter() - started
    return elapsed, target


def coordinates(path: Path) -> dict[str, tuple[str, str]]:
    """Node id -> the x and y as written, compared as text so nothing is rounded away."""
    if not path.exists():
        return {}
    graph = parse_xml(path).getroot().find(f"{GRAPHML_NS}graph")
    result = {}
    for node in graph.findall(f"{GRAPHML_NS}node"):
        values = {d.get("key"): d.text for d in node.findall(f"{GRAPHML_NS}data")}
        result[node.get("id")] = (values.get("x"), values.get("y"))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--algorithm", choices=ALGORITHMS)
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--timeout-note", type=float, default=120.0,
                        help="runtime above which a size is called impractical")
    parser.add_argument("--out", type=Path, default=HERE / "algorithm_timing.csv")
    args = parser.parse_args()

    algorithms = [args.algorithm] if args.algorithm else list(ALGORITHMS)
    scratch = HERE / ".profile-scratch"
    rows = []

    for context, scale, concepts in LADDER:
        cxt_path = HERE / "contexts" / context / f"{scale}.cxt"
        for algorithm in algorithms:
            first: dict | None = None
            for run in range(1, args.runs + 1):
                shutil.rmtree(scratch, ignore_errors=True)
                try:
                    elapsed, target = draw_once(algorithm, cxt_path, scratch)
                    coords = coordinates(target)
                    status = "ok" if coords else "declined"
                except Exception as exc:
                    elapsed, coords, status = 0.0, {}, f"error: {type(exc).__name__}"
                if run == 1:
                    first = coords
                rows.append({
                    "algorithm": algorithm,
                    "context": context,
                    "scale": scale,
                    "concepts": concepts,
                    "run": run,
                    "runtime_s": round(elapsed, 3),
                    "status": status,
                    "identical_to_run_1": "" if run == 1 else (coords == first),
                })
                print(f"  {algorithm:20s} {scale:28s} {concepts:5d} run {run} "
                      f"{elapsed:8.2f}s  {status}"
                      + ("" if run == 1 else f"  identical={coords == first}"))
    shutil.rmtree(scratch, ignore_errors=True)

    with args.out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n{len(rows)} rows -> {args.out.relative_to(HERE)}")
    print(f"\n{'algorithm':20s}" + "".join(f"{c:>9d}" for _, _, c in LADDER) + "   deterministic")
    for algorithm in algorithms:
        cells = []
        for _, scale, _ in LADDER:
            runs = [r for r in rows if r["algorithm"] == algorithm and r["scale"] == scale]
            ok = [r for r in runs if r["status"] == "ok"]
            cells.append(f"{min(r['runtime_s'] for r in ok):9.2f}" if ok
                         else f"{runs[0]['status'][:9]:>9s}")
        repeats = [r["identical_to_run_1"] for r in rows
                   if r["algorithm"] == algorithm and r["run"] > 1 and r["status"] == "ok"]
        verdict = "yes" if repeats and all(repeats) else ("no" if repeats else "unknown")
        print(f"{algorithm:20s}" + "".join(cells) + f"   {verdict}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
