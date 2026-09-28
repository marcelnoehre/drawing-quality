from __future__ import annotations

import argparse
import sys
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, ElementTree, indent

import odis

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
from plotting import draw_graphml

CONTEXT_DIRS = {
    'm4': REPO_ROOT / 'contexts' / 'm4',
    'random': REPO_ROOT / 'contexts' / 'random',
    'theory': REPO_ROOT/ 'contexts' / 'theory',
    'real_world_reduced': REPO_ROOT / 'contexts' / 'real-world' / 'reduced',
}
GRAPHML_ROOT = REPO_ROOT / 'graphml' / 'sugiyama'
DRAWINGS_ROOT = REPO_ROOT / 'drawings' / 'sugiyama'

GRAPHML_NS = 'http://graphml.graphdrawing.org/xmlns'
XSI_NS = 'http://www.w3.org/2001/XMLSchema-instance'

def slug(stem: str) -> str:
    return stem.lower().replace('-', '_')

def write_graphml(drawing: odis.Drawing, path: Path) -> None:
    root = Element('graphml', {
        'xmlns': GRAPHML_NS,
        'xmlns:xsi': XSI_NS,
        'xsi:schemaLocation': f'{GRAPHML_NS} {GRAPHML_NS}/1.0/graphml.xsd',
    })
    SubElement(root, 'key', {'id': 'y', 'for': 'node', 'attr.name': 'y', 'attr.type': 'double'})
    SubElement(root, 'key', {'id': 'x', 'for': 'node', 'attr.name': 'x', 'attr.type': 'double'})
    graph = SubElement(root, 'graph', {'edgedefault': 'directed'})

    for node in drawing.nodes:
        node_el = SubElement(graph, 'node', {'id': str(node.index)})
        x_data = SubElement(node_el, 'data', {'key': 'x'})
        x_data.text = str(node.x)
        y_data = SubElement(node_el, 'data', {'key': 'y'})
        y_data.text = str(-node.y)

    for source, target in drawing.edges:
        SubElement(graph, 'edge', {'source': str(source), 'target': str(target)})

    tree = ElementTree(root)
    indent(tree, space='  ')
    tree.write(path, encoding='utf-8', xml_declaration=True)

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

    context = odis.FormalContext.from_file(str(cxt_path))
    drawing = context.draw('sugiyama', timeout_ms=None)
    if drawing is None:
        print(f'skipped {cxt_path.name}: no drawing found')
        return
    write_graphml(drawing, graphml_path)
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