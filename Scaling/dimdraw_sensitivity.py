"""Does dimdraw's budget change its scores, or has the anytime search converged?

The confound this settles is ours, not his. RQ1 asks whether drawing quality
improves as a lattice gets smaller. dimdraw's search is bounded by a wall-clock
budget, and a larger lattice gets less search per concept, so its quality could
fall with size for two reasons at once, genuine difficulty and a truncated search,
which cannot be separated after the fact. Every other algorithm's size trend is
clean; dimdraw's is not.

The test: draw the same scales twice, once with the 60 second budget its generator
uses and once with ten times that, and score both. If the scores move, the
confound is real and dimdraw's size trend has to be reported separately, split by
whether the budget was consumed. If they do not move, the anytime search had
already converged and the trend is clean after all, which is the better outcome.

    python dimdraw_sensitivity.py                       # the default three scales
    python dimdraw_sensitivity.py --budgets 60 600 --scales practice

Writes `dimdraw_sensitivity.csv`.
"""

from __future__ import annotations

import argparse
import csv
import sys
import time
from pathlib import Path

import odis

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(HERE))

from check_node_mapping import load_generator  # noqa: E402
from lattice_metrics import evaluate_all, load_layout  # noqa: E402

# Mid-size scales: past the roughly thirty concepts where dimdraw stops finishing,
# but small enough that two runs each are affordable.
DEFAULT_SCALES = [("instruments", "playing-mechanism"), ("instruments", "practice"),
                  ("instruments", "family-making")]


def draw_with_budget(context: str, scale: str, budget_s: float,
                     out_root: Path) -> tuple[Path, float]:
    """Draw one scale with an explicit budget, writing in the generator's own format."""
    module = load_generator("dimdraw")
    cxt_path = HERE / "contexts" / context / f"{scale}.cxt"
    target = out_root / f"{scale}-{int(budget_s)}s.graphml"
    target.parent.mkdir(parents=True, exist_ok=True)

    formal_context = odis.FormalContext.from_file(str(cxt_path))
    started = time.perf_counter()
    drawing = formal_context.draw("dimdraw", int(budget_s * 1000))
    elapsed = time.perf_counter() - started
    module.write_graphml(drawing, target)
    return target, elapsed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--budgets", type=float, nargs=2, default=[60.0, 600.0])
    parser.add_argument("--scales", nargs="*")
    parser.add_argument("--out", type=Path, default=HERE / "dimdraw_sensitivity.csv")
    args = parser.parse_args()

    scales = ([("instruments", s) for s in args.scales] if args.scales else DEFAULT_SCALES)
    out_root = HERE / ".dimdraw-sensitivity"
    rows = []

    for context, scale in scales:
        scores = {}
        for budget in args.budgets:
            path, elapsed = draw_with_budget(context, scale, budget, out_root)
            layout = load_layout(str(path))
            metrics = evaluate_all(layout)
            scores[budget] = metrics
            rows.append({"context": context, "scale": scale, "budget_s": budget,
                         "elapsed_s": round(elapsed, 2),
                         "consumed_budget": elapsed > budget * 0.95,
                         "n_nodes": layout.n, **metrics})
            print(f"  {scale:24s} budget {budget:5.0f}s  took {elapsed:7.2f}s  "
                  f"{'consumed' if elapsed > budget * 0.95 else 'finished'}", flush=True)

        low, high = args.budgets
        changed = {k: (scores[high][k] - scores[low][k]) for k in scores[low]
                   if abs(scores[high][k] - scores[low][k]) > 1e-9}
        if changed:
            print(f"    {len(changed)} of {len(scores[low])} metrics moved; largest: "
                  + ", ".join(f"{k} {v:+.4f}" for k, v in
                              sorted(changed.items(), key=lambda kv: -abs(kv[1]))[:4]))
        else:
            print("    every metric identical: the anytime search had converged")

    with args.out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"\n-> {args.out.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
