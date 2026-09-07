'''
Crossing angle: crossings closer to 90 degrees are easier to read apart
than near-parallel (near-0/180 degree) crossings (Huang et al., 2014;
Purchase, 1997).
'''
from __future__ import annotations

import numpy as np

from .geometry import find_crossings, unsigned_angle_deg
from .graph_utils import LatticeLayout


def crossing_angle_score(layout: LatticeLayout) -> float:
    '''
    1.0 = no crossings, or every crossing is a perfect right angle.
    0.0 = every crossing is (near-)parallel, the hardest case to read.

    Edges that overlap along a shared sub-segment (rather than crossing at a
    single point) are scored as the worst case (angle 0), since two edges
    running on top of each other is strictly harder to read than any
    genuine crossing.
    '''
    edges = list(layout.graph.edges())
    positions = layout.positions

    crossings = find_crossings(edges, positions)
    if not crossings:
        return 1.0

    deviations = []
    for crossing in crossings:
        if not crossing.is_proper:
            deviations.append(1.0)
            continue
        d1 = positions[crossing.edge_a[1]] - positions[crossing.edge_a[0]]
        d2 = positions[crossing.edge_b[1]] - positions[crossing.edge_b[0]]
        angle = unsigned_angle_deg(d1, d2)
        angle = min(angle, 180.0 - angle)  # fold to [0, 90]: direction of travel doesn't matter
        deviations.append(abs(90.0 - angle) / 90.0)

    return float(1.0 - np.mean(deviations))
