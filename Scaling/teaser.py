"""The first-page figure: DimDraw across a ladder of strictly nested views.

One row, View 1 ⊑ View 2 ⊑ View 3 ⊑ View 4, the ladder `ladder_figure.py` chooses
for the context. Each view nests into the next (checked against `nesting.csv`), so
the ⊑ between the column heads is true. Under View 1 its scores on the 14 metrics
of the metric set, coloured by family; under the others the order consistency CO
against View 1.

The concepts of View 1 are coloured by their left-to-right position in DimDraw's
drawing of View 1 and followed through every panel; a panel whose order is kept the
other way round (tau < 0 against View 1) is shown reflected and marked "mirrored",
as in `ladder_figure.py`.

    python teaser.py                       # olympics -> figures/teaser.pdf, .png
    python teaser.py --context wd40pc      # any context whose ladder is strict

Reads drawings, `quality.csv` and `consistency.csv` that `run_harness.py` produced.
"""

from __future__ import annotations

import argparse
from xml.etree.ElementTree import parse as parse_xml

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch

from ladder_figure import (GRAPHML_NS, HERE, PAGE_WIDTH_IN, choose_ladder, graphml_path,
                           load_drawing, read, read_positions)

ALGORITHM = "dimdraw"
DEFAULT_CONTEXT = "olympics"

# Paper order, abbreviations and families as in analysis/results.ipynb (METRICS).
METRICS = {
    "edge_crossing": ("EC", "Crossings"), "crossing_angle": ("CA", "Crossings"),
    "layer_consistency": ("LC", "Layering"), "vertical_axis_balance": ("SY", "Layering"),
    "slope_verticality": ("FE", "Slopes"), "slope_economy": ("SE", "Slopes"),
    "slope_parallelism": ("SP", "Slopes"), "edge_length_uniformity": ("EH", "Slopes"),
    "slope_standard": ("SC", "Slopes"), "visual_chain_linearity": ("CL", "Slopes"),
    "node_edge_conflict": ("NE", "Clearance"), "node_node_conflict": ("NN", "Clearance"),
    "edge_edge_conflict": ("EE", "Clearance"), "nested_suitability": ("NS", "Clearance"),
}
# Tableau 10 (Stone 2016), a standard qualitative palette whose colours are matched in
# saturation and lightness: its red, orange, purple and brown. Its blue, teal, green and
# yellow are left out, being too close to viridis, which encodes left-to-right position
# in the same figure (steel blue is CIEDE2000 8 from viridis at 0.34; these four are 30
# or more); black is the colour of the CO meters.
FAMILY_COLOUR = {"Crossings": "#e15759", "Layering": "#f28e2b", "Slopes": "#b07aa1",
                 "Clearance": "#9c755f"}

INK = "#1f1f1f"         # text
MUTED = "#3a3a3a"       # secondary text: counts, legend titles, "mirrored", bar labels
CARD = "#f5f5f2"        # panel background
TRACK = "#e2e2de"       # empty part of a bar or meter
EDGE = "#a9a9a6"        # lattice edges
NODE = "#8f8f8c"        # concepts not followed

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["STIX Two Text", "TeX Gyre Termes", "Times New Roman", "DejaVu Serif"],
    "mathtext.fontset": "stix",
    "font.size": 8,
    "pdf.fonttype": 42,
})


# --------------------------------------------------------------------------- data

def strict_ladder(context: str) -> list[str]:
    ladder = choose_ladder(context)
    nested = {(r["scale_a"], r["scale_b"]) for r in read(HERE / "contexts" / context / "nesting.csv")
              if r["nested"] == "True"}
    if len(ladder) != 4 or not all((a, b) in nested for a, b in zip(ladder, ladder[1:])):
        raise SystemExit(f"{context}: the ladder {ladder} is not four strictly nested views")
    return ladder


def quality(context: str, scale: str) -> list[float]:
    for r in read(HERE / "quality.csv"):
        if (r["context"], r["scale"], r["algorithm"]) == (context, scale, ALGORITHM):
            return [float(r[m]) for m in METRICS]
    raise SystemExit(f"no quality scores for {ALGORITHM} on {scale}")


def concepts(context: str, scale: str) -> int:
    return next(int(r["concepts"]) for r in read(HERE / "contexts" / context / "manifest.csv")
                if r["scale"] == scale)


# --------------------------------------------------------------------------- drawing

