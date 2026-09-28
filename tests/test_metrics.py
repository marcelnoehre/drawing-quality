'''
Metrics are validated against synthetic layouts with a known-good or
known-bad geometric property, rather than only checking they run. Each test
asserts the metric responds in the correct *direction* to a targeted
perturbation, which is what actually matters for trusting the numbers.
'''
from itertools import combinations

import networkx as nx
import numpy as np
import pytest

from lattice_metrics.chains import visual_chain_linearity_score
from lattice_metrics.conflict import distance_conflict_min_score, distance_conflict_score
from lattice_metrics.conflict_distance import (
    DEFAULT_THRESHOLD_FACTOR,
    nearest_non_incident_edge_distances,
    node_edge_conflict_min_score,
    node_edge_conflict_score,
)
from lattice_metrics.geometry import find_crossings, point_segment_distance, unsigned_angle_deg
from lattice_metrics.crossing_angle import crossing_angle_min_score, crossing_angle_score
from lattice_metrics.edge_conflict import DEFAULT_ANGLE_TOLERANCE as EDGE_CONFLICT_ANGLE_TOLERANCE
from lattice_metrics.edge_conflict import edge_edge_conflict_min_score, edge_edge_conflict_score
from lattice_metrics.edge_crossings import edge_crossing_score
from lattice_metrics.edge_length import edge_length_uniformity_score
from lattice_metrics.graph_utils import LatticeLayout, freese_ranks
from lattice_metrics.layering import layer_consistency_score
from lattice_metrics.nesting import bottleneck_clearance_radius, nested_suitability_score
from lattice_metrics.node_conflict import DEFAULT_THRESHOLD_FACTOR as NODE_CONFLICT_THRESHOLD_FACTOR
from lattice_metrics.node_conflict import nearest_node_distances, node_node_conflict_min_score, node_node_conflict_score
from lattice_metrics.slopes import (
    DEFAULT_ANGLE_TOLERANCE,
    edge_min_slope,
    slope_harmony_score,
    slope_standard_score,
    slope_verticality_score,
)
from lattice_metrics.symmetry import vertical_axis_balance_score


def layout_of(edges, positions) -> LatticeLayout:
    g = nx.DiGraph()
    g.add_nodes_from(positions)
    g.add_edges_from(edges)
    pos = {n: np.array(p, dtype=float) for n, p in positions.items()}
    return LatticeLayout(graph=g, positions=pos)


CHAIN_EDGES = [('a', 'b'), ('b', 'c'), ('c', 'd')]

DIAMOND_EDGES = [('a', 'b'), ('a', 'c'), ('b', 'd'), ('c', 'd')]


# ---------------------------------------------------------------- chains ---

def test_straight_chain_is_perfectly_linear():
    layout = layout_of(CHAIN_EDGES, {'a': (0, 3), 'b': (0, 2), 'c': (0, 1), 'd': (0, 0)})
    assert visual_chain_linearity_score(layout) == pytest.approx(1.0)


def test_bent_chain_scores_lower_than_straight_chain():
    straight = layout_of(CHAIN_EDGES, {'a': (0, 3), 'b': (0, 2), 'c': (0, 1), 'd': (0, 0)})
    bent = layout_of(CHAIN_EDGES, {'a': (0, 3), 'b': (2, 2), 'c': (0, 1), 'd': (0, 0)})
    assert visual_chain_linearity_score(bent) < visual_chain_linearity_score(straight)


def test_u_turn_chain_is_worst_case_zero():
    # a-b-c-d zigzags between y=1 and y=0: both b and c see their
    # predecessor and successor on the *same side*, i.e. the path folds
    # completely back on itself at every interior vertex.
    layout = layout_of(CHAIN_EDGES, {'a': (0, 1), 'b': (0, 0), 'c': (0, 1), 'd': (0, -1)})
    assert visual_chain_linearity_score(layout) == pytest.approx(0.0)


def test_no_interior_vertex_returns_one():
    layout = layout_of([('a', 'b')], {'a': (0, 1), 'b': (0, 0)})
    assert visual_chain_linearity_score(layout) == 1.0


# v has two predecessors (a: straight below v, e: off to the side) but only
# one successor (b, straight above v). The smaller side (b, the lone
# successor) has a perfectly straight partner in a, so the extra off-axis
# predecessor e -- which can never be simultaneously collinear with b -- must
# not drag the score down.
TWO_PREDS_ONE_SUCC_EDGES = [('a', 'v'), ('e', 'v'), ('v', 'b')]


def test_off_axis_extra_predecessor_does_not_penalize_straight_match():
    layout = layout_of(
        TWO_PREDS_ONE_SUCC_EDGES,
        {'a': (0, -1), 'v': (0, 0), 'b': (0, 1), 'e': (1, -1)},
    )
    assert visual_chain_linearity_score(layout) == pytest.approx(1.0)


