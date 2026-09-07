'''
Visual chain linearity.

A chain in the poset (u < v < w, ...) is drawn 'straight' when consecutive
elements lie on a common line. Rather than enumerating every maximal chain
(exponential in the number of source-to-sink paths for wide lattices, and
inflating the score by however many maximal chains happen to reuse the same
sub-path), we score straightness locally: at every vertex v of the Hasse
diagram (transitive reduction) that has both a predecessor u and a successor
w, the pair (u, v, w) is itself a valid three-element chain, and every
three-element sub-chain of every maximal chain shows up this way exactly
once. This makes the metric O(sum(indeg(v) * outdeg(v))) instead of
exponential, and removes the need for an arbitrary 'close enough to
collinear' threshold or a post-hoc normalization against a longest-chain
heuristic.
'''
from __future__ import annotations

from .graph_utils import LatticeLayout
from .geometry import unsigned_angle_deg


def visual_chain_linearity_score(layout: LatticeLayout) -> float:
    '''
    1.0 = every chain that passes through a shared vertex is drawn as a
    straight line there; 0.0 = every such chain folds back on itself.

    Returns 1.0 for layouts with no vertex having both a predecessor and a
    successor in the Hasse diagram (i.e. no interior chain vertex exists to
    measure), since there is nothing to penalize.
    '''
    tr = layout.transitive_reduction
    positions = layout.positions

    straightness = []
    for v in tr.nodes:
        preds = list(tr.predecessors(v))
        succs = list(tr.successors(v))
        if not preds or not succs:
            continue
        pv = positions[v]
        for u in preds:
            vec_to_u = positions[u] - pv
            if float(vec_to_u @ vec_to_u) < 1e-18:
                continue
            for w in succs:
                vec_to_w = positions[w] - pv
                if float(vec_to_w @ vec_to_w) < 1e-18:
                    continue
                angle = unsigned_angle_deg(vec_to_u, vec_to_w)
                # angle == 180 <=> u, v, w collinear with v between them.
                straightness.append(angle / 180.0)

    if not straightness:
        return 1.0
    return float(sum(straightness) / len(straightness))
