'''
Layering quality: does the drawing visually express the poset's rank
structure?

Elements of the same rank (same longest-path distance from a source) should
be drawn at the same position along the layering axis.

Computed against the *exact* rank of each node (a longest-path layering,
computed once in :class:`~lattice_metrics.graph_utils.LatticeLayout`) rather
than inferred from the drawn coordinates via clustering, which removes a free
clustering-tolerance hyperparameter from the metric entirely.

An 'upward drawing' criterion (every cover edge moves consistently along the
layering axis) was deliberately dropped from this module: for a valid line
diagram, that property isn't a graded quality dimension but the definitional
precondition for the drawing to encode the order relation at all, and it was
verified to hold (score 1.0) across all 655 graphs in this dataset -- so it
carries no discriminative signal here and doesn't belong in a battery of
[0, 1] *quality* scores.
'''
from __future__ import annotations

import numpy as np

from .graph_utils import LatticeLayout, poset_width, rank_groups

LAYER_AXIS = 1  # y


def layer_consistency_score(layout: LatticeLayout, axis: int = LAYER_AXIS) -> float:
    '''
    1.0 = every rank is drawn at a single, consistent coordinate along
    ``axis``; lower means nodes of the same rank are visually scattered.

    The within-rank spread (population std along ``axis``) is compared, per
    rank, to the average gap between consecutive rank centroids -- i.e. 'is
    the spread within a rank small relative to the spacing between ranks',
    which is scale-invariant and needs no manually tuned tolerance.
    '''
    groups = rank_groups(layout.rank)
    if len(groups) <= 1:
        return 1.0

    positions = layout.positions
    centroids = []
    within_rank_stds = []
    within_rank_sizes = []
    for r in sorted(groups):
        coords = np.array([positions[n][axis] for n in groups[r]])
        centroids.append(float(coords.mean()))
        within_rank_stds.append(float(coords.std()))
        within_rank_sizes.append(len(coords))

    avg_gap = float(np.mean(np.abs(np.diff(centroids))))
    if avg_gap < 1e-12:
        # All ranks collapse onto the same coordinate: only consistent if
        # every rank is also internally a single point.
        return 1.0 if max(within_rank_stds) < 1e-12 else 0.0

    weighted_std = float(np.average(within_rank_stds, weights=within_rank_sizes))
    return float(1.0 - np.clip(weighted_std / avg_gap, 0.0, 1.0))


def structural_width(layout: LatticeLayout) -> int:
    '''
    The poset's width (see :func:`lattice_metrics.graph_utils.poset_width`),
    exposed here as a descriptive/diagnostic quantity -- e.g. to sanity
    check that a layout's horizontal spread scales with what the lattice
    structurally requires -- rather than as a [0, 1] aesthetic score itself.
    '''
    return poset_width(layout.graph)
