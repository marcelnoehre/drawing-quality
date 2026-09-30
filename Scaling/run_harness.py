"""Draw every scale with every algorithm, score the drawings, compare across scales.

Three passes, each idempotent, each writing one long-format CSV. Long format
rather than wide: contexts have different numbers of scales, so a column per scale
would break the first time a context is added, while different scale counts are
just different row counts here. Anything else is a join on (context, scale).

    python run_harness.py                    # draw what is missing, then score, then compare
    python run_harness.py --draw-only
    python run_harness.py --context instruments --algorithm fdp

Outputs, all in this directory:

| File | One row per | Notes |
|---|---|---|
| `scales.csv` | scale | copied from the per-context manifests |
| `drawings.csv` | scale x algorithm | runtime, status, and the metric scores |
| `consistency.csv` | nested pair x algorithm | Kendall tau on x-ranks, rank drift |

Drawings land in `graphml/<algorithm>/<context>/<scale>.graphml` and
`drawings/<algorithm>/<context>/<scale>.pdf`, beside `contexts/` rather than in
the surrounding repository's tree.

**Declines are data, not errors.** `cole_ducrou_eklund` refuses contexts where it
cannot find a satisfactory layer diagram, and other algorithms may fail on
particular structures. Every attempt is recorded with a status and the reason, so
the design is visibly unbalanced rather than silently so, and so that which
structures an algorithm refuses can be looked at later.

**Seeds.** None of the generators exposes one, so a run cannot be pinned by seed;
what can be done is to rerun and measure the spread, which is what
`profile_algorithms.py` does and what the rerun null in RQ4 needs.
"""

from __future__ import annotations

import argparse
import contextlib
import csv
import io
import sys
import time
from itertools import combinations
from pathlib import Path

import odis

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(HERE))

from check_node_mapping import ALGORITHMS, EXCLUDED, load_generator  # noqa: E402
from consistency import compare, tau_by_stratum  # noqa: E402
from graphml_loader import load_drawing  # noqa: E402
from nulls import permutation_null  # noqa: E402
from lattice_metrics import evaluate_all, load_layout, structural_width  # noqa: E402

CONTEXTS = HERE / "contexts"
GRAPHML = HERE / "graphml"
DRAWINGS = HERE / "drawings"

# Wall-clock budgets the generators impose on themselves, in seconds. These are
# parameters of the result, not implementation details: an anytime algorithm that
# consumes its budget returns the best layout it reached, which is a legitimate
# drawing but a different one from what it would return given longer. Every
# drawing therefore records the budget, the time taken, and whether the budget was
# consumed, so that any size trend can be read with that in view.
#
# `cole_ducrou_eklund` is bounded by a search budget rather than a clock
# (n1=5, n2=3, max_solutions=5000); when it exhausts that it declines outright,
# which shows up as a status rather than as a flag.
BUDGET_S = {
    "dimdraw": 60.0,      # context.draw('dimdraw', 60000), anytime
    # FDP_Additive_Features(..., {'timeout_s': 60.0}), keeping its best iterate. It
    # is checked once per optimiser iteration and bounds nothing before the
    # optimiser, so it cannot be relied on; see REQUIRES_CLARIFIED below.
    "fdp": 60.0,
    "sugiyama": None,     # timeout_ms=None
    "freese": None,
    "aeschlimann_schmid": None,
    "redraw": None,       # bounded by its dimension fallback, not by a clock
    "cole_ducrou_eklund": None,
}
# Below this fraction of the budget the run is taken to have finished on its own.
COMPLETION_MARGIN = 0.95

# Feasibility is per algorithm, not a property of the lattice. `drawable` in the
# scale manifests says whether a lattice is worth drawing at all; this says which
# algorithm can actually be asked. The numbers come from timing, not from taste:
#
#   freese     1.8 s at 46, 464 s at 319. Usable but slow; 576 not yet measured.
#   dimdraw    completes to about 30 concepts and is anytime above that, so it
#              always returns and is flagged by completed_within_budget instead.
#   fdp        9.8 s at 319. Its limit is not size at all; see below.
#   the rest   under two seconds at 576 where measured.
#
# None means no measured limit. A scale beyond the limit is recorded as skipped
# with the reason, not attempted, so a sweep cannot hang on one cell.
FEASIBLE_MAX_CONCEPTS = {
    "freese": 400,
    "cole_ducrou_eklund": 400,
    "redraw": 400,
    "fdp": None,
    "aeschlimann_schmid": None,
    "sugiyama": None,
    "dimdraw": None,
}


