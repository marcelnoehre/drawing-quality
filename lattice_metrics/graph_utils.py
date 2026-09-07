'''
Graph/poset utilities shared by the metrics.

All metrics take a :class:`LatticeLayout` rather than re-deriving positions,
transitive reductions/closures, and ranks themselves. Building it once per
graph and passing it to every metric avoids paying for the (non-trivial)
transitive closure/reduction repeatedly when running the whole battery of
metrics on the same drawing.
'''
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Hashable, List

import networkx as nx
import numpy as np

from .geometry import PositionMap


@dataclass
class LatticeLayout:
    '''
    A DAG together with a straight-line drawing of it.

    ``graph`` is assumed to be a directed acyclic graph representing a
    partial order (an edge u -> v means u < v), drawn with ``positions``.
    '''

    graph: nx.DiGraph
    positions: PositionMap
    transitive_reduction: nx.DiGraph = field(init=False)
    transitive_closure: nx.DiGraph = field(init=False)
    rank: Dict[Hashable, int] = field(init=False)

    def __post_init__(self) -> None:
        if not nx.is_directed_acyclic_graph(self.graph):
            raise ValueError('LatticeLayout requires a directed acyclic graph')
        self.transitive_reduction = nx.transitive_reduction(self.graph)
        self.transitive_closure = nx.transitive_closure(self.graph, reflexive=False)
        self.rank = longest_path_ranks(self.graph)

    @property
    def n(self) -> int:
        return self.graph.number_of_nodes()

    def is_comparable(self, u: Hashable, v: Hashable) -> bool:
        return u == v or self.transitive_closure.has_edge(u, v) or self.transitive_closure.has_edge(v, u)

    def average_cover_edge_length(self) -> float:
        lengths = [
            float(np.linalg.norm(self.positions[u] - self.positions[v]))
            for u, v in self.transitive_reduction.edges
        ]
        return float(np.mean(lengths)) if lengths else 1.0


def load_layout(path: str) -> LatticeLayout:
    '''
    Read a GraphML file with per-node ``x``/``y`` attributes.
    '''
    graph = nx.read_graphml(path)
    positions = {
        node: np.array([float(data['x']), float(data['y'])])
        for node, data in graph.nodes(data=True)
    }
    return LatticeLayout(graph=graph, positions=positions)


def longest_path_ranks(graph: nx.DiGraph) -> Dict[Hashable, int]:
    '''
    Standard longest-path layer assignment: rank 0 for sources, and
    ``rank[v] = 1 + max(rank[u] for u predecessor of v)`` otherwise.

    This is the layering used throughout the Sugiyama-style layered-drawing
    literature, computed exactly (as opposed to inferring layers from
    drawn y-coordinates via clustering).
    '''
    rank: Dict[Hashable, int] = {}
    for node in nx.topological_sort(graph):
        preds = list(graph.predecessors(node))
        rank[node] = 0 if not preds else 1 + max(rank[p] for p in preds)
    return rank


def poset_width(graph: nx.DiGraph) -> int:
    '''
    Width of the poset represented by ``graph`` (size of its largest
    antichain), computed via Dilworth's theorem: width = n - (size of a
    maximum matching in the bipartite graph of the comparability relation).

    This is the graph-theoretic minimum number of 'parallel tracks' any
    upward drawing of this poset needs, independent of any particular
    drawing -- useful as a structural reference point when judging how a
    layout uses horizontal space.
    '''
    tc = nx.transitive_closure(graph, reflexive=False)
    bipartite = nx.Graph()
    left = {v: ('l', v) for v in graph}
    right = {v: ('r', v) for v in graph}
    bipartite.add_nodes_from(left.values(), bipartite=0)
    bipartite.add_nodes_from(right.values(), bipartite=1)
    for u, v in tc.edges():
        bipartite.add_edge(left[u], right[v])
    matching = nx.bipartite.maximum_matching(bipartite, top_nodes=set(left.values()))
    matched = sum(1 for key in matching if key[0] == 'l')
    return graph.number_of_nodes() - matched


def rank_groups(rank: Dict[Hashable, int]) -> Dict[int, List[Hashable]]:
    groups: Dict[int, List[Hashable]] = {}
    for node, r in rank.items():
        groups.setdefault(r, []).append(node)
    return groups
