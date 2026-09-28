'''
Edge-edge angular conflict (angular resolution).

Two cover edges that share an endpoint but leave it at nearly the same
angle are hard to tell apart right where it matters most -- at the vertex a
reader has to follow one edge away from without confusing it for the
other. This is a distinct failure mode from the drawing's other
angle-related metrics:

- :mod:`lattice_metrics.slopes` scores the drawing's *global* slope
  distribution -- many unrelated edges sharing a common slope is a good,
  legible rhythm when they're spread across the page.
- :mod:`lattice_metrics.crossing_angle` scores *non-incident* edges that
  cross at an interior point (edges sharing an endpoint are explicitly
  excluded there -- that is not a crossing).
- This module scores edges that *do* share an endpoint, where the concern
  is the opposite of slope harmony's: two such edges being close in angle
  concentrates the ambiguity at a single point instead of spreading it
  across the drawing.

Known in the graph-drawing literature as angular resolution (Formann et
al., "Drawing Graphs in the Plane with High Angular Resolution", 1993): the
minimum angle between any two edges incident to the same vertex.
:func:`edge_edge_conflict_score` scores each vertex's own minimum incident
angle against :data:`DEFAULT_ANGLE_TOLERANCE`.
'''
from __future__ import annotations

from itertools import combinations
from typing import List

from .conflict import distance_conflict_min_score, distance_conflict_score
from .geometry import unsigned_angle_deg
from .graph_utils import LatticeLayout

# Deliberately *not* the tolerance :mod:`lattice_metrics.slopes` uses for
# 'the same slope' (5 degrees). That one answers whether two *separate*
# edges read as parallel, and orientation differences of a few degrees are
# already noticeable. This one answers whether two edges leaving the *same*
# point can be told apart, and they overlap near that point: their
# separation at distance r from it is only about r * sin(angle), so edges a
# few degrees apart stay merged, under the node marker and stroke width,
# along much of their length. On this repo's drawings a 5 degree tolerance
# gave 87% of drawings a perfect score, flagging almost only near-collinear
# (< 1 degree) pairs that the node-edge conflict metric already catches.
#
# Kept well below the structural ceiling: a vertex with k upper (or lower)
# covers has to fit those k edges into a half-plane, so some pair of them
# is at most 180 / (k - 1) degrees apart however it is drawn. At 15
# degrees, only vertices with more than 13 covers on one side are
# penalized regardless of how well they are drawn.
DEFAULT_ANGLE_TOLERANCE = 15.0


def _incident_angles(node, layout: LatticeLayout) -> List[float]:
    positions = layout.positions
    p = positions[node]
    tr = layout.transitive_reduction
    neighbors = list(tr.predecessors(node)) + list(tr.successors(node))

    vectors = [positions[u] - p for u in neighbors]
    vectors = [v for v in vectors if float(v @ v) >= 1e-18]
    if len(vectors) < 2:
        return []

    return [unsigned_angle_deg(v1, v2) for v1, v2 in combinations(vectors, 2)]


def _min_incident_angle(node, layout: LatticeLayout) -> float:
    angles = _incident_angles(node, layout)
    return min(angles) if angles else float('inf')


def _vertex_min_angles(layout: LatticeLayout) -> List[float]:
    angles = (_min_incident_angle(node, layout) for node in layout.graph.nodes)
    return [angle for angle in angles if angle != float('inf')]


def edge_edge_conflict_score(
    layout: LatticeLayout,
    angle_tolerance: float = DEFAULT_ANGLE_TOLERANCE,
) -> float:
    '''
    1.0 = at every vertex, every pair of incident cover edges leaves it at
    least ``angle_tolerance`` degrees apart; lower means increasingly
    severe angular ambiguity between edges sharing an endpoint.

    Scored per *vertex*, from each vertex's own minimum pairwise angle
    among its incident edges -- not averaged over every incident pair --
    for the same reason the node-node and node-edge conflict metrics score
    per node from their single nearest threat: a vertex's legibility is
    threatened by its closest pair of edges, not diluted by however many
    other, well-separated pairs also happen to meet there.

    Vertices with fewer than two incident cover edges have no pair to
    compare and are excluded, not counted as a trivial pass or fail.
    Returns 1.0 if no vertex has two or more incident edges.
    '''
    return distance_conflict_score(_vertex_min_angles(layout), angle_tolerance, floor=0.0)


def edge_edge_conflict_min_score(
    layout: LatticeLayout,
    angle_tolerance: float = DEFAULT_ANGLE_TOLERANCE,
) -> float:
    '''
    The worst single vertex's term in :func:`edge_edge_conflict_score`: the
    penalty for the narrowest incident angle in the drawing, on the same
    [0, 1] scale as the score, which is the mean of these per-vertex terms.
    '''
    return distance_conflict_min_score(_vertex_min_angles(layout), angle_tolerance, floor=0.0)