def equivalent_attributes(path: Path) -> list[tuple[str, str]]:
    """Pairs of attributes that imply each other, i.e. that have equal extents.

    A context containing one is not attribute-clarified. Ours regularly are not,
    and legitimately so: a scale's attributes are the conjunctions we chose, and
    two of them having the same extent is a fact about the data, not an accident
    of construction. `Requires electricity` and `Electrical sound` hold of exactly
    the same instruments.
    """
    context = odis.FormalContext.from_file(str(path))
    attributes = list(context.attributes)
    closures = {m: context.attribute_hull([m]).to_frozenset() for m in attributes}
    return [(a, b) for a, b in combinations(attributes, 2)
            if b in closures[a] and a in closures[b]]


# Preconditions an algorithm needs from the context itself, checked before it is
# asked. Unlike the size limits above, these are not about cost.
#
#   fdp  does not terminate on a context with two equivalent attributes, at any
#        size. `_initialize_vectors` places each non-coatom attribute only once
#        every attribute implied by it has a position; two attributes implying
#        each other wait for one another forever, and the queue cycles. `timeout_s`
#        cannot stop it: that is checked in the optimiser's callback, which this
#        never reaches. Reproduced at 17 concepts, and removing one attribute of
#        the pair draws 319 concepts in 9.8 s. See tests/test_fdp_termination.py
#        and the report in pipeline.md.
#
# Do not "fix" this by clarifying the contexts. The attribute set is the view we
# chose, and dropping a label because it is coextensive with another edits that
# view silently, in every figure label and in the conjunctive normal form. Eleven
# of the 39 contexts and scales here have such a pair, four of them imported
# unchanged from the surrounding repository's real-world collection, which is a
# finding about real data that clarifying would erase. The skip is the right
# behaviour until fdp is fixed; pipeline.md, "Decided: we do not clarify the
# scales", has the argument in full.
REQUIRES_CLARIFIED = ("fdp",)


def manifests() -> list[dict]:
    """Every scale of every context, from the manifests the scale build wrote."""
    rows = []
    for manifest in sorted(CONTEXTS.glob("*/manifest.csv")):
        with manifest.open(encoding="utf-8") as f:
            rows.extend(csv.DictReader(f))
    return rows


def scale_path(context: str, scale: str) -> Path:
    return CONTEXTS / context / f"{scale}.cxt"


def slug(scale: str) -> str:
    """His generators name the output file after a slug of the .cxt stem.

    ``slug()`` in every generate.py lowercases and turns hyphens into
    underscores, so `family-practice.cxt` is written as `family_practice.graphml`.
    Looking for the unslugged name makes a successful drawing look like a decline,
    which is exactly what it did until this was found.
    """
    return scale.lower().replace("-", "_")


def graphml_path(algorithm: str, context: str, scale: str) -> Path:
    return GRAPHML / algorithm / context / f"{slug(scale)}.graphml"


# ---------------------------------------------------------------------------
# Pass 1: draw
# ---------------------------------------------------------------------------

class MissingDrawing(RuntimeError):
    """A generator returned normally and produced neither a drawing nor a reason.

    This exists because the opposite convention, inferring a decline from a
    missing file, failed silently and directionally: his generators name the
    output after a slug of the .cxt stem, turning `family-practice` into
    `family_practice`, so looking for the unslugged name turned every successful
    drawing of a hyphenated scale into a recorded decline. Declines are now only
    ever taken from what the generator itself reports; anything else is a crash.
    """


