"""Read a drawing back as {extent: (x, y)}, with the node identification checked.

The generators write `<node id="0">` and nothing else, so a drawing on its own does
not say which concept a node is. `node_extents.py` records that while the drawing
is being written, from the generator's own data, and saves it beside the drawing
as `<name>.extents.json`. This module reads that table and never rebuilds the
numbering, which would depend on reproducing each generator's internal order.

A recorded table can still be wrong -- a stale file from another context, or a
generator whose internals changed -- and a wrong table produces plausible
coordinates and plausible correlations with no error anywhere. So every load
checks it, and any failure raises rather than returns:

  0. the drawing was made from exactly this .cxt (its sha256 is recorded);
  1. the ids in the table are exactly the node ids in the drawing;
  2. its extents are exactly the extents of the lattice of the given .cxt;
  3. every drawn edge joins a concept to one of its lower covers.

The third check catches most tables that name the right concepts but the wrong
nodes, since a swap usually breaks an edge. **It cannot catch a swap of two
concepts with the same upper and the same lower covers** -- the two middle
elements of a diamond -- because the drawing's edges are then the same either way.
21 such pairs exist, all in four instruments scales. The table is read from the
generator's own objects rather than inferred, so there is no known way for it to
swap them; the limit is in what can be checked afterwards, and it is stated here
and in pipeline.md rather than assumed away.

    from graphml_loader import load_drawing
    positions = load_drawing(cxt_path, graphml_path)   # {frozenset: (x, y)}
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from xml.etree.ElementTree import parse as parse_xml

import odis

from node_extents import sidecar, source_hash

GRAPHML_NS = "{http://graphml.graphdrawing.org/xmlns}"


class NodeIdentificationError(RuntimeError):
    """The recorded id -> extent table does not fit this drawing or this lattice."""


@lru_cache(maxsize=128)
def lattice_extents(cxt_path: str) -> frozenset[frozenset[str]]:
    """Every extent of the lattice of a .cxt."""
    context = odis.FormalContext.from_file(cxt_path)
    return frozenset(frozenset(c.extent.to_frozenset()) for c in context.concepts())


def read_positions(graphml_path: Path) -> dict[str, tuple[float, float]]:
    """Node id -> (x, y), exactly as written."""
    graph = parse_xml(graphml_path).getroot().find(f"{GRAPHML_NS}graph")
    positions = {}
    for node in graph.findall(f"{GRAPHML_NS}node"):
        values = {d.get("key"): d.text for d in node.findall(f"{GRAPHML_NS}data")}
        positions[node.get("id")] = (float(values["x"]), float(values["y"]))
    return positions


def read_edges(graphml_path: Path) -> list[tuple[str, str]]:
    graph = parse_xml(graphml_path).getroot().find(f"{GRAPHML_NS}graph")
    return [(e.get("source"), e.get("target")) for e in graph.findall(f"{GRAPHML_NS}edge")]


def read_sidecar(graphml_path: Path) -> dict:
    path = sidecar(Path(graphml_path))
    if not path.exists():
        raise NodeIdentificationError(
            f"{Path(graphml_path).name}: no {path.name} beside it, so which concept each "
            f"node is was never recorded. Redraw it through run_harness.py.")
    return json.loads(path.read_text(encoding="utf-8"))


def read_extents(graphml_path: Path) -> dict[str, frozenset[str]]:
    """The recorded id -> extent table of a drawing."""
    table = read_sidecar(graphml_path)["extents"]
    return {node_id: frozenset(extent) for node_id, extent in table.items()}


def check_source(cxt_path: Path, graphml_path: Path) -> None:
    """Raise unless the drawing was made from exactly this .cxt."""
    recorded = read_sidecar(graphml_path).get("source_sha256")
    if recorded != source_hash(cxt_path):
        raise NodeIdentificationError(
            f"{Path(graphml_path).name}: drawn from "
            f"{'an unrecorded file' if recorded is None else 'a different version of'} "
            f"{Path(cxt_path).name}; redraw it through run_harness.py")


def check_identification(cxt_path: Path, graphml_path: Path,
                         table: dict[str, frozenset[str]]) -> None:
    """Raise unless the table fits both the drawing and the lattice."""
    name = Path(graphml_path).name
    positions = read_positions(graphml_path)
    if set(table) != set(positions):
        raise NodeIdentificationError(
            f"{name}: the recorded table has {len(table)} ids, the drawing "
            f"{len(positions)}, and they are not the same ids")

    extents = lattice_extents(str(cxt_path))
    recorded = set(table.values())
    if len(recorded) != len(table) or recorded != extents:
        raise NodeIdentificationError(
            f"{name}: the recorded extents are not the {len(extents)} extents of "
            f"{Path(cxt_path).name}; the table belongs to a different context")

    # Every edge must join a concept to a lower cover: strictly below it, with
    # nothing in between. Checked per edge, which stays cheap at 576 concepts.
    for source, target in read_edges(graphml_path):
        a, b = table[source], table[target]
        upper, lower = (a, b) if b < a else (b, a)
        if not lower < upper or any(lower < c < upper for c in extents):
            raise NodeIdentificationError(
                f"{name}: edge {source}-{target} does not join a concept to a lower "
                f"cover under the recorded table, so the table names the wrong nodes")


def load_drawing(cxt_path: Path, graphml_path: Path,
                 algorithm: str | None = None) -> dict[frozenset[str], tuple[float, float]]:
    """One drawing as {extent: (x, y)}, keyed so two scales can be compared.

    `algorithm` is accepted for compatibility with older callers and ignored: the
    recorded table makes the identification the same for every algorithm.
    """
    check_source(cxt_path, graphml_path)
    table = read_extents(graphml_path)
    check_identification(cxt_path, graphml_path, table)
    positions = read_positions(graphml_path)
    return {table[node_id]: position for node_id, position in positions.items()}
