"""Draw every scale with every algorithm, score and compare the drawings, rank the algorithms.

Four passes -- draw, score on the fourteen quality metrics, compare across scales, rank --
each idempotent and cached, each writing long-format CSVs. Long format rather
than wide: contexts have different numbers of scales, so a column per scale would
break the first time a context is added, while different scale counts are just
different row counts here.

    python run_harness.py                      # everything, 8 drawings at a time
    python run_harness.py --context instruments --algorithm fdp
    python run_harness.py --draw-only
    python run_harness.py --retry-failed       # attempt recorded failures again

| File | One row per |
|---|---|
| `scales.csv` | scale, copied from the per-context manifests |
| `drawings.csv` | scale x algorithm: status, failure reason, runtime |
| `quality.csv` | scale x algorithm: the fourteen quality scores |
| `consistency.csv` | nested pair x algorithm: tau, rank drift, the permutation null |
| `consistency_strata.csv` | nested pair x algorithm x rank stratum |
| `ranking.csv`, `sensitivity.csv`, `profile.csv` | written by `ranking.py` from the files above |

**Nothing is recomputed without a reason.** A drawing is reused while it exists with
its extents. Every row of `quality.csv` and `consistency.csv` carries a
`fingerprint` of the files it was computed from and of the code computing it, and
is recomputed only when that changes.

Drawings land in `graphml/<algorithm>/<context>/<scale>.graphml`, each with its
`<scale>.extents.json` recording which concept every node is (see
`node_extents.py`), and their renders in `drawings/`.

**Every algorithm is asked to draw every drawable scale.** Nothing is dropped and
nothing is skipped on a guess. A drawing that does not happen is a failure, and
failures are kept, classified and penalised in the ranking rather than removed:

| status | meaning |
|---|---|
| `drawn`, `cached` | a drawing exists, with its extents recorded |
| `declined` | the generator said it could not draw this lattice (cole_ducrou_eklund) |
| `timeout` | still running after the wall-clock budget, so killed |
| `error` | the generator raised |
| `nonterminating` | a known non-termination; not run, because it would only time out |
| `invalid` | output was written but is not a usable drawing: diverged or collapsed coordinates |

**The wall-clock budget is 30 minutes per drawing, the same for every algorithm.**
It is enforced by running each drawing in its own process and killing it at the
limit. It is distinct from the internal budgets of dimdraw, fdp and dimflux, which
are part of those algorithms -- they bound a search and return its best layout --
and are recorded separately; fdp's bounds only its optimiser, which is why fdp can
still fail to terminate (see NONTERMINATING). Because a timeout counts as a failure, the budget can change
the ranking; that is why it is a reported parameter and why every runtime is kept.

**Failures on our side are not recorded as the algorithm's.** If redraw's conexp
server is unreachable before a redraw drawing or after one fails, or a generator
returns without writing anything or giving a reason, the run stops instead of
writing a row.

**A drawing belongs to one exact file.** Each records the sha256 of the .cxt it was
drawn from, and is reused, scored and compared only while that file is unchanged;
a recorded failure is reused only for the same file under the same budget.

    python run_harness.py --no-draw            # rescore, recompare, re-rank only
"""

from __future__ import annotations

import argparse
import contextlib
import csv
import hashlib
import inspect
import io
import json
import math
import os
import signal
import subprocess
import sys
import tempfile
import time
import urllib.request
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from itertools import combinations
from pathlib import Path

import odis

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(HERE))

from node_extents import (ALGORITHMS, RecordingFault, load_generator, recording,  # noqa: E402
                          sidecar, source_hash)
from consistency import compare, tau_by_stratum  # noqa: E402
from graphml_loader import load_drawing  # noqa: E402
from nulls import permutation_null  # noqa: E402
import progress  # noqa: E402
from ranking import QUALITY_METRICS  # noqa: E402

CONTEXTS = HERE / "contexts"
GRAPHML = HERE / "graphml"
DRAWINGS = HERE / "drawings"

# The wall-clock budget for one drawing, the same for every algorithm; pipeline.md,
# *Drawing*, says why 30 minutes.
WALL_BUDGET_S = 30 * 60