def draw(algorithm: str, context: str, scale: str) -> dict:
    """Draw one scale with one algorithm, unless it is already drawn.

    A decline is recorded only when the generator says it declined. If it returns
    normally, says nothing, and leaves no file, that is a broken assumption on our
    side and raises rather than becoming a quiet row in the results.
    """
    budget = BUDGET_S.get(algorithm)
    target = graphml_path(algorithm, context, scale)
    if target.exists():
        return {"status": "cached", "runtime_s": "", "budget_s": budget or "",
                "completed_within_budget": "", "note": ""}

    module = load_generator(algorithm)
    module.GRAPHML_ROOT = GRAPHML / algorithm
    module.DRAWINGS_ROOT = DRAWINGS / algorithm

    started = time.perf_counter()
    reported = io.StringIO()
    try:
        with contextlib.redirect_stdout(reported):
            module.generate(context, scale_path(context, scale).resolve())
        elapsed = round(time.perf_counter() - started, 3)
    except Exception as exc:
        return {"status": "error", "runtime_s": round(time.perf_counter() - started, 3),
                "budget_s": budget or "", "completed_within_budget": "",
                "note": f"{type(exc).__name__}: {exc}"[:200]}

    within = "" if budget is None else elapsed < budget * COMPLETION_MARGIN

    message = reported.getvalue().strip()
    if not target.exists():
        # A decline is what the generator says it is. Its own word for it is
        # "skipped", followed by the reason.
        # "skipped ... already exists" is his cache message, not a decline. If we
        # see it while our own target is missing, his path and ours disagree, which
        # is precisely the failure this invariant exists to catch.
        declined = [line for line in message.splitlines()
                    if line.startswith("skipped") and "already exists" not in line]
        if not declined:
            raise MissingDrawing(
                f"{algorithm} on {context}/{scale}: returned after {elapsed}s without "
                f"writing {target.relative_to(HERE)} and without reporting a reason. "
                f"Either the output path is wrong or the generator changed; this is "
                f"not a decline and must not be recorded as one.\n"
                f"what it printed: {message[:300] or '(nothing)'}")
        reason = declined[0].split(":", 1)[-1].strip()
        return {"status": "declined", "runtime_s": elapsed, "budget_s": budget or "",
                "completed_within_budget": within, "note": reason[:200]}
    return {"status": "drawn", "runtime_s": elapsed, "budget_s": budget or "",
            "completed_within_budget": within,
            "note": "" if within != False else
                    "consumed its whole budget: an anytime result, not a converged one"}


# ---------------------------------------------------------------------------
# Pass 2: score
# ---------------------------------------------------------------------------

def score(algorithm: str, context: str, scale: str) -> dict:
    path = graphml_path(algorithm, context, scale)
    if not path.exists():
        return {}
    layout = load_layout(str(path))
    row = {"n_nodes": layout.n, "drawn_width": structural_width(layout)}
    row.update(evaluate_all(layout))
    return row


# ---------------------------------------------------------------------------
# Pass 3: compare across scales
# ---------------------------------------------------------------------------

def nested_pairs(context: str) -> list[dict]:
    path = CONTEXTS / context / "nesting.csv"
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return [r for r in csv.DictReader(f) if r["nested"] == "True"]


def consistency_rows(context: str, algorithms: list[str]) -> tuple[list[dict], list[dict]]:
    """Returns (one row per pair and algorithm, one row per stratum of each pair)."""
    rows, strata_rows = [], []
    for pair in nested_pairs(context):
        coarse, fine = pair["scale_a"], pair["scale_b"]
        for algorithm in algorithms:
            coarse_file = graphml_path(algorithm, context, coarse)
            fine_file = graphml_path(algorithm, context, fine)
            base = {
                "context": context,
                "scale_a": coarse,
                "scale_b": fine,
                "algorithm": algorithm,
                "size_ratio": pair["ratio"],
                "nested_shared": pair["shared"],
            }
            if not (coarse_file.exists() and fine_file.exists()):
                missing = [name for name, f in ((coarse, coarse_file), (fine, fine_file))
                           if not f.exists()]
                rows.append({**base, "n_shared": "", "tau_x": "", "p_value": "",
                             "rank_drift": "", "thin": "",
                             "status": f"not drawn: {', '.join(missing)}"})
                continue
            a = load_drawing(scale_path(context, coarse), coarse_file, algorithm)
            b = load_drawing(scale_path(context, fine), fine_file, algorithm)
            result = compare(a, b)
            # A raw tau is uninterpretable, so every observation is standardised
            # against label permutations within rank strata of the finer drawing.
            result.update(permutation_null(a, b))
            rows.append({**base, **result, "status": "ok"})
            for stratum in tau_by_stratum(a, b):
                strata_rows.append({"context": context, "scale_a": coarse,
                                    "scale_b": fine, "algorithm": algorithm,
                                    "stratum": stratum["stratum"],
                                    "n_in_stratum": stratum["n"],
                                    "tau_x": "" if stratum["tau"] is None else stratum["tau"]})
    return rows, strata_rows


# ---------------------------------------------------------------------------

