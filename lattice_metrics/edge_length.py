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
already free to match: it groups edges by line direction in [0, 180) --
so an edge leaning left and its mirror image leaning right are separate
groups, as in the signed slope metrics, while 0 and 180 both mean
horizontal -- using the same circular tolerance-based clustering as
:mod:`lattice_metrics.slopes` but a looser tolerance (see
:data:`DEFAULT_ANGLE_TOLERANCE`), then scores
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

from .graph_utils import LatticeLayout
from .slopes import edge_directions_and_lengths, group_directions

# Looser than the 1 degree 'same slope' of the slope metrics, which asks
# whether two edges share a slope. This asks which edges are free to share a
# length: at a common vertical span, length = span / sin(angle), so a slope
# difference of d forces a relative length difference of about cot(angle) * d,
# under 10% at 45 degrees for 5 degrees. A tighter tolerance leaves such
# edges in separate groups, never compared, and singleton groups score 1.0.
DEFAULT_ANGLE_TOLERANCE = 5.0


def _length_groups_by_slope(layout: LatticeLayout, angle_tolerance: float) -> List[np.ndarray]:
    directions, lengths = edge_directions_and_lengths(layout)
    if len(directions) == 0:
        return []
    return [lengths[g] for g in group_directions(directions, angle_tolerance, period=180.0)]


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
    1.0 = within every group of (approximately) same-direction edges, all
    lengths match exactly; lower as same-direction edges vary more in length.

    Returns 1.0 for layouts with no edges, since there is nothing to
    penalize.
    '''
    length_groups = _length_groups_by_slope(layout, angle_tolerance)
    if not length_groups:
        return 1.0

    scores = [_coefficient_of_variation_score(g) for g in length_groups]
    weights = [len(g) for g in length_groups]
    return float(np.average(scores, weights=weights))
