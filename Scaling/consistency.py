"""How consistently does one algorithm place the same concept in two scales?

Because the levels of a nesting nest, a concept in the coarser scale *is* a
concept of the finer one, matched by extent. The same algorithm therefore draws it
twice, with no memory in between, and the two placements can be compared. That
comparison is the whole of RQ4.

**Only ranks, never coordinates.** Two runs on related inputs do not produce
comparable coordinates: the origin and the scale are arbitrary, so any statistic
built on distances measures those as much as the placement. The measure here is
Kendall's tau between the horizontal *ranks* of the shared concepts, which is
invariant under translation, scaling and any monotone rescaling of x.

**Vertical movement is reported separately.** New concepts insert into chains and
push shared ones up or down, which is forced by the order rather than chosen by
the algorithm. That is rank drift, and it is a baseline, not a charge against the
algorithm.

Run the fixtures before trusting any number this module produces:

    python consistency.py --self-test
"""

from __future__ import annotations

import argparse
import sys

from math import isqrt, nan, sqrt

from scipy.stats import kendalltau, rankdata

Drawing = dict[frozenset, tuple[float, float]]

# Below this many shared concepts a rank correlation has too little to work with;
# such pairs are computed and flagged in the `thin` column rather than dropped.
THIN_OVERLAP = 8


def shared_extents(a: Drawing, b: Drawing) -> list[frozenset]:
    """The concepts drawn in both, in a fixed order so results are reproducible."""
    return sorted(set(a) & set(b), key=lambda e: (len(e), sorted(e)))


def kendall_tau_b(xs, ys) -> float:
    """Kendall's tau-b, counted in integers so the exact cases come out exact.

    scipy returns 0.9999999999999999 for two identical rankings, because it
    normalises in floating point. The fixtures demand an exact 1 for a drawing
    compared with itself and for one where only non-shared nodes moved, and they
    are right to: a measure that cannot return its own maximum is a measure whose
    edge cases are untested. Concordant and discordant pairs are integers, and so
    is the denominator whenever there are no ties, so the ratio is computed as
    integers and only then divided.
    """
    # Plain floats: numpy booleans do not subtract, and ranks are small anyway.
    xs = [float(v) for v in xs]
    ys = [float(v) for v in ys]
    n = len(xs)
    concordant = discordant = tied_x = tied_y = 0
    for i in range(n):
        for j in range(i + 1, n):
            dx, dy = xs[i] - xs[j], ys[i] - ys[j]
            sx = (dx > 0) - (dx < 0)
            sy = (dy > 0) - (dy < 0)
            if sx == 0:
                tied_x += 1
            if sy == 0:
                tied_y += 1
            if sx and sy:
                concordant += sx == sy
                discordant += sx != sy

    pairs = n * (n - 1) // 2
    denominator_squared = (pairs - tied_x) * (pairs - tied_y)
    if denominator_squared <= 0:
        return nan
    numerator = concordant - discordant
    root = isqrt(denominator_squared)
    if root * root == denominator_squared:          # the no-ties case, and others
        return numerator / root
    return numerator / sqrt(denominator_squared)


def tau_x(a: Drawing, b: Drawing) -> tuple[float, float, int]:
    """Kendall's tau between the horizontal ranks of the shared concepts.

    Returns (tau, p-value, number of shared concepts). tau is 1 when the left to
    right order is identical, -1 when it is exactly reversed, which is what a
    mirrored drawing gives. The statistic is computed exactly; the p-value comes
    from scipy, which is what it is good for.
    """
    shared = shared_extents(a, b)
    if len(shared) < 2:
        return nan, nan, len(shared)
    ranks_a = rankdata([a[e][0] for e in shared])
    ranks_b = rankdata([b[e][0] for e in shared])
    tau = kendall_tau_b(ranks_a, ranks_b)
    _, p = kendalltau(ranks_a, ranks_b)
    return tau, float(p), len(shared)


