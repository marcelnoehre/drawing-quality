"""fdp does not terminate on a context with two equivalent attributes.

Two attributes that imply each other — equal extents, an unclarified context — make
`FDP_Additive_Features.__init__` loop forever, at any size. `_initialize_vectors`
places a non-coatom attribute only once every attribute implied by it already has a
position; two attributes implying each other each wait for the other, and the queue
cycles with neither ever becoming placeable. The `timeout_s` argument cannot stop
it, because that is checked in the optimiser's callback and this never reaches the
optimiser.

The fixture is four objects and three attributes. `x` holds of g1, g2, g3; `a` and
`b` both hold of g1 and g2, so each implies the other and neither is a coatom.
Three concepts in total. Removing `b` draws it at once, and removing the one
equivalent pair from our 319-concept scale draws that in 9.8 seconds, so this is
about clarification and not about cost.

This matters to us because our scales are legitimately unclarified: a scale's
attributes are the conjunctions we chose, and two of them having the same extent is
a fact about the data. `Requires electricity` and `Electrical sound` hold of exactly
the same instruments. Eleven of the 39 contexts and scales here contain such a
pair, four of them imported unchanged from his collection.

We do not clarify them to make fdp work: the attribute set is the view we chose, and
a defect reproduced on a three-concept fixture belongs in his code, not in our
inputs. See pipeline.md, *Decided: we do not clarify the scales*.

`run_harness.py` therefore skips fdp on an unclarified context with that reason
recorded, rather than hanging the sweep. If this test starts failing, fdp has been
fixed and that skip should go.

    python tests/test_fdp_termination.py        # standalone
    pytest tests/test_fdp_termination.py        # or under pytest
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
FDP = HERE.parent.parent / "line_diagrams" / "fdp"

# Long enough that a slow machine is not mistaken for a hang, short enough to keep
# the suite runnable. The clarified fixture returns in well under a second.
CAP_S = 15.0

RUN = """
import sys
sys.path.insert(0, {fdp!r})
import odis
from fdp import FDP_Additive_Features
context = odis.FormalContext.from_file({cxt!r})
FDP_Additive_Features(context, {{'timeout_s': 2.0}})
print('returned')
"""


def run_fdp(cxt: Path) -> subprocess.CompletedProcess | None:
    """Draw one context in a fresh process; None means it never came back."""
    try:
        return subprocess.run(
            [sys.executable, "-c", RUN.format(fdp=str(FDP), cxt=str(cxt))],
            capture_output=True, text=True, timeout=CAP_S)
    except subprocess.TimeoutExpired:
        return None


def test_equivalent_attributes_never_return():
    """Three concepts, and a two-second budget it never gets to consult."""
    assert run_fdp(DATA / "equivalent-attributes.cxt") is None, (
        "fdp returned on a context with two equivalent attributes. It used not to, "
        "so either fdp was fixed — in which case drop REQUIRES_CLARIFIED from "
        "run_harness.py — or this fixture stopped having an equivalent pair.")


def test_the_same_context_clarified_returns_at_once():
    """The difference is the equivalent attribute, not the size of anything."""
    result = run_fdp(DATA / "equivalent-attributes-clarified.cxt")
    assert result is not None, (
        f"fdp did not return within {CAP_S}s on a two-attribute, four-object "
        f"context, so the non-termination above is not about equivalent attributes "
        f"after all and the diagnosis in pipeline.md is wrong.")
    assert result.returncode == 0, f"fdp failed: {result.stderr[-400:]}"


if __name__ == "__main__":
    for name, test in sorted(globals().items()):
        if name.startswith("test_"):
            try:
                test()
                print(f"  ok    {name}")
            except AssertionError as failure:
                print(f"  FAIL  {name}: {failure}")
