"""Checks that protect the comparisons from stale or misread inputs.

    python tests/test_integrity.py      # standalone
    pytest tests/test_integrity.py      # or under pytest
"""
from __future__ import annotations

import atexit
import json
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from consistency import compare, stratum_summary  # noqa: E402
from graphml_loader import NodeIdentificationError, check_source  # noqa: E402
from node_extents import RecordingFault, recording, sidecar, source_hash  # noqa: E402
from nulls import permutation_null, self_test as null_self_test  # noqa: E402


def drawn_from(text: str, recorded: str | None):
    """A .cxt with this content and a drawing whose table records `recorded`."""
    folder = Path(tempfile.mkdtemp(prefix="scaling-test-"))
    atexit.register(shutil.rmtree, folder, ignore_errors=True)
    cxt, graphml = folder / "s.cxt", folder / "s.graphml"
    cxt.write_text(text, encoding="utf-8")
    graphml.write_text("<graphml/>", encoding="utf-8")
    sidecar(graphml).write_text(json.dumps({"source_sha256": recorded, "extents": {}}))
    return cxt, graphml


def test_a_drawing_of_the_current_file_is_accepted():
    cxt, graphml = drawn_from("B\n\n1\n1\n\ng\nm\nX\n", None)
    sidecar(graphml).write_text(json.dumps({"source_sha256": source_hash(cxt), "extents": {}}))
    check_source(cxt, graphml)


def test_a_drawing_of_an_older_version_is_refused():
    # Same lattice, columns in another order: the lattice cannot tell them apart.
    old = "B\n\n1\n2\n\ng\nm\nn\nXX\n"
    cxt, graphml = drawn_from("B\n\n1\n2\n\ng\nn\nm\nXX\n", None)
    sidecar(graphml).write_text(json.dumps({"source_sha256": __import__("hashlib").sha256(
        old.encode()).hexdigest(), "extents": {}}))
    try:
        check_source(cxt, graphml)
    except NodeIdentificationError:
        return
    raise AssertionError("a drawing of another version of the file was accepted")


def test_a_drawing_without_a_recorded_source_is_refused():
    cxt, graphml = drawn_from("B\n\n1\n1\n\ng\nm\nX\n", None)
    try:
        check_source(cxt, graphml)
    except NodeIdentificationError:
        return
    raise AssertionError("a drawing with no recorded source was accepted")


def test_tau_abs_is_the_same_for_a_drawing_and_its_mirror():
    base = {frozenset("a"): (0.0, 0.0), frozenset("ab"): (1.0, 1.0), frozenset("b"): (2.0, 0.0),
            frozenset("c"): (3.0, 0.0), frozenset("abc"): (1.5, 2.0)}
    mirrored = {e: (-x, y) for e, (x, y) in base.items()}
    assert compare(base, mirrored)["tau_x"] == -1.0
    assert compare(base, mirrored)["tau_abs"] == compare(base, base)["tau_abs"] == 1.0


def test_strata_of_two_do_not_make_a_scramble_look_decisive():
    # Two strata of two, both reversed, and one stratum of four, scrambled.
    rows = [{"stratum": 1, "n": 2, "tau": -1.0}, {"stratum": 2, "n": 2, "tau": -1.0},
            {"stratum": 3, "n": 4, "tau": 0.0}]
    summary = stratum_summary(rows)
    assert summary["strata_decisiveness"] == 0.0, summary


def test_the_null_fixtures_pass():
    assert null_self_test() == 0


def test_a_drawing_with_every_shared_concept_at_one_x_keeps_no_order():
    base = {frozenset("a"): (0.0, 0.0), frozenset("b"): (1.0, 0.0), frozenset("c"): (2.0, 0.0),
            frozenset("abc"): (1.0, 1.0)}
    flat = {e: (5.0, y) for e, (x, y) in base.items()}
    result = compare(base, flat)
    assert result["tau_x"] == 0.0 and result["tau_abs"] == 0.0 and result["tau_undefined"]
    assert compare(base, base)["tau_undefined"] is False
    assert permutation_null(base, flat)["n_permutations"] == 0


def test_a_stratum_with_no_order_is_left_out_of_the_summary():
    rows = [{"stratum": 1, "n": 3, "tau": float("nan")}, {"stratum": 2, "n": 3, "tau": 0.5}]
    summary = stratum_summary(rows)
    assert summary["n_strata_compared"] == 1 and summary["strata_decisiveness"] == 0.5


def test_a_failure_in_our_recording_is_ours_not_the_algorithms():
    class Generator:                       # stands in for a generate.py module
        written = []

        @staticmethod
        def write_graphml(payload, path):
            Generator.written.append(path)

    folder = Path(tempfile.mkdtemp(prefix="scaling-test-"))
    atexit.register(shutil.rmtree, folder, ignore_errors=True)
    try:
        with recording(Generator, "no-such-algorithm"):
            Generator.write_graphml(object(), folder / "s.graphml")
    except RecordingFault:
        return
    raise AssertionError("an error while recording extents was not reported as ours")


def graphml_with(points):
    folder = Path(tempfile.mkdtemp(prefix="scaling-test-"))
    atexit.register(shutil.rmtree, folder, ignore_errors=True)
    nodes = "".join(f'<node id="{i}"><data key="x">{x}</data><data key="y">{y}</data></node>'
                    for i, (x, y) in enumerate(points))
    path = folder / "d.graphml"
    path.write_text('<graphml xmlns="http://graphml.graphdrawing.org/xmlns"><graph>'
                    f"{nodes}</graph></graphml>", encoding="utf-8")
    return path


def test_a_diverged_or_collapsed_drawing_is_invalid():
    from run_harness import degenerate
    assert degenerate(graphml_with([(0, 0), (1, 1), (-1, 1), (0, 2)])) is None
    assert degenerate(graphml_with([(0, 0), (1, 1), (1, 1), (0, 2)])) is None      # overlap: poor, not invalid
    assert "diverged" in degenerate(graphml_with([(0, 0), (1e40, 1), (-1, 1), (0, 2)]))
    assert "collapsed" in degenerate(graphml_with([(5, 0), (5, 1), (5, 1), (5, 2)]))
    assert "not finite" in degenerate(graphml_with([(0, 0), (float("nan"), 1), (1, 2)]))


if __name__ == "__main__":
    failed = False
    for name, test in sorted(globals().items()):
        if name.startswith("test_"):
            try:
                test()
                print(f"  ok    {name}")
            except AssertionError as failure:
                print(f"  FAIL  {name}: {failure}")
                failed = True
    raise SystemExit(1 if failed else 0)
