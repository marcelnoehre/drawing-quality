import numpy as np

from lattice_metrics.geometry import (
    find_crossings,
    point_segment_distance,
    unsigned_angle_deg,
)


def test_point_segment_distance_endpoint_projection():
    a, b = np.array([0.0, 0.0]), np.array([10.0, 0.0])
    assert point_segment_distance(np.array([-5.0, 0.0]), a, b) == 5.0
    assert point_segment_distance(np.array([15.0, 0.0]), a, b) == 5.0


def test_point_segment_distance_perpendicular():
    a, b = np.array([0.0, 0.0]), np.array([10.0, 0.0])
    assert point_segment_distance(np.array([5.0, 3.0]), a, b) == 3.0


def test_point_segment_distance_degenerate_segment():
    a = b = np.array([1.0, 1.0])
    assert point_segment_distance(np.array([4.0, 5.0]), a, b) == 5.0


def test_unsigned_angle_deg_basic_cases():
    assert unsigned_angle_deg(np.array([1.0, 0.0]), np.array([1.0, 0.0])) == 0.0
    assert unsigned_angle_deg(np.array([1.0, 0.0]), np.array([0.0, 1.0])) == 90.0
    assert unsigned_angle_deg(np.array([1.0, 0.0]), np.array([-1.0, 0.0])) == 180.0


def test_find_crossings_detects_x_crossing():
    positions = {
        'p1': np.array([0.0, 0.0]),
        'p2': np.array([1.0, 0.0]),
        'p3': np.array([1.0, 1.0]),
        'p4': np.array([0.0, 1.0]),
    }
    edges = [('p1', 'p3'), ('p2', 'p4')]
    crossings = find_crossings(edges, positions)
    assert len(crossings) == 1
    assert crossings[0].is_proper
    assert crossings[0].point == (0.5, 0.5)


def test_find_crossings_ignores_shared_endpoint():
    positions = {
        'a': np.array([0.0, 0.0]),
        'b': np.array([1.0, 1.0]),
        'c': np.array([1.0, 0.0]),
    }
    edges = [('a', 'b'), ('a', 'c')]
    assert find_crossings(edges, positions) == []


def test_find_crossings_flags_overlap_as_improper():
    positions = {
        'a': np.array([0.0, 0.0]),
        'b': np.array([2.0, 0.0]),
        'c': np.array([1.0, 0.0]),
        'd': np.array([3.0, 0.0]),
    }
    edges = [('a', 'b'), ('c', 'd')]  # collinear, overlapping on [1, 2]
    crossings = find_crossings(edges, positions)
    assert len(crossings) == 1
    assert not crossings[0].is_proper
