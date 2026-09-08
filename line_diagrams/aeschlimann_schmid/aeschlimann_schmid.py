from __future__ import annotations

import math
import networkx as nx
import odis

from dataclasses import dataclass
from itertools import combinations
from typing import Dict, List, Optional, Set, Tuple


@dataclass
class Args:
    '''
    Parameters of the Aeschlimann-Schmid "less ink" algorithm (see the
    reference below). Every numeric constant that the paper actually fixes
    (the minimal horizontal distance of 2 units between neighbours on a
    level, §2/§3) is *not* exposed here since changing it would depart from
    the described algorithm; only the constants the paper leaves
    unspecified are collected in this dataclass.

    epsilon : float
        Halting threshold for the X-coordinate iteration (§3, "HALTING
        CONDITION"): iteration stops once the total edge length decreases
        by less than `epsilon` from one iteration to the next (or
        increases). The paper introduces epsilon but never gives it a
        numeric value ("compared to tl of the last iteration ... as soon as
        tl decreases by less than a previously given e > 0"); the default
        below is only a reasonable starting point.
    max_y_iterations : int
        Safety cap on the number of Y-coordinate iteration steps (§2). The
        paper's own halting condition is "no element moves"; this cap only
        guards against a heuristic that never reaches that fixed point.
    max_x_iterations : int
        Safety cap on the number of X-coordinate iteration steps (§3),
        analogous to `max_y_iterations`, guarding against never satisfying
        the epsilon-based halting condition above.
    big_distance : float
        Value substituted for d-up_l(x, y) / d-down_l(x, y) when x and y
        have no common upper (resp. lower) bound in the order -- e.g. when
        they lie in different connected components (§3, "REMARKS": "the
        corresponding value in d-up_l, d-down_l is simply set to a 'big'
        value, e.g., 1000."). Kept at the paper's own example value; for a
        concept lattice (bounded, so every pair has both a meet and a join)
        this value is never actually used.
    '''
    epsilon: float = 1e-3
    max_y_iterations: int = 1000
    max_x_iterations: int = 500
    big_distance: float = 1000.0