def test_smaller_side_still_penalized_when_no_good_match_exists():
    # Neither predecessor lines up with the lone successor b at all.
    layout = layout_of(
        TWO_PREDS_ONE_SUCC_EDGES,
        {'a': (1, -1), 'v': (0, 0), 'b': (0, 1), 'e': (-1, -1)},
    )
    assert visual_chain_linearity_score(layout) < 1.0


# ------------------------------------------------------------- crossings ---

def test_no_possible_crossings_in_a_chain():
    layout = layout_of(CHAIN_EDGES, {'a': (0, 3), 'b': (0, 2), 'c': (0, 1), 'd': (0, 0)})
    assert edge_crossing_score(layout) == 1.0


# A single diamond has no pair of edges with all-incomparable endpoints (a
# and d are comparable to everything), so it can never have an 'avoidable'
# crossing under this metric's definition -- exercising edge_crossing_score
# needs two genuinely disjoint, mutually incomparable 2-chains instead.
DISJOINT_CHAINS_EDGES = [('w1', 'x1'), ('w2', 'x2')]


def test_crossing_disjoint_chains_scores_below_planar_layout():
    planar = layout_of(DISJOINT_CHAINS_EDGES, {'w1': (0, 0), 'x1': (0, 1), 'w2': (2, 0), 'x2': (2, 1)})
    crossed = layout_of(DISJOINT_CHAINS_EDGES, {'w1': (0, 0), 'x1': (2, 1), 'w2': (2, 0), 'x2': (0, 1)})
    assert edge_crossing_score(planar) == pytest.approx(1.0)
    assert edge_crossing_score(crossed) == pytest.approx(0.0)


def test_perpendicular_crossing_scores_higher_than_near_parallel():
    perpendicular = layout_of(
        [('p1', 'p3'), ('p2', 'p4')],
        {'p1': (0, 0), 'p3': (1, 1), 'p2': (1, 0), 'p4': (0, 1)},
    )
    # two long, nearly-horizontal segments crossing at a shallow angle
    near_parallel = layout_of(
        [('p1', 'p3'), ('p2', 'p4')],
        {'p1': (-1, -0.05), 'p3': (1, 0.05), 'p2': (-1, 0.05), 'p4': (1, -0.05)},
    )
    assert crossing_angle_score(perpendicular) > crossing_angle_score(near_parallel)


def test_crossing_angle_min_score_one_when_no_crossings():
    layout = layout_of(CHAIN_EDGES, {'a': (0, 3), 'b': (0, 2), 'c': (0, 1), 'd': (0, 0)})
    assert crossing_angle_min_score(layout) == pytest.approx(1.0)


def test_crossing_angle_min_score_is_sharpest_crossing_on_score_scale():
    '''
    A right-angle crossing and a far-away near-parallel one: the score is
    the mean of the per-crossing terms angle / 90, the min score the
    sharpest crossing's term -- so min <= score, with equality only when
    every crossing is equally sharp.
    '''
    edges = [
        ('a1', 'a2'), ('b1', 'b2'),  # a right-angle crossing
        ('c1', 'c2'), ('d1', 'd2'),  # a near-parallel crossing, far away and unrelated
    ]
    positions = {
        'a1': (0, 0), 'a2': (1, 1),
        'b1': (0, 1), 'b2': (1, 0),
        'c1': (100, 0), 'c2': (101, 0.02),
        'd1': (100, 0.02), 'd2': (101, 0),
    }
    layout = layout_of(edges, positions)
    pos = layout.positions

    expected_angles = []
    for crossing in find_crossings(edges, pos):
        d1 = pos[crossing.edge_a[1]] - pos[crossing.edge_a[0]]
        d2 = pos[crossing.edge_b[1]] - pos[crossing.edge_b[0]]
        angle = unsigned_angle_deg(d1, d2)
        expected_angles.append(min(angle, 180.0 - angle))
    assert len(expected_angles) == 2
    assert min(expected_angles) < 10.0 < max(expected_angles)  # genuinely different severities

    assert crossing_angle_score(layout) == pytest.approx(np.mean(expected_angles) / 90.0)
    assert crossing_angle_min_score(layout) == pytest.approx(min(expected_angles) / 90.0)


def test_crossing_angle_min_score_treats_overlapping_edges_as_worst_case():
    # a1-a2 and b1-b2 lie on the same line and overlap along a sub-segment
    # rather than crossing at a single point -- the worst case, per
    # crossing_angle_score's own docstring.
    edges = [('a1', 'a2'), ('b1', 'b2')]
    positions = {'a1': (0, 0), 'a2': (2, 0), 'b1': (1, 0), 'b2': (3, 0)}
    layout = layout_of(edges, positions)
    assert crossing_angle_min_score(layout) == pytest.approx(0.0)


# -------------------------------------------------------------- layering ---

