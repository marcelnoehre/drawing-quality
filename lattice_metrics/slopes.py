'''
Slope harmony and slope standardness.

Both operate on the *unsigned* angle each edge makes with the horizontal, in
[0, 90], since an edge running up-left and its mirror image running up-right
are equally 'harmonious'/'standard' in a Hasse diagram -- only the steepness
matters, not which side it leans to.
'''
from __future__ import annotations

from typing import Optional, Sequence, Tuple

import numpy as np

from .graph_utils import LatticeLayout, group_within_tolerance

DEFAULT_CANONICAL_ANGLES = (
    float(np.degrees(np.arctan(4 / 5))),
    45.0,
    float(np.degrees(np.arctan(3 / 2))),
    90.0,
)

DEFAULT_ANGLE_TOLERANCE = 5.0


def edge_angles_and_lengths(layout: LatticeLayout) -> Tuple[np.ndarray, np.ndarray]:
    '''
    Every edge's unsigned angle from horizontal (in [0, 90]) paired with its
    drawn length, in matching order -- the shared per-edge geometry this
    module and :mod:`lattice_metrics.edge_length` both score. Zero-length
    edges (coincident endpoints) have no defined angle and are skipped.
    '''
    positions = layout.positions
    angles = []
    lengths = []
    for u, v in layout.graph.edges():
        dx = positions[u][0] - positions[v][0]
        dy = positions[u][1] - positions[v][1]
        if dx == 0 and dy == 0:
            continue
        angles.append(float(np.degrees(np.arctan2(abs(dy), abs(dx)))))
        lengths.append(float(np.hypot(dx, dy)))
    return np.array(angles), np.array(lengths)


def _unsigned_edge_angles(layout: LatticeLayout) -> np.ndarray:
    return edge_angles_and_lengths(layout)[0]


def edge_min_slope(layout: LatticeLayout) -> Optional[float]:
    '''
    Minimum edge angle from horizontal (in [0, 90]), or ``None`` if the
    drawing has no (non-degenerate) edges.

    A companion to slope_harmony_score/slope_standard_score's squashed
    numbers, neither of which flags a single near-horizontal edge on its
    own: slope_harmony only cares whether edges agree with *each other*
    (a drawing where every edge is equally near-horizontal scores a
    perfect 1.0), and slope_standard averages over all edges, so one
    horizontal edge among many canonical ones barely moves it. A
    near-horizontal edge is its own distinct
    legibility problem in a Hasse diagram -- the vertical position is
    what signals which endpoint sits above the other in the order -- so
    the single shallowest edge in the drawing is what actually surfaces
    that risk; the average slope has no comparable diagnostic meaning,
    since a merely middling average says nothing about whether any one
    edge is dangerously close to horizontal.
    '''
    angles = _unsigned_edge_angles(layout)
    if len(angles) == 0:
        return None
    return float(np.min(angles))


def slope_verticality_score(layout: LatticeLayout) -> float:
    '''
    1.0 = every edge is drawn at least 45 degrees from horizontal;
    0.0 = some edge is drawn perfectly horizontal. Returns 1.0 for
    layouts with no (non-degenerate) edges, since there is nothing to
    penalize.

    The [0, 1]-normalized counterpart to edge_min_slope, via
    sin(2 * min(theta_min, 45deg)) rather than a linear theta_min / 90
    degree ratio. A 45-degree edge already reads as unambiguous in
    practice -- there is no further legibility to gain from steepening
    it past that point -- so the angle is clamped to 45deg before
    doubling: the score rises from 0 to 1 as theta_min goes from 0 to
    45deg, then stays pinned at 1.0 all the way to 90deg. Doubling the
    (clamped) angle before taking sin(), rather than using theta_min
    directly, is what makes that rise front-loaded -- e.g. a 30-degree
    edge already scores sin(60deg) ~= 0.87 -- so only edges flattening
    toward horizontal are penalized at all.
    '''
    minimum = edge_min_slope(layout)
    if minimum is None:
        return 1.0
    clamped = min(minimum, 45.0)
    return float(np.sin(np.radians(2.0 * clamped)))


def slope_harmony_score(layout: LatticeLayout, angle_tolerance: float = DEFAULT_ANGLE_TOLERANCE) -> float:
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

    groups = group_within_tolerance(np.sort(angles), angle_tolerance)
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
    0.0 = every edge sits as far as possible from all of them -- halfway
    between two neighbouring canonical angles, or at 0 / 90 degrees when
    that is farther from the nearest one (with the defaults, a horizontal
    edge is the worst case, arctan(4/5) ~ 38.7 degrees away).
    '''
    angles = _unsigned_edge_angles(layout)
    if len(angles) == 0:
        return 1.0

    canonicals = np.sort(np.asarray(canonical_angles, dtype=float))
    half_gaps = np.diff(canonicals) / 2.0
    max_dev = max(float(canonicals[0]), float(90.0 - canonicals[-1]), *half_gaps)

    deviations = np.array([np.min(np.abs(a - canonicals)) for a in angles])
    score = 1.0 - float(np.mean(deviations)) / max_dev
    return float(np.clip(score, 0.0, 1.0))
