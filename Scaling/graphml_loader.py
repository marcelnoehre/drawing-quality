"""Read a drawing back as {extent: (x, y)}, with the node identification checked.

The generators write `<node id="0">` and nothing else, so a drawing on its own
does not say which concept a node is. The id is an index into the concept list the
generator used, and that list is reproducible: six of the seven algorithms number
concepts in the order `odis` enumerates them, which is the lectic order, and
`redraw` sorts its nodes explicitly before numbering. `check_node_mapping.py`
verifies both claims against the generators themselves.

Reproducible is not the same as safe, though. If anything in the stack ever
changed the enumeration, every mapping here would still produce plausible
coordinates and plausible correlations, with no error anywhere. That is the one
silent failure mode in this pipeline, so this module refuses to guess: the extent
sequence taken from `odis` is checked against an independent enumeration before it
is used, and a mismatch raises rather than returns.

    from graphml_loader import load_drawing
    positions = load_drawing(cxt_path, graphml_path, 'fdp')   # {frozenset: (x, y)}
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from xml.etree.ElementTree import parse as parse_xml

import conceptflow as cf
import odis

GRAPHML_NS = "{http://graphml.graphdrawing.org/xmlns}"

# Numbered by position in the odis enumeration.
LECTIC_ALGORITHMS = ("aeschlimann_schmid", "cole_ducrou_eklund", "fdp", "freese",
                     "dimdraw", "sugiyama")
# Numbered after an explicit sort, so independent of any enumeration order.
SORTED_ALGORITHMS = ("redraw",)
SUPPORTED = LECTIC_ALGORITHMS + SORTED_ALGORITHMS


class EnumerationOrderError(RuntimeError):
    """The concept order is not the one the node ids were written against."""


@lru_cache(maxsize=64)
def extent_sequence(cxt_path: str) -> tuple[frozenset[str], ...]:
    """The concept extents in the order the generators number them.

    Taken from odis, then checked against ConceptFlow's NextClosure. The two are
    independent implementations; if they ever disagree the node ids in every
    drawing of this context mean something other than what we think, so this
    raises instead of returning a plausible answer.
    """
    context = odis.FormalContext.from_file(cxt_path)
    from_odis = tuple(frozenset(c.extent.to_frozenset()) for c in context.concepts())

    checked = cf.io.read_cxt(cxt_path)
    names = list(checked.objects)
    independent = tuple(frozenset(names[i] for i in concept.extent)
                        for concept in cf.algorithms.enumerate_concepts(checked, "nextclosure"))

    if from_odis != independent:
        where = next((i for i, (a, b) in enumerate(zip(from_odis, independent)) if a != b),
                     min(len(from_odis), len(independent)))
        raise EnumerationOrderError(
            f"{Path(cxt_path).name}: the odis concept order no longer matches an "
            f"independent NextClosure enumeration, first difference at position {where} "
            f"({len(from_odis)} vs {len(independent)} concepts). Node ids in existing "
            f"drawings of this context cannot be trusted; rerun check_node_mapping.py.")
    return from_odis


@lru_cache(maxsize=64)
def sorted_extent_sequence(cxt_path: str) -> tuple[frozenset[str], ...]:
    """The order redraw numbers its nodes in: extent size, then extent, then intent."""
    context = odis.FormalContext.from_file(cxt_path)
    concepts = [(tuple(sorted(c.extent.to_frozenset())), tuple(sorted(c.intent.to_frozenset())))
                for c in context.concepts()]
    concepts.sort(key=lambda c: (len(c[0]), c[0], c[1]))
    return tuple(frozenset(extent) for extent, _ in concepts)


def read_positions(graphml_path: Path) -> dict[str, tuple[float, float]]:
    """Node id -> (x, y), exactly as written."""
    graph = parse_xml(graphml_path).getroot().find(f"{GRAPHML_NS}graph")
    positions = {}
    for node in graph.findall(f"{GRAPHML_NS}node"):
        values = {d.get("key"): d.text for d in node.findall(f"{GRAPHML_NS}data")}
        positions[node.get("id")] = (float(values["x"]), float(values["y"]))
    return positions


def load_drawing(cxt_path: Path, graphml_path: Path,
                 algorithm: str) -> dict[frozenset[str], tuple[float, float]]:
    """One drawing as {extent: (x, y)}, keyed so two scales can be compared."""
    if algorithm not in SUPPORTED:
        raise KeyError(f"{algorithm}: no node identification is known for this algorithm")

    sequence = (sorted_extent_sequence(str(cxt_path)) if algorithm in SORTED_ALGORITHMS
                else extent_sequence(str(cxt_path)))
    positions = read_positions(graphml_path)

    if len(positions) != len(sequence):
        raise EnumerationOrderError(
            f"{graphml_path.name}: {len(positions)} nodes drawn but {len(sequence)} "
            f"concepts in {Path(cxt_path).name}; the drawing is of a different context")

    drawing = {}
    for node_id, position in positions.items():
        index = int(node_id)
        if not 0 <= index < len(sequence):
            raise EnumerationOrderError(
                f"{graphml_path.name}: node id {node_id} is outside the concept list")
        drawing[sequence[index]] = position

    if len(drawing) != len(positions):
        raise EnumerationOrderError(
            f"{graphml_path.name}: two nodes mapped to the same extent, so the "
            f"identification is wrong")
    return drawing