# How many drawings run at once. Each is its own process; the machine has 16 cores.
DEFAULT_JOBS = 8

# Budgets the generators impose on themselves, in seconds. Part of the algorithm,
# not ours: an anytime algorithm that consumes its budget returns the best layout it
# reached, a legitimate drawing but not necessarily the one it would return given
# longer, so whether the budget was used is recorded with every drawing.
INTERNAL_BUDGET_S = {
    "dimdraw": 60.0,      # context.draw('dimdraw', 60000), anytime
    # FDP_Additive_Features(..., {'timeout_s': 60.0}). Checked once per optimiser
    # iteration and bounds nothing before the optimiser; see NONTERMINATING.
    "fdp": 60.0,
    "dimflux": 60.0,      # DimFlux(timeout_ms=60000), the force phase only
}
# Below this fraction of an internal budget a run is taken to have finished on its own.
COMPLETION_MARGIN = 0.95
# Whether a run used its internal budget is inferred from its runtime, which works
# only where the budget bounds (nearly) the whole run. dimflux's bounds only the
# force phase, so its runtime says nothing about it and no flag is recorded.
BUDGET_INFERABLE = {"dimdraw", "fdp"}

CONEXP_URL = "http://127.0.0.1:8080/"


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


# A drawing whose coordinates are this large has diverged numerically. Every valid
# drawing in the corpus stays within a few hundred units; the diverged ones reach
# 1e40 to 1e84, so any bound between 1e3 and 1e40 classifies them identically.
MAX_COORDINATE = 1e9


def degenerate(graphml: Path) -> str | None:
    """Why a written drawing is not a usable line diagram, or None if it is.

    Invalid: a coordinate that is not finite or beyond MAX_COORDINATE (the layout
    diverged), or every node on one vertical or one horizontal line (the layout
    collapsed). Such output is the algorithm's failure, not a drawing to score: the
    quality metrics would reward a collapsed drawing, whose edges are all vertical,
    with perfect scores. A few coinciding nodes are not invalid; that is a poor
    drawing, which the quality metrics penalise.
    """
    from graphml_loader import read_positions
    points = list(read_positions(graphml).values())
    if any(not (math.isfinite(x) and math.isfinite(y)) for x, y in points):
        return "coordinates that are not finite"
    largest = max((max(abs(x), abs(y)) for x, y in points), default=0.0)
    if largest > MAX_COORDINATE:
        return f"diverged: coordinates up to {largest:.1e}"
    if len(points) >= 3 and (len({x for x, _ in points}) == 1 or len({y for _, y in points}) == 1):
        return "collapsed: every node on one line"
    return None


# Known non-termination, recorded as a failure without spending the budget on it.
#
#   fdp  does not terminate on a context with two equivalent attributes, at any
#        size. `_initialize_vectors` places each non-coatom attribute only once
#        every attribute implied by it has a position; two attributes implying
#        each other wait for one another forever, and the queue cycles. Its own
#        `timeout_s` cannot stop it: that is checked in the optimiser's callback,
#        which this never reaches. Reproduced on three concepts; see
#        tests/test_fdp_termination.py and pipeline.md, *Defects*. Running it
#        would only end in a timeout at the budget, the same failure, later.
#
# Do not "fix" this by clarifying the contexts. The attribute set is the chosen
# view, and dropping a label because it is coextensive with another edits that
# view silently, in every figure label and in the conjunctive normal form.
# Coextensive attributes are ordinary in real data; pipeline.md, *Drawing*.
NONTERMINATING = {"fdp": equivalent_attributes}


def manifests() -> list[dict]:
    """Every scale of every context, from the manifests the scale build wrote."""
    rows = []
    for manifest in sorted(CONTEXTS.glob("*/manifest.csv")):
        with manifest.open(encoding="utf-8") as f:
            rows.extend(csv.DictReader(f))
    return rows


def scale_path(context: str, scale: str) -> Path:
    return CONTEXTS / context / f"{scale}.cxt"


