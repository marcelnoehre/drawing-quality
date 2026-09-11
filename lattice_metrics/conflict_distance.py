'''
Node-edge proximity conflict.

A node drawn too close to a (non-incident) Hasse-diagram edge is easy to
misread as lying on that edge. This measures how close nodes get to edges
they are not endpoints of, relative to a threshold derived from the
drawing's own scale.
'''
from __future__ import annotations

from .conflict import distance_conflict_score
from .geometry import point_segment_distance
from .graph_utils import LatticeLayout

DEFAULT_THRESHOLD_FACTOR = 0.5


def node_edge_conflict_score(
    layout: LatticeLayout,
    threshold_factor: float = DEFAULT_THRESHOLD_FACTOR,
) -> float:
    '''
    1.0 = no node comes within ``threshold_factor`` times the average
    Hasse-diagram edge length of a non-incident edge; lower means
    increasingly severe node-edge occlusion.

    Scored per *node*, using each node's distance to its *nearest*
    non-incident edge -- not the mean distance over every non-incident
    edge. A node is occluded by whichever single edge comes closest to it;
    the other m-1 edges being far away is structurally guaranteed (most
    edges live nowhere near most nodes) and carries no information about
    that node's legibility. Averaging over all n*m pairs would let that
    irrelevant majority dilute real conflicts -- for an n-node lattice
    with m cover edges, a single node sitting on top of an edge would only
    cost 1/(n*m) of the score instead of the 1/n it should, so scores
    collapse toward 1.0 and lose discriminative power as lattices grow.
    Taking the nearest edge per node first makes the aggregate's unit of
    account 'is this node's worst threat acceptable', matching the
    perceptual claim in the module docstring.
    '''
    positions = layout.positions
    cover_edges = list(layout.transitive_reduction.edges)
    if not cover_edges:
        return 1.0

    avg_edge_len = layout.average_cover_edge_length()
    threshold = avg_edge_len * threshold_factor

    nearest_distances = []
    for v in positions:
        candidates = [
            point_segment_distance(positions[v], positions[i], positions[j])
            for i, j in cover_edges
            if v != i and v != j
        ]
        if candidates:
            nearest_distances.append(min(candidates))
    return distance_conflict_score(nearest_distances, threshold)
