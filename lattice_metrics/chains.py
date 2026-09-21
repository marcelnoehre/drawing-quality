'''
Visual chain linearity.

A chain in the poset (u < v < w, ...) is drawn 'straight' when consecutive
elements lie on a common line. Rather than enumerating every maximal chain
(exponential in the number of source-to-sink paths for wide lattices, and
inflating the score by however many maximal chains happen to reuse the same
sub-path), we score straightness locally: at every vertex v of the Hasse
diagram (transitive reduction) that has both a predecessor and a successor,
every three-element sub-chain of every maximal chain through v shows up as
some pair (u, v, w) with u a predecessor and w a successor.

Scoring *every* such pair (the full indeg(v) x outdeg(v) cross product) and
averaging them is unrealistic whenever v has more than one predecessor or
more than one successor: distinct predecessors sit in distinct directions
from v, so at most one of them can be collinear with any given successor --
demanding that every predecessor line up straight with every successor
simultaneously is a geometric impossibility, not a drawing flaw, and
penalizes wide vertices for it. Instead, we only require every neighbor on
v's *smaller* side (fewer predecessors than successors, or vice versa) to
have *some* straight-enough partner on the other side: for each neighbor on
the smaller side we take its best (straightest, i.e. minimum angular
deviation from a straight line) match among the neighbors on the larger
side, and average those best-match scores. This keeps the metric
O(sum(indeg(v) * outdeg(v))) instead of exponential, and removes the need
for an arbitrary 'close enough to collinear' threshold or a post-hoc
normalization against a longest-chain heuristic.
'''
from __future__ import annotations

from .graph_utils import LatticeLayout
from .geometry import unsigned_angle_deg


def visual_chain_linearity_score(layout: LatticeLayout) -> float:
    '''
    1.0 = every neighbor on each vertex's smaller side (predecessors or
    successors, whichever is fewer) has some straight-line partner on the
    other side; 0.0 = every such neighbor's best available partner folds
    all the way back on itself.

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

        pred_vecs = [positions[u] - pv for u in preds]
        pred_vecs = [vec for vec in pred_vecs if float(vec @ vec) >= 1e-18]
        succ_vecs = [positions[w] - pv for w in succs]
        succ_vecs = [vec for vec in succ_vecs if float(vec @ vec) >= 1e-18]
        if not pred_vecs or not succ_vecs:
            continue

        if len(pred_vecs) <= len(succ_vecs):
            primary, secondary = pred_vecs, succ_vecs
        else:
            primary, secondary = succ_vecs, pred_vecs

        for vec_p in primary:
            # angle == 180 <=> the two neighbors are collinear with v
            # between them, i.e. a perfectly straight chain through v.
            best_angle = max(unsigned_angle_deg(vec_p, vec_s) for vec_s in secondary)
            straightness.append(best_angle / 180.0)

    if not straightness:
        return 1.0
    return float(sum(straightness) / len(straightness))
