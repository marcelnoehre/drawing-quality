from __future__ import annotations

import numpy as np
import networkx as nx
import odis

from dataclasses import dataclass
from itertools import combinations
from typing import Dict, List, Optional, Tuple


@dataclass
class Args:
    '''
    Parameters of Freese's force-directed placement algorithm (see §4.2/§4.3
    of the reference). None of these constants are specified numerically in
    the paper; the defaults below are only a reasonable starting point.

    c_rep : float
        Repulsion force constant c_rep.
    c_att : float
        Attraction force constant c_att.
    strong_factor : float
        Factor by which the dominant force of a phase is scaled up relative
        to its base value, cf. §4.3 ("first with the repulsion force strong
        ... then with the attraction force strong and finally with balanced
        forces").
    iterations : int
        Maximum number of force applications performed in each of the three
        phases.
    dt : float
        Step size turning a force into a displacement per iteration (heavy
        damping, §4.2: "imagine the points lying in a thick syrup", i.e. the
        velocity of a point is proportional to the force acting on it).
    tol : float
        A phase stops iterating early once every point moves less than
        `tol` in one step ("iterated until the diagram becomes stable",
        §4.3).
    perturbation : float
        Magnitude of the random perturbation added to the initial circular
        placement to avoid unstable equilibria (§4.2).
    theta : Optional[float]
        Fixed rotation angle (radians) used for the final projection
        <x,y,z> -> <x cos(theta) + y sin(theta), z> (§4.3). If None, the
        angle minimizing the number of edge crossings of the diagram is
        chosen automatically (§5.1).
    theta_samples : int
        Number of candidate angles sampled in [0, 2*pi) when the projection
        angle is chosen automatically.
    min_separation_fraction : float
        A candidate angle is only considered readable if the smallest
        pairwise distance between its projected elements is at least this
        fraction of the best such distance achievable over all sampled
        angles. Among the readable angles the one minimizing the number of
        edge crossings is chosen (ties broken by maximal separation); see
        `_project`.
    seed : Optional[int]
        Seed for the random perturbation, for reproducibility.
    '''
    c_rep: float = 1.0
    c_att: float = 0.05
    strong_factor: float = 6.0
    iterations: int = 200
    dt: float = 0.05
    tol: float = 1e-4
    perturbation: float = 0.1
    theta: Optional[float] = None
    theta_samples: int = 360
    min_separation_fraction: float = 0.5
    seed: Optional[int] = 0


