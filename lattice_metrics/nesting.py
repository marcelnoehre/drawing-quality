'''
Nested suitability: how much uniform clearance the drawing has around every
node.

A drawing has spare room to nest an extra visual element inside each node
(a smaller inset glyph -- e.g. a sub-diagram or an attribute badge) only if
every node can be given a disc of some radius R without that disc
overlapping an equal disc at any other node, crossing a non-incident
Hasse-diagram edge, or spilling past the drawing's own extent. This measures
the largest such R the *worst* node in the layout can support (the
'bottleneck clearance radius'), and scores how it compares to a minimum
useful nesting radius.
'''
from __future__ import annotations

from typing import Tuple

import numpy as np

from .conflict import distance_conflict_score
from .conflict_distance import nearest_non_incident_edge_distances
from .graph_utils import LatticeLayout
from .node_conflict import nearest_node_distances

DEFAULT_R_MIN_NEST_FACTOR = 1 / 3

# Safety margin subtracted from every clearance radius, expressed relative
# to the drawing's own scale like every other threshold in this package.
# Without it a node sitting exactly at its tightest constraint (discs
# touching, not overlapping) would be scored as having strictly positive
# spare room.
DEFAULT_EPSILON_FACTOR = 0.05


def _padded_bounds(layout: LatticeLayout) -> Tuple[np.ndarray, np.ndarray]:
    '''
    Axis-aligned bounding box of all node positions, padded on every side by
    one average cover-edge length.

    The unpadded bounding box is unusable as a 'boundary' reference here:
    every convex-hull vertex of the point set sits exactly on it, so the
    tightest node in any layout with 3+ non-collinear points would always
    have zero boundary clearance. Padding by the drawing's own characteristic
    length gives a canvas margin, matching the scale-relative convention
    used for every other threshold in this package.
    '''
    positions = np.array(list(layout.positions.values()))
    margin = layout.average_cover_edge_length()
    return positions.min(axis=0) - margin, positions.max(axis=0) + margin


def _distance_to_bounds(p: np.ndarray, min_xy: np.ndarray, max_xy: np.ndarray) -> float:
    return float(min(p[0] - min_xy[0], max_xy[0] - p[0], p[1] - min_xy[1], max_xy[1] - p[1]))


def _all_node_clearances(
    layout: LatticeLayout,
    epsilon_factor: float,
    include_boundary: bool = False,
) -> list:
    '''
    R_i - epsilon for every node, where R_i is the largest radius a disc
    centered at that node can have without overlapping an equal disc at
    the nearest other node (d_node / 2), crossing the nearest non-incident
    cover edge (d_edge), or -- if ``include_boundary`` -- spilling past the
    padded drawing boundary (d_bound).

    d_node and d_edge are the same nearest-other-node
    (:func:`~lattice_metrics.node_conflict.nearest_node_distances`) and
    nearest-non-incident-edge
    (:func:`~lattice_metrics.conflict_distance.nearest_non_incident_edge_distances`)
    distances the node-node and node-edge conflict metrics score, so 'how
    close is too close' means the same thing everywhere in this package,
    computed once for every node up front rather than re-derived per node.

    ``include_boundary`` controls whether a node's clearance is also capped
    by distance to the padded drawing boundary. Node/edge conflict alone
    (``include_boundary=False``) answers "how far can every node's radius
    grow before two nodes or a node and an edge collide"; the boundary term
    is a separate, nesting-specific concern (see :func:`_padded_bounds`).
    '''
    if include_boundary:
        min_xy, max_xy = _padded_bounds(layout)
    else:
        min_xy = max_xy = None
    epsilon = epsilon_factor * layout.average_cover_edge_length()

    d_node = nearest_node_distances(layout)
    d_edge = nearest_non_incident_edge_distances(layout)

    clearances = []
    for node, dn in zip(layout.positions, d_node):
        radius = min(float(dn) / 2.0, d_edge[node])
        if min_xy is not None and max_xy is not None:
            radius = min(radius, _distance_to_bounds(layout.positions[node], min_xy, max_xy))
        clearances.append(radius - epsilon)
    return clearances


def bottleneck_clearance_radius(
    layout: LatticeLayout,
    epsilon_factor: float = DEFAULT_EPSILON_FACTOR,
    include_boundary: bool = False,
) -> float:
    '''
    R_uniform = min_i R_i: the tightest per-node clearance radius in the
    whole layout, i.e. the largest radius every node's disc could grow to
    at once before any two nodes overlap or a node's disc crosses a
    non-incident cover edge. Can be negative if some node already has a
    conflict (overlap/crossing) before any growth is added.

    By default this is pure node/edge conflict (``include_boundary=False``):
    it answers "how far can I grow all node radii uniformly before the
    first node-node or node-edge collision", with no reference to the
    canvas extent. Pass ``include_boundary=True`` to additionally cap
    growth at the padded drawing boundary (what :func:`nested_suitability_score`
    uses internally, since an inset glyph spilling off the drawing matters
    for that metric specifically).
    '''
    if layout.n == 0:
        return float('inf')
    return min(_all_node_clearances(layout, epsilon_factor, include_boundary))


def nested_suitability_score(
    layout: LatticeLayout,
    r_min_nest_factor: float = DEFAULT_R_MIN_NEST_FACTOR,
    epsilon_factor: float = DEFAULT_EPSILON_FACTOR,
) -> float:
    '''
    1.0 = every node has at least ``r_min_nest_factor`` times the average
    cover-edge length of *uniform* clearance to spare -- the same single
    shared radius, grown at every node at once, comfortably clears every
    node/node, node/edge, and boundary conflict in the drawing -- falling
    toward 0.0 quadratically as that shared radius shrinks toward zero and
    keeps falling as it goes negative (an actual conflict already exists
    before any nesting is even added), floored at an overlap as deep as
    the fixed ``epsilon_factor`` safety margin itself, so a drawing that's
    just barely touching and one that's overlapping outright are still
    told apart, without requiring the very deep (``r_min_nest``-sized)
    overlap it would take a real drawing tool to ever produce before a
    drawing is treated as fully, unambiguously conflicting.

    Deliberately scores only the single global bottleneck (see
    :func:`bottleneck_clearance_radius`), not an average over individual
    nodes: nesting is a *uniform* radius shared by the whole drawing, so
    the first conflict anywhere -- however isolated -- is the one radius
    that actually matters; it is not diluted by how many other nodes
    happen to be comfortable. One consequence: two drawings whose worst
    conflict is equally deep score the same here even if one has many
    simultaneously-tight nodes and the other just one -- that distinction
    is not this metric's job.

    Unlike a bare call to :func:`bottleneck_clearance_radius`, this *does*
    include the padded drawing boundary as a constraint
    (``include_boundary=True``): a nested inset that would spill off the
    edge of the drawing is not usable, even if it wouldn't collide with
    another node or edge.

    Reuses :func:`lattice_metrics.conflict.distance_conflict_score` -- the
    same documented, already-vetted bounded penalty shape used for
    node-edge conflict -- applied to the single bottleneck radius, rather
    than introducing a new squashing function.
    '''
    if layout.n == 0:
        return 1.0
    r_uniform = bottleneck_clearance_radius(layout, epsilon_factor, include_boundary=True)
    avg = layout.average_cover_edge_length()
    r_min_nest = r_min_nest_factor * avg
    floor = -epsilon_factor * avg
    return distance_conflict_score([r_uniform], r_min_nest, floor=floor)