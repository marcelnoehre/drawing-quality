'''
Slope metrics.

Standardness and verticality operate on the *unsigned* angle each edge makes
with the horizontal, in [0, 90]: an edge running up-left and its mirror image
running up-right are equally steep, and only the steepness matters there.

Economy and parallelism instead use *signed* directions of cover edges, as in
an additive drawing, where each irreducible gets its own vector and mirror
images are different vectors. Economy asks whether the drawing uses more
directions than the order forces; parallelism asks whether it uses them
consistently, i.e. whether cover edges that are the same step at different
heights (transposed edges, e.g. opposite sides of a covering square) are drawn
parallel.
'''
from __future__ import annotations

from typing import Dict, Hashable, List, Optional, Sequence, Tuple

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

    A companion to slope_economy_score/slope_standard_score's squashed
    numbers, neither of which flags a single near-horizontal edge on its
    own: slope_economy only counts directions (a drawing whose edges all
    share one near-horizontal direction can score a perfect 1.0), and
    slope_standard averages over all edges, so one
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


def _signed_cover_directions(layout: LatticeLayout) -> Dict[Tuple[Hashable, Hashable], float]:
    '''
    Every cover edge u -> v (u < v) mapped to the direction of the drawn
    vector from u to v, in degrees in [0, 360). Signed, unlike the angles
    above: in an additive drawing an edge leaning left and one leaning
    right belong to different irreducibles, so they are different
    directions here. Zero-length edges have no direction and are omitted.
    '''
    positions = layout.positions
    directions = {}
    for u, v in layout.transitive_reduction.edges():
        dx, dy = positions[v] - positions[u]
        if dx == 0 and dy == 0:
            continue
        directions[(u, v)] = float(np.degrees(np.arctan2(dy, dx)) % 360.0)
    return directions


def _angular_difference(a: float, b: float) -> float:
    d = abs(a - b) % 360.0
    return min(d, 360.0 - d)


def _count_direction_clusters(directions: np.ndarray, tolerance: float) -> int:
    '''
    :func:`group_within_tolerance` on the circle: cut it at the widest gap
    between consecutive directions, which no group can usefully span, and
    group the unrolled values as usual.
    '''
    ordered = np.sort(directions)
    gaps = np.diff(np.append(ordered, ordered[0] + 360.0))
    cut = int(np.argmax(gaps)) + 1
    unrolled = np.concatenate([ordered[cut:], ordered[:cut] + 360.0])
    return len(group_within_tolerance(unrolled, tolerance))


def min_direction_count(layout: LatticeLayout) -> int:
    '''
    Lower bound on the number of distinct edge directions in any drawing of
    the order: the largest number of upper or lower covers of one element.
    The cover edges at one element must all point in different directions,
    or they would lie on top of each other.

    Tight for distributive lattices L = O(P): the largest up-degree equals
    width(P), and an additive drawing that gives each chain of a Dilworth
    decomposition of P one vector uses exactly that many directions.
    '''
    cover = layout.transitive_reduction
    return max((max(cover.in_degree(x), cover.out_degree(x)) for x in cover.nodes), default=0)


def slope_economy_score(layout: LatticeLayout, angle_tolerance: float = DEFAULT_ANGLE_TOLERANCE) -> float:
    '''
    k_min / k: the fewest edge directions the order allows
    (:func:`min_direction_count`) over the number of distinct signed
    directions the drawing uses (clusters of diameter ``angle_tolerance``).

    1.0 = the drawing uses no more slopes than the order forces, e.g. a
    vertical chain or an additive drawing of a distributive lattice from a
    minimum chain decomposition; a Boolean lattice B_n is not penalized for
    its n directions. Independent of the number of edges. Clipped at 1.0:
    k < k_min only happens when cover edges at one element are within
    ``angle_tolerance`` of overlapping, which edge_edge_conflict_score
    penalizes instead.
    '''
    directions = _signed_cover_directions(layout)
    if not directions:
        return 1.0
    k = _count_direction_clusters(np.array(list(directions.values())), angle_tolerance)
    return float(min(1.0, min_direction_count(layout) / k))


def transposed_cover_pairs(
    layout: LatticeLayout,
) -> List[Tuple[Tuple[Hashable, Hashable], Tuple[Hashable, Hashable]]]:
    '''
    Every pair of cover edges (u -> v, u' -> v') where u -> v transposes up
    to u' -> v': v meet u' = u and v join u' = v'. Joining with u' maps
    the lower edge onto the upper one and meeting with v maps it back, so
    both are the same step taken at different heights. The sides u -> u'
    and v -> v' need not be covers.

    Includes the opposite sides of every covering square (x, a, b, y):
    x -> a with b -> y, and x -> b with a -> y. Unlike squares alone it
    also pairs edges across pentagons (N5 has no covering square but two
    transposed pairs) and across several squares at once (in a distributive
    lattice, every two comparable edges carrying the same join-irreducible).
    Pairs whose meet or join does not exist (non-lattices) are skipped.
    '''
    cover = layout.transitive_reduction
    closure = layout.transitive_closure
    nodes = list(cover.nodes)
    bit = {x: 1 << i for i, x in enumerate(nodes)}
    down = {x: bit[x] | sum(bit[p] for p in closure.predecessors(x)) for x in nodes}
    up = {x: bit[x] | sum(bit[s] for s in closure.successors(x)) for x in nodes}
    by_down = {mask: x for x, mask in down.items()}
    by_up = {mask: x for x, mask in up.items()}

    pairs = []
    for u, v in cover.edges:
        for w in nodes:
            if w == u or not down[w] & bit[u] or by_down.get(down[v] & down[w]) != u:
                continue
            top = by_up.get(up[v] & up[w])
            if top is not None and cover.has_edge(w, top):
                pairs.append(((u, v), (w, top)))
    return pairs


def slope_parallelism_score(layout: LatticeLayout, angle_tolerance: float = DEFAULT_ANGLE_TOLERANCE) -> float:
    '''
    Share of transposed cover pairs (see :func:`transposed_cover_pairs`)
    drawn parallel, i.e. with signed directions within ``angle_tolerance``
    of each other.

    This generalizes the parallelogram rule of additive drawings, where
    each edge is parallel to the vector of the irreducible that labels it
    and opposite sides of a covering square carry the same label: the
    upper edge of a transposed pair adds exactly what the lower one adds.
    Only directions are compared, never lengths, so the score does not
    ask for additivity itself. Additive drawings of distributive lattices
    score 1.0. For other lattices 1.0 can be unreachable (in M3, 0 -> a
    transposes to both b -> 1 and c -> 1, which cannot be parallel), so
    the score is meant for comparing drawings of the same lattice. Each
    pair is checked on its own, so directions can still drift through a
    chain of pairs that are not themselves transposed. A pair with a
    zero-length edge counts as not parallel. Returns 1.0 when there are no
    transposed pairs (chains).
    '''
    pairs = transposed_cover_pairs(layout)
    if not pairs:
        return 1.0
    directions = _signed_cover_directions(layout)

    def parallel(e: Tuple[Hashable, Hashable], f: Tuple[Hashable, Hashable]) -> bool:
        if e not in directions or f not in directions:
            return False
        return _angular_difference(directions[e], directions[f]) <= angle_tolerance

    return sum(parallel(e, f) for e, f in pairs) / len(pairs)


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