def test_same_rank_nodes_aligned_scores_higher():
    aligned = layout_of(DIAMOND_EDGES, {'a': (0, 2), 'b': (-1, 1), 'c': (1, 1), 'd': (0, 0)})
    staggered = layout_of(DIAMOND_EDGES, {'a': (0, 2), 'b': (-1, 1), 'c': (1, -3), 'd': (0, -5)})
    assert layer_consistency_score(aligned) == pytest.approx(1.0)
    assert layer_consistency_score(staggered) < layer_consistency_score(aligned)

UNGRADED_EDGES = [('a', 'b'), ('a', 'c'), ('b', 'd'), ('d', 'e'), ('c', 'e')]

def test_freese_ranks_match_height_minus_depth_plus_m_formula():
    g = nx.DiGraph()
    g.add_nodes_from(['a', 'b', 'c', 'd', 'e'])
    g.add_edges_from(UNGRADED_EDGES)
    assert freese_ranks(g) == {'a': 0, 'b': 2, 'c': 3, 'd': 4, 'e': 6}

def test_layer_consistency_uses_freese_rank_not_longest_path():
    positions = {'a': (0, 3), 'b': (0, 2), 'c': (0, 1.5), 'd': (0, 1), 'e': (0, 0)}
    layout = layout_of(UNGRADED_EDGES, positions)
    assert layer_consistency_score(layout) == pytest.approx(1.0)

def test_layer_consistency_penalizes_bad_layout_even_with_all_distinct_ranks():
    # A chain gives every node a distinct Freese rank, so there is nothing
    # to compare *within* a rank group -- the score must instead check that
    # the coordinate tracks rank order/spacing, not just default to 1.0.
    ranks = freese_ranks(nx.DiGraph(CHAIN_EDGES))
    assert len(set(ranks.values())) == len(ranks)  # sanity check: no ties

    ordered = layout_of(CHAIN_EDGES, {'a': (0, 3), 'b': (0, 2), 'c': (0, 1), 'd': (0, 0)})
    scrambled = layout_of(CHAIN_EDGES, {'a': (0, 1), 'b': (0, 3), 'c': (0, 0), 'd': (0, 2)})
    assert layer_consistency_score(ordered) == pytest.approx(1.0)
    assert layer_consistency_score(scrambled) < 1.0

def test_layer_consistency_zero_when_distinct_ranks_collapse_to_one_coordinate():
    layout = layout_of(CHAIN_EDGES, {'a': (0, 0), 'b': (0, 0), 'c': (0, 0), 'd': (0, 0)})
    assert layer_consistency_score(layout) == pytest.approx(0.0)

# --------------------------------------------------------------- overlap ---

def test_node_on_top_of_edge_scores_lower():
    clear = layout_of(DIAMOND_EDGES, {'a': (0, 2), 'b': (-1, 1), 'c': (1, 1), 'd': (0, 0)})
    # move c onto the a-b edge's midpoint (c is not incident to a-b)
    on_edge = layout_of(DIAMOND_EDGES, {'a': (0, 2), 'b': (-2, 0), 'c': (-1, 1), 'd': (0, 0)})
    assert node_edge_conflict_score(on_edge) < node_edge_conflict_score(clear)


def test_node_edge_conflict_uses_nearest_edge_per_node_not_mean_over_all_pairs():
    '''
    A node's conflict score must be driven by its single nearest
    non-incident edge. Averaging over *every* non-incident edge instead
    (most of which are structurally guaranteed to be far away and
    irrelevant) dilutes a real conflict by a factor of roughly the edge
    count -- regression test for that dilution bug.
    '''
    on_edge = layout_of(DIAMOND_EDGES, {'a': (0, 2), 'b': (-2, 0), 'c': (-1, 1), 'd': (0, 0)})
    positions = on_edge.positions
    cover_edges = list(on_edge.transitive_reduction.edges)
    threshold = on_edge.average_cover_edge_length() * DEFAULT_THRESHOLD_FACTOR

    all_pairs = [
        point_segment_distance(positions[v], positions[i], positions[j])
        for v in positions for i, j in cover_edges if v != i and v != j
    ]
    diluted_by_mean_over_all_pairs = distance_conflict_score(all_pairs, threshold)
    assert node_edge_conflict_score(on_edge) < diluted_by_mean_over_all_pairs


def test_node_edge_conflict_min_score_one_when_no_conflict():
    layout = layout_of(DIAMOND_EDGES, {'a': (0, 2), 'b': (-1, 1), 'c': (1, 1), 'd': (0, 0)})
    assert node_edge_conflict_min_score(layout) == pytest.approx(1.0)


