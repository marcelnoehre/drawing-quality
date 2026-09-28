'''
Layering quality: does the drawing visually express the poset's structure?

:func:`layer_consistency_score` compares each node's axis coordinate to its
Freese rank (Sec. 4.1 of the reference below), the *exact*, graph-theoretic
notion of which elements belong on the same layer -- the same quantity
line_diagrams/freese/freese.py itself uses to seed the layering axis. The
score is the R^2 (squared Pearson correlation) of the least-squares affine
fit between rank and coordinate: 1.0 means the coordinate is a perfect
(possibly rescaled/reflected) affine function of rank, which both requires
equal-rank nodes to land at equal coordinates *and* requires unequal ranks
to be spaced proportionally to their rank difference. R^2 is scale-invariant
and needs no manually tuned tolerance, and unlike a purely within-group
comparison it stays meaningful even when every rank is unique (e.g. a
chain), where there is nothing to compare *within* a rank group.

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

import numpy as np

from .graph_utils import LatticeLayout, freese_ranks, poset_width

LAYER_AXIS = 1  # y


def _rank_alignment_score(ranks: np.ndarray, coords: np.ndarray) -> float:
    '''
    R^2 of the least-squares affine fit ``coord ~ a * rank + b``: 1.0 = the
    coordinate is a perfect affine function of rank, 0.0 = no linear
    relationship. Well-defined even when every rank is unique, unlike a
    within-rank-group spread comparison.
    '''
    if np.ptp(ranks) < 1e-12:
        # Every node shares one rank: nothing for the axis to align with.
        return 1.0
    if np.ptp(coords) < 1e-12:
        # Collapsed onto one coordinate despite >1 distinct rank: no linear
        # relationship is possible, so this can't be considered aligned.
        return 0.0

    r = float(np.corrcoef(ranks, coords)[0, 1])
    return r ** 2


def layer_consistency_score(layout: LatticeLayout, axis: int = LAYER_AXIS) -> float:
    '''
    1.0 = the ``axis`` coordinate is a perfect affine function of Freese
    rank (equal ranks at equal coordinates, unequal ranks spaced
    proportionally to their rank difference); lower means the drawing's
    layering doesn't track the poset's intrinsic rank structure.
    '''
    ranks = freese_ranks(layout.graph)
    positions = layout.positions
    nodes = list(ranks)
    rank_arr = np.array([ranks[n] for n in nodes], dtype=float)
    coord_arr = np.array([positions[n][axis] for n in nodes], dtype=float)
    return _rank_alignment_score(rank_arr, coord_arr)


def structural_width(layout: LatticeLayout) -> int:
    '''
    The poset's width (see :func:`lattice_metrics.graph_utils.poset_width`),
    exposed here as a descriptive/diagnostic quantity -- e.g. to sanity
    check that a layout's horizontal spread scales with what the lattice
    structurally requires -- rather than as a [0, 1] aesthetic score itself.
    '''
    return poset_width(layout.graph)
