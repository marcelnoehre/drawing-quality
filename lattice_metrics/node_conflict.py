'''
Node-node proximity conflict.

Two nodes drawn too close together are easy to misread as a single point,
regardless of whether a cover edge connects them -- unlike
:mod:`lattice_metrics.conflict_distance` (a node occluding a *non-incident*
edge), this is a direct node-vs-node collision, and an edge shrunk down to
near-zero length is exactly as much of a fault as two unrelated nodes
drawn on top of each other. This measures how close any two nodes get to
each other, relative to a threshold derived from the drawing's own scale.
'''
from __future__ import annotations

import numpy as np
from scipy.spatial import cKDTree

from .conflict import distance_conflict_score
from .graph_utils import LatticeLayout

DEFAULT_THRESHOLD_FACTOR = 0.5


def nearest_node_distances(layout: LatticeLayout) -> np.ndarray:
    '''
    Every node's distance to its nearest *other* node, whether or not a
    cover edge connects them -- via a k-d tree query, O(n log n) rather
    than a naive O(n^2) all-pairs scan -- in ``layout.positions`` iteration
    order. ``inf`` for every node if there are fewer than two nodes total.

    Shared so every metric that needs 'how close is this node to another
    node' -- currently this one and the clearance-radius computation in
    :mod:`lattice_metrics.nesting` -- answers it the same way instead of
    each re-deriving its own version.
    '''
    n = layout.n
    if n < 2:
        return np.full(n, np.inf)

    coords = np.array(list(layout.positions.values()))
    tree = cKDTree(coords)
    # k=2: a point's own nearest neighbor is itself (distance 0); the
    # second column is the nearest *other* point.
    distances, _ = tree.query(coords, k=2)
    return distances[:, 1]


def node_node_conflict_score(
    layout: LatticeLayout,
    threshold_factor: float = DEFAULT_THRESHOLD_FACTOR,
) -> float:
    '''
    1.0 = every node's nearest other node -- whether or not the two are
    connected by a cover edge -- is at least ``threshold_factor`` times the
    average Hasse-diagram edge length away; lower means increasingly severe
    node-node overlap.

    Scored per node, from each node's nearest-neighbor distance (see
    :func:`nearest_node_distances`), for the same reason
    :func:`~lattice_metrics.conflict_distance.node_edge_conflict_score` is
    scored per node from its nearest edge rather than averaged over every
    pair: a node's legibility is threatened by whichever single other node
    sits closest to it, not diluted by every far-away node that is
    structurally guaranteed to exist in a larger lattice.

    Deliberately does not exclude a node's own cover-edge neighbors from
    the nearest-neighbor search: two adjacent nodes collapsed onto (near)
    the same point are just as unreadable as two unrelated ones, and are
    additionally a degenerate (near-zero-length) edge, not a case to
    exempt.
    '''
    if layout.n < 2:
        return 1.0

    threshold = layout.average_cover_edge_length() * threshold_factor
    return distance_conflict_score(nearest_node_distances(layout), threshold)