def graphml_path(algorithm: str, context: str, scale: str) -> Path:
    # Scale ids are lowercase with underscores only, which is exactly what the
    # generators' slug() leaves unchanged, so the id is the file name as it is.
    return GRAPHML / algorithm / context / f"{scale}.graphml"


# ---------------------------------------------------------------------------
# The cache: every result row carries a fingerprint of what it was computed from
# ---------------------------------------------------------------------------
#
# A row is recomputed only when its fingerprint changes: the files it was computed
# from, or the code that computes it. Changing a drawing recomputes its scores and
# every comparison it is part of; changing the metric code recomputes the scores
# and nothing else; changing nothing recomputes nothing. Drawings themselves are
# cached by existing on disk with their extents (pass 1).

def fingerprint(*paths: Path, extra: str = "") -> str:
    digest = hashlib.sha256(extra.encode())
    for path in paths:
        digest.update(path.name.encode() + b"\0")
        digest.update(path.read_bytes() if path.exists() else b"<missing>")
    return digest.hexdigest()[:16]


CODE_FINGERPRINT = {
    "quality": fingerprint(*sorted((REPO_ROOT / "lattice_metrics").glob("*.py"))),
    # Everything a comparison's numbers depend on, including the function in this
    # file that assembles them (its source, not the whole file, so that editing
    # the drawing pass does not recompute every comparison).
    # "consistency" is set below compare_pair, whose source it includes.
}


# ---------------------------------------------------------------------------
# Pass 1: draw, one process per drawing
# ---------------------------------------------------------------------------

class EnvironmentFault(RuntimeError):
    """Something on our side, not the algorithm, made a drawing impossible.

    redraw needs a local conexp-clj server. If it is down when a redraw drawing
    starts, or turns out to be down after one fails, the failure is ours and the run
    stops instead of recording it against redraw.
    """


def conexp_reachable() -> bool:
    try:
        urllib.request.urlopen(CONEXP_URL, timeout=5)
        return True
    except OSError:
        return False


class MissingDrawing(RuntimeError):
    """A generator returned normally and produced neither a drawing nor a reason.

    This is a fault on our side, never the algorithm's. Inferring a decline from a
    missing file fails silently and in one direction -- a generator that writes its
    output under another name would have every success recorded as a refusal -- so
    declines are only ever taken from what the generator itself reports, and
    anything else stops the run.
    """


def worker(algorithm: str, context: str, scale: str) -> int:
    """Run in a child process: draw one scale, print one JSON line, exit.

    Exit code 0 with a status for anything that is the algorithm's outcome;
    exit code 3 for a fault on our side, which the parent turns into a crash.
    """
    target = graphml_path(algorithm, context, scale)
    try:
        module = load_generator(algorithm)
    except Exception as exc:                       # an environment fault, not a result
        print(f"{algorithm}: its generator could not be loaded "
              f"({type(exc).__name__}: {exc})", file=sys.stderr)
        return 3
    module.GRAPHML_ROOT = GRAPHML / algorithm
    module.DRAWINGS_ROOT = DRAWINGS / algorithm

    reported = io.StringIO()
    # Only when DRAW_PROGRESS_DIR is set (rerun_timeouts.py): a log of the drawing's
    # steps while it runs. It observes the generator and changes nothing it computes.
    log = progress.install(algorithm, context, scale, module)
    started = time.perf_counter()
    try:
        with contextlib.redirect_stdout(progress.Tee(reported, log) if log else reported), \
                recording(module, algorithm, scale_path(context, scale)):
            module.generate(context, scale_path(context, scale).resolve())
    except RecordingFault as exc:
        print(f"{algorithm} on {context}/{scale}: {exc}", file=sys.stderr)
        return 3
    except Exception as exc:
        print(json.dumps({"status": "error",
                          "runtime_s": round(time.perf_counter() - started, 3),
                          "note": f"{type(exc).__name__}: {exc}"[:300]}))
        return 0
    elapsed = round(time.perf_counter() - started, 3)

    if target.exists() and sidecar(target).exists():
        print(json.dumps({"status": "drawn", "runtime_s": elapsed, "note": ""}))
        return 0

    # A decline is what the generator says it is. Its own word for it is "skipped",
    # followed by the reason; "skipped ... already exists" is its cache message, and
    # seeing that while our target is missing means its path and ours disagree.
    message = reported.getvalue().strip()
    declined = [line for line in message.splitlines()
                if line.startswith("skipped") and "already exists" not in line]
    if declined:
        print(json.dumps({"status": "declined", "runtime_s": elapsed,
                          "note": declined[0].split(":", 1)[-1].strip()[:300]}))
        return 0
    print(f"{algorithm} on {context}/{scale}: returned after {elapsed}s without writing "
          f"{target.relative_to(HERE)} and its extents, and without a reason. This is "
          f"not a decline. What it printed: {message[:300] or '(nothing)'}",
          file=sys.stderr)
    return 3


