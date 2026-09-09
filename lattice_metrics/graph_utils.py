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


def freese_ranks(graph: nx.DiGraph) -> Dict[Hashable, int]:
    '''
    Freese's rank function (Freese, "Automated Lattice Drawing", ICFCA 2004,
    LNCS 2961, pp. 112-127, Sec. 4.1):

        rank(a) = height(a) - depth(a) + M

    where height(a) is the length of the longest chain from a down to a
    minimal element, depth(a) is the length of the longest chain from a up
    to a maximal element (both measured along cover relations, i.e. the
    transitive reduction), and M is the length of the longest chain in the
    poset, chosen so minimal elements get rank 0.

    Unlike ``longest_path_ranks`` (pure bottom-up distance from a source),
    this centers each element between its distance from the bottom and its
    distance from the top -- the rank function line_diagrams/freese/freese.py
    uses to seed the vertical axis of its own drawings, so it is a
    theoretically grounded target for 'does this drawing's layering match
    the poset's intrinsic structure' independent of that specific
    force-directed algorithm.
    '''
    cover = nx.transitive_reduction(graph)
    order = list(nx.topological_sort(cover))

    depth: Dict[Hashable, int] = {}
    for a in reversed(order):
        upper_covers = list(cover.successors(a))
        depth[a] = 0 if not upper_covers else 1 + max(depth[p] for p in upper_covers)

    height: Dict[Hashable, int] = {}
    for a in order:
        lower_covers = list(cover.predecessors(a))
        height[a] = 0 if not lower_covers else 1 + max(height[c] for c in lower_covers)

    m = max(height[a] + depth[a] for a in cover.nodes())
    return {a: height[a] - depth[a] + m for a in cover.nodes()}


def group_within_tolerance(sorted_values: np.ndarray, tolerance: float) -> List[list]:
    '''
    Partition sorted 1-D values into contiguous groups, starting a new
    group whenever a gap exceeds ``tolerance``.

    Equivalent to DBSCAN(eps=tolerance, min_samples=1) on 1-D data, computed
    directly instead of pulling in scikit-learn for what a single sort and
    scan already gives exactly.
    '''
    groups = [[sorted_values[0]]]
    for value in sorted_values[1:]:
        if value - groups[-1][-1] > tolerance:
            groups.append([])
        groups[-1].append(value)
    return groups
