'''
Node-node proximity conflict.

Two nodes that are drawn too close together (relative to the typical edge
length in the drawing) are hard to tell apart. This measures how close the
closest pairs get, relative to a threshold derived from the drawing's own
scale.
'''
from __future__ import annotations

from itertools import combinations

import numpy as np

from .conflict import distance_conflict_score
from .graph_utils import LatticeLayout

DEFAULT_THRESHOLD_FACTOR = 0.5


def node_conflict_distance_score(
    layout: LatticeLayout,
    threshold_factor: float = DEFAULT_THRESHOLD_FACTOR,
) -> float:
    '''
    1.0 = no two nodes are closer than ``threshold_factor`` times the
    average Hasse-diagram edge length; lower means increasingly severe
    node-node overlap.
    '''
    positions = layout.positions
    nodes = list(positions)
    if len(nodes) < 2:
        return 1.0

    avg_edge_len = layout.average_cover_edge_length()
    threshold = avg_edge_len * threshold_factor

    distances = [
        float(np.linalg.norm(positions[a] - positions[b]))
        for a, b in combinations(nodes, 2)
    ]
    return distance_conflict_score(distances, threshold)