class AeschlimannSchmid():
    '''
    The Aeschlimann-Schmid algorithm for drawing Hasse diagrams of finite
    orders "using less ink" (§1-3).

    Y- and X-coordinates are found in two separate, sequential stages
    (§1, "The basic setup is to treat ... Y-coordinates and ... X-coordinates
    ... in two separate stages"). The Y-coordinates are computed first, by
    an iterative heuristic that keeps elements with more upper covers than
    lower covers close to their upper covers and vice versa (§2), and are
    then held fixed. The X-coordinates are then found for one level at a
    time, working outward from the widest level (§3, "INITIALIZATION"),
    followed by an iterative relaxation that moves every element towards a
    weighted mean of its covers' X-coordinates while enforcing a minimal
    horizontal distance of 2 between neighbours on the same level (§3,
    "ITERATION STEP").

    Two points in the paper are stated ambiguously or incompletely (as
    scanned); the choices made here are documented at the point they are
    used:
      - §2's iteration step only gives the update rule for n_u(x) > n_l(x)
        (push up) and n_u(x) = n_l(x) (center); the symmetric case
        n_l(x) > n_u(x) is completed here as "push down" by analogy, see
        `_iterate_y_coordinates`.
      - §3's placement criteria 2/3 for the widest level rank candidates by
        their d-up/d-down values "with respect to the elements ... already
        placed", which is an aggregate over possibly several elements; this
        is read here as the sum of d-up + d-down over those elements, see
        `_rank_initial_candidates`.

    Parameters
    ----------
    context : odis.FormalContext
        The formal context whose concept lattice is drawn.
    args : Optional[Dict]
        A dictionary of parameters overriding the defaults in `Args`.

    Reference
    ---------
    @article{AeschlimannSchmid1992,
        author  = {Aeschlimann, A. and Schmid, J.},
        title   = {Drawing Orders Using Less Ink},
        journal = {Order},
        volume  = {9},
        pages   = {5--13},
        year    = {1992},
        publisher = {Kluwer Academic Publishers}
    }
    '''

    MIN_SPACING: float = 2.0

    def __init__(self,
            context: odis.FormalContext,
            args: Optional[Dict] = None
        ):
        self.context = context
        self.args: Args = Args(**(args or {}))
        self._extents: List[frozenset] = [c.extent.to_frozenset() for c in context.concepts()]
        self.concepts: List[int] = list(range(len(self._extents)))

        self._build_order()
        self._init_y_coordinates()
        self._iterate_y_coordinates()
        self._by_level: Dict[int, List[int]] = self._levels()
        self._init_x_coordinates()
        self._iterate_x_coordinates()

        self.coordinates: Dict[int, Tuple[float, float]] = {
            a: (float(self.X[a]), float(self.Y[a])) for a in self.concepts
        }

    def _build_order(self):
        '''
        Build the order relation among concepts from set inclusion of their
        extents: concept a lies above concept b whenever the extent of b is
        a proper subset of the extent of a. The cover (Hasse) digraph is the
        transitive reduction of that order, with an edge a -> b whenever b
        is a lower cover of a, i.e. a covers b. Also precompute, for every
        element, the set of elements weakly above (resp. below) it, used to
        find common upper/lower bounds in `_d_up` / `_d_down`.
        '''
        order = nx.DiGraph()
        order.add_nodes_from(self.concepts)
        for a, b in combinations(self.concepts, 2):
            if self._extents[b] < self._extents[a]:
                order.add_edge(a, b)
            elif self._extents[a] < self._extents[b]:
                order.add_edge(b, a)
        self._order = order
        self._cover_digraph_ = nx.transitive_reduction(order)
        self._above: Dict[int, Set[int]] = {a: nx.ancestors(order, a) | {a} for a in self.concepts}
        self._below: Dict[int, Set[int]] = {a: nx.descendants(order, a) | {a} for a in self.concepts}

    def children(self, a: int) -> List[int]:
        '''Return the lower covers of a, i.e. y with y -< a (§2).'''
        return list(self._cover_digraph_.successors(a))

    def parents(self, a: int) -> List[int]:
        '''Return the upper covers of a, i.e. y with y >- a (§2).'''
        return list(self._cover_digraph_.predecessors(a))

    def cover_relations(self) -> List[Tuple[int, int]]:
        '''Return the cover relations (a, b) of the order, i.e. a covers b.'''
        return list(self._cover_digraph_.edges())

    def n_upper(self, a: int) -> int:
        '''n_u(a) := card{y; y >- a} (§2).'''
        return len(self.parents(a))

    def n_lower(self, a: int) -> int:
        '''n_l(a) := card{y; y -< a} (§2).'''
        return len(self.children(a))

    # ------------------------------------------------------------------
    # Section 2: Y-coordinates
    # ------------------------------------------------------------------

    def _init_y_coordinates(self):
        '''
        Y(x)^0 = 1 if x has no lower covers, else Y(x)^0 = max{Y(y)^0 | y -< x} + 1
        (§2, "INITIALIZATION"), i.e. the diagram closed downward. Computed
        bottom-up, processing lower covers before the elements they cover.
        '''
        order = list(reversed(list(nx.topological_sort(self._cover_digraph_))))
        self.Y: Dict[int, int] = {}
        for x in order:
            lower_covers = self.children(x)
            self.Y[x] = 1 if not lower_covers else 1 + max(self.Y[y] for y in lower_covers)

    def _iterate_y_coordinates(self):
        '''
        Repeatedly move every element towards its more numerous side (§2,
        "ITERATION STEP") until no element moves, or `max_y_iterations` is
        reached:

          - n_u(x) > n_l(x): push x up as much as possible,
            Y(x) := min{Y(y) | x -< y} - 1.
          - n_u(x) = n_l(x): center x,
            Y(x) := ceil((min{Y(y) | x -< y} + max{Y(y) | y -< x}) / 2).
          - n_l(x) > n_u(x): the paper does not give this case explicitly
            (as scanned); by analogy with the other two (and with the
            initialization rule) it is completed here as "push down as
            much as possible", Y(x) := max{Y(y) | y -< x} + 1.

        All updates within one step use the previous step's Y-values
        (Jacobi-style), matching the Y(x)^(l+1) / Y(y)^l notation.
        '''
        for _ in range(self.args.max_y_iterations):
            new_Y = dict(self.Y)
            moved = False
            for x in self.concepts:
                parents = self.parents(x)
                children = self.children(x)
                n_u, n_l = len(parents), len(children)

                if n_u > n_l:
                    new_Y[x] = min(self.Y[y] for y in parents) - 1
                elif n_l > n_u:
                    new_Y[x] = max(self.Y[y] for y in children) + 1
                elif parents and children:
                    new_Y[x] = math.ceil(
                        (min(self.Y[y] for y in parents) + max(self.Y[y] for y in children)) / 2
                    )
                # n_u == n_l == 0 (an isolated element): nothing to center against, stays put.

                if new_Y[x] != self.Y[x]:
                    moved = True
            self.Y = new_Y
            if not moved:
                break

    def _levels(self) -> Dict[int, List[int]]:
        '''Group concepts by their (now fixed) Y-coordinate, i.e. their level (§3).'''
        by_level: Dict[int, List[int]] = {}
        for x in self.concepts:
            by_level.setdefault(self.Y[x], []).append(x)
        return by_level

    # ------------------------------------------------------------------
    # Section 3: X-coordinates -- common bounds and per-level distances
    # ------------------------------------------------------------------

    def _d_up(self, x: int, y: int) -> float:
        '''
        d-up_l(x, y) := min{Y(z) | z >= x and z >= y} - Y(x) (§3), i.e. the
        distance from x up to its closest common upper bound with y (which
        coincides with Y(x v y) if the order is a lattice, per the §3
        remark). `big_distance` if x and y have no common upper bound.
        '''
        common = self._above[x] & self._above[y]
        if not common:
            return self.args.big_distance
        return min(self.Y[z] for z in common) - self.Y[x]

    def _d_down(self, x: int, y: int) -> float:
        '''
        d-down_l(x, y) := Y(x) - max{Y(z) | z <= x and z <= y} (§3), i.e.
        the distance from x down to its closest common lower bound with y
        (which coincides with Y(x ^ y) if the order is a lattice). `big_distance`
        if x and y have no common lower bound.
        '''
        common = self._below[x] & self._below[y]
        if not common:
            return self.args.big_distance
        return self.Y[x] - max(self.Y[z] for z in common)

    def _sum_level(self, x: int, level: List[int]) -> float:
        '''sum_l(x) := sum over y in level of d-up_l(x, y) + d-down_l(x, y) (§3).'''
        return sum(self._d_up(x, y) + self._d_down(x, y) for y in level if y != x)

    # ------------------------------------------------------------------
    # Section 3: X-coordinates -- initial placement
    # ------------------------------------------------------------------

    def _widest_level(self) -> int:
        '''One of the levels with the maximal number of elements (§3, "INITIALIZATION").'''
        return max(sorted(self._by_level), key=lambda level: len(self._by_level[level]))

    def _rank_initial_candidates(
            self,
            candidates: List[int],
            sums: Dict[int, float],
            same_half: List[int],
            opposite_half: List[int],
            turn: str,
        ) -> int:
        '''
        Pick the next element to place on `turn`'s half of the widest
        level, applying the criteria of §3 in order until a single
        candidate remains:

          1. highest sum_l(x),
          2. lowest sum of d-up_l/d-down_l with respect to `same_half`,
          3. highest sum of d-up_l/d-down_l with respect to `opposite_half`,
          4. lowest (for the left half) or highest (for the right half)
             concept index, used as the "given enumeration of the elements".
        '''
        best = max(sums[x] for x in candidates)
        candidates = [x for x in candidates if sums[x] == best]
        if len(candidates) == 1:
            return candidates[0]

        if same_half:
            scores = {x: sum(self._d_up(x, y) + self._d_down(x, y) for y in same_half) for x in candidates}
            best = min(scores.values())
            candidates = [x for x in candidates if scores[x] == best]
            if len(candidates) == 1:
                return candidates[0]

        if opposite_half:
            scores = {x: sum(self._d_up(x, y) + self._d_down(x, y) for y in opposite_half) for x in candidates}
            best = max(scores.values())
            candidates = [x for x in candidates if scores[x] == best]
            if len(candidates) == 1:
                return candidates[0]

        return min(candidates) if turn == 'left' else max(candidates)

    def _place_widest_level(self, level: List[int]) -> Dict[int, float]:
        '''
        Order the elements of the widest level alternately onto a left and
        a right half, moving from the border towards the center (§3,
        "INITIALIZATION"), then space the resulting left-to-right order by
        `MIN_SPACING`, centered on 0.
        '''
        sums = {x: self._sum_level(x, level) for x in level}
        remaining = set(level)
        left: List[int] = []
        right: List[int] = []
        turn = 'left'

        while remaining:
            candidates = list(remaining)
            same_half, opposite_half = (left, right) if turn == 'left' else (right, left)
            chosen = self._rank_initial_candidates(candidates, sums, same_half, opposite_half, turn)
            same_half.append(chosen)
            remaining.discard(chosen)
            turn = 'right' if turn == 'left' else 'left'

        # left[0]/right[0] are the border (outermost) elements, subsequent
        # entries move towards the center; the physical left-to-right order
        # is therefore left as-is, followed by right reversed.
        physical_order = left + list(reversed(right))
        n = len(physical_order)
        return {
            x: self.MIN_SPACING * (i - (n - 1) / 2)
            for i, x in enumerate(physical_order)
        }

    def _pack_level(self, raw: Dict[int, float]) -> Dict[int, int]:
        '''
        Enforce a minimal horizontal distance of `MIN_SPACING` between
        neighbours on a level (§3). Elements are scanned left to right
        (sorted by their raw coordinate); a cluster is a maximal run of
        consecutive elements whose breadth (max - min raw coordinate) is at
        most `MIN_SPACING * (count - 1)` -- exactly the definition of §3's
        "ITERATION STEP" -- and is applied here to any raw placement, not
        only the one arising from that iteration step. Each cluster is then
        spread out to have exactly `MIN_SPACING` between neighbours while
        keeping the mean of its raw coordinates invariant, and rounded to
        integers.
        '''
        order = sorted(raw, key=lambda n: (raw[n], n))
        xs = [raw[n] for n in order]
        count = len(order)
        positions: Dict[int, float] = {}

        i = 0
        while i < count:
            j = i
            while j + 1 < count and (xs[j + 1] - xs[i]) <= self.MIN_SPACING * (j + 1 - i):
                j += 1
            members = order[i:j + 1]
            mean = sum(xs[i:j + 1]) / len(members)
            start = mean - (len(members) - 1) * self.MIN_SPACING / 2
            for k, node in enumerate(members):
                positions[node] = start + k * self.MIN_SPACING
            i = j + 1

        return {node: round(pos) for node, pos in positions.items()}

    def _init_x_coordinates(self):
        '''
        Place the widest level first, then propagate outward one level at a
        time (§3, "INITIALIZATION"): each element of the next *higher*
        level gets its initial X-coordinate as the mean of the
        X-coordinates of its lower covers that are already known, and,
        symmetrically, each element of the next *lower* level uses its
        upper covers ("the initial X-coordinates of the elements in the
        next higher level ... determined as mean values of the
        X-coordinates of lower covers that are already known ... This step
        is repeated for the level just below the initial one"). An element
        with no already-known cover in the expected direction is postponed
        to a second pass, using whichever of its covers (upper or lower)
        are known by then; for a bounded lattice (unique top and bottom,
        hence connected) this always succeeds once enough of the lattice is
        placed, so the paper's fallback for genuinely disconnected orders
        ("assign it an X-coordinate outside the range already used") does
        not apply here.
        '''
        widest = self._widest_level()
        self.X: Dict[int, float] = self._pack_level(self._place_widest_level(self._by_level[widest]))

        levels = sorted(self._by_level)
        postponed: List[int] = []

        for level in [l for l in levels if l > widest]:
            self._init_level_x_coordinates(level, self.children, postponed)
        for level in reversed([l for l in levels if l < widest]):
            self._init_level_x_coordinates(level, self.parents, postponed)

        self._retry_postponed(postponed)

    def _init_level_x_coordinates(self, level: int, covering_fn, postponed: List[int]):
        '''
        Assign initial X-coordinates to `level` from the mean of the
        already-known positions given by `covering_fn` (`self.children` when
        propagating upward from the widest level, `self.parents` when
        propagating downward, §3 "INITIALIZATION"); elements with no
        already-known cover in that direction are appended to `postponed`.
        '''
        raw = {}
        for x in self._by_level[level]:
            covers = [y for y in covering_fn(x) if y in self.X]
            if covers:
                raw[x] = sum(self.X[y] for y in covers) / len(covers)
            else:
                postponed.append(x)
        if raw:
            self.X.update(self._pack_level(raw))

    def _retry_postponed(self, postponed: List[int]):
        '''
        Second pass over elements that had no already-known cover in their
        expected direction when their level was first processed (e.g. a
        cover relation spanning more than one level): assign them from
        whichever of their covers (upper or lower) are known by now,
        repeating until no further progress is made.
        '''
        changed = True
        while postponed and changed:
            changed = False
            still_postponed = []
            for x in postponed:
                covers = [y for y in self.parents(x) + self.children(x) if y in self.X]
                if covers:
                    level = self.Y[x]
                    raw = {n: self.X[n] for n in self._by_level[level] if n in self.X}
                    raw[x] = sum(self.X[y] for y in covers) / len(covers)
                    self.X.update(self._pack_level(raw))
                    changed = True
                else:
                    still_postponed.append(x)
            postponed = still_postponed

    # ------------------------------------------------------------------
    # Section 3: X-coordinates -- iteration step
    # ------------------------------------------------------------------

    def _x_good(self, x: int) -> float:
        '''
        X_good(x) := weighted mean of the X-coordinates of x's upper and
        lower covers, weighted by 1/|Y(y) - Y(x)| (§3, "ITERATION STEP").
        '''
        covers = self.parents(x) + self.children(x)
        weights = []
        for y in covers:
            dy = abs(self.Y[y] - self.Y[x])
            weights.append(1.0 / dy if dy > 0 else self.args.big_distance)
        return sum(w * self.X[y] for w, y in zip(weights, covers)) / sum(weights)

    def _iterate_x_coordinates(self):
        '''
        Repeatedly move every element towards `X_good` (weighted by its
        number of covers), then re-pack every level to restore the minimal
        horizontal distance of `MIN_SPACING` (§3, "ITERATION STEP"), until
        the total edge length fails to decrease by at least `epsilon`, or
        `max_x_iterations` is reached (§3, "HALTING CONDITION").
        '''
        previous_length = self._total_edge_length()
        for _ in range(self.args.max_x_iterations):
            dragged: Dict[int, float] = {}
            for x in self.concepts:
                n = self.n_upper(x) + self.n_lower(x)
                if n == 0:
                    dragged[x] = self.X[x]
                    continue
                factor = 1 - 2.0 ** (-n)
                dragged[x] = self.X[x] + factor * (self._x_good(x) - self.X[x])

            new_X: Dict[int, int] = {}
            for level, elements in self._by_level.items():
                new_X.update(self._pack_level({x: dragged[x] for x in elements}))
            self.X = new_X

            length = self._total_edge_length()
            if previous_length - length < self.args.epsilon:
                break
            previous_length = length

    def _total_edge_length(self) -> float:
        '''Total Euclidean length tl of the cover relations' straight-line edges (§3).'''
        return sum(
            math.hypot(self.X[a] - self.X[b], self.Y[a] - self.Y[b])
            for a, b in self.cover_relations()
        )
