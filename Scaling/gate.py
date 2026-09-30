"""The hand-eye gate: is cross-scale inconsistency visible at all?

This produces no number and settles no question. It is a feasibility check before
the measurement is built out: if an algorithm visibly scrambles shared concepts
when a scale is refined, the effect is worth measuring; if twelve pictures show
nothing, either the generator is wrong or the effect needs a sample nobody has.

Two algorithms, four scales of the instruments context spanning the size range,
drawn side by side. The concepts of one coarse scale are marked in every panel, so
the eye can follow the same concepts as the lattice grows around them. Those marks
are the whole point: a consistent algorithm keeps their left-to-right order, and an
inconsistent one does not.

    python gate.py                       # draw what is missing, then render
    python gate.py --algorithms fdp redraw --out gate-fdp

Writes `figures/<name>.pdf` and `figures/<name>.png`.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from xml.etree.ElementTree import parse as parse_xml

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from graphml_loader import load_drawing, read_positions  # noqa: E402
from run_harness import draw, graphml_path, scale_path  # noqa: E402

GRAPHML_NS = "{http://graphml.graphdrawing.org/xmlns}"

CONTEXT = "instruments"
# Four scales spanning the drawable range, chosen so that the marked set recurs in
# every panel: `practice` nests into each of the other three, so its 46 concepts
# are present in all four drawings and the eye can follow them as the lattice grows
# from 46 to 576. A ladder that merely spanned the sizes would be useless here; a
# first attempt using `capability` shared only two concepts with `practice`, which
# marks nothing worth looking at.
SCALES = ["practice", "family-practice", "capability-practice-making", "instruments"]
# Whose concepts get marked in every panel. It has to nest into all of the above.
FOLLOWED = "practice"
# The pair the committed figures use. fdp and freese were the first choice and
# are a bad default: neither draws the 576-concept scale, so the widest panel
# of the ladder comes out empty.
DEFAULT_ALGORITHMS = ["sugiyama", "aeschlimann_schmid"]


def edges(graphml: Path) -> list[tuple[str, str]]:
    graph = parse_xml(graphml).getroot().find(f"{GRAPHML_NS}graph")
    return [(e.get("source"), e.get("target")) for e in graph.findall(f"{GRAPHML_NS}edge")]


def panel(ax, algorithm: str, scale: str, followed: set[frozenset]) -> str:
    graphml = graphml_path(algorithm, CONTEXT, scale)
    if not graphml.exists():
        ax.text(0.5, 0.5, "not drawn", ha="center", va="center", fontsize=9, color="0.4")
        ax.set_axis_off()
        return "not drawn"

    positions = read_positions(graphml)
    by_extent = load_drawing(scale_path(CONTEXT, scale), graphml, algorithm)
    marked_positions = [by_extent[e] for e in followed if e in by_extent]

    for source, target in edges(graphml):
        if source in positions and target in positions:
            (x1, y1), (x2, y2) = positions[source], positions[target]
            ax.plot([x1, x2], [y1, y2], color="0.75", linewidth=0.4, zorder=1)

    xs = [p[0] for p in positions.values()]
    ys = [p[1] for p in positions.values()]
    ax.scatter(xs, ys, s=6, color="0.35", zorder=2, linewidths=0)
    if marked_positions:
        ax.scatter([p[0] for p in marked_positions], [p[1] for p in marked_positions],
                   s=22, color="#c1121f", zorder=3, linewidths=0)

    ax.set_axis_off()
    ax.set_title(f"{scale}\n{len(positions)} concepts, {len(marked_positions)} marked",
                 fontsize=8)
    return f"{len(positions)} concepts, {len(marked_positions)} marked"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--algorithms", nargs="+", default=DEFAULT_ALGORITHMS)
    parser.add_argument("--scales", nargs="+", help="override the four scales")
    parser.add_argument("--followed", help="whose concepts are marked; must nest into every scale")
    # A basename, not a path, and always under figures/: the repository tracks that
    # directory and ignores loose PDFs at the top level, so writing there would
    # quietly leave half the figure untracked.
    parser.add_argument("--out", default="gate",
                        help="basename of the figure, written into figures/")
    parser.add_argument("--skip-draw", action="store_true")
    args = parser.parse_args()

    scales = args.scales or SCALES
    if not args.skip_draw:
        for algorithm in args.algorithms:
            for scale in scales:
                result = draw(algorithm, CONTEXT, scale)
                print(f"  {algorithm:12s} {scale:28s} {result['status']:9s} "
                      f"{result['runtime_s']} {result['note']}")

    followed_scale = args.followed or FOLLOWED
    if not args.skip_draw:
        for algorithm in args.algorithms:
            draw(algorithm, CONTEXT, followed_scale)
    followed = set(load_drawing(
        scale_path(CONTEXT, followed_scale),
        graphml_path(args.algorithms[0], CONTEXT, followed_scale),
        args.algorithms[0]))

    rows, columns = len(args.algorithms), len(scales)
    fig, axes = plt.subplots(rows, columns, figsize=(4.2 * columns, 4.0 * rows))
    axes = axes.reshape(rows, columns)
    for r, algorithm in enumerate(args.algorithms):
        for c, scale in enumerate(scales):
            summary = panel(axes[r][c], algorithm, scale, followed)
            print(f"  {algorithm:12s} {scale:28s} {summary}")
        axes[r][0].set_ylabel(algorithm)
        axes[r][0].text(-0.05, 0.5, algorithm, transform=axes[r][0].transAxes,
                        rotation=90, va="center", ha="right", fontsize=10)

    fig.suptitle(f"instruments; the {len(followed)} concepts of "
                 f"'{followed_scale}' marked in red wherever they occur", fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    figures = HERE / "figures"
    figures.mkdir(exist_ok=True)
    name = Path(args.out).stem
    for suffix in ("pdf", "png"):
        fig.savefig(figures / f"{name}.{suffix}", dpi=160)
    print(f"\n-> figures/{name}.pdf, figures/{name}.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
