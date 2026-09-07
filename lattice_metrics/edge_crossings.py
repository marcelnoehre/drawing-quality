'''
Edge crossing count, normalized against the crossings this diagram
cannot avoid.

Two edges can only cross in *some* drawing of the poset if their endpoints
are pairwise incomparable -- comparable pairs are connected by a monotone
path in every upward drawing and never need to cross. So instead of
comparing the observed crossing count to the maximum over *all* edge pairs
(most of which could never legally cross anyway), we compare it to the
maximum over pairs that are actually free to cross, which is the right
notion of 'how much of the *avoidable* crossing budget did this drawing
spend'.
'''
from __future__ import annotations

from itertools import combinations

from .geometry import find_crossings
from .graph_utils import LatticeLayout


def _can_cross(edge_a, edge_b, layout: LatticeLayout) -> bool:
    u1, v1 = edge_a
    u2, v2 = edge_b
    if set(edge_a) & set(edge_b):
        return False
    return not (
        layout.is_comparable(u1, u2)
        or layout.is_comparable(u1, v2)
        or layout.is_comparable(v1, u2)
        or layout.is_comparable(v1, v2)
    )


def edge_crossing_score(layout: LatticeLayout) -> float:
    '''
    1.0 = no avoidable crossings at all; 1 - (crossings / avoidable_crossings)
    otherwise. Returns 1.0 when no pair of edges could ever cross (e.g. the
    poset is a single chain).

    A crossing between two edges whose endpoints *are* comparable would mean
    the drawing isn't even a valid upward drawing of the poset -- a far more
    fundamental fault than an ordinary avoidable crossing. Such crossings
    are excluded from both the numerator and denominator here (rather than
    counted in the numerator against a denominator that never budgeted for
    them, which could push the score below 0); callers who need to detect
    that failure mode should check for it directly with `find_crossings`
    and `is_comparable`.
    '''
    edges = list(layout.graph.edges())
    eligible_pairs = {
        frozenset((edge_a, edge_b))
        for edge_a, edge_b in combinations(edges, 2)
        if _can_cross(edge_a, edge_b, layout)
    }
    if not eligible_pairs:
        return 1.0

    crossings = find_crossings(edges, layout.positions)
    avoidable_crossings = sum(
        1 for c in crossings if frozenset((c.edge_a, c.edge_b)) in eligible_pairs
    )
    return float(1.0 - avoidable_crossings / len(eligible_pairs))
