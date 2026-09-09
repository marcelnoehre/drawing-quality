'''
Layering quality: does the drawing visually express the poset's structure?

Two independent notions of 'layer', each scored the same way (within-group
spread compared to the average gap between consecutive group centroids --
i.e. 'is the spread within a group small relative to the spacing between
groups', which is scale-invariant and needs no manually tuned tolerance):

- :func:`layer_consistency_score` groups nodes by Freese's rank function
  (Sec. 4.1 of the reference below), the *exact*, graph-theoretic notion of
  which elements belong on the same layer. Elements of equal rank should be
  drawn at the same coordinate along the layering axis.
- :func:`visual_layer_y_score` and :func:`visual_layer_x_score` instead
  infer groups from the drawn coordinates themselves via gap-threshold
  clustering -- so, unlike the rank-based score, neither requires a drawn
  layer to line up with a single graph-theoretic rank: a tidy row or column
  that merges adjacent ranks (or splits one) still scores well, as long as
  it is internally tight relative to its neighbors. Because these groups
  are inferred rather than fixed by graph structure, internal tightness
  alone isn't enough: a layout that never merges any two nodes (every node
  its own singleton 'group') is trivially perfectly tight with nothing to
  compare it against, even though it shows no layering at all.
  :func:`visual_layer_y_score` corrects this by also scoring how closely
  the *number* of groups found matches the number of distinct Freese ranks
  -- the standard convention that rows correspond to ranks.
  :func:`visual_layer_x_score` deliberately has no equivalent correction:
  poset width (the antichain bound on how many columns a valid drawing
  structurally needs) is a lower bound, not a target -- a node incomparable
  to nothing (e.g. a lone root) still reasonably gets its own column beyond
  what width alone would suggest, so there is no equally solid convention
  for an 'expected' column count to score against, and inventing one would
  be exactly the kind of unjustified assumption this module otherwise
  avoids. :func:`visual_layer_x_score` is reported as tightness-only, and
  documented as such, rather than silently blended with the stronger
  y-axis score into one number that would hide which axis the guarantee
  actually holds for.

  The two are deliberately kept as separate scores rather than combined
  into one 'visual layer' number: they are not equally well-founded (y has
  the Freese-rank-count correction, x does not), and multiplying them would
  bury that asymmetry inside a single figure instead of surfacing it.

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

from typing import List, Sequence

import numpy as np

from .graph_utils import LatticeLayout, freese_ranks, group_within_tolerance, poset_width, rank_groups

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


def _layer_count_agreement(k: int, n: int, expected: int) -> float:
    '''
    1.0 when the observed number of groups ``k`` exactly matches the
    structurally ``expected`` count; degrades linearly to 0 as ``k`` moves
    toward either extreme -- ``k = 1`` (every node merged into one group) or
    ``k = n`` (no two nodes ever merge, the degenerate case
    :func:`_spread_vs_gap_score` cannot see on its own, since an all-
    singleton grouping is trivially 'internally tight' regardless of how
    scattered the drawing actually is).
    '''
    expected = min(max(expected, 1), n)
    if k == expected:
        return 1.0
    span = (n - expected) if k > expected else (expected - 1)
    if span <= 0:
        return 1.0
    return float(1.0 - abs(k - expected) / span)


def _visual_axis_tolerance(layout: LatticeLayout, tolerance_fraction: float) -> float:
    return tolerance_fraction * layout.average_cover_edge_length()


def _visual_axis_groups(layout: LatticeLayout, axis: int, tolerance: float) -> List[np.ndarray]:
    coords = np.sort(np.array([p[axis] for p in layout.positions.values()]))
    if len(coords) <= 1:
        return [coords]
    return group_within_tolerance(coords, tolerance)


def visual_layer_y_score(layout: LatticeLayout, tolerance_fraction: float = 0.25) -> float:
    '''
    1.0 = the drawing's rows are both internally tight and close in number
    to the poset's actual count of distinct Freese ranks; lower means
    either the rows are scattered relative to their spacing, or there are
    too many or too few of them relative to that structural expectation
    (see :func:`_layer_count_agreement`).

    Rows are inferred directly from the drawn y-coordinates (gap-threshold
    clustering, equivalent to DBSCAN(eps=tolerance, min_samples=1) -- see
    :func:`~lattice_metrics.graph_utils.group_within_tolerance`) rather than
    from graph structure, so a row that merges or splits adjacent Freese
    ranks is not penalized on its own, as long as it is itself tidy and the
    resulting row count is still structurally plausible. ``tolerance`` is
    set relative to the drawing's own scale (``tolerance_fraction`` of the
    average cover-edge length) rather than as an absolute constant, so it
    isn't tied to any particular coordinate system.
    '''
    tolerance = _visual_axis_tolerance(layout, tolerance_fraction)
    groups = _visual_axis_groups(layout, LAYER_AXIS, tolerance)
    n = sum(len(g) for g in groups)
    if n <= 1:
        return 1.0

    tightness = _spread_vs_gap_score(groups)
    expected_rows = len(set(freese_ranks(layout.graph).values()))
    agreement = _layer_count_agreement(len(groups), n, expected_rows)
    return float(tightness * agreement)


def visual_layer_x_score(layout: LatticeLayout, tolerance_fraction: float = 0.25) -> float:
    '''
    1.0 = the drawing's columns are internally tight relative to their
    spacing; lower means columns are visually scattered.

    Columns are inferred directly from the drawn x-coordinates the same way
    :func:`visual_layer_y_score` infers rows (gap-threshold clustering, see
    :func:`~lattice_metrics.graph_utils.group_within_tolerance`), but with
    no equivalent correction for how many columns there 'should' be -- see
    the module docstring for why no such correction is applied here. This
    score is therefore tightness-only, and -- unlike the y-axis score --
    still trivially returns 1.0 for a layout that never merges any two
    nodes into a shared column.
    '''
    tolerance = _visual_axis_tolerance(layout, tolerance_fraction)
    groups = _visual_axis_groups(layout, 1 - LAYER_AXIS, tolerance)
    if sum(len(g) for g in groups) <= 1:
        return 1.0
    return _spread_vs_gap_score(groups)


def structural_width(layout: LatticeLayout) -> int:
    '''
    The poset's width (see :func:`lattice_metrics.graph_utils.poset_width`),
    exposed here as a descriptive/diagnostic quantity -- e.g. to sanity
    check that a layout's horizontal spread scales with what the lattice
    structurally requires -- rather than as a [0, 1] aesthetic score itself.
    '''
    return poset_width(layout.graph)
