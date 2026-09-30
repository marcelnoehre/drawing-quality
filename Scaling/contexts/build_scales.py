"""Build the scale-measures of a context and record what was built.

Every scale here is a context on the *same* objects as the original, whose
attributes are either original attributes kept as they are, which is an attribute
projection and a scale-measure by HH Cor. 22, or conjunctions of original
attributes, which are scale-measures by HH Cor. 17. Disjunction and negation are
never used: they are not guaranteed to give a scale-measure.

Scales are not one cumulative chain. They are independent views, each answering a
single question, plus refinement chains where the hierarchy is real and
appositions where the combined view is one somebody would ask for. Every scale is
nested under the full context by definition, so each still gives one usable
coarse-to-fine pair; the chains and appositions add more.

    python contexts/build_scales.py                 # build, measure, verify
    python contexts/build_scales.py --context instruments

Every scale is written into the folder of the context it is derived from, beside
that context, together with a manifest and the nesting matrix. The identity
scale-measure is the original context file itself, so it is not copied. The build
fails if any scale turns out not to be a scale-measure.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import numpy as np
import conceptflow as cf

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_scale import check_scale_measure, extents_of, nesting_rows, write_matrix  # noqa: E402

HERE = Path(__file__).resolve().parent          # the contexts directory
ROOT = HERE.parent                              # the Scaling directory

CONJUNCTION = " ∧ "   # the symbol used in the attribute names of a scale

# A transition this shallow is worth noticing in the results rather than assuming
# it is informative.
LOW_RATIO = 1.5

# What the drawing pipeline can actually take. The floor is where every algorithm
# produces the same picture; a scale outside the band is kept for what it shows
# about the data but must not be fed to a layout algorithm.
#
# The ceiling is PROVISIONAL. It is not from the literature and not from the
# colleague's data: the real constraint is what the ten algorithms can draw in
# reasonable time, which has not been measured yet. 1000 admits (id, K) of the
# contexts we have without pretending to know where the limit falls. Replace it
# once the algorithms have been timed at roughly 50, 150, 300 and 600 concepts.
DRAWABLE_MIN = 12
DRAWABLE_MAX = 1000
MIN_WIDTH = 3

# Width and height are quadratic in the number of concepts, so above this they are
# left unmeasured rather than allowed to stall the build.
MEASURE_LIMIT = 2000


# ---------------------------------------------------------------------------
# Instruments: the groupings. Also written, in prose, into groupings.md.
# ---------------------------------------------------------------------------

FAMILY = ["Chordophone", "Aerophone", "Membranophone", "Idiophone"]

EXCITATION = ["Bowed", "Plucked", "Hammered strings", "Single reed", "Double reed",
              "Free reed", "Lip excited", "Edge or fipple blown", "Mouth blown",
              "Bellows or bag", "Struck with implement", "Struck with hands",
              "Shaken or clashed"]

MECHANISM = ["Frets", "Valves", "Slide", "Finger holes", "Keyboard", "Pedals"]

CAPABILITY = ["Definite pitch", "Fully chromatic", "Three or more simultaneous pitches",
              "Continuously variable pitch", "Sustaining"]

PRACTICE = ["Symphony orchestra", "Concert or marching band", "Jazz", "Rock and pop",
            "Transposing", "Played seated", "Marching or processional"]

MAKING = ["Wooden body", "Metal body", "Resonator", "Non European origin", "Post 1900",
          "Requires electricity", "Electrical sound"]

# The Hornbostel-Sachs branch structure: each family, split by how it is excited.
FAMILY_EXCITATION = [
    ("Chordophone", "Bowed"), ("Chordophone", "Plucked"), ("Chordophone", "Hammered strings"),
    ("Aerophone", "Single reed"), ("Aerophone", "Double reed"), ("Aerophone", "Free reed"),
    ("Aerophone", "Lip excited"), ("Aerophone", "Edge or fipple blown"),
    ("Aerophone", "Mouth blown"), ("Aerophone", "Bellows or bag"),
    ("Membranophone", "Struck with implement"), ("Membranophone", "Struck with hands"),
    ("Idiophone", "Struck with implement"), ("Idiophone", "Struck with hands"),
    ("Idiophone", "Shaken or clashed"),
]

# One level deeper: those branches split again by the mechanism they use.
FAMILY_EXCITATION_MECHANISM = [
    ("Chordophone", "Plucked", "Frets"), ("Chordophone", "Plucked", "Pedals"),
    ("Chordophone", "Hammered strings", "Keyboard"),
    ("Aerophone", "Lip excited", "Valves"), ("Aerophone", "Lip excited", "Slide"),
    ("Aerophone", "Edge or fipple blown", "Finger holes"),
    ("Aerophone", "Single reed", "Finger holes"), ("Aerophone", "Double reed", "Finger holes"),
    ("Aerophone", "Free reed", "Keyboard"),
    ("Idiophone", "Struck with implement", "Keyboard"),
    ("Idiophone", "Struck with implement", "Pedals"),
]

INSTRUMENT_SCALES = [
    dict(name="excitation", kind="facet", attributes=[(a,) for a in EXCITATION],
         description="How the sound is set going."),
    dict(name="capability", kind="facet", attributes=[(a,) for a in CAPABILITY],
         description="What the instrument can play."),
    dict(name="practice", kind="facet", attributes=[(a,) for a in PRACTICE],
         description="Where and how it is played, including posture and mobility."),
    dict(name="making", kind="facet", attributes=[(a,) for a in MAKING],
         description="What it is made of, where it came from, whether it needs power."),
    dict(name="family-excitation", kind="chain", chain="hornbostel-sachs", step=1,
         attributes=[(f,) for f in FAMILY] + FAMILY_EXCITATION,
         description="Each family split by how it is excited."),
    dict(name="family-excitation-mechanism", kind="chain", chain="hornbostel-sachs", step=2,
         attributes=[(f,) for f in FAMILY] + FAMILY_EXCITATION + FAMILY_EXCITATION_MECHANISM,
         description="Those branches split again by the pitch mechanism they use."),
    dict(name="playing-mechanism", kind="apposition",
         attributes=[(a,) for a in EXCITATION + MECHANISM],
         description="The mechanics of playing: how sound starts and how pitch is chosen."),
    dict(name="family-making", kind="apposition",
         attributes=[(a,) for a in FAMILY + MAKING],
         description="Which families are built from which materials, which is where the "
                     "woodwind and brass distinction actually lives."),
    dict(name="family-practice", kind="apposition",
         attributes=[(a,) for a in FAMILY + PRACTICE],
         description="Which families populate which ensembles."),
    dict(name="capability-practice-making", kind="apposition",
         attributes=[(a,) for a in CAPABILITY + PRACTICE + MAKING],
         description="The instrument as a musician meets it, setting aside how the sound "
                     "is produced: what it can play, where it is played and what it is "
                     "made of."),
    dict(name="instruments", kind="full", attributes=None,
         description="The data themselves, the identity scale-measure (id, K)."),
]


# ---------------------------------------------------------------------------
# Olympic disciplines: the groupings. Also written, in prose, into groupings.md.
# ---------------------------------------------------------------------------

STRUCTURE = ["Team events", "Individual events", "Head to head", "Judged", "Measured",
             "Physical contact"]
EQUIPMENT = ["Ball", "Handheld implement", "Net or goal", "Vehicle board or runner",
             "Helmet or head protection", "Animal"]
VENUE = ["Grass or turf", "Indoor venue", "Ice or snow", "Water", "Outdoor venue",
         "Fixed marked area"]
DEMANDS = ["Endurance", "Explosive power", "Aim", "Running", "Jumping", "Weight classes"]
FORMAT = ["Clock", "Fixed attempts", "Points accumulate", "Draw possible", "Turn taking"]
INSTITUTION = ["Olympic debut before 1950", "Professional circuit", "Major spectator sport",
               "School sport"]
ORIGINS = ["British or Irish origin", "American origin", "Asian origin",
           "Codified before 1900", "Women's event in the frame"]

# The standard sport typology: a result is settled by judging, by measurement or by
# accumulating points, and each of those splits by who contests it.
DECISION = ["Judged", "Measured", "Points accumulate"]
DECISION_STRUCTURE = [
    ("Judged", "Individual events"), ("Judged", "Team events"),
    ("Measured", "Individual events"), ("Measured", "Team events"),
    ("Measured", "Head to head"),
    ("Points accumulate", "Team events"), ("Points accumulate", "Individual events"),
    ("Points accumulate", "Head to head"), ("Head to head", "Physical contact"),
]
DECISION_STRUCTURE_FORMAT = [
    ("Judged", "Individual events", "Fixed attempts"),
    ("Measured", "Individual events", "Clock"),
    ("Measured", "Individual events", "Fixed attempts"),
    ("Points accumulate", "Team events", "Clock"),
    ("Points accumulate", "Team events", "Draw possible"),
    ("Points accumulate", "Individual events", "Turn taking"),
]

# The same equipment behaves differently depending on what it is used on.
EQUIPMENT_MEDIUM = [
    ("Vehicle board or runner", "Ice or snow"), ("Vehicle board or runner", "Water"),
    ("Vehicle board or runner", "Outdoor venue"), ("Ball", "Grass or turf"),
    ("Ball", "Indoor venue"), ("Handheld implement", "Ice or snow"),
    ("Handheld implement", "Water"), ("Handheld implement", "Indoor venue"),
    ("Animal", "Grass or turf"),
]

OLYMPIC_SCALES = [
    dict(name="structure", kind="facet", attributes=[(a,) for a in STRUCTURE],
         description="How the contest is organised and how a winner is settled."),
    dict(name="demands", kind="facet", attributes=[(a,) for a in DEMANDS],
         description="What the discipline asks of the body."),
    dict(name="equipment", kind="facet", chain="equipment-medium", step=1,
         attributes=[(a,) for a in EQUIPMENT],
         description="What is carried, ridden or played with. Also the root of the "
                     "equipment chain."),
    dict(name="venue", kind="facet", attributes=[(a,) for a in VENUE],
         description="Where it is contested and on what surface.",
         note="Ice or snow stands in for the winter programme, which is not an attribute"),
    dict(name="format", kind="facet", attributes=[(a,) for a in FORMAT],
         description="How play is bounded and scored."),
    dict(name="institution", kind="facet", attributes=[(a,) for a in INSTITUTION],
         description="Its standing: age, professionalism, audience, schools."),
    dict(name="origins", kind="facet", attributes=[(a,) for a in ORIGINS],
         description="Where the modern form was codified, and whether women contest it."),
    dict(name="decision-structure", kind="chain", chain="typology", step=1,
         attributes=[(d,) for d in DECISION] + DECISION_STRUCTURE,
         description="How the result is settled, each way split by who contests it."),
    dict(name="decision-structure-format", kind="chain", chain="typology", step=2,
         attributes=[(d,) for d in DECISION] + DECISION_STRUCTURE + DECISION_STRUCTURE_FORMAT,
         description="Those branches split again by how play is bounded."),
    dict(name="equipment-medium", kind="chain", chain="equipment-medium", step=2,
         attributes=[(a,) for a in EQUIPMENT] + EQUIPMENT_MEDIUM,
         description="Equipment split by the medium it is used in: a runner on ice, a "
                     "boat on water and a ball on grass are different sports."),
    dict(name="structure-format", kind="apposition",
         attributes=[(a,) for a in STRUCTURE + FORMAT],
         description="The rules of the contest: how it is run and how it is decided."),
    dict(name="institution-origins", kind="apposition",
         attributes=[(a,) for a in INSTITUTION + ORIGINS],
         description="Where the discipline came from and what standing it now has."),
    dict(name="venue-equipment", kind="apposition",
         attributes=[(a,) for a in VENUE + EQUIPMENT],
         description="What the ground you play on requires you to carry or ride."),
    dict(name="venue-equipment-demands", kind="apposition",
         attributes=[(a,) for a in VENUE + EQUIPMENT + DEMANDS],
         description="The physical side of competing: the surface underfoot, the gear in "
                     "hand and the effort required."),
    dict(name="olympics", kind="full", attributes=None,
         description="The data themselves, the identity scale-measure (id, K).",
         note="motivation only, far outside the drawable band; never feed it to a layout run"),
]

CATALOGUE = {"instruments": INSTRUMENT_SCALES, "olympics": OLYMPIC_SCALES}


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

def build_scale(original: cf.FormalContext, attributes) -> cf.FormalContext:
    """A context on the same objects whose attributes are the given conjunctions."""
    if attributes is None:
        return original

    index = {name: i for i, name in enumerate(original.attributes)}
    columns, names = [], []
    for conjuncts in attributes:
        missing = [c for c in conjuncts if c not in index]
        if missing:
            raise KeyError(f"no such attribute in the original context: {missing}")
        column = np.ones(original.n_objects, dtype=bool)
        for conjunct in conjuncts:
            column &= original.incidence[:, index[conjunct]]
        columns.append(column)
        names.append(CONJUNCTION.join(conjuncts))

    if len(set(names)) != len(names):
        raise ValueError("two scale attributes ended up with the same name")
    return cf.FormalContext(objects=tuple(original.objects),
                            attributes=tuple(names),
                            incidence=np.column_stack(columns))


def width(exts: list[frozenset[int]]) -> int:
    """Largest antichain. By Dilworth that is the size minus a maximum matching of
    the strict inclusion order, taken over all comparable pairs, not just covers."""
    items = sorted(exts, key=len)
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

    matching = sum(1 for u in range(n) if augment(u, [False] * n))
    return n - matching


def height(exts: list[frozenset[int]]) -> int:
    """Number of elements of a longest chain."""
    items = sorted(exts, key=len)
    longest: dict[frozenset[int], int] = {}
    for position, a in enumerate(items):
        longest[a] = max((longest[b] + 1 for b in items[:position] if b < a), default=1)
    return max(longest.values()) if longest else 0


def incomparable_pairs(exts: list[frozenset[int]]) -> int:
    """Pairs of concepts neither of which contains the other.

    Recorded for every scale because it is what drives the cost of a two-dimension
    extension: DimDraw's work is orienting incomparable pairs, and its completion
    tracks this far better than it tracks the number of concepts. It is also a
    quadratic stand-in for order dimension, which is NP-hard, if dimension turns
    out to be infeasible at our sizes.
    """
    total = 0
    for i, a in enumerate(exts):
        for b in exts[i + 1:]:
            if not (a <= b or b <= a):
                total += 1
    return total


def measure(scale: cf.FormalContext) -> dict:
    exts = list(extents_of(scale))
    if len(exts) > MEASURE_LIMIT:
        # Quadratic quantities are left unmeasured rather than allowed to stall
        # the build; a scale this large is outside the drawable band anyway.
        return {"concepts": len(exts), "width": None, "height": None,
                "incomparable_pairs": None}
    return {"concepts": len(exts), "width": width(exts), "height": height(exts),
            "incomparable_pairs": incomparable_pairs(exts)}


def is_drawable(stats: dict) -> bool:
    """Whether the drawing pipeline should be given this scale at all."""
    if not DRAWABLE_MIN <= stats["concepts"] <= DRAWABLE_MAX:
        return False
    return stats["width"] is None or stats["width"] >= MIN_WIDTH


# ---------------------------------------------------------------------------

def build_context(name: str, quiet: bool = False) -> int:
    target = HERE / name
    original_path = target / f"{name}.cxt"
    original = cf.io.read_cxt(original_path)

    built: dict[str, cf.FormalContext] = {}
    rows = []
    failures = 0

    for spec in CATALOGUE[name]:
        scale = build_scale(original, spec["attributes"])
        problems = check_scale_measure(original, scale)
        if problems:
            failures += 1
            print(f"FAIL {spec['name']}: not a scale-measure", file=sys.stderr)
            for problem in problems:
                print(f"     {problem}", file=sys.stderr)
            continue

        path = original_path if spec["kind"] == "full" else target / f"{spec['name']}.cxt"
        if spec["kind"] != "full":
            cf.io.write_cxt(scale, path)
        built[spec["name"]] = scale
        stats = measure(scale)
        drawable = is_drawable(stats)
        rows.append({
            "context": name,
            "scale": spec["name"],
            "filename": path.relative_to(ROOT).as_posix(),
            "kind": spec["kind"],
            "chain": spec.get("chain", ""),
            "chain_step": spec.get("step", ""),
            "attributes": len(scale.attributes),
            "concepts": stats["concepts"],
            "width": "" if stats["width"] is None else stats["width"],
            "height": "" if stats["height"] is None else stats["height"],
            "incomparable_pairs": ("" if stats["incomparable_pairs"] is None
                                   else stats["incomparable_pairs"]),
            "drawable": drawable,
            "description": spec["description"],
            "note": spec.get("note", ""),
        })

    if failures:
        return 1

    # Flag shallow transitions inside a chain so they are visible in the results.
    by_name = {r["scale"]: r for r in rows}
    for spec in CATALOGUE[name]:
        if spec["kind"] != "chain" or spec.get("step", 0) < 2:
            continue
        previous = next(s for s in CATALOGUE[name]
                        if s.get("chain") == spec["chain"] and s.get("step") == spec["step"] - 1)
        ratio = by_name[spec["name"]]["concepts"] / by_name[previous["name"]]["concepts"]
        if ratio < LOW_RATIO:
            by_name[spec["name"]]["note"] = (
                f"low-ratio transition from {previous['name']}: "
                f"{by_name[previous['name']]['concepts']} to "
                f"{by_name[spec['name']]['concepts']} concepts, ratio {ratio:.2f}")

    manifest = target / "manifest.csv"
    with manifest.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    matrix = target / "nesting.csv"
    drawable = {r["scale"]: r["drawable"] for r in rows}
    write_matrix(nesting_rows(built, drawable), matrix)

    if not quiet:
        print(f"{name}: {len(rows)} scales -> {target.relative_to(ROOT)}\n")
        print(f"{'scale':32s}{'kind':12s}{'attrs':>6s}{'concepts':>10s}{'width':>7s}"
              f"{'height':>7s}{'incomp':>9s}  drawable")
        for row in rows:
            print(f"{row['scale']:32s}{row['kind']:12s}{row['attributes']:6d}"
                  f"{row['concepts']:10d}{str(row['width']):>7s}{str(row['height']):>7s}"
                  f"{str(row['incomparable_pairs']):>9s}  {'yes' if row['drawable'] else 'NO '}"
                  + ("   " + row["note"] if row["note"] else ""))
        pairs = [r for r in csv.DictReader(matrix.open(encoding="utf-8")) if r["nested"] == "True"]
        print(f"\nevery scale verified as a scale-measure; {len(pairs)} nested pairs "
              f"recorded in {matrix.relative_to(ROOT)}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--context", default="instruments", choices=sorted(CATALOGUE))
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()
    return build_context(args.context, args.quiet)


if __name__ == "__main__":
    raise SystemExit(main())
