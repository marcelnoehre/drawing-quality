'''
Nested suitability: how much uniform clearance the drawing has around every
node.

A drawing has spare room to nest an extra visual element inside each node
(a smaller inset glyph -- e.g. a sub-diagram or an attribute badge) only if
every node can be given a disc of some radius R without that disc
overlapping an equal disc at any other node or crossing a non-incident
Hasse-diagram edge. This measures the largest such R the *worst* node in
the layout can support (the 'bottleneck clearance radius'), and scores how
it compares to a minimum useful nesting radius.
'''
from __future__ import annotations

from .conflict import distance_conflict_score
from .conflict_distance import nearest_non_incident_edge_distances
from .graph_utils import LatticeLayout
from .node_conflict import nearest_node_distances

# Half the average cover-edge length: a nested disc whose diameter matches
# an average edge. A node's disc radius is capped at d_node / 2 -- half the
# way to its nearest other node, whose equal disc takes the other half --
# so this radius fits at every node only when every nearest-node distance
# is at least one average edge length, twice the node-node conflict
# threshold. Nesting therefore asks for more room than merely avoiding
# node-node conflict does.
#
# This also ties the score to edge-length uniformity: a node's cover
# neighbors are at distance equal to the edge length, so
# R_uniform <= (shortest cover edge) / 2 in any drawing, and a perfect
# score requires the shortest edge to be at least 2 * r_min_nest_factor
# times the average -- at 1/2, every cover edge at least as long as the
# average, i.e. all cover edges of equal length.
DEFAULT_R_MIN_NEST_FACTOR = 0.5


def bottleneck_clearance_radius(layout: LatticeLayout) -> float:
    '''
    R_uniform = min_i R_i: the tightest per-node clearance radius in the
    whole layout, i.e. the largest radius every node's disc could grow to
    at once before any two nodes' discs overlap or a node's disc crosses a
    non-incident cover edge.

    R_i = min(d_node / 2, d_edge), where d_node and d_edge are the same
    nearest-other-node
    (:func:`~lattice_metrics.node_conflict.nearest_node_distances`) and
    nearest-non-incident-edge
    (:func:`~lattice_metrics.conflict_distance.nearest_non_incident_edge_distances`)
    distances the node-node and node-edge conflict metrics score, so 'how
    close is too close' means the same thing everywhere in this package.
    Edges incident to a node are not a constraint: they end at that node,
    so they pass through its disc regardless of the radius.

    Always >= 0, since nodes are points and both distances are
    non-negative; 0 exactly when two nodes coincide or a node lies on a
    non-incident edge. ``inf`` for a layout with no node that has either
    another node or a non-incident edge to be constrained by.
    '''
    if layout.n == 0:
        return float('inf')

    d_node = nearest_node_distances(layout)
    d_edge = nearest_non_incident_edge_distances(layout)
    return min(
        min(float(dn) / 2.0, d_edge[node])
        for node, dn in zip(layout.positions, d_node)
    )


def nested_suitability_score(
    layout: LatticeLayout,
    r_min_nest_factor: float = DEFAULT_R_MIN_NEST_FACTOR,
) -> float:
    '''
    1.0 = every node has at least ``r_min_nest_factor`` times the average
    cover-edge length of *uniform* clearance to spare -- the same single
    shared radius, grown at every node at once, clears every node/node and
    node/edge conflict in the drawing -- falling toward 0.0 quadratically as
    that shared radius shrinks, and reaching 0.0 exactly when two nodes
    coincide or a node lies on a non-incident edge.

    Deliberately scores only the single global bottleneck (see
    :func:`bottleneck_clearance_radius`), not an average over individual
    nodes: nesting is a *uniform* radius shared by the whole drawing, so
    the first conflict anywhere -- however isolated -- is the one radius
    that actually matters; it is not diluted by how many other nodes
    happen to be comfortable. One consequence: two drawings whose worst
    conflict is equally deep score the same here even if one has many
    simultaneously-tight nodes and the other just one -- that distinction
    is not this metric's job.

    Reuses :func:`lattice_metrics.conflict.distance_conflict_score` -- the
    same documented bounded penalty shape used for the conflict metrics --
    applied to the single bottleneck radius, rather than introducing a new
    squashing function.
    '''
    if layout.n == 0:
        return 1.0
    r_uniform = bottleneck_clearance_radius(layout)
    r_min_nest = r_min_nest_factor * layout.average_cover_edge_length()
    return distance_conflict_score([r_uniform], r_min_nest)
