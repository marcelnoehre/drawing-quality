from __future__ import annotations

import math
import networkx as nx
import odis

from collections import Counter
from dataclasses import dataclass, field
from fractions import Fraction
from itertools import combinations
from typing import Dict, FrozenSet, List, Optional, Tuple


@dataclass
class Args:
    '''
    Parameters of Cole, Ducrou & Eklund's incremental layer-diagram search
    (§4.2/§4.4 of the reference). The paper's own experiments use
    n1=5, n2=3, max_solutions=5000 (§5.2); those numeric values are kept
    as defaults here except for `max_solutions`, reduced purely to bound
    the runtime of this reference (pure Python) implementation, since every
    extra candidate diagram costs one evaluation of all 16 metrics of
    §4.3 plus an O(solutions^2) domination pass (§4.4).

    n1 : int
        Number of new candidate attribute x-offsets made available at each
        of the `n2` outer passes of the search (§4.2, Fig. 2 `solutions`).
    n2 : int
        Number of outer passes; n1*n2 is therefore the total number of
        distinct candidate x-offsets ever made available to an attribute.
    max_solutions : int
        Upper bound on the number of satisfactory (node-node- and
        node-line-overlap free) diagrams collected before the search
        stops (Fig. 2, `max_solutions`); this counts every diagram that
        clears the overlap tests, not only those that survive the
        domination filter of `_rank`.
    top_n : int
        Number of top-ranked, non-dominated diagrams kept in
        `self.ranked` (§4.4, "the top n diagrams ... are presented to the
        user"); `self.coordinates` is always the single best (rank 1) of
        these.
    max_search_calls : int
        Not part of the paper: a hard cap on the number of `_next` calls
        (i.e. backtracking search nodes) performed in each pass before
        giving up on it. The paper's own pruning (§4.2) keeps the search
        tractable in a fast, compiled implementation; in this pure-Python
        reference implementation a context with many attributes relative
        to concepts (so that collisions among the few candidate x-offsets
        only become likely very late in the attribute order) can make the
        search tree explode long before `max_solutions` satisfactory
        diagrams are found. This cap turns that into a clear failure
        instead of an unbounded hang. It is applied per pass, so that a
        pass thrashing on a too-small offset pool does not starve the
        later passes with larger pools.
    fallback_passes : int
        Not part of the paper: if the `n2` passes find no solution at
        all, up to this many further passes (each making `n1` more
        candidate offsets available, exactly like the paper's own passes)
        are run until one finds a solution. 0 keeps the paper's search
        unchanged. `self.passes` records how many passes were run.
    '''
    n1: int = 5
    n2: int = 3
    max_solutions: int = 500
    top_n: int = 5
    max_search_calls: int = 300_000
    fallback_passes: int = 0


@dataclass
class _Diagram:
    '''One satisfactory candidate diagram: an attribute vector assignment
    `v` (1-indexed candidate index per attribute, in `attribute_order`),
    the resulting x-position of every concept, and (once scored by
    `_rank`) its §4.3 metric values.'''
    v: List[int]
    x: Dict[int, int]
    metrics: Dict[str, float] = field(default_factory=dict)
    is_planar: bool = False


