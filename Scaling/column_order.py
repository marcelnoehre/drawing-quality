"""Do the algorithms respond to the order of a context's columns or rows?

Shuffling the attribute columns, or the object rows, of a `.cxt` changes nothing
about the context, the lattice or any concept. A layout that depended only on the
lattice would be unchanged. This draws four small instruments scales under four
column shuffles and four row shuffles with every algorithm, and compares each
drawing with the drawing of the same scale in its canonical order (from the main
run, `graphml/`), concept by concept, matched by extent.

Per drawing it records whether the drawing is identical, Kendall tau between the
two left-to-right orders (|tau| is what the consistency measure ranks; -1 is an
exact mirror image), and whether any concept changed height relative to the others.

    python column_order.py              # writes column_order.csv and prints a summary
    python column_order.py --figure     # figures/column-order-demo.png from the drawings

The figure is chosen by a fixed rule, not by its look: one scale
(`instruments_excitation`, 21 concepts, which every algorithm draws), the first
seeded column shuffle, and all eight algorithms.

Every shuffle is seeded, so the run is reproducible. redraw needs the conexp-clj API
(see pipeline.md, *Setting up redraw*); without it redraw is left out and said so.
"""

from __future__ import annotations

import csv
import os
import random
import statistics
import sys
import tempfile
import urllib.request
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

from consistency import rank_drift, tau_x  # noqa: E402
from graphml_loader import load_drawing  # noqa: E402
from node_extents import ALGORITHMS, load_generator, recording, sidecar, source_hash  # noqa: E402
from run_harness import NONTERMINATING  # noqa: E402

CONTEXT = "instruments"
SCALES = ["instruments_capability", "instruments_making", "instruments_excitation",
          "instruments_practice"]                        # 13, 17, 21 and 46 concepts
SHUFFLES = 4
SEED = 20261019


def read_cxt(path: Path) -> tuple[list[str], list[str], list[str]]:
    lines = path.read_text(encoding="utf-8").split("\n")
    i = 1
    while not lines[i].strip():
        i += 1
    n, m = int(lines[i]), int(lines[i + 1])
    i += 2
    while not lines[i].strip():
        i += 1
    return lines[i:i + n], lines[i + n:i + n + m], [r[:m] for r in lines[i + n + m:i + n + m + n]]


def write_cxt(path: Path, objects, attributes, rows) -> None:
    path.write_text("B\n\n" + f"{len(objects)}\n{len(attributes)}\n\n"
                    + "\n".join(objects + attributes + rows) + "\n", encoding="utf-8")


def shuffled(source: Path, target: Path, kind: str, seed: int) -> None:
    objects, attributes, rows = read_cxt(source)
    rng = random.Random(seed)
    if kind == "columns":
        order = list(range(len(attributes)))
        rng.shuffle(order)
        attributes = [attributes[j] for j in order]
        rows = ["".join(r[j] for j in order) for r in rows]
    else:
        order = list(range(len(objects)))
        rng.shuffle(order)
        objects = [objects[i] for i in order]
        rows = [rows[i] for i in order]
    write_cxt(target, objects, attributes, rows)


WORK = HERE / ".column-order"          # inside the repository: the generators print
                                       # their output path relative to it; git-ignored


def drawn(algorithm: str, cxt: Path) -> Path | None:
    """The drawing of this shuffled file, if it exists and was made from it."""
    graphml = WORK / "graphml" / algorithm / CONTEXT / f"{cxt.stem}.graphml"
    if graphml.exists() and sidecar(graphml).exists():
        import json
        if json.loads(sidecar(graphml).read_text()).get("source_sha256") == source_hash(cxt):
            return graphml
    return None


def draw(job: tuple[str, Path, Path]) -> str | None:
    """Draw one shuffled file in its own working directory; return an error or None.

    Success is judged by the drawing and its recorded extents existing afterwards,
    not by the generator returning cleanly.
    """
    algorithm, cxt, out = job
    if drawn(algorithm, cxt):
        return None
    os.chdir(tempfile.mkdtemp(prefix="column-order-"))
    try:
        module = load_generator(algorithm)
        module.GRAPHML_ROOT = out / algorithm
        module.DRAWINGS_ROOT = out / "renders" / algorithm
        with recording(module, algorithm, cxt):
            module.generate(CONTEXT, cxt)
    except Exception as exc:                          # recorded, not hidden
        if not drawn(algorithm, cxt):
            return f"{type(exc).__name__}: {exc}"[:200]
    return None if drawn(algorithm, cxt) else "no drawing written"


FIGURE_SCALE = "instruments_excitation"


