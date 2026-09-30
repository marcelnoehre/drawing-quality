"""Regression tests for the claim that DimDraw's cost follows incomparable pairs.

The claim, from measuring odis's DimDraw on its own published examples and on our
scales, is that the work is orienting incomparable pairs rather than handling
concepts: eleven to nineteen concepts with twenty to ninety incomparable pairs
finish instantly, while thirty-odd concepts with several hundred consume any
budget given to them.

`Cn5` is the anchor. It is a contranominal scale of dimension five, 32 concepts
and 285 incomparable pairs, and it comes from DimDraw's own data set rather than
from ours, so it cannot be dismissed as an artefact of how we build scales. If
this test ever stops failing to finish, either odis got faster or the explanation
was wrong, and either way the timing claims in `pipeline.md` need revisiting.

    python tests/test_dimdraw_cost.py        # standalone
    pytest tests/test_dimdraw_cost.py        # or under pytest
"""

from __future__ import annotations

import time
from pathlib import Path

import odis

DATA = Path(__file__).resolve().parent / "data"

# Short budgets: the point is which side of the budget a case falls on, not the
# exact time, and the suite has to stay runnable.
SHORT_BUDGET_S = 10.0
CONSUMED = 0.95


def incomparable_pairs(context: odis.FormalContext) -> int:
    extents = [frozenset(c.extent.to_frozenset()) for c in context.concepts()]
    return sum(1 for i, a in enumerate(extents) for b in extents[i + 1:]
               if not (a <= b or b <= a))


def time_dimdraw(path: Path, budget_s: float) -> tuple[float, int, int]:
    context = odis.FormalContext.from_file(str(path))
    concepts = len(list(context.concepts()))
    incomparable = incomparable_pairs(context)
    started = time.perf_counter()
    context.draw("dimdraw", int(budget_s * 1000))
    return time.perf_counter() - started, concepts, incomparable


def test_contranominal_scale_consumes_the_budget():
    """Cn5: 32 concepts, 285 incomparable pairs, from DimDraw's own data set."""
    elapsed, concepts, incomparable = time_dimdraw(DATA / "Cn5.cxt", SHORT_BUDGET_S)
    assert concepts == 32, f"Cn5 should have 32 concepts, got {concepts}"
    assert incomparable == 285, f"Cn5 should have 285 incomparable pairs, got {incomparable}"
    assert elapsed > SHORT_BUDGET_S * CONSUMED, (
        f"Cn5 finished in {elapsed:.2f}s within a {SHORT_BUDGET_S}s budget. DimDraw "
        f"is faster than when this was measured, so the cost model in pipeline.md "
        f"needs rechecking.")


def test_a_wider_lattice_with_fewer_concepts_costs_more():
    """Concept count does not predict the cost; incomparability does.

    `family-excitation` has 27 concepts and 260 incomparable pairs and finishes at
    once; Cn5 has 32 concepts and 285 and does not. The two are close in size and
    far apart in cost, which is the whole point.
    """
    easy, easy_concepts, easy_pairs = time_dimdraw(DATA / "family-excitation.cxt",
                                                   SHORT_BUDGET_S)
    assert easy < SHORT_BUDGET_S * CONSUMED, (
        f"family-excitation took {easy:.2f}s; it used to finish in well under a second")
    assert easy_concepts == 27 and easy_pairs == 260


if __name__ == "__main__":
    for name, test in sorted(globals().items()):
        if name.startswith("test_"):
            try:
                test()
                print(f"  ok    {name}")
            except AssertionError as failure:
                print(f"  FAIL  {name}: {failure}")