def test_node_edge_conflict_min_score_is_worst_node_on_score_scale():
    '''
    Two nodes crowd edges to different degrees: the score is the mean of
    the per-node penalty terms, the min score the worst node's term.
    '''
    edges = [('p1', 'p2'), ('p3', 'p4')]
    positions = {
        'p1': (-5, 0), 'p2': (5, 0),
        'p3': (-5, 6), 'p4': (5, 6),
        'v': (0, 1),  # close to p1-p2
        'w': (3, 5.8),  # very close to p3-p4
    }
    layout = layout_of(edges, positions)
    threshold = layout.average_cover_edge_length() * DEFAULT_THRESHOLD_FACTOR
    nearest = [d for d in nearest_non_incident_edge_distances(layout).values() if d != float('inf')]

    terms = [1.0 - max(0.0, 1.0 - d / threshold) ** 2 for d in nearest]
    assert min(terms) < max(t for t in terms if t < 1.0) < 1.0  # two conflicts, different severities
    assert node_edge_conflict_score(layout) == pytest.approx(np.mean(terms))
    assert node_edge_conflict_min_score(layout) == pytest.approx(min(terms))


# --------------------------------------------------------- node overlap ---

def test_well_separated_nodes_score_one():
    layout = layout_of(DIAMOND_EDGES, {'a': (0, 0), 'b': (-2, 2), 'c': (2, 2), 'd': (0, 4)})
    assert node_node_conflict_score(layout) == pytest.approx(1.0)


def test_incident_nodes_collapsed_together_are_penalized():
    # a and b are connected by a cover edge shrunk to near-zero length,
    # while every other edge in the diagram stays a normal size -- an edge
    # collapsing its own endpoints together is exactly the kind of
    # node-node conflict this metric should catch, not exempt just because
    # the two nodes are incident.
    layout = layout_of(DIAMOND_EDGES, {'a': (0, 0), 'b': (0, 0.001), 'c': (2, 2), 'd': (0, 4)})
    assert node_node_conflict_score(layout) < 1.0


def test_non_incident_nodes_too_close_are_penalized_even_when_far_from_every_edge():
    # z1 and z2 are not connected to anything and sit nowhere near the
    # single real edge (w1-w2), so node_edge_conflict_score sees nothing
    # wrong -- but z1 and z2 are drawn almost on top of each other, which
    # node_node_conflict_score must still catch.
    edges = [('w1', 'w2')]
    positions = {'w1': (0, 0), 'w2': (0, 4), 'z1': (20, 20), 'z2': (20.01, 20)}
    layout = layout_of(edges, positions)
    assert node_edge_conflict_score(layout) == pytest.approx(1.0)
    assert node_node_conflict_score(layout) < 1.0


def test_node_node_conflict_uses_nearest_node_per_node_not_mean_over_all_pairs():
    '''
    Mirrors the node-edge dilution regression test above: a node's score
    must be driven by its single nearest other node, not averaged over
    every other node in the layout (most of which are structurally
    guaranteed to be irrelevant in a larger lattice).
    '''
    layout = layout_of(DIAMOND_EDGES, {'a': (0, 0), 'b': (0, 0.001), 'c': (2, 2), 'd': (0, 4)})
    positions = layout.positions
    threshold = layout.average_cover_edge_length() * NODE_CONFLICT_THRESHOLD_FACTOR

    all_pairs = [
        float(np.linalg.norm(positions[u] - positions[v]))
        for u in positions for v in positions if u != v
    ]
    diluted_by_mean_over_all_pairs = distance_conflict_score(all_pairs, threshold)
    assert node_node_conflict_score(layout) < diluted_by_mean_over_all_pairs


def test_node_node_conflict_min_score_one_when_no_conflict():
    layout = layout_of(DIAMOND_EDGES, {'a': (0, 0), 'b': (-2, 2), 'c': (2, 2), 'd': (0, 4)})
    assert node_node_conflict_min_score(layout) == pytest.approx(1.0)


def test_node_node_conflict_min_score_is_closest_pair_on_score_scale():
    '''
    Two node pairs overlap to different degrees: the score is the mean of
    the per-node penalty terms, the min score the closest pair's term.
    '''
    edges = [('w1', 'w2')]
    positions = {
        'w1': (0, 0), 'w2': (0, 10),
        'z1': (20, 20), 'z2': (20.5, 20),  # close
        'y1': (40, 40), 'y2': (43, 40),  # less close
    }
    layout = layout_of(edges, positions)
    threshold = layout.average_cover_edge_length() * NODE_CONFLICT_THRESHOLD_FACTOR

    terms = [1.0 - max(0.0, 1.0 - d / threshold) ** 2 for d in nearest_node_distances(layout)]
    assert min(terms) < max(t for t in terms if t < 1.0) < 1.0  # two conflicts, different severities
    assert node_node_conflict_score(layout) == pytest.approx(np.mean(terms))
    assert node_node_conflict_min_score(layout) == pytest.approx(min(terms))


# ----------------------------------------------------------------- slope ---

def test_uniform_slopes_score_higher_than_mixed():
    uniform = layout_of(DIAMOND_EDGES, {'a': (0, 2), 'b': (-1, 1), 'c': (1, 1), 'd': (0, 0)})
    mixed = layout_of(DIAMOND_EDGES, {'a': (0, 2), 'b': (-5, 1), 'c': (1, 1.9), 'd': (0, 0)})
    assert slope_harmony_score(uniform) > slope_harmony_score(mixed)


