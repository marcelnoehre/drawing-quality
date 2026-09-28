'''
Quality metrics for straight-line drawings of lattice diagrams.

Every metric is a pure function of a :class:`LatticeLayout` (a DAG plus a
straight-line drawing of it) and returns a score in [0, 1], where 1 is
'aesthetically ideal' and 0 is the worst case the metric can express.
Loading a graph never has side effects -- call :func:`load_layout` and pass
the result to whichever metrics you need, or use :func:`evaluate_all` to run
the whole battery at once.
'''
from .chains import visual_chain_linearity_score
from .conflict_distance import node_edge_conflict_min_score, node_edge_conflict_score
from .crossing_angle import crossing_angle_min_score, crossing_angle_score
from .edge_conflict import edge_edge_conflict_min_score, edge_edge_conflict_score
from .edge_crossings import edge_crossing_score
from .edge_length import edge_length_uniformity_score
from .graph_utils import LatticeLayout, load_layout, poset_width
from .layering import layer_consistency_score, structural_width
from .nesting import bottleneck_clearance_radius, nested_suitability_score
from .node_conflict import node_node_conflict_min_score, node_node_conflict_score
from .slopes import edge_min_slope, slope_harmony_score, slope_standard_score, slope_verticality_score
from .symmetry import vertical_axis_balance_score

__all__ = [
    'LatticeLayout',
    'load_layout',
    'poset_width',
    'visual_chain_linearity_score',
    'node_edge_conflict_score',
    'node_edge_conflict_min_score',
    'crossing_angle_score',
    'crossing_angle_min_score',
    'edge_edge_conflict_score',
    'edge_edge_conflict_min_score',
    'edge_crossing_score',
    'edge_length_uniformity_score',
    'layer_consistency_score',
    'structural_width',
    'slope_harmony_score',
    'slope_standard_score',
    'slope_verticality_score',
    'edge_min_slope',
    'bottleneck_clearance_radius',
    'nested_suitability_score',
    'node_node_conflict_score',
    'node_node_conflict_min_score',
    'vertical_axis_balance_score',
    'evaluate_all',
]

_SCORE_METRICS = {
    'visual_chain_linearity': visual_chain_linearity_score,
    'node_edge_conflict': node_edge_conflict_score,
    'crossing_angle': crossing_angle_score,
    'edge_edge_conflict': edge_edge_conflict_score,
    'edge_crossing': edge_crossing_score,
    'edge_length_uniformity': edge_length_uniformity_score,
    'layer_consistency': layer_consistency_score,
    'slope_harmony': slope_harmony_score,
    'slope_standard': slope_standard_score,
    'slope_verticality': slope_verticality_score,
    'nested_suitability': nested_suitability_score,
    'node_node_conflict': node_node_conflict_score,
    'vertical_axis_balance': vertical_axis_balance_score,
}

_MIN_METRICS = {
    'node_node_conflict': node_node_conflict_min_score,
    'node_edge_conflict': node_edge_conflict_min_score,
    'edge_edge_conflict': edge_edge_conflict_min_score,
    'crossing_angle': crossing_angle_min_score,
}

def evaluate_all(layout: LatticeLayout) -> dict:
    '''
    Run every [0, 1] quality metric on ``layout``, returning a dict keyed
    by metric name. Raises whatever the first failing metric raises rather
    than silently dropping it, so a bug in one metric can't masquerade as a
    missing key in batch runs.

    Also adds, for each entry in ``_MIN_METRICS``, a ``'{name}_min'``: the
    worst single term of that metric's average (the worst node, vertex, or
    crossing), on the same [0, 1] scale, so ``'{name}'`` and
    ``'{name}_min'`` are the average and worst case of one quantity.
    '''
    scores = {name: metric(layout) for name, metric in _SCORE_METRICS.items()}
    for name, metric in _MIN_METRICS.items():
        scores[f'{name}_min'] = metric(layout)
    return scores