def rank_drift(a: Drawing, b: Drawing) -> float:
    """How far the shared concepts move vertically, in normalised rank terms.

    Each shared concept is ranked by its vertical position within each drawing; the
    drift is the total absolute change of those ranks over the largest total any
    permutation could produce. 0 means every shared concept kept its vertical order,
    1 means the order was exactly reversed. This is order-theoretic and is reported
    as a baseline: refining a scale inserts concepts and moves the others vertically
    whatever the algorithm does.

    The normaliser is floor(n^2 / 2), the maximum of sum |i - s(i)| over
    permutations s, attained by the reversal. It used to be n(n - 1), which is not
    attainable: a reversal scored 0.67 at n = 4 and 0.51 at n = 46, so the column
    was neither bounded by 1 nor comparable between pairs of different size.
    """
    shared = shared_extents(a, b)
    if len(shared) < 2:
        return float("nan")
    n = len(shared)
    ranks_a = rankdata([a[e][1] for e in shared])
    ranks_b = rankdata([b[e][1] for e in shared])
    moved = sum(abs(x - y) for x, y in zip(ranks_a, ranks_b))
    return float(moved / (n * n // 2))


def tau_by_stratum(a: Drawing, b: Drawing) -> list[dict]:
    """Kendall tau within each rank stratum, which separates a flip from a scramble.

    A global tau cannot tell the two apart. If an algorithm reflects a sub-branch
    when concepts are inserted, the strata that branch touches invert while the
    rest stay put, so the per-stratum taus come out bimodal, some near +1 and some
    near -1, and the global figure averages them into something middling. A genuine
    scramble gives values near zero everywhere. The distinction matters for what
    can be said afterwards: "refinement flips sub-branches" names a mechanism,
    "refinement scrambles" does not.

    Strata are heights in the order, so this is the same notion the permutation
    null permutes within.
    """
    from nulls import rank_strata                     # imported here to avoid a cycle

    shared = shared_extents(a, b)
    if len(shared) < 2:
        return []
    strata = rank_strata(shared)
    grouped: dict[int, list[frozenset]] = {}
    for extent in shared:
        grouped.setdefault(strata[extent], []).append(extent)

    rows = []
    for stratum, extents in sorted(grouped.items()):
        if len(extents) < 2:
            # A stratum of one has no pair to agree or disagree about.
            rows.append({"stratum": stratum, "n": len(extents), "tau": None})
            continue
        ranks_a = rankdata([a[e][0] for e in extents])
        ranks_b = rankdata([b[e][0] for e in extents])
        rows.append({"stratum": stratum, "n": len(extents),
                     "tau": kendall_tau_b(ranks_a, ranks_b)})
    return rows


def stratum_summary(rows: list[dict]) -> dict:
    """How the per-stratum taus are distributed: flipped, held, or neither."""
    usable = [r for r in rows if r["tau"] is not None]
    if not usable:
        return {"n_strata": len(rows), "n_strata_compared": 0,
                "frac_strata_strong": "", "frac_strata_inverted": "",
                "strata_bimodality": "", "strata_sign_agreement": ""}
    strong = [r for r in usable if abs(r["tau"]) > 0.5]
    inverted = [r for r in usable if r["tau"] < -0.5]
    # Do the strata agree on a direction? Three patterns have to be told apart:
    #   a branch flip     mixed signs, |tau| high in each stratum
    #   a global mirror   one sign everywhere, |tau| high
    #   a scramble        |tau| low everywhere, sign meaningless
    # Sign agreement separates the first two; mean |tau| separates the third.
    positive = sum(1 for r in usable if r["tau"] > 0)
    agreement = max(positive, len(usable) - positive) / len(usable)
    # Mean |tau| over the strata: near 1 means every stratum either held or
    # flipped, near 0 means no stratum did either, which is a scramble.
    bimodality = sum(abs(r["tau"]) for r in usable) / len(usable)
    return {
        "n_strata": len(rows),
        "n_strata_compared": len(usable),
        "frac_strata_strong": round(len(strong) / len(usable), 3),
        "frac_strata_inverted": round(len(inverted) / len(usable), 3),
        "strata_bimodality": round(bimodality, 3),
        "strata_sign_agreement": round(agreement, 3),
    }


def compare(a: Drawing, b: Drawing) -> dict:
    """Everything recorded for one (coarser, finer, algorithm) triple."""
    tau, p, n_shared = tau_x(a, b)
    strata = tau_by_stratum(a, b)
    return {
        "n_shared": n_shared,
        "tau_x": tau,
        "p_value": p,
        "rank_drift": rank_drift(a, b),
        "thin": n_shared < THIN_OVERLAP,
        **stratum_summary(strata),
    }


# ---------------------------------------------------------------------------
# Fixtures. These run before the measure touches real data; if one fails the
# implementation is wrong and no result from it means anything.
# ---------------------------------------------------------------------------

def _drawing(points: dict[str, tuple[float, float]]) -> Drawing:
    """A toy drawing keyed by extent, written with single-letter objects."""
    return {frozenset(name): position for name, position in points.items()}


def self_test() -> int:
    base = _drawing({
        "a": (0.0, 0.0), "ab": (1.0, 1.0), "abc": (2.0, 2.0),
        "abcd": (3.0, 3.0), "abcde": (4.0, 4.0), "b": (5.0, 1.5),
        "bc": (6.0, 2.5), "bcd": (7.0, 3.5), "cd": (8.0, 2.0), "d": (9.0, 1.0),
    })
    failures = []

    # 1. A drawing against itself: the order is untouched.
    tau, _, n = tau_x(base, base)
    if not (tau == 1.0 and n == len(base)):
        failures.append(f"identical drawings gave tau={tau} over {n} shared concepts, expected 1")

    # 2. A mirror image: every pair is inverted.
    mirrored = {extent: (-x, y) for extent, (x, y) in base.items()}
    tau, _, _ = tau_x(base, mirrored)
    if tau != -1.0:
        failures.append(f"mirrored drawing gave tau={tau}, expected -1")

    # 3. Only concepts outside the shared set move. The shared order is untouched,
    #    so tau must be exactly 1, not merely close to it.
    finer = dict(base)
    finer[frozenset("xyz")] = (-100.0, 0.5)
    finer[frozenset("wx")] = (100.0, 2.5)
    finer[frozenset("vw")] = (50.0, 3.5)
    tau, _, n = tau_x(base, finer)
    if not (tau == 1.0 and n == len(base)):
        failures.append(f"moving only non-shared nodes gave tau={tau} over {n} shared, expected 1")

    # Rank drift behaves the same way on the same three cases.
    # The exact statistic must agree with scipy to within floating point, or one
    # of the two is wrong.
    from scipy.stats import kendalltau as _scipy_tau
    xs = rankdata([base[e][0] for e in shared_extents(base, base)])
    ys = rankdata([mirrored[e][0] for e in shared_extents(base, mirrored)])
    if abs(kendall_tau_b(xs, ys) - _scipy_tau(xs, ys).statistic) > 1e-9:
        failures.append("the exact tau and scipy's disagree by more than floating point")

    if rank_drift(base, base) != 0.0:
        failures.append(f"identical drawings gave rank drift {rank_drift(base, base)}, expected 0")
    if rank_drift(base, mirrored) != 0.0:
        failures.append("a mirror image changes no heights, so its rank drift should be 0")

    # A thin overlap is flagged rather than dropped.
    small = {extent: base[extent] for extent in list(base)[:3]}
    if not compare(small, small)["thin"]:
        failures.append("an overlap of 3 concepts should be flagged thin")

    for failure in failures:
        print(f"FAIL {failure}", file=sys.stderr)
    if failures:
        return 1
    print(f"all fixtures pass: identical -> tau 1, mirrored -> tau -1, "
          f"non-shared moved -> tau 1 exactly, thin overlaps flagged")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--self-test", action="store_true",
                        help="run the adversarial fixtures and exit")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
