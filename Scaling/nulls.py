"""Null distributions, so that a Kendall tau means something.

A raw tau of 0.7, or of -0.3, says nothing on its own: how much agreement is
surprising depends on how many concepts are shared and on how much freedom the
order leaves. Every observed tau is therefore standardised against a null in which
the algorithm's placement carries no information.

**The permutation null**, which is the primary test. Keep the finer drawing
exactly as it is and permute which shared concept sits at which of its positions,
restricted to *rank strata*: a concept may only take the position of another at
the same height in the lattice. Unrestricted shuffling would compare against a
null that violates the order constraint every drawing has to satisfy, and would
make any algorithm look good. Recomputing tau over a few thousand such draws gives
a distribution, and the observed tau becomes a z-score and a two-sided p-value.

**The rerun null** asks the related question of whether cross-scale disagreement is
larger than the disagreement the algorithm produces by being run twice on the same
input. For a deterministic algorithm that is trivially zero, so the rerun null is
tau = 1 and the comparison reduces to whether the cross-scale tau falls short of 1.
It is only worth building seeded machinery for algorithms that are actually
non-deterministic, which the timing sweep establishes.

**The random-valid null** places the finer lattice at random subject to the order
constraint, giving an absolute floor. It is the least informative of the three and
is not implemented yet.

    python nulls.py --self-test
"""

from __future__ import annotations

import argparse
import random
import sys
from statistics import mean, pstdev

from scipy.stats import kendalltau, rankdata

from consistency import Drawing, kendall_tau_b, shared_extents

DEFAULT_PERMUTATIONS = 2000

# Null draws are scipy floats and the observation is exact; a draw equal to the
# observation up to this much counts as reaching it, which errs towards a larger p.
TOLERANCE = 1e-9

NULL_COLUMNS = ("tau_z", "tau_p", "tau_p_is_bound", "n_null_extreme",
                "tau_abs_z", "tau_abs_p", "tau_abs_p_is_bound", "n_null_abs_extreme",
                "null_mean", "null_sd", "null_abs_mean", "null_abs_sd")


def null_summary(observed: float, draws: list[float]) -> dict:
    """Both tests of one observed tau against its null draws.

    **Signed** (`tau_z`, `tau_p`): two-sided, *centred on the null mean*. Restricting
    permutations to rank strata keeps pairs across strata in their places, so the null
    is generally not centred on zero: on our data its mean runs from -0.19 to +0.22.
    A two-sided test must therefore ask how far the observation lies from that mean,
    |tau - mean| >= |observed - mean|, not how far from zero; comparing |tau| with
    |observed| would misjudge any comparison whose null is off centre.

    **Mirror-invariant** (`tau_abs_z`, `tau_abs_p`): the statistic is |tau|. Mirroring
    a drawing negates every x and so negates tau and nothing else, so |tau| is the
    consistency of the shared concepts' left-to-right order *up to a mirror image of
    the whole drawing*. Its null is the distribution of |tau| over the same draws,
    and the test is one-sided: is the order kept, one way round or the other, more
    than placement within strata would keep it by chance. This is the headline
    statistic; a mirror of a subtree inside the drawing still lowers it.

    Both p-values carry the usual +1, so a p-value is never zero. When no draw reached
    the observation the result is a *bound*, 1/(draws+1), not an estimate; the
    `_is_bound` columns mark those.
    """
    k = len(draws)
    null_mean, null_sd = mean(draws), pstdev(draws)
    extreme = sum(1 for t in draws
                  if abs(t - null_mean) >= abs(observed - null_mean) - TOLERANCE)
    magnitudes = [abs(t) for t in draws]
    abs_mean, abs_sd = mean(magnitudes), pstdev(magnitudes)
    abs_extreme = sum(1 for m in magnitudes if m >= abs(observed) - TOLERANCE)
    return {
        "tau_z": (observed - null_mean) / null_sd if null_sd > 0 else "",
        "tau_p": (extreme + 1) / (k + 1),
        "tau_p_is_bound": extreme == 0,
        "n_null_extreme": extreme,
        "tau_abs_z": (abs(observed) - abs_mean) / abs_sd if abs_sd > 0 else "",
        "tau_abs_p": (abs_extreme + 1) / (k + 1),
        "tau_abs_p_is_bound": abs_extreme == 0,
        "n_null_abs_extreme": abs_extreme,
        "null_mean": null_mean,
        "null_sd": null_sd,
        "null_abs_mean": abs_mean,
        "null_abs_sd": abs_sd,
    }


def rank_strata(extents: list[frozenset]) -> dict[frozenset, int]:
    """Each concept's height: the length of the longest chain below it.

    Computed on the concepts being compared, by inclusion of extents, so it is a
    property of the order rather than of any drawing.
    """
    ordered = sorted(extents, key=len)
    height: dict[frozenset, int] = {}
    for position, extent in enumerate(ordered):
        below = [height[other] for other in ordered[:position] if other < extent]
        height[extent] = max(below, default=0) + 1
    return height


