"""Pick the standard example contexts that are large enough to scale, and import them.

Source: ``contexts/real-world/original`` of the surrounding drawing-quality
repository, that is two levels up from this file. The *original* variant is used
rather than *reduced* because only it keeps the real object and attribute names,
which hand-picked scales need; the reduced files carry `g1`, `m1` and so on.

Only contexts comparable in size to the ones collected here are wanted. Those five
run from 371 to 10463 concepts, and from 101 to 1106 objects plus attributes:

    tenpc_exoplanets    85 x 16      371 concepts
    instruments         64 x 42      576
    wd40pc            1078 x 28      728
    tenpc_stars        456 x 35      732
    olympics            70 x 38    10463

A candidate is kept when it reaches either end of that: a lattice of at least 60
concepts, which still allows three or four coarsening steps above the floor of 10 to
12, or at least 100 objects plus attributes, which makes it a comparable drawing
problem even when its lattice is smaller. Width must be at least 3 in any case,
since a chain has no horizontal freedom to measure. Rather smaller than our own is
deliberately allowed, so that the classic two-mode network examples come in; the
textbook contexts of a dozen concepts do not.

Run it from the Scaling directory, so the interpreter path is not relative:

    .venv/bin/python contexts/import_standard_contexts.py            # measure and import
    .venv/bin/python contexts/import_standard_contexts.py --dry-run  # measure only
    .venv/bin/python contexts/import_standard_contexts.py --min-concepts 300

Two adjustments are made to the plain size filter. Several of the 42 files hold
the same data twice under different names, so duplicates are detected and only one
of each is imported. And Living Beings and Water is imported whatever its size,
because it is the published worked example the method is validated against, not a
member of the corpus.

Imported contexts land in ``<name>/<name>.cxt``, each with a `.imported-from`
marker recording its origin. A folder without that marker is never written to, so
the contexts built here are safe, and a folder that has since gained scales or
notes of its own is never deleted either.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import conceptflow as cf

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent.parent / "contexts" / "real-world" / "original"
MARKER = ".imported-from"

# A lattice bigger than this cannot be drawn legibly at full size. Such contexts
# are still worth importing: their chain simply has to stop below the top.
DRAWABLE_LIMIT = 500

# Width is computed by matching, which is quadratic in the number of concepts.
WIDTH_LIMIT = 600

# Imported whatever its size: the published worked example the construction is
# checked against before anything larger is scaled.
BASELINE = {"living_beings_and_water"}

# When two files hold the same data, keep these names rather than the first
# alphabetically: seasoning_planner is the name the literature uses, and
# southern_woman carries the real names of the Davis study while its twin has
# first names and numbered events.
PREFERRED_DUPLICATE = {"seasoning_planner", "southern_woman", "bird_diet"}


def width(extents: list[frozenset[int]]) -> int:
    """Largest antichain. By Dilworth that is the number of concepts minus a maximum
    matching of the strict inclusion order, taken over all comparable pairs."""
    items = sorted(extents, key=len)
    n = len(items)
    adjacency: list[list[int]] = [[] for _ in range(n)]
    for a in range(n):
        for b in range(a + 1, n):
            if items[a] < items[b]:
                adjacency[a].append(b)

    matched = [-1] * n

    def augment(u: int, seen: list[bool]) -> bool:
        for v in adjacency[u]:
            if not seen[v]:
                seen[v] = True
                if matched[v] == -1 or augment(matched[v], seen):
                    matched[v] = u
                    return True
        return False

    return n - sum(1 for u in range(n) if augment(u, [False] * n))


def measure(path: Path) -> dict:
    context = cf.io.read_cxt(path)
    incidence = np.asarray(context.incidence, dtype=bool)
    extents = [c.extent for c in cf.algorithms.enumerate_concepts(context)]
    n_obj, n_att = context.n_objects, context.n_attributes
    return {
        "name": path.stem,
        "path": path,
        "objects": n_obj,
        "attributes": n_att,
        "density": float(incidence.sum()) / (n_obj * n_att) if n_obj and n_att else 0.0,
        "concepts": len(extents),
        "width": width(extents) if len(extents) <= WIDTH_LIMIT else None,
        # Same table, same object order: certainly one data set twice.
        "signature": (n_obj, n_att, tuple(sorted(tuple(row) for row in incidence.tolist()))),
        # Same shape, same row and column degrees, same lattice size: the same data
        # under a relabelling. Strong evidence rather than a proof of isomorphism.
        "shape": (n_obj, n_att, len(extents),
                  tuple(sorted(incidence.sum(axis=1).tolist())),
                  tuple(sorted(incidence.sum(axis=0).tolist()))),
        "twin": None,
    }


def mark_duplicates(records: list[dict]) -> None:
    """Where two files hold the same data, keep one and point the others at it."""
    for key, exact in (("signature", True), ("shape", False)):
        groups: dict[tuple, list[dict]] = {}
        for record in records:
            if record["twin"] is None:
                groups.setdefault(record[key], []).append(record)
        for group in groups.values():
            if len(group) < 2:
                continue
            names = sorted(r["name"] for r in group)
            keep = next((n for n in names if n in PREFERRED_DUPLICATE), names[0])
            for record in group:
                if record["name"] != keep:
                    record["twin"] = keep
                    record["twin_exact"] = exact


def qualifies(record: dict, min_concepts: int, min_size: int) -> tuple[bool, str]:
    if record["twin"]:
        how = "same data as" if record.get("twin_exact") else "same data, relabelled, as"
        return False, f"{how} {record['twin']}"
    if record["name"] in BASELINE:
        return True, ""
    if record["width"] is not None and record["width"] < 3:
        return False, f"width {record['width']}, no horizontal freedom"
    size = record["objects"] + record["attributes"]
    if record["concepts"] < min_concepts and size < min_size:
        return False, f"too small: {record['concepts']} concepts, {size} objects plus attributes"
    return True, ""


def import_context(record: dict) -> str:
    """Copy one context into its own folder here. Returns a status word."""
    target_dir = HERE / record["name"]
    marker = target_dir / MARKER
    if target_dir.exists() and not marker.exists():
        return "skipped (folder exists and is not an import)"
    target_dir.mkdir(parents=True, exist_ok=True)
    (target_dir / f"{record['name']}.cxt").write_text(
        record["path"].read_text(encoding="utf-8"), encoding="utf-8")
    marker.write_text(
        f"{record['path'].relative_to(HERE.parent.parent.parent)}\n"
        f"imported by contexts/import_standard_contexts.py\n", encoding="utf-8")
    return "imported"


def remove_stale(kept: list[dict]) -> None:
    """Drop earlier imports that no longer qualify, but never anything derived."""
    wanted = {r["name"] for r in kept}
    for folder in sorted(HERE.iterdir()):
        if not (folder.is_dir() and (folder / MARKER).exists()) or folder.name in wanted:
            continue
        ours = {MARKER, f"{folder.name}.cxt"}
        extra = sorted(p.name for p in folder.iterdir() if p.name not in ours)
        if extra:
            print(f"  {folder.name:34s} no longer selected, but kept: it also holds "
                  f"{', '.join(extra)}")
            continue
        for item in folder.iterdir():
            item.unlink()
        folder.rmdir()
        print(f"  {folder.name:34s} removed, no longer selected")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--min-concepts", type=int, default=60,
                        help="lattice size that qualifies on its own (default: 60)")
    parser.add_argument("--min-size", type=int, default=100,
                        help="objects plus attributes that qualify on their own (default: 100)")
    parser.add_argument("--dry-run", action="store_true", help="measure but import nothing")
    parser.add_argument("--markdown", action="store_true", help="print the table as markdown")
    args = parser.parse_args()

    if not SOURCE.is_dir():
        print(f"source not found: {SOURCE}", file=sys.stderr)
        return 1

    records = []
    for path in sorted(SOURCE.glob("*.cxt")):
        try:
            records.append(measure(path))
        except Exception as exc:  # a malformed file should not stop the survey
            print(f"  unreadable: {path.name}: {exc}", file=sys.stderr)
    records.sort(key=lambda r: -r["concepts"])
    mark_duplicates(records)

    kept = []
    for record in records:
        ok, reason = qualifies(record, args.min_concepts, args.min_size)
        record["reason"] = reason
        if ok:
            kept.append(record)

    if args.markdown:
        print("| Context | Objects | Attributes | Concepts | Width |")
        print("|---|---|---|---|---|")
        for r in kept:
            print(f"| `{r['name']}` | {r['objects']} | {r['attributes']} | {r['concepts']} | "
                  f"{r['width'] if r['width'] is not None else 'n/a'} |")
        return 0

    print(f"{len(records)} contexts in {SOURCE.relative_to(HERE.parent.parent.parent)}\n")
    print(f"{'context':34s}{'obj':>5s}{'att':>5s}{'o+a':>7s}{'dens':>7s}"
          f"{'concepts':>10s}{'width':>7s}  verdict")
    for r in records:
        w = "-" if r["width"] is None else str(r["width"])
        verdict = "keep" if not r["reason"] else r["reason"]
        if not r["reason"] and r["name"] in BASELINE:
            verdict = "keep as the baseline example"
        elif not r["reason"] and r["concepts"] > DRAWABLE_LIMIT:
            verdict = "keep, too large to draw at full size"
        print(f"{r['name']:34s}{r['objects']:5d}{r['attributes']:5d}"
              f"{r['objects'] + r['attributes']:7d}{r['density']:7.3f}"
              f"{r['concepts']:10d}{w:>7s}  {verdict}")

    print(f"\n{len(kept)} of {len(records)} pass the filter (at least "
          f"{args.min_concepts} concepts or {args.min_size} objects plus attributes, "
          f"width at least 3).")

    if args.dry_run:
        print("dry run: nothing written.")
        return 0

    print()
    for r in kept:
        print(f"  {r['name']:34s} {import_context(r)}")
    remove_stale(kept)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
