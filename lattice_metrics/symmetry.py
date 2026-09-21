'''
Left-right visual balance around the lattice's vertical axis.

A concept lattice line diagram is conventionally drawn with its top (the
greatest concept) anchoring a vertical axis that the rest of the drawing is
balanced around. This module scores how well a *drawn* layout realizes that
balance, purely from the drawn x-coordinates -- it does not require the
poset to actually have a mirror automorphism (most real-world lattices
don't), unlike a literal reflective-symmetry check would.

:func:`vertical_axis_balance_score` multiplies three independent [0, 1]
components, each catching a different way a drawing can look lopsided
around the vertical line x = position(top).x:

- ``count_balance``: are there roughly as many nodes left of the axis as
  right of it? Naively summing signed x-offsets can't see this failure
  mode on its own -- e.g. nine nodes sitting just left of the axis and one
  node far to its right sum to (near) zero while looking obviously
  lopsided -- so this compares raw left/right *counts* instead.
- ``mass_balance``: is the total horizontal 'weight' (sum of |offset|, so
  magnitudes on one side can't be cancelled out by the other side's sign)
  roughly equal left vs. right? This is what summing signed offsets is
  actually trying to measure, done without the sign cancellation, and it
  catches the complementary failure ``count_balance`` can't: equal counts
  on each side that are still lopsided because one side's nodes sit much
  further from the axis.
- ``bottom_alignment``: is the lattice's least element -- the drawing's
  other canonical, single fixed point -- itself on the axis? Unlike the
  first two components (judged against the aggregate spread of the whole
  drawing), this is judged against a single average cover-edge length, the
  same scale-relative tolerance used throughout this package (see
  :func:`~lattice_metrics.graph_utils.LatticeLayout.average_cover_edge_length`)
  -- a much finer yardstick, so a given pixel deviation costs this
  component far more than the same deviation costs the other two. This is
  deliberate: the bottom is a single point that should coincide with the
  axis, not one of many nodes whose only requirement is to balance out in
  aggregate.

Requires ``layout.graph`` to have a unique top and bottom element (true of
any concept lattice's Hasse diagram by construction; see
:func:`~lattice_metrics.graph_utils.top_node`/:func:`~lattice_metrics.graph_utils.bottom_node`).
'''
from __future__ import annotations

import numpy as np

from .graph_utils import LatticeLayout, bottom_node, top_node


def _ratio_balance(left: float, right: float) -> float:
    total = left + right
    if total <= 1e-12:
        return 1.0
    return float(1.0 - abs(left - right) / total)


def vertical_axis_balance_score(layout: LatticeLayout) -> float:
    '''
    1.0 = the drawing is fully left-right balanced (both in node count and
    in total horizontal offset) around the vertical line through the top
    element, and the bottom element sits exactly on that line; 0.0 = worst
    case on every component (see module docstring).
    '''
    top = top_node(layout.transitive_closure)
    bottom = bottom_node(layout.transitive_closure)
    axis_x = float(layout.positions[top][0])

    offsets = [
        float(layout.positions[v][0]) - axis_x
        for v in layout.graph.nodes if v != top
    ]

    left_count = sum(1 for o in offsets if o < 0)
    right_count = sum(1 for o in offsets if o > 0)
    count_balance = _ratio_balance(left_count, right_count)

    left_mass = sum(-o for o in offsets if o < 0)
    right_mass = sum(o for o in offsets if o > 0)
    mass_balance = _ratio_balance(left_mass, right_mass)

    bottom_offset = abs(float(layout.positions[bottom][0]) - axis_x)
    tolerance = layout.average_cover_edge_length()
    bottom_alignment = float(1.0 - np.clip(bottom_offset / tolerance, 0.0, 1.0))

    return float(count_balance * mass_balance * bottom_alignment)
