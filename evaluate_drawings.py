'''
Score every algorithm's drawings of every lattice and collect the results
in one CSV for later analysis.

Expects the layout produced by the graphml/ directory: one subdirectory per
algorithm, each containing one subdirectory per dataset (m4, random, ...)
with one .graphml file per lattice (same dataset/stem across algorithms where
a lattice was drawn by that algorithm).

Only lattices that every algorithm drew (and that scored without error for
every algorithm) are written, so all algorithms are compared on the same set.

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


def _score_file(path: Path, algorithm: str, dataset: str, lattice: str) -> dict:
    layout = load_layout(str(path))
    row = {
        'algorithm': algorithm,
        'dataset': dataset,
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
    for a, algorithm_dir in enumerate(algorithm_dirs, 1):
        algorithm = algorithm_dir.name
        paths = sorted(algorithm_dir.rglob('*.graphml'))
        print(f'[{a}/{len(algorithm_dirs)}] {algorithm}: {len(paths)} drawings', flush=True)
        n_failed = 0
        for i, path in enumerate(paths, 1):
            dataset = path.parent.relative_to(algorithm_dir).as_posix()
            lattice = path.stem
            print(f'  [{i}/{len(paths)}] {algorithm}/{dataset}/{lattice}', flush=True)
            try:
                rows.append(_score_file(path, algorithm, dataset, lattice))
            except Exception as exc:  # noqa: BLE001 - report and continue a batch run
                n_failed += 1
                print(f'failed on {path}: {exc}', file=sys.stderr, flush=True)
        print(f'  {algorithm}: scored {len(paths) - n_failed}, failed {n_failed}', flush=True)

    if not rows:
        print(f'no .graphml files could be scored under {graphml_dir}', file=sys.stderr)
        return 1

    algorithms = [d.name for d in algorithm_dirs]
    drawn_by = {}
    for row in rows:
        drawn_by.setdefault((row['dataset'], row['lattice']), set()).add(row['algorithm'])
    complete = {key for key, algos in drawn_by.items() if len(algos) == len(algorithms)}
    dropped = sorted(drawn_by.keys() - complete)
    for dataset, lattice in dropped:
        missing = sorted(set(algorithms) - drawn_by[(dataset, lattice)])
        print(f'skipping {dataset}/{lattice}: missing for {", ".join(missing)}', file=sys.stderr)
    rows = [row for row in rows if (row['dataset'], row['lattice']) in complete]

    if not rows:
        print('no lattice was drawn by all algorithms', file=sys.stderr)
        return 1

    fieldnames = list(rows[0].keys())
    with open(args.out, 'w', newline='') as out:
        writer = csv.DictWriter(out, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f'wrote {len(rows)} rows ({len(complete)} lattices x {len(algorithms)} algorithms) to {args.out}, '
          f'skipped {len(dropped)} incomplete lattices')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
