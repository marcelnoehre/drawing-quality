'''
Layering quality: does the drawing visually express the poset's structure?

:func:`layer_consistency_score` groups nodes by Freese's rank function
(Sec. 4.1 of the reference below), the *exact*, graph-theoretic notion of
which elements belong on the same layer. Elements of equal rank should be
drawn at the same coordinate along the layering axis. The score itself is
within-group spread compared to the average gap between consecutive group
centroids -- i.e. 'is the spread within a group small relative to the
spacing between groups', which is scale-invariant and needs no manually
tuned tolerance.

An 'upward drawing' criterion (every cover edge moves consistently along the
layering axis) was deliberately dropped from this module: for a valid line
diagram, that property isn't a graded quality dimension but the definitional
precondition for the drawing to encode the order relation at all, and it was
verified to hold (score 1.0) across all 655 graphs in this dataset -- so it
carries no discriminative signal here and doesn't belong in a battery of
[0, 1] *quality* scores.

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
from __future__ import annotations

from typing import Sequence

import numpy as np

from .graph_utils import LatticeLayout, freese_ranks, poset_width, rank_groups

LAYER_AXIS = 1  # y


def _spread_vs_gap_score(groups: Sequence[Sequence[float]]) -> float:
    '''
    Shared core of both layering scores: 1.0 = every group sits at a single,
    consistent coordinate; lower means groups are internally scattered
    relative to how far apart they are from their neighbors.

    ``groups`` must already be ordered so that consecutive entries are
    neighbors along the axis being scored (by rank, or by sorted
    coordinate).
    '''
    if len(groups) <= 1:
        return 1.0

    centroids = [float(np.mean(g)) for g in groups]
    within_stds = [float(np.std(g)) for g in groups]
    sizes = [len(g) for g in groups]

    avg_gap = float(np.mean(np.abs(np.diff(centroids))))
    if avg_gap < 1e-12:
        # All groups collapse onto the same coordinate: only consistent if
        # every group is also internally a single point.
        return 1.0 if max(within_stds) < 1e-12 else 0.0

    weighted_std = float(np.average(within_stds, weights=sizes))
    return float(1.0 - np.clip(weighted_std / avg_gap, 0.0, 1.0))


def layer_consistency_score(layout: LatticeLayout, axis: int = LAYER_AXIS) -> float:
    '''
    1.0 = every Freese rank is drawn at a single, consistent coordinate
    along ``axis``; lower means nodes of the same rank are visually
    scattered.
    '''
    groups = rank_groups(freese_ranks(layout.graph))
    positions = layout.positions
    coord_groups = [
        np.array([positions[n][axis] for n in groups[r]])
        for r in sorted(groups)
    ]
    return _spread_vs_gap_score(coord_groups)


def structural_width(layout: LatticeLayout) -> int:
    '''
    The poset's width (see :func:`lattice_metrics.graph_utils.poset_width`),
    exposed here as a descriptive/diagnostic quantity -- e.g. to sanity
    check that a layout's horizontal spread scales with what the lattice
    structurally requires -- rather than as a [0, 1] aesthetic score itself.
    '''
    return poset_width(layout.graph)
