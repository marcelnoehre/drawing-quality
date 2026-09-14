from __future__ import annotations

import sys
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, ElementTree, indent

import odis

from cole_ducrou_eklund import ColeDucrouEklund

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
from plotting import draw_graphml

CONTEXT_DIRS = {
    'm4': REPO_ROOT / 'contexts' / 'm4',
    'random': REPO_ROOT / 'contexts' / 'random',
    'theory': REPO_ROOT / 'contexts' / 'theory',
    'real_world_reduced': REPO_ROOT / 'contexts' / 'real-world' / 'reduced',
}
GRAPHML_ROOT = REPO_ROOT / 'graphml' / 'cole_ducrou_eklund'
DRAWINGS_ROOT = REPO_ROOT / 'drawings' / 'cole_ducrou_eklund'

GRAPHML_NS = 'http://graphml.graphdrawing.org/xmlns'
XSI_NS = 'http://www.w3.org/2001/XMLSchema-instance'

def slug(stem: str) -> str:
    return stem.lower().replace('-', '_')

def write_graphml(layout: ColeDucrouEklund, path: Path) -> None:
    root = Element('graphml', {
        'xmlns': GRAPHML_NS,
        'xmlns:xsi': XSI_NS,
        'xsi:schemaLocation': f'{GRAPHML_NS} {GRAPHML_NS}/1.0/graphml.xsd',
    })
    SubElement(root, 'key', {'id': 'y', 'for': 'node', 'attr.name': 'y', 'attr.type': 'double'})
    SubElement(root, 'key', {'id': 'x', 'for': 'node', 'attr.name': 'x', 'attr.type': 'double'})
    graph = SubElement(root, 'graph', {'edgedefault': 'directed'})

    for concept in layout.concepts:
        x, y = layout.coordinates[concept]
        node_el = SubElement(graph, 'node', {'id': str(concept)})
        x_data = SubElement(node_el, 'data', {'key': 'x'})
        x_data.text = str(x)
        y_data = SubElement(node_el, 'data', {'key': 'y'})
        y_data.text = str(y)

    for source, target in layout.cover_relations():
        SubElement(graph, 'edge', {'source': str(source), 'target': str(target)})

    tree = ElementTree(root)
    indent(tree, space='  ')
    tree.write(path, encoding='utf-8', xml_declaration=True)

def main() -> None:
    for dataset, contexts_dir in CONTEXT_DIRS.items():
        graphml_dir = GRAPHML_ROOT / dataset
        drawings_dir = DRAWINGS_ROOT / dataset

        graphml_dir.mkdir(parents=True, exist_ok=True)
        drawings_dir.mkdir(parents=True, exist_ok=True)

        if not contexts_dir.exists():
            print(f'skipped {dataset}: directory not found: {contexts_dir}')
            continue

        cxt_paths = sorted(contexts_dir.glob('*.cxt'))
        print(f'\n{dataset}: {len(cxt_paths)} contexts')
        for cxt_path in cxt_paths:
            name = slug(cxt_path.stem)
            graphml_path = graphml_dir / f'{name}.graphml'
            pdf_path = drawings_dir / f'{name}.pdf'

            if graphml_path.exists():
                print(
                    f'skipped {cxt_path.name}: '
                    f'{graphml_path.relative_to(REPO_ROOT)} already exists'
                )
                continue

            context = odis.FormalContext.from_file(str(cxt_path))
            try:
                layout = ColeDucrouEklund(context)
            except RuntimeError as e:
                print(f'skipped {cxt_path.name}: {e}')
                continue
            write_graphml(layout, graphml_path)
            draw_graphml(graphml_path, pdf_path, title=name)
            print(
                f'{cxt_path.name} -> '
                f'{graphml_path.relative_to(REPO_ROOT)}, '
                f'{pdf_path.relative_to(REPO_ROOT)}'
            )

if __name__ == '__main__':
    main()
