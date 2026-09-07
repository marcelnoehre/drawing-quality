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
    '''
    positions = layout.positions
    cover_edges = list(layout.transitive_reduction.edges)
    if not cover_edges:
        return 1.0

    avg_edge_len = layout.average_cover_edge_length()
    threshold = avg_edge_len * threshold_factor

    distances = [
        point_segment_distance(positions[v], positions[i], positions[j])
        for v in positions
        for i, j in cover_edges
        if v != i and v != j
    ]
    return distance_conflict_score(distances, threshold)
