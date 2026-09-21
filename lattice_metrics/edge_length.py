'''
Edge length uniformity, correlated with slope.

Uniform edge length is a classic graph-drawing aesthetic, but a straight-line
Hasse diagram cannot satisfy it edge-by-edge without contradiction: once a
layering has picked each node's vertical position (see layering.py), an
edge's length is fixed by its vertical span *and* its slope --
``length = vertical_span / sin(angle from horizontal)``. Two edges with the
same vertical span but different slopes are therefore *necessarily*
different lengths (the shallower one is longer); scoring raw length
uniformity across the whole diagram would penalize a drawing for the same
geometric fact that gives it a legible, varied slope structure (see
slopes.py), not for an actual drawing flaw.

:func:`edge_length_uniformity_score` instead only compares edges that are
already free to match: it groups edges by slope, using the same
tolerance-based clustering :func:`~lattice_metrics.slopes.slope_harmony_score`
uses (so 'same slope' means the same thing in both metrics), then scores
length uniformity *within* each slope group by its coefficient of variation
(std / mean, clipped to [0, 1] since it isn't itself bounded). Group scores
are averaged weighted by group size, so a slope shared by many edges must
actually be uniform to score well, while an outlier slope with only one or
two edges -- nothing to compare it to -- trivially scores 1.0 and can't drag
the result down on its own.
'''
from __future__ import annotations

from typing import List

import numpy as np

from .graph_utils import LatticeLayout, group_within_tolerance
from .slopes import DEFAULT_ANGLE_TOLERANCE, edge_angles_and_lengths


def _length_groups_by_slope(layout: LatticeLayout, angle_tolerance: float) -> List[np.ndarray]:
    angles, lengths = edge_angles_and_lengths(layout)
    if len(angles) == 0:
        return []

    order = np.argsort(angles)
    sorted_angles = angles[order]
    sorted_lengths = lengths[order]

    angle_groups = group_within_tolerance(sorted_angles, angle_tolerance)
    sizes = [len(g) for g in angle_groups]
    return np.split(sorted_lengths, np.cumsum(sizes)[:-1])


def _coefficient_of_variation_score(group: np.ndarray) -> float:
    if len(group) <= 1:
        return 1.0
    mean = float(np.mean(group))
    if mean < 1e-12:
        return 1.0
    std = float(np.std(group))
    return float(1.0 - np.clip(std / mean, 0.0, 1.0))


def edge_length_uniformity_score(
    layout: LatticeLayout,
    angle_tolerance: float = DEFAULT_ANGLE_TOLERANCE,
) -> float:
    '''
    1.0 = within every group of (approximately) same-slope edges, all
    lengths match exactly; lower as same-slope edges vary more in length.

    Returns 1.0 for layouts with no edges, since there is nothing to
    penalize.
    '''
    length_groups = _length_groups_by_slope(layout, angle_tolerance)
    if not length_groups:
        return 1.0

    scores = [_coefficient_of_variation_score(g) for g in length_groups]
    weights = [len(g) for g in length_groups]
    return float(np.average(scores, weights=weights))
