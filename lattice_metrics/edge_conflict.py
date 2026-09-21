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
angle against the same tolerance :mod:`lattice_metrics.slopes` already uses
as this package's operational definition of 'the same slope' -- two
incident edges closer together than that are exactly the edges
``slope_harmony_score`` would itself cluster as indistinguishable, just now
meeting at a shared point instead of scattered across the drawing.
'''
from __future__ import annotations

from itertools import combinations

from .conflict import distance_conflict_score
from .geometry import unsigned_angle_deg
from .graph_utils import LatticeLayout
from .slopes import DEFAULT_ANGLE_TOLERANCE


def _min_incident_angle(node, layout: LatticeLayout) -> float:
    positions = layout.positions
    p = positions[node]
    tr = layout.transitive_reduction
    neighbors = list(tr.predecessors(node)) + list(tr.successors(node))

    vectors = [positions[u] - p for u in neighbors]
    vectors = [v for v in vectors if float(v @ v) >= 1e-18]
    if len(vectors) < 2:
        return float('inf')

    return min(unsigned_angle_deg(v1, v2) for v1, v2 in combinations(vectors, 2))


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
    min_angles = []
    for node in layout.graph.nodes:
        angle = _min_incident_angle(node, layout)
        if angle != float('inf'):
            min_angles.append(angle)

    if not min_angles:
        return 1.0
    return distance_conflict_score(min_angles, angle_tolerance, floor=0.0)