def permutation_null(coarse: Drawing, fine: Drawing,
                     n_permutations: int = DEFAULT_PERMUTATIONS,
                     seed: int = 20260929) -> dict:
    """Standardise the observed tau against label permutations within rank strata."""
    shared = shared_extents(coarse, fine)
    observed = kendall_tau_b(rankdata([coarse[e][0] for e in shared]),
                             rankdata([fine[e][0] for e in shared]))
    if len(shared) < 3 or observed != observed:
        # Too few concepts, or no order to test (every shared concept at one x).
        return {key: "" for key in NULL_COLUMNS} | {"n_permutations": 0}

    strata = rank_strata(shared)
    positions_by_stratum: dict[int, list[int]] = {}
    for index, extent in enumerate(shared):
        positions_by_stratum.setdefault(strata[extent], []).append(index)

    coarse_ranks = rankdata([coarse[e][0] for e in shared])
    fine_x = [fine[e][0] for e in shared]

    # The observed statistic is computed exactly, in integers, because its edge
    # cases have to be exact. The null draws use scipy's tau instead: it is the
    # same statistic to within floating point but runs in n log n rather than n
    # squared, and at 319 shared concepts the quadratic version would need about
    # a hundred million operations per pair. Nothing about a null distribution
    # turns on the sixteenth decimal place.
    rng = random.Random(seed)
    draws = []
    for _ in range(n_permutations):
        shuffled = list(fine_x)
        for positions in positions_by_stratum.values():
            if len(positions) > 1:
                values = [fine_x[p] for p in positions]
                rng.shuffle(values)
                for p, value in zip(positions, values):
                    shuffled[p] = value
        draws.append(float(kendalltau(coarse_ranks, rankdata(shuffled)).statistic))

    return {**null_summary(observed, draws), "n_permutations": n_permutations,
        # How much freedom the null actually had: strata of one cannot be permuted,
        # so a null built almost entirely of singletons is not a null at all.
        "null_free_positions": sum(len(p) for p in positions_by_stratum.values()
                                   if len(p) > 1),
    }


def self_test() -> int:
    failures = []
    rng = random.Random(7)

    # A drawing against itself: the order is reproduced exactly, so the observed
    # tau should sit far above what shuffling within strata produces.
    base: Drawing = {}
    for i in range(24):
        extent = frozenset(range(i + 1))          # a chain, one stratum per concept
        base[extent] = (float(rng.random()), float(i))
    result = permutation_null(base, base, n_permutations=500)
    if result["null_free_positions"] != 0:
        failures.append("a chain has one concept per stratum, so nothing can be permuted")

    # A genuine test: concepts at equal height, so the strata have room.
    wide: Drawing = {frozenset({"bottom"}): (0.0, 0.0)}
    for i in range(12):
        wide[frozenset({f"a{i}"})] = (float(i), 1.0)
    identical = permutation_null(wide, wide, n_permutations=1000)
    if not (identical["tau_z"] != "" and identical["tau_z"] > 3):
        failures.append(f"an identical drawing should stand out from its null, "
                        f"got z={identical['tau_z']}")
    if identical["tau_p"] > 0.01:
        failures.append(f"an identical drawing should be improbable under the null, "
                        f"got p={identical['tau_p']}")
    if abs(identical["null_mean"]) > 0.15:
        failures.append(f"the null should centre near zero, got {identical['null_mean']}")

    # A drawing whose horizontal order carries no information should not stand out.
    scrambled = dict(wide)
    keys = [k for k in wide if k != frozenset({"bottom"})]
    values = [wide[k][0] for k in keys]
    rng.shuffle(values)
    for k, v in zip(keys, values):
        scrambled[k] = (v, wide[k][1])
    noise = permutation_null(wide, scrambled, n_permutations=1000)
    if noise["tau_p"] < 0.01:
        failures.append(f"a shuffled drawing should not be significant, got p={noise['tau_p']}")

    # A mirror image keeps the order exactly, the other way round: the
    # mirror-invariant test must judge it exactly as it judges the identical drawing.
    mirrored = {e: (-x, y) for e, (x, y) in wide.items()}
    flipped = permutation_null(wide, mirrored, n_permutations=1000)
    if (flipped["tau_abs_p"], flipped["tau_abs_z"]) != (identical["tau_abs_p"], identical["tau_abs_z"]):
        failures.append(f"a mirror image should be as consistent as the identical drawing "
                        f"up to mirroring, got p={flipped['tau_abs_p']} vs {identical['tau_abs_p']}")

    # The signed test is centred on the null mean, not on zero. Draws centred on
    # +0.2: an observation at +0.2 is the most ordinary value there is (p = 1), and
    # one at -0.2 is as far out as one at +0.6.
    draws = [0.2 + 0.1 * ((i % 9) - 4) / 4 for i in range(900)]     # 0.1 .. 0.3
    if null_summary(0.2, draws)["tau_p"] != 1.0:
        failures.append("an observation at the null mean must have p = 1")
    low, high = null_summary(-0.2, draws), null_summary(0.6, draws)
    if not (low["tau_p"] == high["tau_p"] == 1 / 901 and low["tau_p_is_bound"]):
        failures.append("observations equally far either side of the null mean must get "
                        "the same p, and none of these draws reaches them")
    if null_summary(0.25, draws)["tau_p"] <= null_summary(0.3, draws)["tau_p"]:
        failures.append("p must fall as the observation moves away from the null mean")

    for failure in failures:
        print(f"FAIL {failure}", file=sys.stderr)
    if failures:
        return 1
    print("null fixtures pass: identical drawings stand out, shuffled ones do not, "
          "the null centres near zero, strata of one are reported as unpermutable, "
          "a mirror image is judged as the identical drawing up to mirroring, and the "
          "signed test is centred on the null mean")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
