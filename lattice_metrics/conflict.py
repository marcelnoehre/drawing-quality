'''
Shared scoring for 'something is too close to something else' metrics.

Given a set of measured distances and a perceptual threshold below which two
drawn elements are hard to tell apart, how bad is the drawing? Kept as a
standalone function (currently used by node-edge proximity, see
:mod:`lattice_metrics.conflict_distance`) rather than inlined, so any other
'too close' metric can reuse the same, documented [0, 1] shape instead of
inventing its own ad hoc squashing function.
'''
from __future__ import annotations

from typing import Sequence

import numpy as np


def distance_conflict_score(
    distances: Sequence[float],
    threshold: float,
) -> float:
    '''
    Score in [0, 1] from a set of measured distances against a
    'too close' ``threshold``.

    Each distance contributes a penalty that is 0 at/above ``threshold`` and
    rises to 1 as the distance approaches 0, quadratically (so near-misses
    barely matter but near-overlaps are punished heavily, matching how
    overlap actually degrades legibility). The score is the mean of
    ``1 - penalty`` over *all* supplied distances, not just the conflicting
    ones, so it is naturally scale-invariant in the number of pairs: adding
    more far-apart pairs cannot make a bad drawing look better, and a single
    severe conflict cannot be hidden by averaging over a huge unrelated
    population -- it still costs exactly ``1/len(distances)``.

    Returns 1.0 (no conflicts possible) if ``distances`` is empty or
    ``threshold`` is not positive.
    '''
    if len(distances) == 0 or threshold <= 0:
        return 1.0
    d = np.asarray(distances, dtype=float)
    penalty = np.clip(1.0 - d / threshold, 0.0, 1.0) ** 2
    return float(1.0 - np.mean(penalty))
