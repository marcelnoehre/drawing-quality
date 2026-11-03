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
import conceptflow.io  # noqa: F401  (cf.io is a subpackage, not loaded by the line above)
from conceptflow.metrics import lattice_width

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent.parent / "contexts" / "real-world" / "original"
MARKER = ".imported-from"

# Corrections applied while importing, so that re-importing reproduces them instead
# of silently undoing a hand edit. Only attribute *labels* are ever corrected here,
# never an incidence: the lattice of a corrected context is the lattice of its
# source, under names that say what its columns hold.
#
# zoo: the first eleven yes/no variables carry the label of the variable before
# them in the UCI Zoo order, and the label "venomous" is missing. Checked against
# the animals, not assumed: "[hair 1]" holds exactly the 20 birds, so it is
# feathers; "[eggs 1]" exactly the 41 mammals, so it is milk; "[breathes 1]" holds
# frog, honeybee, pit viper, scorpion, sea snake, sea wasp, stingray and wasp, so it
# is venomous; no fish has "[backbone 1]", so it is breathes. fins, leg, tail,
# domestic, catsize and type are correct. Both readers, odis and ConceptFlow, parse
# the file identically, so this is the file's labelling, not its format.
LABEL_CORRECTIONS = {
    "zoo": {
        "animal-name": "hair", "hair": "feathers", "feathers": "eggs", "eggs": "milk",
        "milk": "airborne", "airborne": "aquatic", "aquatic": "predator",
        "predator": "toothed", "toothed": "backbone", "backbone": "breathes",
        "breathes": "venomous",
    },
}


def correct_labels(name: str, text: str) -> str:
    """Apply LABEL_CORRECTIONS to the attribute names of a Burmeister file.

    Attribute names have the form "[variable value]"; only the variable is renamed,
    all at once, so no rename feeds into another. Objects and incidences are left
    exactly as they are.
    """
    mapping = LABEL_CORRECTIONS.get(name)
    if not mapping:
        return text
    lines = text.split("\n")
    n_objects, n_attributes = int(lines[2]), int(lines[3])
    first = 5 + n_objects
    for i in range(first, first + n_attributes):
        label = lines[i]
        if label.startswith("[") and " " in label:
            variable, rest = label[1:].split(" ", 1)
            if variable in mapping:
                lines[i] = f"[{mapping[variable]} {rest}"
    return "\n".join(lines)

# A lattice bigger than this cannot be drawn legibly at full size. Such contexts
# are still worth importing: their chain simply has to stop below the top.
DRAWABLE_LIMIT = 500

# Width is computed by matching, which is quadratic in the number of concepts.
WIDTH_LIMIT = 600

# Imported whatever its size: the published worked example the construction is
# checked against before anything larger is scaled.
BASELINE = {"living_beings_and_water"}

# Qualify on size but are not imported: their attributes are individuals (dolphins,
# numbered events, unnamed organisations) with no published meaning to group by,
# and this corpus exists to be scaled by meaning.
EXCLUDED = {
    "brunson_club": "organisations unnamed and untyped, nothing to group by",
    "dolphins": "attributes are individual dolphins, nothing to group by",
    "southern_woman": "attributes are numbered events, nothing to group by",
}

# When two files hold the same data, keep these names rather than the first
# alphabetically: seasoning_planner is the name the literature uses, and
# southern_woman carries the real names of the Davis study while its twin has
# first names and numbered events.
PREFERRED_DUPLICATE = {"seasoning_planner", "southern_woman", "bird_diet"}


def measure(path: Path) -> dict:
    context = cf.io.read_cxt(path)
    incidence = np.asarray(context.incidence, dtype=bool)
    lattice = cf.ConceptLattice.from_context(context)
    extents = [c.extent for c in lattice.concepts]
    n_obj, n_att = context.n_objects, context.n_attributes
    return {
        "name": path.stem,
        "path": path,
        "objects": n_obj,
        "attributes": n_att,
        "density": float(incidence.sum()) / (n_obj * n_att) if n_obj and n_att else 0.0,
        "concepts": len(extents),
        "width": lattice_width(lattice) if len(extents) <= WIDTH_LIMIT else None,
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
    if record["name"] in EXCLUDED:
        return False, f"excluded: {EXCLUDED[record['name']]}"
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
        correct_labels(record["name"], record["path"].read_text(encoding="utf-8")),
        encoding="utf-8")
    note = ("attribute labels corrected on import; see LABEL_CORRECTIONS and the README\n"
            if record["name"] in LABEL_CORRECTIONS else "")
    marker.write_text(
        f"{record['path'].relative_to(HERE.parent.parent.parent)}\n"
        f"imported by contexts/import_standard_contexts.py\n{note}", encoding="utf-8")
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