def test_forty_five_degree_edges_are_maximally_standard():
    layout = layout_of([('a', 'b')], {'a': (0, 1), 'b': (1, 0)})
    assert slope_standard_score(layout) == pytest.approx(1.0)


def test_off_canonical_slope_scores_below_one():
    layout = layout_of([('a', 'b')], {'a': (0, 1), 'b': (2, 0.3)})
    assert slope_standard_score(layout) < 1.0


def test_horizontal_edge_is_least_standard():
    # 0 degrees is not canonical; the nearest canonical angle is arctan(4/5),
    # which is also the worst-case deviation, so a horizontal edge scores 0.
    layout = layout_of([('a', 'b')], {'a': (0, 0), 'b': (1, 0)})
    assert slope_standard_score(layout) == pytest.approx(0.0)


def test_slope_standard_known_value():
    # Edges at 45 (deviation 0) and arctan(4/5)/2 (deviation half the worst
    # case): mean normalized deviation 1/4.
    half = np.arctan(4 / 5) / 2
    layout = layout_of(
        [('a', 'b'), ('c', 'd')],
        {'a': (0, 1), 'b': (1, 0), 'c': (0, np.sin(half)), 'd': (np.cos(half), 0)},
    )
    assert slope_standard_score(layout) == pytest.approx(0.75)


def test_single_canonical_angle_uses_farther_end_as_worst_case():
    # With canonical {45}, the worst deviation is 45 (at 0 or 90), not 90.
    layout = layout_of([('a', 'b')], {'a': (0, 0), 'b': (1, 0)})
    assert slope_standard_score(layout, canonical_angles=(45.0,)) == pytest.approx(0.0)


def test_edge_min_slope_none_when_no_edges():
    layout = layout_of([], {'a': (0, 0)})
    assert edge_min_slope(layout) is None


def test_edge_min_slope_reports_min_angle_from_horizontal():
    '''
    Neither slope_harmony_score (only cares whether edges agree with each
    other) nor slope_standard_score (averages over all edges) flags a
    single near-horizontal edge on its own -- the minimum here is what actually surfaces that risk, since a
    near-horizontal edge in a Hasse diagram makes it hard to tell which
    endpoint sits above the other in the order.
    '''
    edges = [('r', 'a'), ('r', 'b'), ('r', 'c')]
    positions = {'r': (0, 0), 'a': (10, 10), 'b': (10, 1), 'c': (1, 10)}
    layout = layout_of(edges, positions)
    pos = layout.positions

    expected_angles = [
        float(np.degrees(np.arctan2(abs(pos[u][1] - pos[v][1]), abs(pos[u][0] - pos[v][0]))))
        for u, v in edges
    ]
    minimum = edge_min_slope(layout)
    assert minimum == pytest.approx(min(expected_angles))
    assert minimum < 10.0  # (r, b) is nearly horizontal and should be what this flags


def test_slope_verticality_score_no_edges_is_perfect():
    layout = layout_of([], {'a': (0, 0)})
    assert slope_verticality_score(layout) == pytest.approx(1.0)


def test_slope_verticality_score_vertical_edge_is_perfect():
    layout = layout_of([('a', 'b')], {'a': (0, 1), 'b': (0, 0)})
    assert slope_verticality_score(layout) == pytest.approx(1.0)


def test_slope_verticality_score_horizontal_edge_is_zero():
    layout = layout_of([('a', 'b')], {'a': (0, 0.001), 'b': (1, 0)})
    assert slope_verticality_score(layout) == pytest.approx(0.0, abs=2e-3)


def test_slope_verticality_score_matches_sine_of_doubled_clamped_edge_min_slope():
    edges = [('r', 'a'), ('r', 'b'), ('r', 'c')]
    positions = {'r': (0, 0), 'a': (10, 10), 'b': (10, 1), 'c': (1, 10)}
    layout = layout_of(edges, positions)
    clamped = min(edge_min_slope(layout), 45.0)
    expected = np.sin(np.radians(2.0 * clamped))
    assert slope_verticality_score(layout) == pytest.approx(expected)


def test_slope_verticality_score_forty_five_degrees_is_perfect():
    # A 45-degree edge already reads as unambiguous, so it should score
    # a full 1.0 rather than being flatly halved by a linear theta/90
    # degree ratio.
    layout = layout_of([('a', 'b')], {'a': (0, 1), 'b': (1, 0)})
    assert slope_verticality_score(layout) == pytest.approx(1.0)


def test_slope_verticality_score_steeper_than_forty_five_stays_perfect():
    # Angles beyond 45 degrees are clamped before doubling, so a
    # 60-degree edge (which would otherwise fall past the sin(2*theta)
    # peak) still scores a full 1.0, matching a vertical edge.
    layout = layout_of([('a', 'b')], {'a': (0, np.sqrt(3)), 'b': (1, 0)})
    assert slope_verticality_score(layout) == pytest.approx(1.0)


# ---------------------------------------------------------- edge length ---

