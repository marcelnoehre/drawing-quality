from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, ElementTree, indent

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
from plotting import draw_graphml

# ReDraw (Force-Directed Layout of Order Diagrams using Dimensional Reduction)
# lives in its own sibling repository and is called out-of-process: it needs a
# conexp-clj REST API instance running on 127.0.0.1:8080 to compute the concept
# lattice (see redraw's README/run_redraw.md). Point REDRAW_ROOT at a checkout
# of https://github.com/... via the REDRAW_ROOT env var if it isn't the
# default sibling checkout next to this repo.
REDRAW_ROOT = Path(os.environ.get('REDRAW_ROOT', REPO_ROOT.parent / 'redraw'))
sys.path.insert(0, str(REDRAW_ROOT))
import algorithm as redraw_algorithm

CONTEXT_DIRS = {
    'm4': REPO_ROOT / 'contexts' / 'm4',
    'random': REPO_ROOT / 'contexts' / 'random',
    'theory': REPO_ROOT / 'contexts' / 'theory',
    'real_world_reduced': REPO_ROOT / 'contexts' / 'real-world' / 'reduced',
}
GRAPHML_ROOT = REPO_ROOT / 'graphml' / 'redraw'
DRAWINGS_ROOT = REPO_ROOT / 'drawings' / 'redraw'

GRAPHML_NS = 'http://graphml.graphdrawing.org/xmlns'
XSI_NS = 'http://www.w3.org/2001/XMLSchema-instance'

# starting embedding dimension for the dimensional-reduction force layout,
# stepped down to 2 via PCA; matches redraw's own algorithm.py:main() example.
# If redraw fails at a dimension, it is retried one dimension lower, down to
# MIN_DIMENSION.
DIMENSION = 5
MIN_DIMENSION = 2

def slug(stem: str) -> str:
    return stem.lower().replace('-', '_')

def write_graphml(order: 'redraw_algorithm.util.Order', path: Path) -> None:
    nodes = sorted(order.G.nodes, key=lambda n: (len(n[0]), n[0], n[1]))
    node_ids = {node: str(i) for i, node in enumerate(nodes)}

    root = Element('graphml', {
        'xmlns': GRAPHML_NS,
        'xmlns:xsi': XSI_NS,
        'xsi:schemaLocation': f'{GRAPHML_NS} {GRAPHML_NS}/1.0/graphml.xsd',
    })
    SubElement(root, 'key', {'id': 'y', 'for': 'node', 'attr.name': 'y', 'attr.type': 'double'})
    SubElement(root, 'key', {'id': 'x', 'for': 'node', 'attr.name': 'x', 'attr.type': 'double'})
    graph = SubElement(root, 'graph', {'edgedefault': 'directed'})

    for node in nodes:
        vertical, horizontal = order.pos(node)
        node_el = SubElement(graph, 'node', {'id': node_ids[node]})
        x_data = SubElement(node_el, 'data', {'key': 'x'})
        x_data.text = str(horizontal)
        y_data = SubElement(node_el, 'data', {'key': 'y'})
        # order.drawing[node][0] is the node's position in a linear extension
        # built top-down (the top concept gets the smallest value, the bottom
        # concept the largest); negate it so higher concepts plot higher up
        y_data.text = str(-vertical)

    for extent_a, extent_b in order.edges():
        # redraw's cover edges point from child to parent (extent_a subset of
        # extent_b); normalize to the parent -> child convention used by the
        # other algorithms in this repo (larger extent is closer to the top)
        source, target = (extent_b, extent_a) if len(extent_a[0]) < len(extent_b[0]) else (extent_a, extent_b)
        SubElement(graph, 'edge', {'source': node_ids[source], 'target': node_ids[target]})

    tree = ElementTree(root)
    indent(tree, space='  ')
    tree.write(path, encoding='utf-8', xml_declaration=True)

def compute_drawing(cxt_path: Path) -> 'redraw_algorithm.util.Order':
    for dimension in range(DIMENSION, MIN_DIMENSION - 1, -1):
        try:
            return redraw_algorithm.compute_drawing(str(cxt_path), dimension, False)
        except Exception as exc:
            if dimension == MIN_DIMENSION:
                raise
            print(f'{cxt_path.name}: failed at dimension {dimension} ({exc}), retrying with {dimension - 1}')

def pending_contexts() -> list[tuple[str, Path]]:
    pending = []
    for dataset, contexts_dir in CONTEXT_DIRS.items():
        if not contexts_dir.exists():
            print(f'skipped {dataset}: directory not found: {contexts_dir}', file=sys.stderr)
            continue
        for cxt_path in sorted(contexts_dir.glob('*.cxt')):
            if not (GRAPHML_ROOT / dataset / f'{slug(cxt_path.stem)}.graphml').exists():
                pending.append((dataset, cxt_path))
    return pending

def generate(dataset: str, cxt_path: Path) -> None:
    name = slug(cxt_path.stem)
    graphml_dir = GRAPHML_ROOT / dataset
    drawings_dir = DRAWINGS_ROOT / dataset
    graphml_dir.mkdir(parents=True, exist_ok=True)
    drawings_dir.mkdir(parents=True, exist_ok=True)
    graphml_path = graphml_dir / f'{name}.graphml'
    pdf_path = drawings_dir / f'{name}.pdf'

    if graphml_path.exists():
        print(
            f'skipped {cxt_path.name}: '
            f'{graphml_path.relative_to(REPO_ROOT)} already exists'
        )
        return

    try:
        order = compute_drawing(cxt_path)
    except Exception as exc:
        print(f'skipped {cxt_path.name}: {exc}')
        return
    write_graphml(order, graphml_path)
    draw_graphml(graphml_path, pdf_path, title=name)
    print(
        f'{cxt_path.name} -> '
        f'{graphml_path.relative_to(REPO_ROOT)}, '
        f'{pdf_path.relative_to(REPO_ROOT)}'
    )

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--list', action='store_true', help='print the pending (dataset, context) pairs and exit')
    parser.add_argument('--dataset', choices=CONTEXT_DIRS, help='dataset of --context')
    parser.add_argument('--context', type=Path, help='draw only this .cxt file')
    args = parser.parse_args()

    if args.list:
        for dataset, cxt_path in pending_contexts():
            print(f'{dataset}\t{cxt_path}')
        return

    if args.context is not None:
        if args.dataset is None:
            parser.error('--context requires --dataset')
        generate(args.dataset, args.context.resolve())
        return

    for dataset, contexts_dir in CONTEXT_DIRS.items():
        if not contexts_dir.exists():
            print(f'skipped {dataset}: directory not found: {contexts_dir}')
            continue

        cxt_paths = sorted(contexts_dir.glob('*.cxt'))
        print(f'\n{dataset}: {len(cxt_paths)} contexts')
        for cxt_path in cxt_paths:
            generate(dataset, cxt_path)

if __name__ == '__main__':
    main()
