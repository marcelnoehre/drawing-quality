"""Verify that generated scales really are scale-measures, and record their nesting.

Two checks, both run during generation by ``build_scales.py`` and available here
on the command line.

**Scale-measure property.** Our map is the identity on objects, so by HH
Proposition 20 a scale is a scale-measure exactly when it is one for each of its
attributes separately. For every attribute of the scale we therefore check that
its extent is an extent of the original context, that is, that it equals its own
closure there. That is one closure per attribute. Enumerating the extents of the
scale, which is exponential, is not needed and is not done.

**Nesting.** For RQ4 we need pairs where the coarser view's extents are all
extents of the finer one. This is checked by enumerating both extent sets, which
is affordable at our sizes, and is written out as a matrix so that it is derived
from the files rather than asserted in prose.

    python contexts/verify_scale.py contexts/instruments/instruments.cxt \\
        contexts/instruments/excitation.cxt                     # one scale
    python contexts/verify_scale.py contexts/instruments/instruments.cxt \\
        --dir contexts/instruments --matrix contexts/instruments/nesting.csv

With --dir the scales are taken from the manifest in that folder, so the other
.cxt files living beside them are not mistaken for scales.

Exits non-zero when any check fails, naming the attribute or the pair.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import conceptflow as cf

# CLAUDE.md sets this floor: below eight shared concepts a rank correlation over
# the shared nodes has too little to work with.
THIN_OVERLAP = 8


def extents_of(context: cf.FormalContext) -> set[frozenset[int]]:
    """Every extent of a context, as frozensets of object indices."""
    return {c.extent for c in cf.algorithms.enumerate_concepts(context)}


def check_scale_measure(original: cf.FormalContext,
                        scale: cf.FormalContext) -> list[str]:
    """HH Prop. 20 check. Returns a list of problems; empty means it is a scale-measure."""
    problems: list[str] = []
    if tuple(scale.objects) != tuple(original.objects):
        problems.append("object sets differ, so the identity is not a map between them")
        return problems

    for index, name in enumerate(scale.attributes):
        extent = scale.attribute_derivation([index])
        # The same object set, closed in the original context.
        closed = original.attribute_derivation(original.object_derivation(extent))
        if closed != extent:
            problems.append(
                f"attribute {name!r}: its extent has {len(extent)} objects but closes to "
                f"{len(closed)} in the original context, so it is not an extent there")
    return problems


def nesting_rows(contexts: dict[str, cf.FormalContext],
                 drawable: dict[str, bool] | None = None) -> list[dict]:
    """One row per ordered pair: does a's extent set sit inside b's, and how much overlaps.

    A pair is *usable* for a cross-level comparison when it nests, shares enough
    concepts to correlate ranks over, and both sides can actually be drawn. A scale
    kept only to show how large the data are is nested under all the same way, but
    nothing is ever drawn from it, so those pairs are marked unusable here rather
    than being discovered later in the pipeline."""
    extent_sets = {name: extents_of(context) for name, context in contexts.items()}
    rows = []
    for a in contexts:
        for b in contexts:
            if a == b:
                continue
            ext_a, ext_b = extent_sets[a], extent_sets[b]
            shared = len(ext_a & ext_b)
            rows.append({
                "scale_a": a,
                "scale_b": b,
                "nested": ext_a <= ext_b,
                "ext_a": len(ext_a),
                "ext_b": len(ext_b),
                "shared": shared,
                "ratio": round(len(ext_b) / len(ext_a), 3) if ext_a else "",
                "thin": shared < THIN_OVERLAP,
                "usable": bool(ext_a <= ext_b and shared >= THIN_OVERLAP
                               and (drawable is None
                                    or (drawable.get(a, True) and drawable.get(b, True)))),
            })
    return rows


def write_matrix(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def verify_directory(original_path: Path, directory: Path, matrix_path: Path | None,
                     quiet: bool = False) -> int:
    """Check every scale in a directory and optionally write the nesting matrix."""
    original = cf.io.read_cxt(original_path)
    manifest = directory / "manifest.csv"
    if manifest.exists():
        with manifest.open(encoding="utf-8") as f:
            names = [row["scale"] for row in csv.DictReader(f)]
        scales = {n: cf.io.read_cxt(directory / f"{n}.cxt") for n in names}
    else:
        scales = {p.stem: cf.io.read_cxt(p) for p in sorted(directory.glob("*.cxt"))}
    if not scales:
        print(f"no scales found in {directory}", file=sys.stderr)
        return 1

    failures = 0
    for name, scale in scales.items():
        problems = check_scale_measure(original, scale)
        if problems:
            failures += 1
            print(f"FAIL {name}", file=sys.stderr)
            for problem in problems:
                print(f"     {problem}", file=sys.stderr)
        elif not quiet:
            print(f"  ok  {name:32s} {len(scale.attributes):3d} attributes, "
                  f"scale-measure property holds for every attribute")

    if matrix_path is not None:
        drawable = None
        if manifest.exists():
            with manifest.open(encoding="utf-8") as f:
                drawable = {row["scale"]: row.get("drawable", "True") == "True"
                            for row in csv.DictReader(f)}
        rows = nesting_rows(scales, drawable)
        write_matrix(rows, matrix_path)
        nested = [r for r in rows if r["nested"]]
        thin = [r for r in nested if r["thin"]]
        usable = [r for r in nested if r["usable"]]
        if not quiet:
            print(f"\n  {len(nested)} nested pairs of {len(rows)} ordered pairs, "
                  f"{len(usable)} of them usable for a cross-level comparison "
                  f"-> {matrix_path}")
            for r in sorted(nested, key=lambda r: r["ratio"] if r["ratio"] != "" else 0):
                flag = ("  THIN" if r["thin"] else "") + ("" if r["usable"] else "  not usable")
                print(f"    {r['scale_a']:32s} in {r['scale_b']:32s} "
                      f"{r['ext_a']:4d} -> {r['ext_b']:4d}  shared {r['shared']:4d}  "
                      f"ratio {r['ratio']}{flag}")
        if thin:
            print(f"  note: {len(thin)} nested pairs share fewer than {THIN_OVERLAP} "
                  f"concepts and are too thin for a rank correlation", file=sys.stderr)

    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("original", type=Path, help="the context the scales are taken from")
    parser.add_argument("scales", type=Path, nargs="*", help="scale files to check")
    parser.add_argument("--dir", type=Path, help="check every .cxt in this directory")
    parser.add_argument("--matrix", type=Path, help="write the nesting matrix here")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    if args.dir:
        return verify_directory(args.original, args.dir, args.matrix, args.quiet)

    if not args.scales:
        parser.error("give scale files, or --dir")

    original = cf.io.read_cxt(args.original)
    failures = 0
    for path in args.scales:
        problems = check_scale_measure(original, cf.io.read_cxt(path))
        if problems:
            failures += 1
            print(f"FAIL {path}", file=sys.stderr)
            for problem in problems:
                print(f"     {problem}", file=sys.stderr)
        elif not args.quiet:
            print(f"  ok  {path}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