class ColeDucrouEklund():
    '''
    Cole, Ducrou & Eklund's algorithm for the automated layout of small
    concept lattices as x-dimensional attribute-additive layer diagrams
    (§4).

    The y-position of a concept is its *uprank* -- the length of the
    longest path from the concept up to the top of the lattice (§4.1) --
    fixed once and for all before any search takes place. The x-position
    is attribute-additive: pos_x(a) = sum of vec(m) over the attributes m
    in the intent of a (§2, §4.1), where vec assigns every attribute one
    of a small, fixed pool of candidate integer offsets,

        vec_i = (-1)^i * floor(i/2),  i.e. 0, 1, -1, 2, -2, 3, -3, ...

    (§4.2). Rather than search over all N! ways of ordering attributes,
    attributes are first fixed in one order (by descending extent size,
    ties broken by their order in the context, §4.2 "To make our
    experiments more deterministic..."), and candidate offsets are then
    assigned to attributes m_1, m_2, ... in turn by a backtracking search
    that only elaborates an assignment for m_1..m_k into one for
    m_1..m_{k+1} if it is *satisfactory*: no two concepts of the
    (k-attribute) sub-lattice L_k, generated using only m_1..m_k, coincide
    in position (§4.2, Fig. 2). This is sound because an unsatisfactory
    pos_k can only ever elaborate into an unsatisfactory pos_{k+1} (§4.2),
    so the search never wastes effort completing an assignment that is
    already known to collide.

    Every assignment for all N attributes that both avoids node-node
    collisions (guaranteed by the above) and avoids node-line collisions
    (checked once, only at the leaves) is a *solution* diagram. Up to
    `args.max_solutions` solutions are collected (over `args.n2` passes
    that each make more candidate offsets available, §4.2), scored by 16
    diagram metrics (§4.3), filtered to keep only diagrams not dominated
    by another (§4.4, plus the rule that a planar diagram always dominates
    a non-planar one), and ranked by the number of metrics for which they
    equal the best value achieved by any surviving diagram, ties broken in
    favour of the diagram produced earlier (§4.4). `self.coordinates`
    holds the positions of the rank-1 diagram; `self.ranked` and
    `self.solutions` are kept for inspection.

    Ambiguities/omissions in the paper (as scanned) and the choices made
    here are documented at the point they matter:
      - "number of edge vectors applied to meet irreducibles" (§4.3) is
        read as the number of distinct edge vectors among cover edges
        whose lower endpoint is a meet-irreducible concept, see
        `_compute_metrics`.
      - "Number of symmetric siblings (Non Zero)" (§4.3) is read as
        excluding sibling pairs that are both centered (offset 0 from
        their parent), see `_symmetric_siblings`.
      - "Child Balance" (§4.3) is read per-child (not per-parent): a
        child counts as unbalanced if no sibling of it sits at the
        negated offset, and a lone, non-centered child is unbalanced,
        see `_child_balance`.
      - "Sum of ... children" for well-/ok-placed children (§4.3, Fig. 3)
        is read as summing the number of children of every qualifying
        parent, see `_well_ok_placed_children`.
      - the paper never states, for any of its 16 metrics, whether a
        larger or smaller value is the "good" direction used when
        computing the best value for ranking (§4.4); `_MAXIMIZE` records
        the reading used here (metrics that count an explicitly rewarded
        pattern -- symmetric siblings, aligned multi-level chains,
        well-/ok-placed children -- are maximized, every other metric
        counts or measures something undesirable and is minimized).

    Parameters
    ----------
    context : odis.FormalContext
        The (assumed clarified) formal context whose concept lattice is
        drawn.
    args : Optional[Dict]
        A dictionary of parameters overriding the defaults in `Args`.

    Reference
    ---------
    @inproceedings{ColeDucrouEklund2006,
        author    = {Cole, Richard and Ducrou, Jon and Eklund, Peter},
        title     = {Automated Layout of Small Lattices Using Layer
                     Diagrams},
        booktitle = {Formal Concept Analysis, 4th International
                     Conference, ICFCA 2006},
        series    = {Lecture Notes in Computer Science},
        volume    = {3874},
        publisher = {Springer},
        pages     = {291--305},
        year      = {2006}
    }
    '''

    _MAXIMIZE = frozenset({
        'symmetric_siblings', 'symmetric_siblings_nonzero',
        'two_chains', 'three_chains',
        'well_placed_children', 'ok_placed_children',
    })

    def __init__(self,
            context: odis.FormalContext,
            args: Optional[Dict] = None
        ):
        self.context = context
        self.args: Args = Args(**(args or {}))
        self._extents: List[FrozenSet[str]] = [c.extent.to_frozenset() for c in context.concepts()]
        self._intents: List[FrozenSet[str]] = [c.intent.to_frozenset() for c in context.concepts()]
        self.concepts: List[int] = list(range(len(self._extents)))

        self._build_order()
        self._rank_function()
        self._structural_precomputation()
        self._order_attributes()
        self._build_offsets()
        self._build_subcontexts()

        self.solutions: List[_Diagram] = self._search()
        self.ranked: List[_Diagram] = self._rank(self.solutions)

        best = self.ranked[0]
        self.coordinates: Dict[int, Tuple[float, float]] = {
            a: (float(best.x[a]), float(self.level[a])) for a in self.concepts
        }

    # ------------------------------------------------------------------
    # Lattice order
    # ------------------------------------------------------------------

    @staticmethod
    def _cover_from_extents(extents: List[FrozenSet[str]]) -> nx.DiGraph:
        '''
        Build the cover (Hasse) digraph among concepts 0..len(extents)-1
        from set inclusion of their extents: concept a lies above concept
        b whenever the extent of b is a proper subset of the extent of a.
        The cover digraph is the transitive reduction of that order, with
        an edge a -> b whenever b is a lower cover of a, i.e. a covers b.
        '''
        order = nx.DiGraph()
        order.add_nodes_from(range(len(extents)))
        for a, b in combinations(range(len(extents)), 2):
            if extents[b] < extents[a]:
                order.add_edge(a, b)
            elif extents[a] < extents[b]:
                order.add_edge(b, a)
        return nx.transitive_reduction(order)

    @staticmethod
    def _uprank_from_cover(cover: nx.DiGraph) -> List[int]:
        '''
        uprank(top) = 0; uprank(p) = 1 + max(uprank(q) for q a parent of
        p), i.e. the length of the longest path from p up to the top of
        the lattice (§4.1). Computed top-down: `nx.topological_sort` of
        the cover digraph visits every parent before its children.
        '''
        topo = list(nx.topological_sort(cover))
        uprank: Dict[int, int] = {}
        for a in topo:
            parents = list(cover.predecessors(a))
            uprank[a] = 0 if not parents else 1 + max(uprank[p] for p in parents)
        return [uprank[a] for a in range(cover.number_of_nodes())]

    def _build_order(self):
        self._cover_digraph_ = self._cover_from_extents(self._extents)

    def children(self, a: int) -> List[int]:
        '''Return direct child concept indices of a, i.e. its lower covers.'''
        return list(self._cover_digraph_.successors(a))

    def parents(self, a: int) -> List[int]:
        '''Return direct parent concept indices of a, i.e. its upper covers.'''
        return list(self._cover_digraph_.predecessors(a))

    def cover_relations(self) -> List[Tuple[int, int]]:
        '''Return the cover relations (a, b) of the lattice, i.e. a covers b.'''
        return list(self._cover_digraph_.edges())

    def _rank_function(self):
        '''uprank of every concept of the full lattice (§4.1), and the
        y-position it induces: `self.level[a] = -uprank(a)`, so that the
        top concept (uprank 0) sits highest and a < b implies
        level(a) < level(b) (uprank strictly increases down any cover
        edge, so this holds for every comparable pair, not just covers).'''
        self.uprank: Dict[int, int] = dict(enumerate(self._uprank_from_cover(self._cover_digraph_)))
        self.level: Dict[int, int] = {a: -self.uprank[a] for a in self.concepts}

    def _structural_precomputation(self):
        '''Precompute the purely structural (diagram-independent) pieces
        needed by the metrics of §4.3: the top/bottom concepts, the
        meet-irreducible concepts (those with exactly one parent -- the
        standard characterisation of meet-irreducibility in a finite
        lattice), a top-down topological order of the concepts (for the
        average path width metric), and every (child, parent, grandparent) /
        (child, parent, grandparent, great-grandparent) run of consecutive
        cover edges (for the two-/three-chain metrics).'''
        self._top = next(a for a in self.concepts if not self.parents(a))
        self._bottom = next(a for a in self.concepts if not self.children(a))
        self._meet_irreducibles = frozenset(a for a in self.concepts if len(self.parents(a)) == 1)
        self._topological_order: List[int] = list(nx.topological_sort(self._cover_digraph_))
        self._two_chain_triples: List[Tuple[int, int, int]] = [
            (c, p, g)
            for p in self.concepts
            for c in self.children(p)
            for g in self.parents(p)
        ]
        self._three_chain_quads: List[Tuple[int, int, int, int]] = [
            (c, p, g, gg)
            for (c, p, g) in self._two_chain_triples
            for gg in self.parents(g)
        ]

    # ------------------------------------------------------------------
    # Attribute order and candidate x-offsets (§4.2)
    # ------------------------------------------------------------------

    def _order_attributes(self):
        '''
        Order attributes m_1, ..., m_N by descending extent size, ties
        broken by their order in the input context (§4.2, "we ordered the
        attributes by their extent size in the reduced context ... If two
        attributes have the same extent size then we ordered based on the
        order of the attributes in the input context"); Python's stable
        sort preserves that tie order automatically.
        '''
        attributes = list(self.context.attributes)
        extent_size = {m: len(self.context.extent([m]).to_frozenset()) for m in attributes}
        self.attribute_order: List[str] = sorted(attributes, key=lambda m: -extent_size[m])
        self._attr_index: Dict[str, int] = {m: i for i, m in enumerate(self.attribute_order)}

    def _build_offsets(self):
        '''
        The pool of n1*n2 candidate x-offsets, vec_i = (-1)^i * floor(i/2)
        for i = 1..n1*n2 (§4.2): 0, 1, -1, 2, -2, 3, -3, ... `self._offsets`
        is 1-indexed (index 0 unused) to match the 1-based candidate
        indices used throughout the search. The pool is extended by n1
        offsets for each of the `fallback_passes`.
        '''
        total = self.args.n1 * (self.args.n2 + self.args.fallback_passes)
        self._offsets: List[int] = [0] + [((-1) ** i) * (i // 2) for i in range(1, total + 1)]

    def _build_subcontexts(self):
        '''
        For every k = 1..N-1, precompute the concept lattice L_k generated
        by only the first k attributes m_1..m_k (§4.2): its concepts'
        intents (necessarily subsets of {m_1,...,m_k}, so already equal to
        rep_k(x)) and the y-position (uprank-derived level) each of its
        concepts would have. This depends only on which attributes are
        included, not on the candidate offsets assigned to them, so it is
        computed once and reused by every call to `_satisfactory`. The
        case k == N is not needed here: it is answered directly from the
        full lattice's own `self._intents` / `self.level` in
        `_satisfactory`, since L_N (all attributes, just possibly
        reordered) is exactly the original context.
        '''
        N = len(self.attribute_order)
        all_attributes = set(self.context.attributes)
        self._sub_intents: List[List[FrozenSet[str]]] = []
        self._sub_level: List[List[int]] = []
        for k in range(1, N):
            keep = set(self.attribute_order[:k])
            sub = self.context.copy()
            for m in all_attributes - keep:
                sub.remove_attribute(m)
            sub_concepts = sub.concepts()
            extents = [c.extent.to_frozenset() for c in sub_concepts]
            intents = [c.intent.to_frozenset() for c in sub_concepts]
            cover = self._cover_from_extents(extents)
            uprank = self._uprank_from_cover(cover)
            self._sub_intents.append(intents)
            self._sub_level.append([-u for u in uprank])

    # ------------------------------------------------------------------
    # Incremental search (§4.2, Fig. 2)
    # ------------------------------------------------------------------

    def _positions(self, v: List[int]) -> Dict[int, int]:
        '''pos_x(a) = sum of the assigned offset of every attribute in
        a's intent (§4.1), for the full lattice, given a complete
        (length-N) candidate assignment v.'''
        return {
            a: sum(self._offsets[v[self._attr_index[m]]] for m in self._intents[a])
            for a in self.concepts
        }

    def _satisfactory(self, v: List[int]) -> bool:
        '''
        pos_k is satisfactory if no two concepts of L_k (the sub-lattice
        generated by the first k = len(v) attributes) coincide in
        position, where position combines the x-offset implied by v with
        L_k's own uprank-derived level (§4.2). Unsatisfactory partial
        assignments are never elaborated further, since they can only
        elaborate into unsatisfactory ones (§4.2).
        '''
        k = len(v)
        if k == len(self.attribute_order):
            intents, levels = self._intents, [self.level[a] for a in self.concepts]
        else:
            intents, levels = self._sub_intents[k - 1], self._sub_level[k - 1]

        seen = set()
        for intent, y in zip(intents, levels):
            x = sum(self._offsets[v[self._attr_index[m]]] for m in intent)
            pos = (x, y)
            if pos in seen:
                return False
            seen.add(pos)
        return True

    def _has_line_overlap(self, x: Dict[int, int]) -> bool:
        '''
        A full (N-attribute) position assignment additionally has a
        node-line overlap if some concept's point lies on a cover edge's
        straight line segment without being one of its two endpoints
        (§3.1); node-node overlaps need not be re-checked here since they
        are already ruled out by `_satisfactory` having accepted this v.
        '''
        points = {a: (x[a], self.level[a]) for a in self.concepts}
        for p, c in self.cover_relations():
            for o in self.concepts:
                if o == p or o == c:
                    continue
                if self._point_on_segment(points[o], points[p], points[c]):
                    return True
        return False

    @staticmethod
    def _point_on_segment(o: Tuple[int, int], p: Tuple[int, int], c: Tuple[int, int]) -> bool:
        '''Whether point o lies on the closed segment pc, using exact
        integer arithmetic (all diagram coordinates are integers).'''
        ox, oy = o
        px, py = p
        cx, cy = c
        cross = (cx - px) * (oy - py) - (cy - py) * (ox - px)
        if cross != 0:
            return False
        return min(px, cx) <= ox <= max(px, cx) and min(py, cy) <= oy <= max(py, cy)

    def _next(self, v: List[int], num_attr: int, base: int):
        '''
        Fig. 2's `next`: elaborate the partial candidate assignment v one
        attribute at a time, from 1..base, pruning any extension that
        makes pos_k unsatisfactory; once v assigns all `num_attr`
        attributes, keep it as a solution if it has no node-line overlap.
        An assignment already stored by an earlier pass (every pass
        re-explores the smaller pools of the passes before it) is not
        stored again. Also aborts once `max_search_calls` search nodes
        have been visited in this pass (see `Args.max_search_calls`).
        '''
        self._search_calls += 1
        if self._search_calls > self.args.max_search_calls:
            return

        if len(v) == num_attr:
            if tuple(v) in self._found:
                return
            self._found.add(tuple(v))
            x = self._positions(v)
            if not self._has_line_overlap(x):
                self._solutions.append(_Diagram(v=list(v), x=x))
                self._solution_count += 1
            return

        for i in range(1, base + 1):
            v.append(i)
            if self._satisfactory(v):
                self._next(v, num_attr, base)
            if self._solution_count >= self.args.max_solutions or self._search_calls > self.args.max_search_calls:
                break
            v.pop()

    def _search(self) -> List[_Diagram]:
        '''Fig. 2's `solutions`: run `_next` for n2 passes, the i'th
        allowing candidate offsets 1..i*n1, until `max_solutions`
        satisfactory diagrams have been collected (each pass visiting at
        most `max_search_calls` search nodes, see `Args.max_search_calls`).
        If no pass found a solution, up to `fallback_passes` further passes
        are run until one does (see `Args.fallback_passes`).'''
        N = len(self.attribute_order)
        self._solution_count = 0
        self._solutions: List[_Diagram] = []
        self._found: set = set()
        self.passes = 0
        for i in range(1, self.args.n2 + self.args.fallback_passes + 1):
            if i > self.args.n2 and self._solutions:
                break
            self._search_calls = 0
            self._next([], N, i * self.args.n1)
            self.passes = i
            if self._solution_count >= self.args.max_solutions:
                break
        if not self._solutions:
            raise RuntimeError(
                f'no satisfactory layer diagram found within {self.passes} '
                f'passes (candidate offset pool of {self.passes * self.args.n1}), '
                f'max_solutions and max_search_calls per pass; try increasing '
                f'n1, n2, fallback_passes, max_solutions or max_search_calls'
            )
        return self._solutions

    # ------------------------------------------------------------------
    # Diagram metrics (§4.3)
    # ------------------------------------------------------------------

    @staticmethod
    def _segments_intersect(p1, p2, p3, p4) -> bool:
        '''Standard orientation-based test for the intersection of the
        two closed segments p1p2 and p3p4, exact over integer
        coordinates.'''
        def orientation(a, b, c) -> int:
            val = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
            return 0 if val == 0 else (1 if val > 0 else -1)

        def on_segment(a, b, c) -> bool:
            return min(a[0], b[0]) <= c[0] <= max(a[0], b[0]) and min(a[1], b[1]) <= c[1] <= max(a[1], b[1])

        o1, o2 = orientation(p1, p2, p3), orientation(p1, p2, p4)
        o3, o4 = orientation(p3, p4, p1), orientation(p3, p4, p2)

        if o1 != o2 and o3 != o4:
            return True
        if o1 == 0 and on_segment(p1, p2, p3):
            return True
        if o2 == 0 and on_segment(p1, p2, p4):
            return True
        if o3 == 0 and on_segment(p3, p4, p1):
            return True
        if o4 == 0 and on_segment(p3, p4, p2):
            return True
        return False

    def _count_crossings(self, pos: Dict[int, Tuple[int, int]], edges: List[Tuple[int, int]]) -> int:
        '''Number of edge crossings (§4.3): pairwise proper crossings
        among the straight-line cover edges, excluding pairs that share an
        endpoint.'''
        crossings = 0
        for (a, b), (c, d) in combinations(edges, 2):
            if {a, b} & {c, d}:
                continue
            if self._segments_intersect(pos[a], pos[b], pos[c], pos[d]):
                crossings += 1
        return crossings

    @staticmethod
    def _gradient(dx: int, dy: int):
        '''Canonical (exact) representation of an edge's gradient, a
        sentinel for vertical edges.'''
        return ('vertical',) if dx == 0 else Fraction(dy, dx)

    @staticmethod
    def _abs_gradient(dx: int, dy: int):
        return ('vertical',) if dx == 0 else abs(Fraction(dy, dx))

    def _average_path_width(self, x: Dict[int, int]) -> float:
        '''Average path width (§4.3): for each maximal chain (path from
        top to bottom in the cover digraph), max(x) - min(x) over its
        concepts, averaged over all such chains.

        The number of maximal chains can be exponential in the number of
        concepts, so they are not enumerated. Instead, every concept a
        carries the number of chains from the top down to a for each
        (min x, max x) pair seen along the way, propagated top-down along
        cover edges. The chains that reach the bottom then give the exact
        average. This takes O(|edges| * R^2) steps, where R is the number
        of distinct x-positions.'''
        chains: Dict[int, Counter] = {a: Counter() for a in self.concepts}
        chains[self._top][(x[self._top], x[self._top])] = 1
        for p in self._topological_order:
            for c in self.children(p):
                xc = x[c]
                for (lo, hi), count in chains[p].items():
                    chains[c][(min(lo, xc), max(hi, xc))] += count
        at_bottom = chains[self._bottom]
        return sum((hi - lo) * count for (lo, hi), count in at_bottom.items()) / sum(at_bottom.values())

    def _child_balance(self, x: Dict[int, int]) -> int:
        '''Child balance (§4.3): number of unbalanced children, where a
        child is unbalanced if it has no sibling at the negated x-offset
        from their shared parent (a lone, centered child, offset 0, is
        considered balanced -- see the class docstring).'''
        unbalanced = 0
        for p in self.concepts:
            dxs = [x[c] - x[p] for c in self.children(p)]
            for i, dxi in enumerate(dxs):
                mirrored = any(j != i and dxs[j] == -dxi for j in range(len(dxs)))
                if not mirrored and dxi != 0:
                    unbalanced += 1
        return unbalanced

    def _symmetric_siblings(self, x: Dict[int, int]) -> Tuple[int, int]:
        '''Number of symmetric siblings, and its "non zero" variant
        excluding pairs that are both centered (§4.3; see the class
        docstring for the reading of "non zero" used here).'''
        total = 0
        nonzero = 0
        for p in self.concepts:
            dxs = [x[c] - x[p] for c in self.children(p)]
            for i, j in combinations(range(len(dxs)), 2):
                if dxs[i] == -dxs[j]:
                    total += 1
                    if dxs[i] != 0 or dxs[j] != 0:
                        nonzero += 1
        return total, nonzero

    def _sum_logs_avg_points(self, x: Dict[int, int]) -> float:
        '''Sum of logs of number of elements at average points (§4.3):
        sum over unordered pairs a, b of logth(count_ave_points(a, b)),
        logth(n) = log(n) if n >= 1 else 0.'''
        at_x = Counter(x.values())
        total = 0.0
        for a, b in combinations(self.concepts, 2):
            if (x[a] + x[b]) % 2:
                continue
            count = at_x[(x[a] + x[b]) // 2]
            if count >= 1:
                total += math.log(count)
        return total

    def _well_ok_placed_children(self, x: Dict[int, int]) -> Tuple[int, int]:
        '''Sum of well-placed and ok-placed children (§4.3, Fig. 3): a
        parent's children are well-placed if there are 1-3 of them at
        offsets exactly {0}, {-1, 1} or {-1, 0, 1}; a parent's children
        are ok-placed if there are 2 or more of them and at least one
        sits at offset -1 and another at +1 (the rest unconstrained). Both
        variants sum the number of children of every qualifying parent.'''
        well = 0
        ok = 0
        for p in self.concepts:
            kids = self.children(p)
            n = len(kids)
            if n == 0:
                continue
            dxs = sorted(x[c] - x[p] for c in kids)
            if (n == 1 and dxs == [0]) or (n == 2 and dxs == [-1, 1]) or (n == 3 and dxs == [-1, 0, 1]):
                well += n
            if n >= 2 and -1 in dxs and 1 in dxs:
                ok += n
        return well, ok

    def _compute_metrics(self, diagram: _Diagram) -> Dict[str, float]:
        x = diagram.x
        y = self.level
        pos = {a: (x[a], y[a]) for a in self.concepts}
        edges = self.cover_relations()
        vectors = [(x[c] - x[p], y[c] - y[p]) for p, c in edges]

        metrics: Dict[str, float] = {}
        metrics['edge_crossings'] = self._count_crossings(pos, edges)
        metrics['edge_vectors'] = len(set(vectors))
        # see the class docstring: read as edges whose lower endpoint is a
        # meet-irreducible concept.
        metrics['edge_vectors_meet_irreducibles'] = len({
            (x[c] - x[p], y[c] - y[p])
            for p, c in edges
            if c in self._meet_irreducibles
        })
        metrics['edge_gradients'] = len({self._gradient(dx, dy) for dx, dy in vectors})
        metrics['absolute_edge_gradients'] = len({self._abs_gradient(dx, dy) for dx, dy in vectors})
        metrics['average_path_width'] = self._average_path_width(x)
        metrics['total_edge_length'] = sum(math.hypot(dx, dy) for dx, dy in vectors)
        metrics['horizontal_shift'] = abs(x[self._top] - x[self._bottom])
        metrics['child_balance'] = self._child_balance(x)
        sym, sym_nonzero = self._symmetric_siblings(x)
        metrics['symmetric_siblings'] = sym
        metrics['symmetric_siblings_nonzero'] = sym_nonzero
        metrics['sum_logs_avg_points'] = self._sum_logs_avg_points(x)
        metrics['two_chains'] = sum(
            1 for c, p, g in self._two_chain_triples
            if (x[p] - x[c], y[p] - y[c]) == (x[g] - x[p], y[g] - y[p])
        )
        metrics['three_chains'] = sum(
            1 for c, p, g, gg in self._three_chain_quads
            if (x[p] - x[c], y[p] - y[c]) == (x[g] - x[p], y[g] - y[p]) == (x[gg] - x[g], y[gg] - y[g])
        )
        well, ok = self._well_ok_placed_children(x)
        metrics['well_placed_children'] = well
        metrics['ok_placed_children'] = ok
        return metrics

    # ------------------------------------------------------------------
    # Filtering and ranking (§4.4)
    # ------------------------------------------------------------------

    def _dominates(self, a: _Diagram, b: _Diagram) -> bool:
        '''Whether diagram a dominates diagram b: a planar diagram always
        dominates a non-planar one (§4.2, "store_solution"); otherwise a
        dominates b if a is at least as good as b on every metric
        (accounting for `_MAXIMIZE`) and strictly better on at least
        one.'''
        if a.is_planar != b.is_planar:
            return a.is_planar

        better_or_equal = True
        strictly_better = False
        for name, av in a.metrics.items():
            bv = b.metrics[name]
            if name in self._MAXIMIZE:
                av, bv = -av, -bv
            if av > bv:
                better_or_equal = False
                break
            if av < bv:
                strictly_better = True
        return better_or_equal and strictly_better

    def _rank(self, solutions: List[_Diagram]) -> List[_Diagram]:
        '''Score every solution by its §4.3 metrics, keep only the
        diagrams not dominated by another (plus the planar-dominance
        rule), then rank the survivors by how many metrics they achieve
        the best value (over the survivors) for, ties broken in favour of
        the diagram produced earlier (§4.4). `solutions` is already in
        production order and the sort below is stable, so that tie-break
        falls out automatically.'''
        for d in solutions:
            d.metrics = self._compute_metrics(d)
            d.is_planar = d.metrics['edge_crossings'] == 0

        kept = [
            d for d in solutions
            if not any(self._dominates(other, d) for other in solutions if other is not d)
        ]
        if not kept:
            return solutions[:1]

        names = list(kept[0].metrics.keys())
        best = {
            name: (max if name in self._MAXIMIZE else min)(d.metrics[name] for d in kept)
            for name in names
        }
        scored = sorted(
            kept,
            key=lambda d: -sum(1 for name in names if d.metrics[name] == best[name]),
        )
        return scored[:self.args.top_n]