def drawing_is_current(algorithm: str, context: str, scale: str) -> bool:
    """A drawing exists, with its extents, made from exactly the current .cxt."""
    target = graphml_path(algorithm, context, scale)
    if not (target.exists() and sidecar(target).exists()):
        return False
    recorded = json.loads(sidecar(target).read_text(encoding="utf-8")).get("source_sha256")
    return recorded == source_hash(scale_path(context, scale))


def draw(algorithm: str, context: str, scale: str) -> dict:
    """Draw one scale in a child process, killing it at the wall-clock budget."""
    target = graphml_path(algorithm, context, scale)
    if drawing_is_current(algorithm, context, scale):
        return {"status": "cached"}
    if algorithm == "redraw" and not conexp_reachable():
        raise EnvironmentFault(f"redraw on {context}/{scale}: the conexp-clj API at "
                               f"{CONEXP_URL} is not reachable; start it (pipeline.md, "
                               f"'Setting up redraw') and run again")
    for stale in (target, sidecar(target)):
        # The generator would serve a drawing without extents from its own cache
        # and never call write_graphml, so the extents would never be recorded.
        stale.unlink(missing_ok=True)

    # Its own working directory: dim-flux writes and deletes input.cxt in the
    # current directory, so two at once in one directory would clobber each other.
    with tempfile.TemporaryDirectory(prefix="draw-") as workdir:
        started = time.perf_counter()
        child = subprocess.Popen(
            [sys.executable, str(Path(__file__).resolve()), "--worker",
             algorithm, context, scale],
            cwd=workdir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            start_new_session=True)
        try:
            out, err = child.communicate(timeout=WALL_BUDGET_S)
        except subprocess.TimeoutExpired:
            with contextlib.suppress(ProcessLookupError):
                os.killpg(child.pid, signal.SIGKILL)       # the whole process group
            child.communicate()
            for partial in (target, sidecar(target)):
                partial.unlink(missing_ok=True)
            return {"status": "timeout", "runtime_s": round(time.perf_counter() - started, 1),
                    "note": f"still running after the {WALL_BUDGET_S:g} s wall-clock "
                            f"budget; killed"}

    if child.returncode == 3:
        raise MissingDrawing(err.strip())
    lines = [line for line in out.splitlines() if line.startswith("{")]
    if child.returncode != 0 or not lines:
        # The child died without reporting: a crash of the generator's process
        # (a segfault, an exit() inside the library) is still the algorithm's outcome.
        return {"status": "error", "runtime_s": round(time.perf_counter() - started, 3),
                "note": f"process exited with code {child.returncode}: "
                        f"{(err.strip().splitlines() or ['no output'])[-1][:300]}"}
    return json.loads(lines[-1])


