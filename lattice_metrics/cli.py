'''
Command-line entry point: score one GraphML drawing, or batch-score a
whole directory of them and write a CSV.

Usage:
    python -m lattice_metrics graphs/dim_flux/27.graphml
    python -m lattice_metrics graphs/dim_flux --out scores.csv
'''
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

from . import evaluate_all, load_layout, structural_width


def _score_file(path: Path) -> dict:
    layout = load_layout(str(path))
    row = {'file': str(path), 'n_nodes': layout.n, 'width': structural_width(layout)}
    row.update(evaluate_all(layout))
    return row


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path', help='a .graphml file, or a directory to scan recursively')
    parser.add_argument('--out', help='write results as CSV to this path instead of stdout')
    args = parser.parse_args(argv)

    target = Path(args.path)
    files = [target] if target.is_file() else sorted(target.rglob('*.graphml'))
    if not files:
        print(f'no .graphml files found under {target}', file=sys.stderr)
        return 1

    rows = []
    for path in files:
        try:
            rows.append(_score_file(path))
        except Exception as exc:  # noqa: BLE001 - report and continue a batch run
            print(f'failed on {path}: {exc}', file=sys.stderr)

    if not rows:
        return 1

    fieldnames = list(rows[0].keys())
    out = open(args.out, 'w', newline='') if args.out else sys.stdout
    try:
        writer = csv.DictWriter(out, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    finally:
        if args.out:
            out.close()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