def draw_lattice(ax, context: str, scale: str, colour_of: dict, mirrored: bool) -> None:
    """One line diagram. Edges thin out with their number, so a large lattice reads as
    structure rather than a grey mass; the followed concepts sit on top, white-rimmed."""
    graphml = graphml_path(ALGORITHM, context, scale)
    positions = read_positions(graphml)
    by_extent = load_drawing(HERE / "contexts" / context / f"{scale}.cxt", graphml)
    root = parse_xml(graphml).getroot().find(f"{GRAPHML_NS}graph")
    edges = [(positions[e.get("source")], positions[e.get("target")])
             for e in root.findall(f"{GRAPHML_NS}edge")]
    alpha = float(np.clip((80 / max(1, len(edges))) ** 0.5, 0.22, 0.9))
    width = 0.45 if len(edges) < 80 else 0.3
    for (x1, y1), (x2, y2) in edges:
        ax.plot([x1, x2], [y1, y2], color=EDGE, linewidth=width, alpha=alpha,
                solid_capstyle="round", zorder=1)
    xs, ys = zip(*positions.values())
    ax.scatter(xs, ys, s=2.2 if len(xs) < 150 else 1.2, color=NODE, linewidths=0, zorder=2)
    followed = [(by_extent[e], c) for e, c in colour_of.items() if e in by_extent]
    ax.scatter([p[0] for p, _ in followed], [p[1] for p, _ in followed], s=17,
               c=[c for _, c in followed], edgecolors="white", linewidths=0.55, zorder=3)
    pad_x = 0.04 * (max(xs) - min(xs) or 1)
    pad_y = 0.04 * (max(ys) - min(ys) or 1)
    ax.set_xlim(min(xs) - pad_x, max(xs) + pad_x)
    ax.set_ylim(min(ys) - pad_y, max(ys) + pad_y)
    if mirrored:
        ax.invert_xaxis()
    ax.set_axis_off()


def metric_bars(ax, scores: list[float]) -> None:
    """14 bars in [0, 1] on a light track, grouped and coloured by family, labelled."""
    xs, x, prev = [], 0.0, None
    for _, family in METRICS.values():
        if prev is not None and family != prev:
            x += 0.7
        xs.append(x)
        x, prev = x + 1, family
    colours = [FAMILY_COLOUR[f] for _, f in METRICS.values()]
    ax.bar(xs, [1] * len(xs), width=0.74, color=TRACK, zorder=1)
    ax.bar(xs, scores, width=0.74, color=colours, zorder=2)
    ax.set_facecolor("none")                     # the card shows through the gaps
    ax.set_xlim(xs[0] - 0.5, xs[-1] + 0.5)
    ax.set_ylim(0, 1)
    ax.set_yticks([])
    ax.set_xticks(xs, [a for a, _ in METRICS.values()])
    ax.tick_params(axis="x", length=0, pad=1.6, labelsize=5.3, labelrotation=90,
                   labelcolor=MUTED)
    for side in ax.spines.values():
        side.set_visible(False)


def co_meter(fig, cx: float, y: float, width: float, tau: float, H: float) -> None:
    """CO as a value and a thin meter on [0, 1]; "mirrored" beneath when tau < 0."""
    fig.text(cx, y, rf"$\mathrm{{CO}} = \mathbf{{{abs(tau):.2f}}}$", ha="center", va="bottom",
             fontsize=8.5, color=INK)
    track_h = 0.035 / H
    ty = y - 0.07 / H
    for w, colour in ((width, TRACK), (width * abs(tau), INK)):
        fig.add_artist(FancyBboxPatch((cx - width / 2, ty), w, track_h,
                                      boxstyle="round,pad=0,rounding_size=0.002",
                                      transform=fig.transFigure, facecolor=colour,
                                      edgecolor="none"))
    if tau < 0:
        fig.text(cx, ty - 0.04 / H, "mirrored", ha="center", va="top", fontsize=6.5,
                 color=MUTED, style="italic")