def test_uniform_same_slope_edges_score_one():
    # All four cover edges share the same 45-degree slope and the same
    # length by construction.
    layout = layout_of(DIAMOND_EDGES, {'a': (0, 0), 'b': (-1, 1), 'c': (1, 1), 'd': (0, 2)})
    assert edge_length_uniformity_score(layout) == pytest.approx(1.0)


def test_different_slopes_at_same_layer_are_not_penalized():
    # d has four cover edges at two distinct slopes (~33.7 and ~81.5
    # degrees), each pair internally identical in length. A naive
    # whole-diagram length check would flag this (lengths range from ~2.0
    # to ~3.6), but that variation is exactly what different slopes at a
    # fixed vertical span *require* -- not a drawing flaw -- so grouping by
    # slope first should still score this perfectly uniform.
    edges = [('d', 'b1'), ('d', 'b2'), ('d', 'c1'), ('d', 'c2')]
    positions = {
        'd': (0, 4),
        'b1': (-3, 2), 'b2': (3, 2),      # dx=3, dy=2 -> ~33.7 deg, len ~3.606
        'c1': (-0.3, 2), 'c2': (0.3, 2),  # dx=0.3, dy=2 -> ~81.5 deg, len ~2.022
    }
    layout = layout_of(edges, positions)
    assert edge_length_uniformity_score(layout) == pytest.approx(1.0)


def test_length_variation_within_a_shared_slope_is_penalized():
    # b1 and b2 share the exact same slope (dy/dx = 2/3 for both) but b2 is
    # half the length of b1 -- unlike the previous test, this variation
    # can't be explained away by a slope difference, so it should cost.
    edges = [('d', 'b1'), ('d', 'b2')]
    positions = {'d': (0, 4), 'b1': (-3, 2), 'b2': (1.5, 3)}
    layout = layout_of(edges, positions)
    assert edge_length_uniformity_score(layout) < 1.0


def test_lone_outlier_slope_does_not_drag_down_a_uniform_majority():
    # Three edges share a 45-degree slope and an identical length; a fourth
    # edge at a very different, unmatched slope and a wildly different
    # length has nothing to be compared against, so it can't be scored and
    # must not drag the (otherwise perfectly uniform) result down.
    edges = [('d', 'p1'), ('p1', 'q'), ('d', 'p2'), ('d', 'r')]
    positions = {
        'd': (0, 4),
        'p1': (-1, 3), 'q': (-2, 2), 'p2': (1, 3),  # all 45 deg, length sqrt(2)
        'r': (50, 0),                                # ~4.6 deg, length ~50.2
    }
    layout = layout_of(edges, positions)
    assert edge_length_uniformity_score(layout) == pytest.approx(1.0)


def test_no_edges_returns_one():
    layout = layout_of([], {'a': (0, 0)})
    assert edge_length_uniformity_score(layout) == 1.0


# --------------------------------------------------------- edge conflict ---

def test_well_spread_incident_edges_score_one():
    # At every vertex of a symmetric diamond, the two incident cover edges
    # meet at 90 degrees.
    layout = layout_of(DIAMOND_EDGES, {'a': (0, 0), 'b': (-1, 1), 'c': (1, 1), 'd': (0, 2)})
    assert edge_edge_conflict_score(layout) == pytest.approx(1.0)


NEAR_PARALLEL_EDGES = [('bottom', 'p1'), ('bottom', 'p2')]
NEAR_PARALLEL_POSITIONS = {'bottom': (0, 0), 'p1': (1, 10), 'p2': (1.02, 10)}


def test_near_parallel_incident_edges_penalized():
    # p1 and p2 both leave 'bottom' at nearly the same angle (< 2 degrees
    # apart) -- exactly the angular ambiguity this metric exists to catch.
    layout = layout_of(NEAR_PARALLEL_EDGES, NEAR_PARALLEL_POSITIONS)
    assert edge_edge_conflict_score(layout) < 1.0


def test_catches_what_slope_harmony_does_not():
    # slope_harmony_score *rewards* p1 and p2 for sharing (almost) the same
    # slope -- with only one slope cluster in the whole drawing, it scores
    # a perfect 1.0. But the two edges meet at a single shared vertex, so
    # that same near-identical slope is exactly the angular ambiguity
    # edge_edge_conflict_score is meant to catch: the two concerns are
    # complementary, not redundant.
    layout = layout_of(NEAR_PARALLEL_EDGES, NEAR_PARALLEL_POSITIONS)
    assert slope_harmony_score(layout) == pytest.approx(1.0)
    assert edge_edge_conflict_score(layout) < 1.0