def drawing_row(spec: dict, algorithm: str, previous: dict, retry_failed: bool) -> dict:
    """The outcome of one (scale, algorithm), drawing it if it has not been done."""
    context, scale = spec["context"], spec["scale"]
    source = source_hash(scale_path(context, scale))
    row = {"context": context, "scale": scale, "algorithm": algorithm,
           "concepts": spec["concepts"], "wall_budget_s": WALL_BUDGET_S,
           "internal_budget_s": INTERNAL_BUDGET_S.get(algorithm, ""),
           "source_sha256": source}

    precondition = NONTERMINATING.get(algorithm)
    if precondition:
        found = precondition(scale_path(context, scale))
        if found:
            row.update(status="nonterminating", runtime_s="",
                       note=f"{algorithm} does not terminate on a context with equivalent "
                            f"attributes ({' == '.join(found[0])}); not run. See "
                            f"tests/test_fdp_termination.py")
            return row

    earlier = previous.get((context, scale, algorithm))
    # An outcome is reused only for the same input file. Only a timeout depends on
    # the budget: it is reused if it already had at least the current budget, and
    # attempted again under a larger one. A drawing, a decline or an error does not
    # depend on the budget, so changing the budget changes nothing about them.
    same_experiment = bool(earlier) and earlier.get("source_sha256") == source
    try:
        earlier_budget = float(earlier.get("wall_budget_s") or 0) if earlier else 0.0
    except ValueError:
        earlier_budget = 0.0
    timed_out_before = same_experiment and earlier.get("status") == "timeout" \
        and earlier_budget >= WALL_BUDGET_S
    failed_before = timed_out_before or (
        same_experiment and earlier.get("status") in ("declined", "error"))
    if failed_before and not retry_failed:
        # A recorded failure is not attempted again by default: a timeout costs
        # the whole budget each time. --retry-failed attempts them again.
        return {**row, **{k: earlier.get(k, "") for k in ("status", "runtime_s", "note")},
                "wall_budget_s": earlier.get("wall_budget_s", WALL_BUDGET_S)}

    outcome = draw(algorithm, context, scale)
    if algorithm == "redraw" and outcome["status"] in ("error", "timeout") \
            and not conexp_reachable():
        # The server went down while it was drawing: our failure, not redraw's.
        raise EnvironmentFault(f"redraw on {context}/{scale} ended '{outcome['status']}' and "
                               f"the conexp-clj API at {CONEXP_URL} is no longer reachable; "
                               f"nothing recorded. Restart it and run again.")
    if outcome["status"] == "cached" and same_experiment and earlier.get("status") in ("drawn", "cached"):
        # Keep the runtime measured when it was actually drawn.
        outcome = {"status": "cached", "runtime_s": earlier.get("runtime_s", ""),
                   "note": earlier.get("note", "")}
    row.update(status=outcome["status"], runtime_s=outcome.get("runtime_s", ""),
               note=outcome.get("note", ""))
    if outcome["status"] == "cached" and same_experiment and earlier.get("wall_budget_s"):
        row["wall_budget_s"] = earlier["wall_budget_s"]      # the budget it was drawn under

    if row["status"] in ("drawn", "cached"):
        why = degenerate(graphml_path(algorithm, context, scale))
        if why:
            row.update(status="invalid", note=f"output is not a usable drawing: {why}")
            return row

    internal = INTERNAL_BUDGET_S.get(algorithm) if algorithm in BUDGET_INFERABLE else None
    if internal and row["status"] in ("drawn", "cached") and row["runtime_s"] not in ("", None):
        used = float(row["runtime_s"]) >= internal * COMPLETION_MARGIN
        row["used_internal_budget"] = used
        if used and not row["note"]:
            row["note"] = "used its whole internal budget: an anytime result"
    return row


# ---------------------------------------------------------------------------
# Pass 2: drawing quality, the fourteen metrics
# ---------------------------------------------------------------------------

def quality_row(job: tuple[str, str, str, str]) -> dict:
    """Score one drawing on the fourteen metrics the repository's analysis uses.

    Every score must be present, a finite number and within [0, 1] -- the range the
    metrics are defined on. Anything else is refused here, where it can be traced to
    one drawing, rather than discovered by the ranking.
    """
    from lattice_metrics import evaluate_all, load_layout
    context, scale, algorithm, fp = job
    scores = evaluate_all(load_layout(str(graphml_path(algorithm, context, scale))))
    bad = []
    for m in QUALITY_METRICS:
        value = scores.get(m)
        try:
            ok = value is not None and math.isfinite(float(value)) \
                and -1e-9 <= float(value) <= 1 + 1e-9
        except (TypeError, ValueError):
            ok = False
        if not ok:
            bad.append(f"{m}={value!r}")
    if bad:
        raise ValueError(f"scores outside [0, 1] or not numbers: {', '.join(bad)}")
    return {"context": context, "scale": scale, "algorithm": algorithm,
            **{m: float(scores[m]) for m in QUALITY_METRICS}, "fingerprint": fp}


