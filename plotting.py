from __future__ import annotations

from pathlib import Path
from typing import Dict, Hashable, Tuple

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import networkx as nx

NODE_SIZE: float = 50.0
LINE_WIDTH: float = 1.0
PADDING: float = 0.02
DPI: float = 150.0

PositionMap = Dict[Hashable, Tuple[float, float]]


def read_positions(graphml_path: str | Path) -> Tuple[nx.DiGraph, PositionMap]:
    '''
    Read a GraphML file with per-node ``x``/``y`` attributes.
    '''
    graph = nx.read_graphml(str(graphml_path))
    positions = {node: (float(data['x']), float(data['y'])) for node, data in graph.nodes(data=True)}
    return graph, positions


def draw_graph(
    graph: nx.Graph,
    positions: PositionMap,
    output_path: str | Path,
    title: str = '',
) -> None:
    '''
    Draw ``graph`` with straight-line edges at ``positions`` and save it as a PDF.
    '''
    fig, ax = plt.subplots(figsize=(8, 6), dpi=DPI)
    fig.canvas.manager.set_window_title(title)

    for u, v in graph.edges:
        (x0, y0), (x1, y1) = positions[u], positions[v]
        ax.plot([x0, x1], [y0, y1], color='black', linewidth=LINE_WIDTH, zorder=2)

    for node in graph.nodes:
        x, y = positions[node]
        ax.scatter(x, y, facecolor='white', edgecolor='black', linewidth=LINE_WIDTH, s=NODE_SIZE, zorder=10, clip_on=False)

    xs = [x for x, _ in positions.values()]
    ys = [y for _, y in positions.values()]
    # the coordinate scale differs between algorithms, so the padding is
    # relative to the drawing's extent (1 for a drawing without extent)
    padding = PADDING * (max(max(xs) - min(xs), max(ys) - min(ys)) or 1.0)
    ax.set_xlim(min(xs) - padding, max(xs) + padding)
    ax.set_ylim(min(ys) - padding, max(ys) + padding)
    ax.set_aspect('equal', adjustable='box')
    ax.axis('off')

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, format='pdf', bbox_inches='tight', pad_inches=0.05)
    plt.close(fig)


def draw_graphml(graphml_path: str | Path, output_path: str | Path, title: str = '') -> None:
    '''
    Read a GraphML file and draw it, see :func:`draw_graph`.
    '''
    graph, positions = read_positions(graphml_path)
    draw_graph(graph, positions, output_path, title=title)