def test_edge_edge_conflict_uses_min_pair_per_vertex_not_mean_over_all_pairs():
    '''
    Mirrors the node-edge/node-node dilution regression tests: a vertex's
    score must be driven by its single closest pair of incident edges, not
    averaged over every pair meeting there -- p1/p3 and p2/p3 are both
    well-separated (~50 degrees) and would dilute the one genuinely bad
    pair, p1/p2, if averaged in.
    '''
    edges = [('bottom', 'p1'), ('bottom', 'p2'), ('bottom', 'p3')]
    positions = {'bottom': (0, 0), 'p1': (1, 10), 'p2': (1.02, 10), 'p3': (-10, 10)}
    layout = layout_of(edges, positions)
    pos = layout.positions
    vectors = [pos['p1'] - pos['bottom'], pos['p2'] - pos['bottom'], pos['p3'] - pos['bottom']]

    all_pair_angles = [unsigned_angle_deg(v1, v2) for v1, v2 in combinations(vectors, 2)]
    diluted_by_mean_over_all_pairs = distance_conflict_score(
        all_pair_angles, EDGE_CONFLICT_ANGLE_TOLERANCE, floor=0.0,
    )
    assert edge_edge_conflict_score(layout) < diluted_by_mean_over_all_pairs


def test_edge_edge_conflict_min_score_one_when_no_conflict():
    layout = layout_of(DIAMOND_EDGES, {'a': (0, 0), 'b': (-1, 1), 'c': (1, 1), 'd': (0, 2)})
    assert edge_edge_conflict_min_score(layout) == pytest.approx(1.0)


def test_edge_edge_conflict_min_score_is_narrowest_vertex_on_score_scale():
    '''
    Two vertices with near-parallel incident edges of different severity:
    the score is the mean of the per-vertex penalty terms, the min score
    the narrowest vertex's term.
    '''
    edges = [('s', 'p1'), ('s', 'p2'), ('t', 'q1'), ('t', 'q2')]
    positions = {
        's': (0, 0), 'p1': (1, 10), 'p2': (1.1, 10),  # ~0.6 degrees apart
        't': (50, 0), 'q1': (51, 10), 'q2': (51.5, 10),  # ~2.8 degrees apart
    }
    layout = layout_of(edges, positions)
    pos = layout.positions

    def narrowest(v, a, b):
        return unsigned_angle_deg(pos[a] - pos[v], pos[b] - pos[v])

    # p1, p2, q1, q2 have a single incident edge and are skipped
    angles = [narrowest('s', 'p1', 'p2'), narrowest('t', 'q1', 'q2')]
    terms = [1.0 - max(0.0, 1.0 - a / EDGE_CONFLICT_ANGLE_TOLERANCE) ** 2 for a in angles]
    assert terms[0] < terms[1] < 1.0
    assert edge_edge_conflict_score(layout) == pytest.approx(np.mean(terms))
    assert edge_edge_conflict_min_score(layout) == pytest.approx(min(terms))


def test_distance_conflict_min_score_is_min_of_mean_terms():
    distances = [0.0, 0.25, 0.5, 2.0]
    terms = [0.0, 1.0 - 0.75 ** 2, 1.0 - 0.5 ** 2, 1.0]
    assert distance_conflict_score(distances, threshold=1.0) == pytest.approx(np.mean(terms))
    assert distance_conflict_min_score(distances, threshold=1.0) == pytest.approx(0.0)
    assert distance_conflict_min_score([], threshold=1.0) == pytest.approx(1.0)


def test_no_vertex_with_two_incident_edges_returns_one():
    # Both endpoints of a single edge have degree 1 -- no vertex has a pair
    # of incident edges to compare, so there is nothing to penalize.
    layout = layout_of([('a', 'b')], {'a': (0, 0), 'b': (1, 1)})
    assert edge_edge_conflict_score(layout) == pytest.approx(1.0)


# -------------------------------------------------------------- nesting ---

def test_spacious_layout_has_full_nesting_suitability():
    layout = layout_of(DIAMOND_EDGES, {'a': (0, 4), 'b': (-2, 2), 'c': (2, 2), 'd': (0, 0)})
    assert nested_suitability_score(layout) == pytest.approx(1.0)


def test_cramped_non_adjacent_nodes_score_lower_than_spacious():
    spacious = layout_of(DIAMOND_EDGES, {'a': (0, 4), 'b': (-2, 2), 'c': (2, 2), 'd': (0, 0)})
    # b and c are not adjacent (only a-b, a-c, b-d, c-d are edges), so
    # pulling them close together shrinks d_node for both without an edge
    # ever crossing anything.
    cramped = layout_of(DIAMOND_EDGES, {'a': (0, 4), 'b': (-0.3, 2), 'c': (0.3, 2), 'd': (0, 0)})
    assert nested_suitability_score(cramped) < nested_suitability_score(spacious)


def test_node_on_top_of_edge_has_lower_bottleneck_clearance():
    clear = layout_of(DIAMOND_EDGES, {'a': (0, 2), 'b': (-1, 1), 'c': (1, 1), 'd': (0, 0)})
    # move c onto the a-b edge's midpoint (c is not incident to a-b)
    on_edge = layout_of(DIAMOND_EDGES, {'a': (0, 2), 'b': (-2, 0), 'c': (-1, 1), 'd': (0, 0)})
    assert bottleneck_clearance_radius(on_edge) < bottleneck_clearance_radius(clear)