def _guarded(function, job):
    """Run one job; return (result, None) or (None, why it failed)."""
    try:
        return function(job), None
    except Exception as exc:
        return None, f"{type(exc).__name__}: {exc}"[:500]


def _quality_job(job):
    return _guarded(quality_row, job)


def _compare_guarded(job):
    return _guarded(_compare_job, job)


# ---------------------------------------------------------------------------
# Pass 3: compare across scales
# ---------------------------------------------------------------------------

def nested_pairs(context: str) -> list[dict]:
    path = CONTEXTS / context / "nesting.csv"
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return [r for r in csv.DictReader(f) if r["nested"] == "True"]


def compare_pair(context: str, pair: dict, algorithm: str, status: dict) -> tuple[dict, list[dict]]:
    """One (nested pair, algorithm): the comparison, or why there is none."""
    coarse, fine = pair["scale_a"], pair["scale_b"]
    base = {"context": context, "scale_a": coarse, "scale_b": fine, "algorithm": algorithm,
            "usable": pair["usable"], "size_ratio": pair["ratio"],
            "nested_shared": pair["shared"]}
    failed = [f"{s} ({status.get((context, s, algorithm), 'not attempted')})"
              for s in (coarse, fine)
              if status.get((context, s, algorithm)) not in ("drawn", "cached")]
    if failed:
        return {**base, "status": "failed", "note": "no drawing of " + ", ".join(failed)}, []

    a = load_drawing(scale_path(context, coarse), graphml_path(algorithm, context, coarse))
    b = load_drawing(scale_path(context, fine), graphml_path(algorithm, context, fine))
    result = compare(a, b)
    # A raw tau is uninterpretable, so every observation is standardised against
    # label permutations within rank strata of the finer drawing.
    result.update(permutation_null(a, b))
    strata = [{"context": context, "scale_a": coarse, "scale_b": fine, "algorithm": algorithm,
               "stratum": s["stratum"], "n_in_stratum": s["n"],
               "tau_x": "" if s["tau"] is None else s["tau"]}
              for s in tau_by_stratum(a, b)]
    return {**base, **result, "status": "ok", "note": ""}, strata


CODE_FINGERPRINT["consistency"] = fingerprint(
    HERE / "consistency.py", HERE / "nulls.py", HERE / "graphml_loader.py",
    HERE / "node_extents.py", extra=inspect.getsource(compare_pair))


def _compare_job(job):
    row, strata = compare_pair(*job[:4])
    row["fingerprint"] = job[4]
    return row, strata