def figure() -> int:
    """The same lattice in canonical and in shuffled column order, every algorithm."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from xml.etree.ElementTree import parse as parse_xml
    from graphml_loader import GRAPHML_NS, read_positions

    name = f"{FIGURE_SCALE}_columns_0"
    cxt = WORK / f"{name}.cxt"
    canonical_cxt = HERE / "contexts" / CONTEXT / f"{FIGURE_SCALE}.cxt"
    algorithms = [a for a in ALGORITHMS if cxt.exists() and drawn(a, cxt)]
    if not algorithms:
        print("run column_order.py first: no shuffled drawings found", file=sys.stderr)
        return 1
    cmap = plt.get_cmap("viridis")
    fig, axes = plt.subplots(2, len(algorithms), figsize=(2.6 * len(algorithms), 5.6))
    for j, a in enumerate(algorithms):
        files = [(canonical_cxt, HERE / "graphml" / a / CONTEXT / f"{FIGURE_SCALE}.graphml"),
                 (cxt, drawn(a, cxt))]
        base = load_drawing(*files[0])
        order = sorted(base, key=lambda e: base[e][0])
        colour = {e: cmap(k / max(1, len(order) - 1)) for k, e in enumerate(order)}
        for i, (c, g) in enumerate(files):
            ax = axes[i][j]
            positions, by_extent = read_positions(g), load_drawing(c, g)
            graph = parse_xml(g).getroot().find(f"{GRAPHML_NS}graph")
            for e in graph.findall(f"{GRAPHML_NS}edge"):
                (x1, y1), (x2, y2) = positions[e.get("source")], positions[e.get("target")]
                ax.plot([x1, x2], [y1, y2], color="#c9c9c9", linewidth=0.4, zorder=1)
            ax.scatter([by_extent[e][0] for e in order], [by_extent[e][1] for e in order],
                       s=22, c=[colour[e] for e in order], zorder=2, linewidths=0.3,
                       edgecolors="#222222")
            ax.set_axis_off()
            if i == 0:
                ax.set_title(f"{a}\ncanonical order", fontsize=8.5)
            else:
                tau, _, _ = tau_x(base, by_extent)
                ax.set_title(f"columns shuffled\n|tau| = {abs(tau):.2f}"
                             + (" (mirrored)" if tau < 0 else ""), fontsize=8.5)
    fig.suptitle(f"The same lattice ({FIGURE_SCALE}, {len(order)} concepts) with its columns in "
                 f"canonical and in shuffled order; colour = left-to-right position in the "
                 f"canonical drawing", fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    for suffix in ("png", "pdf"):
        fig.savefig(HERE / "figures" / f"column-order-demo.{suffix}", dpi=160)
    print("-> figures/column-order-demo.png, .pdf")
    return 0


def main() -> int:
    if "--figure" in sys.argv:
        return figure()
    try:
        urllib.request.urlopen("http://127.0.0.1:8080/", timeout=5)
        algorithms = list(ALGORITHMS)
    except OSError:
        algorithms = [a for a in ALGORITHMS if a != "redraw"]
        print("conexp-clj API not reachable: redraw left out", file=sys.stderr)

    work = WORK
    work.mkdir(exist_ok=True)
    jobs, variants = [], []
    for s, scale in enumerate(SCALES):
        source = HERE / "contexts" / CONTEXT / f"{scale}.cxt"
        for kind in ("columns", "rows"):
            for k in range(SHUFFLES):
                name = f"{scale}_{kind}_{k}"
                cxt = work / f"{name}.cxt"
                shuffled(source, cxt, kind, SEED + 1000 * s + 100 * (kind == "rows") + k)
                variants.append((scale, kind, k, name, cxt))
                jobs += [(a, cxt, work / "graphml") for a in algorithms
                         if not (a in NONTERMINATING and NONTERMINATING[a](cxt))]

    with ProcessPoolExecutor(max_workers=8) as pool:
        errors = dict(zip([(j[0], j[1]) for j in jobs], pool.map(draw, jobs)))
    for scale, kind, k, name, cxt in variants:          # known non-termination, not run
        for a in algorithms:
            if a in NONTERMINATING and NONTERMINATING[a](cxt):
                errors[(a, cxt)] = "nonterminating: coextensive attributes; not run"

    rows = []
    for scale, kind, k, name, cxt in variants:
        canonical_cxt = HERE / "contexts" / CONTEXT / f"{scale}.cxt"
        for a in algorithms:
            row = {"scale": scale, "concepts": "", "shuffle": kind, "seed_index": k,
                   "algorithm": a}
            canonical = HERE / "graphml" / a / CONTEXT / f"{scale}.graphml"
            drawing = drawn(a, cxt)
            if errors.get((a, cxt)) or not drawing or not canonical.exists():
                row["status"] = errors.get((a, cxt)) or "no drawing"
                rows.append(row)
                continue
            base = load_drawing(canonical_cxt, canonical)
            other = load_drawing(cxt, drawing)
            tau, _, n = tau_x(base, other)
            row.update(status="ok", concepts=n,
                       identical=all(base[e] == other[e] for e in base),
                       tau_x=round(tau, 4), tau_abs=round(abs(tau), 4),
                       exact_mirror=tau == -1.0,
                       heights_changed=rank_drift(base, other) > 0)
            rows.append(row)

    with (HERE / "column_order.csv").open("w", newline="", encoding="utf-8") as f:
        fields = ["scale", "concepts", "shuffle", "seed_index", "algorithm", "status",
                  "identical", "tau_x", "tau_abs", "exact_mirror", "heights_changed"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    print(f"{'algorithm':20s}{'cols: unchanged':>16s}{'median |tau|':>14s}{'lowest |tau|':>14s}"
          f"{'mirror':>8s}{'heights':>9s}{'rows: unchanged':>17s}")
    for a in algorithms:
        cols = [r for r in rows if r["algorithm"] == a and r["shuffle"] == "columns" and r["status"] == "ok"]
        rws = [r for r in rows if r["algorithm"] == a and r["shuffle"] == "rows" and r["status"] == "ok"]
        if not cols:
            print(f"{a:20s} no drawings")
            continue
        share = lambda rs, key: f"{100 * sum(r[key] for r in rs) / len(rs):.0f}%"
        print(f"{a:20s}{share(cols, 'identical'):>16s}"
              f"{statistics.median(r['tau_abs'] for r in cols):>14.2f}"
              f"{min(r['tau_abs'] for r in cols):>14.2f}"
              f"{share(cols, 'exact_mirror'):>8s}{share(cols, 'heights_changed'):>9s}"
              f"{share(rws, 'identical') if rws else '-':>17s}")
    failed = [r for r in rows if r["status"] != "ok"]
    if failed:
        print(f"{len(failed)} drawings missing; see column_order.csv")
    print("-> column_order.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
