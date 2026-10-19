"""Record which concept each node is, at the moment a drawing is written.

A generator writes `<node id="7">` with an x and a y and nothing else, so a drawing
does not say which concept node 7 is. Rebuilding the numbering afterwards, from the
.cxt alone, would mean re-deriving the order each generator numbers its concepts
in, and that fails silently whenever the re-derivation differs: redraw, for
instance, sorts its own (extent, intent) tuples, whose object order comes from
conexp, so an alphabetical rebuild agrees with it on small lattices and not on
larger ones.

So nothing is rebuilt. While the generator runs, its `write_graphml` is
wrapped in memory, never edited on disk, and the object it is handed is asked
directly which extent each id stands for. That table is written beside the drawing
as `<name>.extents.json`, and `graphml_loader` reads it and checks it against the
lattice on every load.

    from node_extents import load_generator, recording
    module = load_generator("freese")
    with recording(module, "freese"):
        module.generate(dataset, cxt_path)
"""
from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent            # the Scaling directory
REPO_ROOT = HERE.parent                            # the drawing-quality repository

# Keyed by how the extent has to be pulled out of the object each generator hands
# to its write_graphml.
ODIS_WRAPPER = ("aeschlimann_schmid", "cole_ducrou_eklund", "fdp", "freese")
ODIS_DRAWING = ("dimdraw", "sugiyama")
ALGORITHMS = ODIS_WRAPPER + ODIS_DRAWING + ("redraw", "dimflux")


class RecordingFault(RuntimeError):
    """Recording which concept each node is failed: a fault in our code, not the
    algorithm's. The harness turns it into a stop, never into an `error` row."""


def load_generator(algorithm: str):
    """Import an algorithm's generate.py under its own name, without editing it."""
    path = REPO_ROOT / "line_diagrams" / algorithm / "generate.py"
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location(f"generate_{algorithm}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sidecar(graphml_path: Path) -> Path:
    """Where the id -> extent table of a drawing lives."""
    return graphml_path.with_name(graphml_path.stem + ".extents.json")


def source_hash(cxt_path: Path) -> str:
    """sha256 of the exact .cxt a drawing is made from.

    Recorded beside every drawing and compared before one is reused or read. The
    lattice alone cannot tell a stale drawing from a current one: reordering a
    scale's columns leaves its lattice unchanged and changes most drawings.
    """
    return hashlib.sha256(Path(cxt_path).read_bytes()).hexdigest()


def extents_from_payload(algorithm: str, payload, recorded_vars=None) -> dict[str, list[str]]:
    """The id -> extent table, read from the object the generator is about to write."""
    if algorithm in ODIS_WRAPPER:
        # generate.py writes id=str(concept) while iterating payload.concepts,
        # and payload.concepts is range(len(payload._extents)).
        return {str(c): sorted(payload._extents[c]) for c in payload.concepts}

    if algorithm in ODIS_DRAWING:
        # generate.py writes id=str(node.index), and the node carries its concept.
        return {str(n.index): sorted(n.concept.extent.to_frozenset()) for n in payload.nodes}

    if algorithm == "redraw":
        # Nodes are redraw's own (extent, intent) tuples, numbered after sorting by
        # extent size, then extent, then intent -- the tuples as redraw holds them,
        # which is the whole point: their object order is conexp's, not ours.
        nodes = sorted(payload.G.nodes, key=lambda n: (len(n[0]), n[0], n[1]))
        return {str(i): sorted(n[0]) for i, n in enumerate(nodes)}

    if algorithm == "dimflux":
        # The wrapper writes id=str(concept) for concept in vars.concepts and then
        # discards vars, so it is captured while the wrapper runs. dim-flux keeps
        # the whole context (from 1.0.10): full_extents are over the original
        # objects with their original names.
        if recorded_vars is None:
            raise RuntimeError("dimflux: the Variables object was not captured")
        return {str(c): sorted(recorded_vars.full_extents[c]) for c in payload.concepts}

    raise KeyError(algorithm)


@contextlib.contextmanager
def recording(module, algorithm: str, source: Path | None = None):
    """While active, every drawing the generator writes gets its extents.json.

    `source`, the .cxt being drawn, is hashed into the table so that a drawing can
    later be matched to the exact file it was made from.
    """
    digest = source_hash(source) if source is not None else None
    original_write = module.write_graphml
    captured: dict = {}

    restore_variables = None
    if algorithm == "dimflux":
        wrapper = sys.modules["dimflux"]
        Real = wrapper.Variables

        class Recording(Real):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                captured["vars"] = self

        wrapper.Variables = Recording
        restore_variables = (wrapper, Real)

    def write_and_record(payload, path):
        original_write(payload, path)
        try:
            table = extents_from_payload(algorithm, payload, captured.get("vars"))
        except Exception as exc:
            raise RecordingFault(f"{algorithm}: could not read the extents of the "
                                 f"drawing it wrote ({type(exc).__name__}: {exc})") from exc
        sidecar(Path(path)).write_text(
            json.dumps({"algorithm": algorithm, "source_sha256": digest, "extents": table},
                       ensure_ascii=False,
                       sort_keys=True, indent=0),
            encoding="utf-8")

    module.write_graphml = write_and_record
    try:
        yield
    finally:
        module.write_graphml = original_write
        if restore_variables:
            restore_variables[0].Variables = restore_variables[1]