def test_nesting_ranks_near_overlap_above_coincidence_and_zero_at_coincidence():
    # b and c are pulled onto the same point in 'severe', merely very close
    # in 'mild'. Nodes are points, so the bottleneck clearance bottoms out
    # at exactly 0 when two of them coincide -- the one fully conflicting
    # case -- and near-overlaps still score strictly above it.
    mild = layout_of(DIAMOND_EDGES, {'a': (0, 4), 'b': (-0.05, 2), 'c': (0.05, 2), 'd': (0, 0)})
    severe = layout_of(DIAMOND_EDGES, {'a': (0, 4), 'b': (0, 2), 'c': (0, 2), 'd': (0, 0)})
    assert bottleneck_clearance_radius(severe) == pytest.approx(0.0)
    assert bottleneck_clearance_radius(mild) > 0.0
    assert nested_suitability_score(severe) == pytest.approx(0.0)
    assert nested_suitability_score(mild) > 0.0


def test_nested_suitability_matches_hand_computed_value():
    '''
    Diamond with b and c pulled to within 0.4 of each other. All four cover
    edges have length sqrt(0.2^2 + 2^2), so r_min_nest = that / 2. The
    bottleneck is the b-c pair: d_node / 2 = 0.2, while b's nearest
    non-incident edge (a-c) is ~0.398 away and a and d are ~2 from
    everything, so R_uniform = 0.2.
    '''
    layout = layout_of(DIAMOND_EDGES, {'a': (0, 4), 'b': (-0.2, 2), 'c': (0.2, 2), 'd': (0, 0)})
    r_min_nest = np.hypot(0.2, 2.0) / 2
    assert bottleneck_clearance_radius(layout) == pytest.approx(0.2)
    assert nested_suitability_score(layout) == pytest.approx(1.0 - (1.0 - 0.2 / r_min_nest) ** 2)


# -------------------------------------------------------------- symmetry ---

def test_symmetric_diamond_scores_one():
    layout = layout_of(DIAMOND_EDGES, {'a': (0, 0), 'b': (-1, 1), 'c': (1, 1), 'd': (0, 2)})
    assert vertical_axis_balance_score(layout) == pytest.approx(1.0)


# 9 nodes sit just left of the axis (x=-1) and 1 sits far to its right
# (x=9): the signed offsets sum to (near) zero -- what naively summing raw
# x-values, or equivalently just comparing total left/right *mass*, would
# score as perfectly balanced -- even though 9 of the poset's 10 middle
# elements are visibly bunched on one side. count_balance is what actually
# catches this.
def _fan_edges(n):
    return [('bottom', f'm{i}') for i in range(n)] + [(f'm{i}', 'top') for i in range(n)]


def test_count_imbalance_penalized_despite_balanced_mass():
    positions = {'bottom': (0, 0), 'top': (0, 3)}
    positions.update({f'm{i}': (-1, 1) for i in range(9)})
    positions['m9'] = (9, 1)
    layout = layout_of(_fan_edges(10), positions)
    assert vertical_axis_balance_score(layout) < 0.5


def test_mass_imbalance_penalized_despite_equal_counts():
    symmetric = layout_of(DIAMOND_EDGES, {'a': (0, 0), 'b': (-1, 1), 'c': (1, 1), 'd': (0, 2)})
    # one node left, one node right (equal counts), but the left one sits
    # three times further from the axis than the right one.
    lopsided_mass = layout_of(DIAMOND_EDGES, {'a': (0, 0), 'b': (-3, 1), 'c': (1, 1), 'd': (0, 2)})
    assert vertical_axis_balance_score(lopsided_mass) < vertical_axis_balance_score(symmetric)


def test_bottom_off_axis_penalized_harder_than_equal_offset_elsewhere():
    # Both layouts introduce the exact same x-shift (0.5) from an otherwise
    # symmetric diamond -- once applied to the bottom element, once applied
    # to a middle element instead -- to isolate bottom_alignment's stricter,
    # cover-edge-length-scaled tolerance from the aggregate count/mass
    # tolerance the middle elements are judged against.
    bottom_shifted = layout_of(DIAMOND_EDGES, {'a': (0.5, 0), 'b': (-2, 2), 'c': (2, 2), 'd': (0, 4)})
    peer_shifted = layout_of(DIAMOND_EDGES, {'a': (0, 0), 'b': (-1.5, 2), 'c': (2, 2), 'd': (0, 4)})
    assert vertical_axis_balance_score(bottom_shifted) < vertical_axis_balance_score(peer_shifted)


def test_raises_without_a_unique_top_and_bottom():
    layout = layout_of(DISJOINT_CHAINS_EDGES, {'w1': (0, 0), 'x1': (0, 1), 'w2': (2, 0), 'x2': (2, 1)})
    with pytest.raises(ValueError):
        vertical_axis_balance_score(layout)
