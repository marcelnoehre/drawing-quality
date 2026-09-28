'''
Shared scoring for 'something is too close to something else' metrics.

Given a set of measured distances and a perceptual threshold below which two
drawn elements are hard to tell apart, how bad is the drawing? Kept as a
standalone function (used by the node-node, node-edge and edge-edge
conflict metrics and by nesting) rather than inlined, so any other 'too
close' metric can reuse the same, documented [0, 1] shape instead of
inventing its own ad hoc squashing function.
'''
from __future__ import annotations

from typing import Sequence

import numpy as np



# Smallest per-item 'goodness' factor allowed into the geometric mean's log.
# A factor of exactly 0.0 (an item at or past ``floor``) would make
# log(factor) = -inf, and the mean of any list containing -inf is -inf --
# so a single maximally-bad item would drag the whole aggregate to 0.0
# regardless of how good every other item is, rather than merely
# dominating it. Clipping to a tiny positive value keeps that domination
# (log(1e-12) is still enormously more negative than any real item can
# get) without the discontinuous collapse.
_MIN_GEOMETRIC_FACTOR = 1e-12


def _goodness_factors(distances: Sequence[float], threshold: float, floor: float) -> np.ndarray:
    d = np.asarray(distances, dtype=float)
    penalty = np.clip((threshold - d) / (threshold - floor), 0.0, 1.0) ** 2
    return 1.0 - penalty


def distance_conflict_score(
    distances: Sequence[float],
    threshold: float,
    floor: float = 0.0,
    aggregation: str = 'mean',
) -> float:
    '''
    Score in [0, 1] from a set of measured distances against a
    'too close' ``threshold``.

    Each distance contributes a penalty that is 0 at/above ``threshold`` and
    rises to 1 as the distance approaches ``floor``, quadratically (so
    near-misses barely matter but near-overlaps are punished heavily,
    matching how overlap actually degrades legibility).

    ``floor`` defaults to 0, matching the physical distances this was
    originally written for (a point-segment distance can't go negative, so
    0 -- full overlap -- is already the worst case). Callers whose
    'distance' is a signed clearance that can go negative (e.g. an overlap
    depth) can lower ``floor`` below 0 so that gradations *among* conflicts
    still show up instead of every d <= 0 collapsing to the same score.

    ``aggregation`` controls how per-item scores combine:
    - ``'mean'`` (default): the arithmetic mean of ``1 - penalty`` over
      *all* supplied distances, not just the conflicting ones, so it is
      naturally scale-invariant in the number of items: adding more
      far-apart items cannot make a bad drawing look better, and a single
      severe conflict costs exactly ``1/len(distances)`` -- appropriate
      when many far-apart items are expected and unrelated to each other
      (e.g. node-edge pairs).
    - ``'geometric'``: the geometric mean of ``1 - penalty``, for callers
      where every item is required to be simultaneously acceptable (e.g.
      one shared nesting radius across every node) -- a single fully
      conflicting item should cost far more than ``1/len(distances)``,
      since it blocks the shared property everywhere, not just locally.

    Returns 1.0 (no conflicts possible) if ``distances`` is empty or
    ``threshold`` is not greater than ``floor``.
    '''
    if len(distances) == 0 or threshold <= floor:
        return 1.0
    factors = _goodness_factors(distances, threshold, floor)

    if aggregation == 'mean':
        return float(np.mean(factors))
    elif aggregation == 'geometric':
        log_factors = np.log(np.maximum(factors, _MIN_GEOMETRIC_FACTOR))
        return float(np.exp(np.mean(log_factors)))
    else:
        raise ValueError(f"Unknown aggregation: {aggregation!r}. Use 'mean' or 'geometric'.")


def distance_conflict_min_score(
    distances: Sequence[float],
    threshold: float,
    floor: float = 0.0,
) -> float:
    '''
    The single worst item's score under the same per-item penalty as
    :func:`distance_conflict_score` -- i.e. the minimum of the per-item
    factors whose arithmetic mean that function returns -- so a metric's
    average (its score) and its worst case share one [0, 1] scale.

    Returns 1.0 under the same conditions as :func:`distance_conflict_score`.
    '''
    if len(distances) == 0 or threshold <= floor:
        return 1.0
    return float(np.min(_goodness_factors(distances, threshold, floor)))
