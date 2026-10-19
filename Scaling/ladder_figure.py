"""The best and the worst algorithm drawing one ladder of nested scales.

Two rows -- the best and the worst algorithm by the combined ranking, among those
that draw every scale of the ladder -- and one column per scale, from a coarse
scale up to the full lattice. The concepts of the first scale are followed through
every panel; the ladder is chosen so that they occur in all of them (the first
scale nests into each of the others), which `nesting.csv` is checked for.

**Colour is position.** Each followed concept is coloured by its left-to-right
position in that algorithm's drawing of the first scale. An algorithm that keeps
the order as the lattice grows keeps the colours running left to right in every
panel; one that rearranges mixes them. That is what tau measures, and each panel
gives |tau| against the first, marked "mirrored" where the order is kept the other
way round -- the colours then run right to left, which is not counted against it.

    python ladder_figure.py --all                            # every context, ladders by rule
    python ladder_figure.py --context wd40pc                 # one context, ladder by rule
    python ladder_figure.py --followed instruments_practice --out ladder_instruments_practice \\
        --scales instruments_family_practice instruments_capability_practice_making instruments
    python ladder_figure.py --algorithms dimdraw sugiyama    # choose the rows yourself

**The ladder is chosen by a rule that never looks at results** (`choose_ladder`):
it ends at the context's largest drawable scale and its first scale nests into
every panel; then, in order of preference, (1) as many panels as possible, up to
four; (2) as many steps as possible where each panel nests into the next, i.e. a
true refinement; (3) the smallest first scale, whose concepts are the ones followed
by eye; (4) alphabetical, so the choice is unique. It reproduces the two ladders
chosen by hand before it existed, instruments *making* and olympics *equipment*,
and pipeline.md, *Ladder figures*, lists what it picks for every context.

Writes `figures/<out>.pdf` and `figures/<out>.png`. Reads drawings, rankings and
comparisons that `run_harness.py` has produced; it draws nothing itself.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from xml.etree.ElementTree import parse as parse_xml

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from graphml_loader import load_drawing, read_positions  # noqa: E402

GRAPHML_NS = "{http://graphml.graphdrawing.org/xmlns}"

# The default ladder, chosen by a rule that does not look at results: of the
# ladders that run to the full lattice through four scales, the one whose followed
# concepts can be told apart by eye. In instruments two qualify -- making (17
# concepts, to 39, 319, 576) and practice (46, to 107, 319, 576) -- and 46 coloured
# points among 576 nodes cannot be followed, so making is the default. Picking the
# ladder whose picture best fits a conclusion would be the circularity the
# groupings rule exists to prevent; both remain one command away.
DEFAULT_CONTEXT = "instruments"
MAX_PANELS = 4


def choose_ladder(context: str) -> list[str]:
    """The ladder for a context, by the rule in the module docstring."""
    from itertools import combinations
    manifest = read(HERE / "contexts" / context / "manifest.csv")
    size = {r["scale"]: int(r["concepts"]) for r in manifest if r["drawable"] == "True"}
    nested = {(r["scale_a"], r["scale_b"]) for r in read(HERE / "contexts" / context / "nesting.csv")
              if r["nested"] == "True"}
    top = max(size, key=lambda s: (size[s], s))
    candidates = []
    for first in size:
        if first == top or (first, top) not in nested:
            continue
        middle = sorted((s for s in size if s not in (first, top) and (first, s) in nested
                         and size[first] < size[s] < size[top]), key=lambda s: (size[s], s))
        for k in range(MAX_PANELS - 1):
            for chosen in combinations(middle, k):
                ladder = [first, *chosen, top]
                steps = sum((a, b) in nested for a, b in zip(ladder, ladder[1:]))
                candidates.append((-len(ladder), -steps, size[first], tuple(ladder)))
    if not candidates:
        raise SystemExit(f"{context}: no drawable scale nests into {top}; no ladder")
    return list(min(candidates)[3])


def read(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def graphml_path(algorithm: str, context: str, scale: str) -> Path:
    return HERE / "graphml" / algorithm / context / f"{scale}.graphml"


def choose_rows(context: str, ladder: list[str]) -> tuple[str, str, dict[str, float]]:
    """Best and worst by the combined ranking, among those that draw the whole ladder."""
    combined = {r["algorithm"]: float(r["mean_rank"]) for r in read(HERE / "ranking.csv")
                if r["context"] == context and r["measure"] == "combined"
                and r.get("view_weighting", "log2") == "log2"}
    drawn = {(r["scale"], r["algorithm"]) for r in read(HERE / "drawings.csv")
             if r["context"] == context and r["status"] in ("drawn", "cached")}
    if not combined:
        raise SystemExit("not ranked yet: not every algorithm has an outcome on every scale")
    complete = [a for a in combined if all((s, a) in drawn for s in ladder)]
    if len(complete) < 2:
        raise SystemExit(f"fewer than two algorithms draw every scale of {ladder}")
    complete.sort(key=combined.get)
    return complete[0], complete[-1], combined


def check_ladder(context: str, followed: str, scales: list[str]) -> None:
    nested = {(r["scale_a"], r["scale_b"]) for r in read(HERE / "contexts" / context / "nesting.csv")
              if r["nested"] == "True"}
    missing = [s for s in scales if (followed, s) not in nested]
    if missing:
        raise SystemExit(f"{followed} does not nest into {missing}, so its concepts would not "
                         f"occur in every panel; choose a ladder from nesting.csv")


def panel(ax, context, algorithm, scale, colour_of, tau, short) -> None:
    graphml = graphml_path(algorithm, context, scale)
    positions = read_positions(graphml)
    by_extent = load_drawing(HERE / "contexts" / context / f"{scale}.cxt", graphml)
    root = parse_xml(graphml).getroot().find(f"{GRAPHML_NS}graph")
    for e in root.findall(f"{GRAPHML_NS}edge"):
        (x1, y1), (x2, y2) = positions[e.get("source")], positions[e.get("target")]
        ax.plot([x1, x2], [y1, y2], color="#c9c9c9", linewidth=0.35, zorder=1)
    xs, ys = zip(*positions.values())
    ax.scatter(xs, ys, s=5, color="#8a8a8a", zorder=2, linewidths=0)
    followed = [(by_extent[e], c) for e, c in colour_of.items() if e in by_extent]
    ax.scatter([p[0] for p, _ in followed], [p[1] for p, _ in followed], s=26,
               c=[c for _, c in followed], zorder=3, linewidths=0.3, edgecolors="#222222")
    title = f"{short}\n{len(positions)} concepts"
    # |tau| is what is ranked; a negative tau means the order was kept mirrored,
    # which the colours show running right to left.
    title += "" if tau is None else (f",  |tau| = {abs(tau):.2f}"
                                     + (" (mirrored)" if tau < 0 else ""))
    ax.set_title(title, fontsize=8.5)
    ax.set_axis_off()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--context", default=DEFAULT_CONTEXT)
    parser.add_argument("--all", action="store_true",
                        help="one figure per context, each ladder chosen by the rule")
    parser.add_argument("--followed", help="the first scale, whose concepts are followed; "
                                           "default: by the rule")
    parser.add_argument("--scales", nargs="+",
                        help="the larger scales, smallest first; the followed scale must nest "
                             "into each; default: by the rule")
    parser.add_argument("--algorithms", nargs=2, metavar=("TOP", "BOTTOM"),
                        help="the two rows; default: best and worst that draw the whole ladder")
    parser.add_argument("--out", help="basename, written into figures/; default ladder_<context>")
    args = parser.parse_args()
    if args.all:
        contexts = sorted(p.parent.name for p in (HERE / "contexts").glob("*/manifest.csv"))
        made = 0
        for context in contexts:
            ladder = choose_ladder(context)
            try:
                figure(context, ladder[0], ladder[1:], None, f"ladder_{context}")
                made += 1
            except SystemExit as reason:
                print(f"{context}: skipped, {reason}")
        print(f"{made} of {len(contexts)} figures written")
        return 0
    if bool(args.followed) != bool(args.scales):
        parser.error("give --followed and --scales together, or neither")
    if args.followed:
        followed, scales = args.followed, args.scales
    else:
        ladder = choose_ladder(args.context)
        followed, scales = ladder[0], ladder[1:]
    figure(args.context, followed, scales, args.algorithms, args.out or f"ladder_{args.context}")
    return 0


def figure(context: str, followed: str, scales: list[str], algorithms, out: str) -> None:
    """One ladder figure; raises SystemExit if it cannot be drawn honestly."""
    from types import SimpleNamespace
    args = SimpleNamespace(context=context, followed=followed, scales=scales,
                           algorithms=algorithms, out=out)
    ladder = [args.followed] + args.scales
    check_ladder(args.context, args.followed, args.scales)
    best, worst, combined = choose_rows(args.context, ladder)
    rows = args.algorithms or [best, worst]
    short = {r["scale"]: r["short_name"] for r in read(HERE / "contexts" / args.context / "manifest.csv")}
    tau = {(r["algorithm"], r["scale_b"]): float(r["tau_x"]) for r in read(HERE / "consistency.csv")
           if r["context"] == args.context and r["scale_a"] == args.followed and r["tau_x"]}

    cmap = plt.get_cmap("viridis")
    fig, axes = plt.subplots(len(rows), len(ladder), figsize=(3.6 * len(ladder), 3.5 * len(rows)))
    for i, algorithm in enumerate(rows):
        first = load_drawing(HERE / "contexts" / args.context / f"{args.followed}.cxt",
                             graphml_path(algorithm, args.context, args.followed))
        order = sorted(first, key=lambda e: first[e][0])           # left to right
        colour_of = {e: cmap(k / max(1, len(order) - 1)) for k, e in enumerate(order)}
        for j, scale in enumerate(ladder):
            panel(axes[i][j], args.context, algorithm, scale, colour_of,
                  None if j == 0 else tau.get((algorithm, scale)), short.get(scale, scale))
        label = (f"{algorithm}\ncombined rank {combined[algorithm]:.2f}"
                 if algorithm in combined else algorithm)
        axes[i][0].text(-0.08, 0.5, label, transform=axes[i][0].transAxes, rotation=90,
                        ha="right", va="center", fontsize=10)

    fig.suptitle(f"{args.context}: the {len(first)} concepts of '{short.get(args.followed)}' followed as "
                 f"the lattice grows, coloured by their left-to-right position in the first panel\n"
                 f"(purple = leftmost, yellow = rightmost); |tau| against the first panel", fontsize=10.5)
    fig.tight_layout(rect=(0.02, 0, 1, 0.95))
    out = args.out
    (HERE / "figures").mkdir(exist_ok=True)
    for suffix in ("pdf", "png"):
        fig.savefig(HERE / "figures" / f"{out}.{suffix}", dpi=170)
    plt.close(fig)
    print(f"{args.context}: rows {rows[0]} (best), {rows[1]} (worst among those drawing "
          f"the whole ladder) -> figures/{out}.pdf, .png")


if __name__ == "__main__":
    raise SystemExit(main())