class Freese():
    '''
    Freese's force-directed algorithm for drawing (finite) lattices as Hasse
    diagrams.

    The algorithm places every element of the ordered set in 3-space. The
    z-coordinate (height) of an element is fixed once and for all by a rank
    function combining its height and depth in the order (§4.1). The
    x,y-coordinates are then found by repeatedly applying, in three phases
    with different relative strengths, an attractive force between all
    pairs of comparable elements and a repulsive force between all pairs of
    incomparable elements (§4.2, §4.3). Finally the 3D layout is projected
    to the plane by a rotation of the x,y-coordinates around the z-axis
    (§4.3).

    Parameters
    ----------
    context : odis.FormalContext
        The formal context whose concept lattice is drawn.
    args : Optional[Dict]
        A dictionary of parameters overriding the defaults in `Args`.

    Reference
    ---------
    @inproceedings{Freese2004,
        author    = {Freese, Ralph},
        title     = {Automated Lattice Drawing},
        booktitle = {Concept Lattices, Second International Conference on
                     Formal Concept Analysis, ICFCA 2004},
        series    = {Lecture Notes in Computer Science},
        volume    = {2961},
        publisher = {Springer},
        pages     = {112--127},
        year      = {2004}
    }
    '''

    def __init__(self,
            context: odis.FormalContext,
            args: Optional[Dict] = None
        ):
        self.context = context
        self.args: Args = Args(**(args or {}))
        self._extents: List[frozenset] = [c.extent.to_frozenset() for c in context.concepts()]
        self.concepts: List[int] = list(range(len(self._extents)))
        self._rng = np.random.default_rng(self.args.seed)

        self._build_order()
        self._rank_function()
        self._comparability()
        self._initialize_points()
        self._force_iteration()
        self._project()

    def _build_order(self):
        '''
        Build the order relation among concepts from set inclusion of their
        extents: concept a lies above concept b whenever the extent of b is
        a proper subset of the extent of a. The cover (Hasse) digraph is
        the transitive reduction of that order, with an edge a -> b
        whenever b is a lower cover of a, i.e. a covers b.
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

    def _cover_digraph(self) -> nx.DiGraph:
        return self._cover_digraph_

    def children(self, a: int) -> List[int]:
        '''
        Return direct child concept indices of a given concept, i.e. its
        lower covers.
        '''
        return list(self._cover_digraph_.successors(a))

    def parents(self, a: int) -> List[int]:
        '''
        Return direct parent concept indices of a given concept, i.e. its
        upper covers.
        '''
        return list(self._cover_digraph_.predecessors(a))

    def cover_relations(self) -> List[Tuple[int, int]]:
        '''
        Return the cover relations (a, b) of the lattice, i.e. a covers b.
        '''
        return list(self._cover_digraph_.edges())

    def _rank_function(self):
        '''
        Compute the rank function of §4.1,

            rank(a) = height(a) - depth(a) + M,

        where height(a) is the length of the longest chain from a down to a
        minimal element, depth(a) is the length of the longest chain from a
        up to a maximal element, and M is the length of the longest chain in
        P, chosen so that the rank of the least element of a lattice is 0.
        '''
        cover_digraph = self._cover_digraph()
        order = list(nx.topological_sort(cover_digraph))

        # depth(a): parents (upper covers) are processed before a
        self.depth: Dict[int, int] = {}
        for a in order:
            upper_covers = self.parents(a)
            self.depth[a] = 0 if not upper_covers else 1 + max(self.depth[p] for p in upper_covers)

        # height(a): children (lower covers) are processed before a
        self.height: Dict[int, int] = {}
        for a in reversed(order):
            lower_covers = self.children(a)
            self.height[a] = 0 if not lower_covers else 1 + max(self.height[c] for c in lower_covers)

        M = max(self.height[a] + self.depth[a] for a in self.concepts)
        self.rank: Dict[int, int] = {a: self.height[a] - self.depth[a] + M for a in self.concepts}

    def _comparability(self):
        '''
        Split all pairs of distinct elements into the comparable pairs,
        which attract each other, and the incomparable pairs, which repel
        each other (§4.2).
        '''
        self.comparable_pairs: List[Tuple[int, int]] = list(self._order.edges())
        self.incomparable_pairs: List[Tuple[int, int]] = list(nx.complement(self._order.to_undirected()).edges())

    def _initialize_points(self):
        '''
        Associate a point (x, y, z) in 3-space with every element (§4.2).
        The z-coordinate is the rank computed above. Points of the same
        rank are placed with equal spacing around a circle, parallel to the
        x-y plane, of radius equal to the number of elements of that rank;
        a small random perturbation is added to avoid unstable equilibria.
        '''
        by_rank: Dict[int, List[int]] = {}
        for a in self.concepts:
            by_rank.setdefault(self.rank[a], []).append(a)

        self.z: Dict[int, float] = {a: float(self.rank[a]) for a in self.concepts}
        self.x: Dict[int, float] = {}
        self.y: Dict[int, float] = {}

        for elements in by_rank.values():
            n_r = len(elements)
            radius = float(n_r)
            for i, a in enumerate(elements):
                angle = 2 * np.pi * i / n_r
                jitter = self._rng.uniform(-self.args.perturbation, self.args.perturbation, size=2)
                self.x[a] = radius * np.cos(angle) + jitter[0]
                self.y[a] = radius * np.sin(angle) + jitter[1]

    def _forces(self, c_att: float, c_rep: float) -> Dict[int, np.ndarray]:
        '''
        Compute the total force acting on every point for the current
        positions (§4.2). Comparable points attract each other with a force
        proportional to their x,y-displacement (a spring of natural length
        0); incomparable points repel each other with a force following an
        inverse-cube law of their coordinate-wise displacements. Both
        forces lie in the x-y plane, so the z-coordinate never changes.

        Parameters
        ----------
        c_att : float
            The attraction force constant used for this call.
        c_rep : float
            The repulsion force constant used for this call.

        Returns
        -------
        force : Dict[int, np.ndarray]
            The total force (x, y) acting on every element.
        '''
        force = {a: np.zeros(2) for a in self.concepts}

        for (a, b) in self.comparable_pairs:
            delta = np.array([self.x[b] - self.x[a], self.y[b] - self.y[a]])
            f = c_att * delta
            force[a] += f
            force[b] -= f

        for (a, b) in self.incomparable_pairs:
            dx = self.x[b] - self.x[a]
            dy = self.y[b] - self.y[a]
            dz = self.z[b] - self.z[a]
            denom = abs(dx) ** 3 + abs(dy) ** 3 + abs(dz) ** 3

            if denom == 0:
                # degenerate coincidence of two incomparable points: nudge them
                # apart in an arbitrary direction to escape the singularity
                direction = self._rng.normal(size=2)
                direction /= np.linalg.norm(direction)
                f = c_rep * direction
            else:
                f = c_rep * np.array([-dx, -dy]) / denom

            force[a] += f
            force[b] -= f

        return force

    def _force_iteration(self):
        '''
        Repeatedly apply the forces to the points in three phases (§4.3):
        first with the repulsion force strong, then with the attraction
        force strong, and finally with balanced forces. Only the
        x,y-coordinates are updated; the z-coordinate (rank) stays fixed.
        '''
        phases = [
            (self.args.c_att, self.args.c_rep * self.args.strong_factor),
            (self.args.c_att * self.args.strong_factor, self.args.c_rep),
            (self.args.c_att, self.args.c_rep),
        ]

        for c_att, c_rep in phases:
            for _ in range(self.args.iterations):
                force = self._forces(c_att, c_rep)
                max_move = 0.0
                for a in self.concepts:
                    dx, dy = force[a] * self.args.dt
                    self.x[a] += dx
                    self.y[a] += dy
                    max_move = max(max_move, float(np.hypot(dx, dy)))
                if max_move < self.args.tol:
                    break

    def _project(self):
        '''
        Project the 3D layout to the plane via the family of projections
        <x, y, z> -> <x cos(theta) + y sin(theta), z> (section 4.3). If
        `args.theta` is given it is used directly; otherwise theta is
        chosen among `theta_samples` equally spaced candidates in
        [0, 2*pi). A projection that lets two distinct elements coincide is
        a degenerate diagram regardless of its crossing number, so
        candidates whose smallest pairwise projected distance falls below
        `min_separation_fraction` of the best such distance achievable are
        first discarded as unreadable; among the remaining, readable
        candidates the angle minimizing the number of pairwise crossings
        among the straight line segments of the Hasse diagram's cover
        edges is chosen, the "niceness" criterion discussed in section
        5.1 (ties broken by maximal separation).
        '''
        cover_edges = self.cover_relations()

        if self.args.theta is not None:
            theta = self.args.theta
        else:
            thetas = np.linspace(0, 2 * np.pi, self.args.theta_samples, endpoint=False)
            separations = np.array([self._min_point_separation(t) for t in thetas])
            threshold = self.args.min_separation_fraction * separations.max()
            readable = thetas[separations >= threshold]

            crossings = np.array([self._count_crossings(t, cover_edges) for t in readable])
            min_crossings = crossings.min()
            candidates = readable[crossings == min_crossings]
            theta = max(candidates, key=self._min_point_separation)

        self.theta: float = float(theta)
        self.coordinates: Dict[int, Tuple[float, float]] = {
            a: (self.x[a] * np.cos(theta) + self.y[a] * np.sin(theta), self.z[a])
            for a in self.concepts
        }

    def _count_crossings(self, theta: float, edges: List[Tuple[int, int]]) -> int:
        '''
        Count the number of pairwise proper crossings among the straight
        line segments of the Hasse diagram's cover edges under the
        projection angle `theta`.

        Parameters
        ----------
        theta : float
            The candidate projection angle (radians).
        edges : List[Tuple[int, int]]
            The cover relations of the lattice.

        Returns
        -------
        crossings : int
        '''
        proj = {
            a: np.array([self.x[a] * np.cos(theta) + self.y[a] * np.sin(theta), self.z[a]])
            for a in self.concepts
        }

        crossings = 0
        for (a, b), (c, d) in combinations(edges, 2):
            if {a, b} & {c, d}:
                # edges sharing an endpoint meet at a vertex; not a crossing
                continue
            if self._segments_intersect(proj[a], proj[b], proj[c], proj[d]):
                crossings += 1

        return crossings

    def _min_point_separation(self, theta: float) -> float:
        '''
        Compute the smallest pairwise distance between the projected
        positions of two distinct elements under the projection angle
        `theta`, used as a tie-breaking niceness criterion in `_project`.

        Parameters
        ----------
        theta : float
            The candidate projection angle (radians).

        Returns
        -------
        min_distance : float
        '''
        projected_x = np.array([self.x[a] * np.cos(theta) + self.y[a] * np.sin(theta) for a in self.concepts])
        z = np.array([self.z[a] for a in self.concepts])
        points = np.stack([projected_x, z], axis=1)
        distances = np.linalg.norm(points[:, None, :] - points[None, :, :], axis=-1)
        np.fill_diagonal(distances, np.inf)
        return float(distances.min())

    @staticmethod
    def _segments_intersect(p1: np.ndarray, p2: np.ndarray, p3: np.ndarray, p4: np.ndarray, eps: float = 1e-9) -> bool:
        '''
        Standard orientation-based test for the intersection of the two
        closed segments p1p2 and p3p4, including the degenerate case of
        overlapping collinear segments.

        Parameters
        ----------
        p1, p2 : np.ndarray
            Endpoints of the first segment.
        p3, p4 : np.ndarray
            Endpoints of the second segment.
        eps : float
            Numerical tolerance used to decide collinearity.

        Returns
        -------
        intersect : bool
        '''
        def orientation(a, b, c) -> int:
            val = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
            if abs(val) < eps:
                return 0
            return 1 if val > 0 else -1

        def on_segment(a, b, c) -> bool:
            # c is assumed collinear with a, b; check containment in the bounding box
            return (min(a[0], b[0]) - eps <= c[0] <= max(a[0], b[0]) + eps and
                    min(a[1], b[1]) - eps <= c[1] <= max(a[1], b[1]) + eps)

        o1 = orientation(p1, p2, p3)
        o2 = orientation(p1, p2, p4)
        o3 = orientation(p3, p4, p1)
        o4 = orientation(p3, p4, p2)

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
