'''
Score every algorithm's drawings of every lattice and collect the results
in one CSV for later analysis.

Expects the layout produced by the graphml/ directory: one subdirectory per
algorithm, each containing one .graphml file per lattice (same stem across
algorithms where a lattice was drawn by that algorithm).

Usage:
    python evaluate_drawings.py
    python evaluate_drawings.py --graphml-dir graphml --out results.csv
'''
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

from lattice_metrics import evaluate_all, load_layout, structural_width


def _score_file(path: Path, algorithm: str, lattice: str) -> dict:
    layout = load_layout(str(path))
    row = {
        'algorithm': algorithm,
        'lattice': lattice,
        'n_nodes': layout.n,
        'width': structural_width(layout),
    }
    row.update(evaluate_all(layout))
    return row


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--graphml-dir', default='graphml', help='directory with one subdirectory per algorithm (default: graphml)')
    parser.add_argument('--out', default='results.csv', help='CSV output path (default: results.csv)')
    args = parser.parse_args(argv)

    graphml_dir = Path(args.graphml_dir)
    algorithm_dirs = sorted(d for d in graphml_dir.iterdir() if d.is_dir())
    if not algorithm_dirs:
        print(f'no algorithm subdirectories found under {graphml_dir}', file=sys.stderr)
        return 1

    rows = []
    for algorithm_dir in algorithm_dirs:
        algorithm = algorithm_dir.name
        for path in sorted(algorithm_dir.glob('*.graphml')):
            lattice = path.stem
            try:
                rows.append(_score_file(path, algorithm, lattice))
            except Exception as exc:  # noqa: BLE001 - report and continue a batch run
                print(f'failed on {path}: {exc}', file=sys.stderr)

    if not rows:
        return 1

    fieldnames = list(rows[0].keys())
    with open(args.out, 'w', newline='') as out:
        writer = csv.DictWriter(out, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f'wrote {len(rows)} rows to {args.out}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
