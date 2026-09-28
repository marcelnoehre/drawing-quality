'''
Crossing angle: crossings closer to 90 degrees are easier to read apart
than near-parallel (near-0/180 degree) crossings (Huang et al., 2014;
Purchase, 1997).
'''
from __future__ import annotations

from typing import List

import numpy as np

from .geometry import find_crossings, unsigned_angle_deg
from .graph_utils import LatticeLayout


def crossing_angles(layout: LatticeLayout) -> List[float]:
    '''
    The folded-to-[0, 90] angle of every crossing in the drawing (0 =
    (near-)parallel, the hardest to read; 90 = a perfect right angle), and
    0.0 -- the worst case -- for every pair of edges that overlap along a
    shared sub-segment rather than crossing at a single point.

    Unlike the per-node conflict metrics' raw measurements, this needs no
    'is it actually a conflict' threshold: every crossing
    :func:`~lattice_metrics.geometry.find_crossings` reports is already a
    genuine geometric event, not a distance sampled from a much larger
    population of structurally-irrelevant pairs.
    '''
    edges = list(layout.graph.edges())
    positions = layout.positions

    angles = []
    for crossing in find_crossings(edges, positions):
        if not crossing.is_proper:
            angles.append(0.0)
            continue
        d1 = positions[crossing.edge_a[1]] - positions[crossing.edge_a[0]]
        d2 = positions[crossing.edge_b[1]] - positions[crossing.edge_b[0]]
        angle = unsigned_angle_deg(d1, d2)
        angles.append(min(angle, 180.0 - angle))  # fold to [0, 90]: direction of travel doesn't matter
    return angles


def crossing_angle_score(layout: LatticeLayout) -> float:
    '''
    1.0 = no crossings, or every crossing is a perfect right angle.
    0.0 = every crossing is (near-)parallel, the hardest case to read.

    Edges that overlap along a shared sub-segment (rather than crossing at a
    single point) are scored as the worst case (angle 0), since two edges
    running on top of each other is strictly harder to read than any
    genuine crossing.
    '''
    angles = crossing_angles(layout)
    if not angles:
        return 1.0

    deviations = [abs(90.0 - angle) / 90.0 for angle in angles]
    return float(1.0 - np.mean(deviations))


def crossing_angle_min_score(layout: LatticeLayout) -> float:
    '''
    The worst single crossing's term in :func:`crossing_angle_score`
    (1 - |90 - angle| / 90 = angle / 90 for the sharpest crossing), on the
    same [0, 1] scale as the score, which is the mean of these terms. 1.0
    if the drawing has no crossings.
    '''
    angles = crossing_angles(layout)
    if not angles:
        return 1.0
    return float(1.0 - abs(90.0 - min(angles)) / 90.0)
