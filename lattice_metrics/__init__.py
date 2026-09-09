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
from .conflict_distance import node_edge_conflict_score
from .crossing_angle import crossing_angle_score
from .edge_crossings import edge_crossing_score
from .graph_utils import LatticeLayout, load_layout, poset_width
from .layering import layer_consistency_score, structural_width, visual_layer_x_score, visual_layer_y_score
from .node_conflict_distance import node_conflict_distance_score
from .slopes import slope_harmony_score, slope_standard_score

__all__ = [
    'LatticeLayout',
    'load_layout',
    'poset_width',
    'visual_chain_linearity_score',
    'node_edge_conflict_score',
    'node_conflict_distance_score',
    'crossing_angle_score',
    'edge_crossing_score',
    'layer_consistency_score',
    'visual_layer_x_score',
    'visual_layer_y_score',
    'structural_width',
    'slope_harmony_score',
    'slope_standard_score',
    'evaluate_all',
]

_SCORE_METRICS = {
    'visual_chain_linearity': visual_chain_linearity_score,
    'node_edge_conflict': node_edge_conflict_score,
    'node_conflict_distance': node_conflict_distance_score,
    'crossing_angle': crossing_angle_score,
    'edge_crossing': edge_crossing_score,
    'layer_consistency': layer_consistency_score,
    'visual_layer_x': visual_layer_x_score,
    'visual_layer_y': visual_layer_y_score,
    'slope_harmony': slope_harmony_score,
    'slope_standard': slope_standard_score,
}

def evaluate_all(layout: LatticeLayout) -> dict:
    '''
    Run every [0, 1] quality metric on ``layout``, returning a dict keyed
    by metric name. Raises whatever the first failing metric raises rather
    than silently dropping it, so a bug in one metric can't masquerade as a
    missing key in batch runs.
    '''
    return {name: metric(layout) for name, metric in _SCORE_METRICS.items()}