# --------------------------------------------------------------------------- figure

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--context", default=DEFAULT_CONTEXT)
    parser.add_argument("--out", default="teaser", help="basename, written into figures/")
    args = parser.parse_args()
    context = args.context

    ladder = strict_ladder(context)
    tau = {r["scale_b"]: float(r["tau_x"]) for r in read(HERE / "consistency.csv")
           if r["context"] == context and r["algorithm"] == ALGORITHM
           and r["scale_a"] == ladder[0] and r["tau_x"]}
    cmap = plt.get_cmap("viridis")
    first = load_drawing(HERE / "contexts" / context / f"{ladder[0]}.cxt",
                         graphml_path(ALGORITHM, context, ladder[0]))
    order = sorted(first, key=lambda e: first[e][0])                    # left to right
    colour_of = {e: cmap(k / max(1, len(order) - 1)) for k, e in enumerate(order)}

    # Laid out in inches and converted, so spacing is exact on the page.
    W, H = PAGE_WIDTH_IN, 2.22
    fig = plt.figure(figsize=(W, H))
    fx, fy = (lambda v: v / W), (lambda v: v / H)
    margin, gap = 0.02, 0.22
    card_w = (W - 2 * margin - 3 * gap) / 4
    key_band = 0.19                                   # legend strip at the bottom
    card_y0, card_y1 = key_band, H - 0.02
    head_h, foot_h = 0.22, 0.42
    lat_y0, lat_y1 = card_y0 + foot_h, card_y1 - head_h

    for j, scale in enumerate(ladder):
        x0 = margin + j * (card_w + gap)
        cx = x0 + card_w / 2
        fig.add_artist(FancyBboxPatch((fx(x0), fy(card_y0)), fx(card_w), fy(card_y1 - card_y0),
                                      boxstyle="round,pad=0,rounding_size=0.012",
                                      transform=fig.transFigure, facecolor=CARD,
                                      edgecolor="none", zorder=0))
        # One header line, "View n · k concepts", centred as a whole on the card.
        renderer = fig.canvas.get_renderer()
        hy = fy(card_y1 - 0.14)
        name = fig.text(0, hy, f"View {j + 1}", ha="left", va="baseline", fontsize=9,
                        weight="bold", color=INK)
        size = fig.text(0, hy, f"  ·  {concepts(context, scale)} concepts", ha="left",
                        va="baseline", fontsize=7.5, color=MUTED)
        w_name = name.get_window_extent(renderer).width / fig.dpi
        w_size = size.get_window_extent(renderer).width / fig.dpi
        name.set_x(fx(cx - (w_name + w_size) / 2))
        size.set_x(fx(cx - (w_name + w_size) / 2 + w_name))
        if j:
            fig.text(fx(x0 - gap / 2), fy((card_y0 + card_y1) / 2), r"$\sqsubseteq$",
                     ha="center", va="center_baseline", fontsize=13, color=INK)

        t = tau.get(scale) if j else None
        ax = fig.add_axes((fx(x0 + 0.05), fy(lat_y0), fx(card_w - 0.10), fy(lat_y1 - lat_y0)))
        draw_lattice(ax, context, scale, colour_of, mirrored=t is not None and t < 0)

        if j == 0:
            bars = fig.add_axes((fx(x0 + 0.14), fy(card_y0 + 0.13), fx(card_w - 0.28), fy(0.25)))
            metric_bars(bars, quality(context, scale))
        elif t is not None:
            co_meter(fig, fx(cx), fy(card_y0 + 0.22), fx(0.62), t, H)

    # Legend strip: metric families on the left, the colour scale on the right.
    # Widths are measured, so the spacing is even whatever the labels say.
    ky = fy(key_band / 2 - 0.01)
    renderer = fig.canvas.get_renderer()

    def put(x, text, **kw):
        """Place text left-aligned at x inches; return the x where it ends."""
        t = fig.text(fx(x), ky, text, ha="left", va="center", fontsize=7, **kw)
        return x + t.get_window_extent(renderer).width / fig.dpi

    x = put(margin + 0.1, "Metric families:", color=MUTED, style="italic") + 0.14
    for family, colour in FAMILY_COLOUR.items():
        fig.add_artist(FancyBboxPatch((fx(x), ky - fy(0.035)), fx(0.07), fy(0.07),
                                      boxstyle="round,pad=0,rounding_size=0.002",
                                      transform=fig.transFigure, facecolor=colour,
                                      edgecolor="none"))
        x = put(x + 0.1, family, color=INK) + 0.2

    # The colour scale, right-aligned to the last card: measure, then place.
    probe = [fig.text(0, 0, s, fontsize=7) for s in ("Position in View 1:", "left", "right")]
    w_title, w_left, w_right = (t.get_window_extent(renderer).width / fig.dpi for t in probe)
    for t in probe:
        t.remove()
    bar_w = 0.7
    x = W - margin - 0.1 - (w_title + 0.14 + w_left + 0.06 + bar_w + 0.06 + w_right)
    x = put(x, "Position in View 1:", color=MUTED, style="italic") + 0.14
    x = put(x, "left", color=INK) + 0.06
    key = fig.add_axes((fx(x), ky - fy(0.03), fx(bar_w), fy(0.06)))
    key.imshow(np.linspace(0, 1, 256)[None, :], cmap=cmap, aspect="auto")
    key.set_axis_off()
    put(x + bar_w + 0.06, "right", color=INK)

    (HERE / "figures").mkdir(exist_ok=True)
    for suffix in ("pdf", "png"):
        fig.savefig(HERE / "figures" / f"{args.out}.{suffix}", dpi=250)
    plt.close(fig)
    print(f"{context}: {' ⊑ '.join(ladder)}; CO vs View 1: "
          + ", ".join(f"{abs(tau[s]):.2f}" for s in ladder[1:] if s in tau)
          + f" -> figures/{args.out}.pdf, .png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
