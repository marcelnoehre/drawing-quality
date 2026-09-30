"""Can a graphml node id be mapped back to the concept it draws?

RQ4 compares where an algorithm places *the same concept* in two different
scales, so every node has to be identified by its extent. The generators in the
surrounding repository write only `<node id="0">` with an x and a y: no extent, no
label. The question this script answers is whether the id can nevertheless be
recovered on our side, by recomputing the concept list the way the generator did,
or whether the generators have to be patched to write the extent themselves.

Three things are checked per algorithm.

*Ground truth.* The generator is imported and its ``write_graphml`` is replaced,
in memory only, by a version that records which extent each node id stood for at
the moment of writing. Nothing in the repository is edited.

*Reconstruction.* The same mapping is computed independently from the .cxt file,
using the ordering the generator relies on, and compared elementwise as sets of
object names. "Looks similar" is not a result; only exact equality counts.

*Stability.* The capture is repeated in fresh processes under PYTHONHASHSEED 0, 1
and random. An ordering that comes out of set or dict iteration can be stable
within a run and differ between runs, which would give a mapping that looks right
and is wrong with no error raised. Only an ordering that survives this is safe to
reconstruct.

    python check_node_mapping.py                          # all algorithms
    python check_node_mapping.py --algorithm fdp --context contexts/instruments/capability.cxt
    python check_node_mapping.py --capture fdp --context ... --out mapping.json   # one process

dimflux is skipped: the dim-flux package clarifies and relabels the objects, so
its extents are not expressed over our object set at all. That is being fixed
upstream.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent            # the Scaling directory
REPO_ROOT = HERE.parent                            # the drawing-quality repository
GRAPHML_ROOT = HERE / "graphml"                    # our graphml, kept out of his tree
DRAWINGS_ROOT = HERE / "drawings"

# The generators keyed by how the extent has to be pulled out of the object they
# hand to write_graphml.
ODIS_WRAPPER = ("aeschlimann_schmid", "cole_ducrou_eklund", "fdp", "freese")
ODIS_DRAWING = ("dimdraw", "sugiyama")
ALGORITHMS = ODIS_WRAPPER + ODIS_DRAWING + ("redraw",)

# dim-flux reduces and renames the objects, so its extents cannot be compared
# with ours until the upstream mapping lands.
EXCLUDED = ("dimflux",)

DEFAULT_CONTEXT = HERE / "contexts" / "instruments" / "capability.cxt"


def load_generator(algorithm: str):
    """Import an algorithm's generate.py under its own name, without editing it."""
    path = REPO_ROOT / "line_diagrams" / algorithm / "generate.py"
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location(f"generate_{algorithm}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def extents_from_payload(algorithm: str, payload) -> dict[str, frozenset[str]]:
    """The id -> extent mapping the generator itself would have written."""
    if algorithm in ODIS_WRAPPER:
        # generate.py writes id=str(concept) while iterating payload.concepts,
        # and payload.concepts is range(len(payload._extents)).
        extents = payload._extents
        return {str(c): frozenset(extents[c]) for c in payload.concepts}

    if algorithm in ODIS_DRAWING:
        # generate.py writes id=str(node.index) and the node carries its concept.
        return {str(node.index): frozenset(node.concept.extent.to_frozenset())
                for node in payload.nodes}

    if algorithm == "redraw":
        # nodes are (extent, intent) tuples; generate.py numbers them after
        # sorting by extent size, then extent, then intent.
        nodes = sorted(payload.G.nodes, key=lambda n: (len(n[0]), n[0], n[1]))
        return {str(i): frozenset(node[0]) for i, node in enumerate(nodes)}

    raise KeyError(algorithm)


def capture(algorithm: str, cxt_path: Path) -> dict[str, list[str]]:
    """Run the generator, recording what each node id stood for as it was written."""
    module = load_generator(algorithm)
    module.GRAPHML_ROOT = GRAPHML_ROOT / algorithm
    module.DRAWINGS_ROOT = DRAWINGS_ROOT / algorithm

    recorded: dict[str, frozenset[str]] = {}
    original = module.write_graphml

    def recording_write_graphml(payload, path):
        recorded.update(extents_from_payload(algorithm, payload))
        return original(payload, path)

    module.write_graphml = recording_write_graphml
    # A fresh file every time, so the generator never takes its skip path.
    target = module.GRAPHML_ROOT / "check" / f"{module.slug(cxt_path.stem)}.graphml"
    target.unlink(missing_ok=True)
    module.generate("check", cxt_path.resolve())
    return {node_id: sorted(extent) for node_id, extent in recorded.items()}


def reconstruct(algorithm: str, cxt_path: Path) -> dict[str, list[str]]:
    """Rebuild the same mapping from the .cxt alone, the way the generator orders it."""
    if algorithm in ODIS_WRAPPER + ODIS_DRAWING:
        import odis
        context = odis.FormalContext.from_file(str(cxt_path))
        concepts = list(context.concepts())
        return {str(i): sorted(c.extent.to_frozenset()) for i, c in enumerate(concepts)}

    if algorithm == "redraw":
        sys.path.insert(0, str(Path(os.environ.get(
            "REDRAW_ROOT", REPO_ROOT.parent / "redraw"))))
        import util as redraw_util
        graph = redraw_util.compute_lattice(str(cxt_path))
        nodes = sorted(graph.nodes, key=lambda n: (len(n[0]), n[0], n[1]))
        return {str(i): sorted(node[0]) for i, node in enumerate(nodes)}

    raise KeyError(algorithm)


def capture_in_subprocess(algorithm: str, cxt_path: Path, hash_seed: str) -> dict:
    """Capture again in a fresh interpreter, with PYTHONHASHSEED set."""
    out = HERE / ".mapping-check.json"
    env = dict(os.environ, PYTHONHASHSEED=hash_seed)
    subprocess.run([sys.executable, str(Path(__file__).resolve()),
                    "--capture", algorithm, "--context", str(cxt_path), "--out", str(out)],
                   check=True, env=env, capture_output=True)
    mapping = json.loads(out.read_text())
    out.unlink(missing_ok=True)
    return mapping


def check(algorithm: str, cxt_path: Path, seed_test: bool = True) -> dict:
    truth = capture(algorithm, cxt_path)
    rebuilt = reconstruct(algorithm, cxt_path)

    same_keys = set(truth) == set(rebuilt)
    mismatches = [k for k in truth if same_keys and truth[k] != rebuilt.get(k)]
    reconstruction_ok = same_keys and not mismatches

    # The seed test costs three more runs of the generator, which is unaffordable
    # on a large lattice. What it establishes is a property of the *ordering*, not
    # of the size: an order that comes from set or dict iteration is hash-dependent
    # whatever the lattice. Having established it at three sizes, it can be skipped
    # when the point of the run is to confirm the mapping at scale.
    if seed_test:
        seeds = {seed: capture_in_subprocess(algorithm, cxt_path, seed)
                 for seed in ("0", "1", "random")}
        stable = all(m == truth for m in seeds.values())
    else:
        stable = None

    return {
        "algorithm": algorithm,
        "nodes": len(truth),
        "reconstruction": reconstruction_ok,
        "mismatches": len(mismatches),
        "hash_stable": stable,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--algorithm", choices=ALGORITHMS)
    parser.add_argument("--context", type=Path, default=DEFAULT_CONTEXT)
    parser.add_argument("--capture", choices=ALGORITHMS,
                        help="internal: capture once and write JSON, used for the seed test")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--no-seed-test", action="store_true",
                        help="skip the three extra runs; use on large lattices")
    args = parser.parse_args()

    if args.capture:
        mapping = capture(args.capture, args.context)
        args.out.write_text(json.dumps(mapping, sort_keys=True))
        return 0

    algorithms = [args.algorithm] if args.algorithm else list(ALGORITHMS)
    rows = []
    for algorithm in algorithms:
        try:
            rows.append(check(algorithm, args.context, seed_test=not args.no_seed_test))
        except Exception as exc:
            rows.append({"algorithm": algorithm, "nodes": 0, "reconstruction": False,
                         "mismatches": -1, "hash_stable": False, "error": repr(exc)[:120]})

    print(f"\ncontext: {args.context}")
    print(f"{'algorithm':22s}{'nodes':>7s}{'reconstructs':>14s}{'mismatches':>12s}"
          f"{'hash-stable':>13s}")
    for r in rows:
        print(f"{r['algorithm']:22s}{r['nodes']:7d}{str(r['reconstruction']):>14s}"
              f"{r['mismatches']:12d}{str(r['hash_stable']) if r['hash_stable'] is not None else 'not run':>13s}"
              + ("   " + r["error"] if r.get("error") else ""))
    return 0 if all(r["reconstruction"] and r["hash_stable"] is not False
                    for r in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
