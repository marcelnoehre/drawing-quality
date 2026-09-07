'''
Slope harmony and slope standardness.

Both operate on the *unsigned* angle each edge makes with the horizontal, in
[0, 90], since an edge running up-left and its mirror image running up-right
are equally 'harmonious'/'standard' in a Hasse diagram -- only the steepness
matters, not which side it leans to.
'''
from __future__ import annotations

from typing import Sequence

import numpy as np

from .graph_utils import LatticeLayout

# A small set of visually 'nice' slopes: perfectly horizontal (same rank,
# should not normally occur in an upward drawing but is included for
# robustness), 45 degrees (the default expectation for a single Hasse-edge
# step), and perfectly vertical (a strict single-file chain). Callers with a
# house style favoring other slopes (e.g. octilinear 22.5/67.5 degree
# routing) should pass their own set explicitly -- this default is
# intentionally minimal rather than encoding unstated assumptions.
DEFAULT_CANONICAL_ANGLES = (0.0, 45.0, 90.0)


def _unsigned_edge_angles(layout: LatticeLayout) -> np.ndarray:
    positions = layout.positions
    angles = []
    for u, v in layout.graph.edges():
        dx = positions[u][0] - positions[v][0]
        dy = positions[u][1] - positions[v][1]
        if dx == 0 and dy == 0:
            continue
        angles.append(np.degrees(np.arctan2(abs(dy), abs(dx))))
    return np.array(angles)


def _group_within_tolerance(sorted_values: np.ndarray, tolerance: float) -> list:
    '''
    Partition sorted 1-D values into contiguous groups, starting a new
    group whenever a gap exceeds ``tolerance``.

    Equivalent to DBSCAN(eps=tolerance, min_samples=1) on 1-D data, computed
    directly instead of pulling in scikit-learn for what a single sort and
    scan already gives exactly.
    '''
    groups = [[sorted_values[0]]]
    for value in sorted_values[1:]:
        if value - groups[-1][-1] > tolerance:
            groups.append([])
        groups[-1].append(value)
    return groups


def slope_harmony_score(layout: LatticeLayout, angle_tolerance: float = 5.0) -> float:
    '''
    1.0 = every edge shares (up to ``angle_tolerance`` degrees) a common
    slope; lower as edges spread across more, and more evenly populated,
    distinct slopes.

    Uses the normalized entropy of the slope-cluster size distribution
    rather than raw cluster count, so a drawing with one dominant slope and
    a single outlier scores much better than one split evenly across the
    same number of clusters -- cluster count alone can't distinguish those,
    but they read very differently.
    '''
    angles = _unsigned_edge_angles(layout)
    if len(angles) == 0:
        return 1.0
    if len(angles) == 1:
        return 1.0

    groups = _group_within_tolerance(np.sort(angles), angle_tolerance)
    sizes = np.array([len(g) for g in groups], dtype=float)
    if len(sizes) == 1:
        return 1.0

    probs = sizes / sizes.sum()
    entropy = float(-np.sum(probs * np.log(probs)))
    max_entropy = np.log(len(angles))  # entropy if every edge were its own cluster
    return float(1.0 - entropy / max_entropy)


def slope_standard_score(
    layout: LatticeLayout,
    canonical_angles: Sequence[float] = DEFAULT_CANONICAL_ANGLES,
) -> float:
    '''
    1.0 = every edge's slope exactly matches one of ``canonical_angles``;
    0.0 = every edge sits as far as possible (in the worst case, halfway
    between two canonical angles) from all of them.
    '''
    angles = _unsigned_edge_angles(layout)
    if len(angles) == 0:
        return 1.0

    canonicals = np.sort(np.asarray(canonical_angles, dtype=float))
    if len(canonicals) == 1:
        max_dev = 90.0
    else:
        gaps = np.diff(canonicals)
        max_dev = float(np.max(gaps)) / 2.0
        max_dev = max(max_dev, float(canonicals[0]), float(90.0 - canonicals[-1]))

    deviations = np.array([np.min(np.abs(a - canonicals)) for a in angles])
    score = 1.0 - float(np.mean(deviations)) / max_dev
    return float(np.clip(score, 0.0, 1.0))
