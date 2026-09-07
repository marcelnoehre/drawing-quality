'''
Low-level geometric primitives shared by several metrics.

Kept separate so every metric operates on the same, once-verified
implementations of 'do these segments cross' and 'how far is this point
from that segment' instead of each metric re-deriving (and possibly
mis-deriving) them.
'''
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Hashable, List, Sequence, Tuple

import numpy as np
from shapely.geometry import LineString, Point
from shapely.strtree import STRtree

Position = np.ndarray
PositionMap = Dict[Hashable, Position]
Edge = Tuple[Hashable, Hashable]


@dataclass(frozen=True)
class Crossing:
    '''
    A crossing between two edges that do not share an endpoint.
    '''

    edge_a: Edge
    edge_b: Edge
    point: Tuple[float, float]
    # False for two edges that overlap along a shared sub-segment instead of
    # crossing at a single point (a severe, degenerate drawing fault).
    is_proper: bool


def edge_vector(edge: Edge, positions: PositionMap) -> np.ndarray:
    u, v = edge
    return positions[v] - positions[u]


def find_crossings(edges: Sequence[Edge], positions: PositionMap) -> List[Crossing]:
    '''
    Find all crossings between edges that do not share an endpoint.

    Uses an STRtree for O((n + k) log n) performance instead of the naive
    O(n^2) all-pairs check, where k is the number of candidate pairs the
    tree actually reports.
    '''
    lines = [LineString([positions[u], positions[v]]) for u, v in edges]
    non_degenerate = [i for i, line in enumerate(lines) if line.length > 1e-12]
    if not non_degenerate:
        return []

    tree = STRtree([lines[i] for i in non_degenerate])
    # STRtree.query returns positions into the array it was built from, not
    # the original edge indices, so keep an explicit map back.
    tree_to_edge = non_degenerate

    crossings: List[Crossing] = []
    seen_pairs = set()
    for edge_i in tree_to_edge:
        line = lines[edge_i]
        for local_j in tree.query(line, predicate='intersects'):
            edge_j = tree_to_edge[int(local_j)]
            if edge_j <= edge_i:
                continue
            if (edge_i, edge_j) in seen_pairs:
                continue
            if set(edges[edge_i]) & set(edges[edge_j]):
                continue  # sharing an endpoint is not a crossing
            seen_pairs.add((edge_i, edge_j))

            inter = line.intersection(lines[edge_j])
            if inter.is_empty:
                continue
            if isinstance(inter, Point):
                point = (inter.x, inter.y)
                is_proper = True
            else:
                # Overlapping / collinear-touching segments: shapely returns
                # a LineString (or MultiPoint) instead of a single Point.
                # This is itself a serious drawing fault, so it is reported
                # rather than silently dropped.
                rep = inter.centroid if hasattr(inter, 'centroid') else inter
                point = (rep.x, rep.y)
                is_proper = False
            crossings.append(Crossing(edges[edge_i], edges[edge_j], point, is_proper))
    return crossings


def point_segment_distance(p: np.ndarray, a: np.ndarray, b: np.ndarray) -> float:
    '''
    Euclidean distance from point ``p`` to the segment ``a``-``b``.
    '''
    ab = b - a
    length_sq = float(ab @ ab)
    if length_sq < 1e-18:
        return float(np.linalg.norm(p - a))
    t = np.clip(float((p - a) @ ab) / length_sq, 0.0, 1.0)
    projection = a + t * ab
    return float(np.linalg.norm(p - projection))


def unsigned_angle_deg(u: np.ndarray, v: np.ndarray) -> float:
    '''
    Unsigned angle in degrees between two vectors, in [0, 180].

    Returns ``None``-safe behaviour is not provided: callers must filter out
    zero-length vectors first, since the angle is undefined for them.
    '''
    norm_u = np.linalg.norm(u)
    norm_v = np.linalg.norm(v)
    cos_angle = float(u @ v) / (norm_u * norm_v)
    cos_angle = float(np.clip(cos_angle, -1.0, 1.0))
    return float(np.degrees(np.arccos(cos_angle)))