def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def merge_csv(path: Path, rows: list[dict], key: tuple[str, ...]) -> None:
    """Write these rows into an existing results file without losing the others.

    A filtered run — one algorithm, or one context — produces rows for that slice
    only. Writing them straight out truncates the file to the slice, which silently
    discards every result the previous runs recorded: exactly what happened the
    first time `--algorithm fdp` was run after the instruments sweep. Runs are
    incremental by design, since drawings are cached and a full sweep takes hours,
    so the results file has to be too.

    Rows already present under the same key are replaced, so re-running a slice
    updates it rather than duplicating it.
    """
    if not rows:
        return
    existing: list[dict] = []
    if path.exists():
        with path.open(encoding="utf-8") as f:
            existing = list(csv.DictReader(f))
    replaced = {tuple(str(row[k]) for k in key) for row in rows}
    kept = [row for row in existing
            if tuple(str(row.get(k, "")) for k in key) not in replaced]
    write_csv(path, sorted(kept + rows,
                           key=lambda row: tuple(str(row.get(k, "")) for k in key)))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--context", help="only this context")
    parser.add_argument("--algorithm", choices=ALGORITHMS, help="only this algorithm")
    parser.add_argument("--draw-only", action="store_true")
    parser.add_argument("--skip-draw", action="store_true", help="score what is already drawn")
    args = parser.parse_args()

    algorithms = [args.algorithm] if args.algorithm else list(ALGORITHMS)
    scales = [s for s in manifests() if s["drawable"] == "True"]
    if args.context:
        scales = [s for s in scales if s["context"] == args.context]

    print(f"{len(scales)} drawable scales x {len(algorithms)} algorithms "
          f"({', '.join(EXCLUDED)} excluded)")

    write_csv(HERE / "scales.csv", [{
        "context": s["context"], "scale": s["scale"], "kind": s["kind"],
        "chain": s["chain"], "chain_step": s["chain_step"],
        "n_scale_attrs": s["attributes"], "n_concepts": s["concepts"],
        "width": s["width"], "height": s["height"],
        "incomparable_pairs": s.get("incomparable_pairs", ""),
        "drawable": s["drawable"],
        "description": s["description"],
    } for s in manifests()])

    drawing_rows = []
    for s in scales:
        for algorithm in algorithms:
            result = {"context": s["context"], "scale": s["scale"], "algorithm": algorithm,
                      "concepts": s["concepts"], "seed": "none"}
            limit = FEASIBLE_MAX_CONCEPTS.get(algorithm)
            if limit is not None and int(s["concepts"]) > limit:
                result.update({
                    "status": "skipped", "runtime_s": "", "budget_s": "",
                    "completed_within_budget": "",
                    "note": f"beyond the measured feasible range for {algorithm} "
                            f"({limit} concepts); see pipeline.md"})
                drawing_rows.append(result)
                print(f"  {algorithm:20s} {s['context']:12s} {s['scale']:28s} skipped "
                      f"({s['concepts']} concepts > {limit})")
                continue
            if algorithm in REQUIRES_CLARIFIED:
                equivalent = equivalent_attributes(scale_path(s["context"], s["scale"]))
                if equivalent:
                    pair = " == ".join(equivalent[0])
                    result.update({
                        "status": "skipped", "runtime_s": "", "budget_s": "",
                        "completed_within_budget": "",
                        "note": f"{algorithm} does not terminate on a context with "
                                f"equivalent attributes ({pair}); see pipeline.md"})
                    drawing_rows.append(result)
                    print(f"  {algorithm:20s} {s['context']:12s} {s['scale']:28s} skipped "
                          f"(equivalent attributes: {pair})")
                    continue
            if not args.skip_draw:
                result.update(draw(algorithm, s["context"], s["scale"]))
                print(f"  {algorithm:20s} {s['context']:12s} {s['scale']:28s} "
                      f"{result['status']:9s} {result['runtime_s']}")
            result.update(score(algorithm, s["context"], s["scale"]))
            drawing_rows.append(result)
    merge_csv(HERE / "drawings.csv", drawing_rows,
              ("context", "scale", "algorithm"))

    if args.draw_only:
        return 0

    contexts = sorted({s["context"] for s in scales})
    rows, strata_rows = [], []
    for context in contexts:
        pair_rows, pair_strata = consistency_rows(context, algorithms)
        rows.extend(pair_rows)
        strata_rows.extend(pair_strata)
    merge_csv(HERE / "consistency.csv", rows,
              ("context", "scale_a", "scale_b", "algorithm"))
    # Long format again: strata per pair vary, so they get their own file rather
    # than a list squeezed into a cell.
    merge_csv(HERE / "consistency_strata.csv", strata_rows,
              ("context", "scale_a", "scale_b", "algorithm", "stratum"))

    drawn = sum(1 for r in drawing_rows if r.get("status") in ("drawn", "cached"))
    declined = sum(1 for r in drawing_rows if r.get("status") == "declined")
    errored = sum(1 for r in drawing_rows if r.get("status") == "error")
    measured = sum(1 for r in rows if r.get("status") == "ok")
    print(f"\ndrawings: {drawn} drawn, {declined} declined, {errored} errored")
    print(f"consistency: {measured} of {len(rows)} (pair, algorithm) combinations measured")
    print(f"-> scales.csv, drawings.csv, consistency.csv, consistency_strata.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