def compare_fingerprint(context: str, pair: dict, algorithm: str, status: dict) -> str:
    files = []
    for scale in (pair["scale_a"], pair["scale_b"]):
        g = graphml_path(algorithm, context, scale)
        files += [scale_path(context, scale), g, sidecar(g)]
    states = ",".join(status.get((context, s, algorithm), "") for s in (pair["scale_a"], pair["scale_b"]))
    return fingerprint(*files, extra=CODE_FINGERPRINT["consistency"] + pair["usable"] + states)


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


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def merge_csv(path: Path, rows: list[dict], key: tuple[str, ...]) -> None:
    """Write these rows into an existing results file without losing the others.

    A filtered run -- one algorithm, or one context -- produces rows for that slice
    only. Writing them straight out would truncate the file to the slice and
    silently discard every result the previous runs recorded.
    Rows already present under the same key are replaced, so re-running a slice
    updates it rather than duplicating it.
    """
    if not rows:
        return
    replaced = {tuple(str(row[k]) for k in key) for row in rows}
    kept = [row for row in read_csv(path)
            if tuple(str(row.get(k, "")) for k in key) not in replaced]
    write_csv(path, sorted(kept + rows,
                           key=lambda row: tuple(str(row.get(k, "")) for k in key)))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--context", help="only this context")
    parser.add_argument("--algorithm", choices=ALGORITHMS, help="only this algorithm")
    parser.add_argument("--draw-only", action="store_true")
    parser.add_argument("--no-draw", action="store_true",
                        help="skip pass 1 and recompute scores, comparisons and the ranking "
                             "from the drawings already recorded")
    parser.add_argument("--jobs", type=int, default=DEFAULT_JOBS)
    parser.add_argument("--retry-failed", action="store_true",
                        help="attempt drawings recorded as declined, timeout or error again")
    parser.add_argument("--worker", nargs=3, metavar=("ALGORITHM", "CONTEXT", "SCALE"),
                        help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        return worker(*args.worker)

    algorithms = [args.algorithm] if args.algorithm else list(ALGORITHMS)
    scales = [s for s in manifests() if s["drawable"] == "True"]
    if args.context:
        scales = [s for s in scales if s["context"] == args.context]

    write_csv(HERE / "scales.csv", [{
        "context": s["context"], "scale": s["scale"], "short_name": s["short_name"],
        "kind": s["kind"], "chain": s["chain"], "chain_step": s["chain_step"],
        "n_scale_attrs": s["attributes"], "n_concepts": s["concepts"],
        "width": s["width"], "height": s["height"],
        "incomparable_pairs": s.get("incomparable_pairs", ""),
        "drawable": s["drawable"], "description": s["description"],
    } for s in manifests()])

    previous = {(r["context"], r["scale"], r["algorithm"]): r
                for r in read_csv(HERE / "drawings.csv")}
    jobs = [] if args.no_draw else [(s, a) for s in scales for a in algorithms]
    print(f"{len(scales)} drawable scales x {len(algorithms)} algorithms = {len(jobs)} "
          f"drawings, {args.jobs} at a time, {WALL_BUDGET_S // 60}-minute budget each")

    drawing_rows = []
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures = [pool.submit(drawing_row, s, a, previous, args.retry_failed) for s, a in jobs]
        for done, future in enumerate(as_completed(futures), start=1):
            row = future.result()                     # re-raises MissingDrawing
            drawing_rows.append(row)
            # Saved the moment it finishes, so an interrupted run -- a closed
            # laptop, a killed session -- loses only the drawings still in progress.
            # Only this thread writes the file.
            merge_csv(HERE / "drawings.csv", [row], ("context", "scale", "algorithm"))
            print(f"  [{done:3d}/{len(jobs)}] {row['algorithm']:20s} {row['scale']:42s} "
                  f"{row['status']:14s} {row.get('runtime_s', '')}", flush=True)

    if args.draw_only:
        return 0

    status = {(r["context"], r["scale"], r["algorithm"]): r["status"]
              for r in read_csv(HERE / "drawings.csv")}
    # A drawing counts only if it is still the drawing of the current .cxt; one made
    # from an older version is not compared or scored, whatever its row says.
    for key, state in list(status.items()):
        if state in ("drawn", "cached") and not drawing_is_current(key[2], key[0], key[1]):
            status[key] = "stale"

    # Pass 2: quality, recomputed only where the drawing or the metric code changed.
    known = {(r["context"], r["scale"], r["algorithm"]): r["fingerprint"]
             for r in read_csv(HERE / "quality.csv")}
    todo = []
    for s in scales:
        for a in algorithms:
            key = (s["context"], s["scale"], a)
            if status.get(key) not in ("drawn", "cached"):
                continue
            fp = fingerprint(graphml_path(a, s["context"], s["scale"]),
                             extra=CODE_FINGERPRINT["quality"])
            if known.get(key) != fp:
                todo.append((*key, fp))
    quality_rows, faults = [], []
    with ProcessPoolExecutor(max_workers=args.jobs) as pool:
        for job, (row, why) in zip(todo, pool.map(_quality_job, todo)):
            if why is None:
                quality_rows.append(row)
            else:
                faults.append(f"scoring {job[0]}/{job[1]} by {job[2]}: {why}")
    # Whatever succeeded is saved, whatever failed is listed; the run then stops
    # before the ranking, which would refuse an unscored drawing anyway.
    merge_csv(HERE / "quality.csv", quality_rows, ("context", "scale", "algorithm"))
    # Scores of anything that is not (or no longer) a valid drawing -- a failure, an
    # invalid layout, a drawing of an older file -- are removed, not left to linger.
    # Only the current metrics are kept as columns, so a metric the repository has
    # retired does not survive as an empty column.
    columns = ["context", "scale", "algorithm", *QUALITY_METRICS, "fingerprint"]
    kept = [{k: r.get(k, "") for k in columns} for r in read_csv(HERE / "quality.csv")
            if status.get((r["context"], r["scale"], r["algorithm"])) in ("drawn", "cached")]
    write_csv(HERE / "quality.csv", kept)
    print(f"\nquality: {len(quality_rows)} drawings scored, the rest unchanged since last time")

    contexts = sorted({s["context"] for s in scales})
    # Only pairs whose two scales are both meant to be drawn. A pair into a scale
    # outside the drawable band -- the full olympics lattice, at 10463 concepts --
    # is not a failure of any algorithm and is not compared at all.
    drawable = {(s["context"], s["scale"]) for s in scales}
    # And only where both drawings have been attempted: a pair with a drawing never
    # attempted has no outcome yet, and must not be recorded as a failure.
    work = [(c, p, a, status) for c in contexts for p in nested_pairs(c)
            if (c, p["scale_a"]) in drawable and (c, p["scale_b"]) in drawable
            for a in algorithms
            if all(status.get((c, s, a)) not in (None, "stale") for s in (p["scale_a"], p["scale_b"]))]
    # Pass 3: comparisons, recomputed only where a drawing, a scale or the code changed.
    known = {(r["context"], r["scale_a"], r["scale_b"], r["algorithm"]): r.get("fingerprint")
             for r in read_csv(HERE / "consistency.csv")}
    todo = []
    for c, p, a, st in work:
        fp = compare_fingerprint(c, p, a, st)
        if known.get((c, p["scale_a"], p["scale_b"], a)) != fp:
            todo.append((c, p, a, st, fp))
    rows, strata_rows = [], []
    with ProcessPoolExecutor(max_workers=args.jobs) as pool:
        for job, (result, why) in zip(todo, pool.map(_compare_guarded, todo)):
            if why is None:
                rows.append(result[0])
                strata_rows.extend(result[1])
            else:
                faults.append(f"comparing {job[0]}: {job[1]['scale_a']} -> "
                              f"{job[1]['scale_b']} by {job[2]}: {why}")
    print(f"consistency: {len(rows)} comparisons computed, {len(work) - len(rows)} unchanged")
    merge_csv(HERE / "consistency.csv", rows, ("context", "scale_a", "scale_b", "algorithm"))
    # Long format again: strata per pair vary, so they get their own file rather
    # than a list squeezed into a cell.
    merge_csv(HERE / "consistency_strata.csv", strata_rows,
              ("context", "scale_a", "scale_b", "algorithm", "stratum"))

    counts = {}
    for r in drawing_rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    print(f"\ndrawings: " + ", ".join(f"{n} {k}" for k, n in sorted(counts.items())))
    usable = [r for r in read_csv(HERE / "consistency.csv") if r["usable"] == "True"]
    print(f"consistency: {sum(1 for r in usable if r['status'] == 'ok')} of {len(usable)} "
          f"usable (pair, algorithm) comparisons measured; the rest have a failed drawing")

    if faults:
        print(f"\n{len(faults)} jobs failed on our side; everything else is saved. "
              f"Nothing is ranked until they are fixed:", file=sys.stderr)
        for fault in faults:
            print(f"  {fault}", file=sys.stderr)
        return 1

    import ranking                                     # pass 4
    try:
        ranking.main([])
    except ranking.RankingInputError as exc:
        print(f"\nranking refused its input: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
