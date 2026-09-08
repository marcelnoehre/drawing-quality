from __future__ import annotations

import sys
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, ElementTree, indent

import odis

from cole_ducrou_eklund import ColeDucrouEklund

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
from plotting import draw_graphml

CONTEXTS_DIR = REPO_ROOT / 'contexts'
GRAPHML_DIR = REPO_ROOT / 'graphml' / 'cole_ducrou_eklund'
DRAWINGS_DIR = REPO_ROOT / 'drawings' / 'cole_ducrou_eklund'

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
    GRAPHML_DIR.mkdir(parents=True, exist_ok=True)
    DRAWINGS_DIR.mkdir(parents=True, exist_ok=True)
    for cxt_path in sorted(CONTEXTS_DIR.glob('*.cxt')):
        context = odis.FormalContext.from_file(str(cxt_path))
        try:
            layout = ColeDucrouEklund(context)
        except RuntimeError as e:
            print(f'skipped {cxt_path.name}: {e}')
            continue
        name = slug(cxt_path.stem)
        graphml_path = GRAPHML_DIR / f'{name}.graphml'
        write_graphml(layout, graphml_path)
        draw_graphml(graphml_path, DRAWINGS_DIR / f'{name}.pdf', title=name)
        print(f'{cxt_path.name} -> {graphml_path.name}, {name}.pdf')

if __name__ == '__main__':
    main()
