import networkx as nx
import numpy as np
import pytest

from lattice_metrics.graph_utils import LatticeLayout, group_within_tolerance, longest_path_ranks, poset_width


def diamond() -> nx.DiGraph:
    g = nx.DiGraph()
    g.add_edges_from([('a', 'b'), ('a', 'c'), ('b', 'd'), ('c', 'd')])
    return g


def test_longest_path_ranks_diamond():
    ranks = longest_path_ranks(diamond())
    assert ranks == {'a': 0, 'b': 1, 'c': 1, 'd': 2}


def test_poset_width_diamond_is_two():
    assert poset_width(diamond()) == 2


def test_poset_width_chain_is_one():
    g = nx.DiGraph()
    g.add_edges_from([('a', 'b'), ('b', 'c'), ('c', 'd')])
    assert poset_width(g) == 1


def test_layout_rejects_cyclic_graph():
    g = nx.DiGraph()
    g.add_edges_from([('a', 'b'), ('b', 'a')])
    positions = {'a': np.array([0.0, 0.0]), 'b': np.array([1.0, 1.0])}
    with pytest.raises(ValueError):
        LatticeLayout(graph=g, positions=positions)


def test_layout_is_comparable():
    positions = {n: np.array([0.0, float(-i)]) for i, n in enumerate('abcd')}
    layout = LatticeLayout(graph=diamond(), positions=positions)
    assert layout.is_comparable('a', 'd')
    assert not layout.is_comparable('b', 'c')


def test_group_within_tolerance_does_not_chain_across_a_wide_span():
    # Each consecutive gap is 4, within tolerance=5, so single-linkage
    # chaining would merge all four values into one group spanning 12 --
    # far more than the tolerance actually promises. Complete linkage
    # instead bounds every group's own diameter to the tolerance.
    values = np.array([0.0, 4.0, 8.0, 12.0])
    groups = group_within_tolerance(values, tolerance=5.0)
    assert [list(g) for g in groups] == [[0.0, 4.0], [8.0, 12.0]]
    for group in groups:
        assert max(group) - min(group) <= 5.0


def test_group_within_tolerance_single_group_when_diameter_fits():
    values = np.array([0.0, 2.0, 4.0])
    groups = group_within_tolerance(values, tolerance=5.0)
    assert len(groups) == 1
