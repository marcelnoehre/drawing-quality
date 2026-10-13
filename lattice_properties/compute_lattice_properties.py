'''
Compute conexp-clj's lattice-property metrics (rises, distributivity and
modularity measures from conexp.fca.metrics) for the concept lattice of every
context that has drawings, and collect them in one CSV.

A context counts as drawn if every algorithm under graphml/ has a .graphml
for it (generate_all_drawings.py draws every context with all algorithms or
with none), so the rows match the lattices compared in results.csv.

Each context is computed by its own JVM running conexp_metrics.clj, up to
--jobs at a time. That script prints every metric as soon as it is computed,
so when a context runs into --timeout the metrics finished so far are kept
and the rest are left empty. Metrics that raised an error in conexp-clj are
left empty as well; all failures are listed at the end.

Usage:
    python lattice_properties/compute_lattice_properties.py
    python lattice_properties/compute_lattice_properties.py --jobs 8 --timeout 600
    python lattice_properties/compute_lattice_properties.py --conexp-dir ../conexp-clj --out lattice_properties.csv
'''
from __future__ import annotations

import argparse
import csv
import os
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKER = Path(__file__).resolve().parent / 'conexp_metrics.clj'
GRAPHML_ROOT = REPO_ROOT / 'graphml'

CONTEXT_DIRS = {
    'm4': REPO_ROOT / 'contexts' / 'm4',
    'random': REPO_ROOT / 'contexts' / 'random',
    'theory': REPO_ROOT / 'contexts' / 'theory',
    'real_world_reduced': REPO_ROOT / 'contexts' / 'real-world' / 'reduced',
}

# in the order conexp_metrics.clj prints them
METRICS = [
    'n_objects',
    'n_attributes',
    'n_concepts',
    'distributive',
    'modular',
    'double_arrow_distributivity_index',
    'birkhoff_distributivity_index',
    'distributivity_degree',
    'modularity_degree',
    'non_unit_meet_rise_rate',
    'non_unit_join_rise_rate',
    'node_distributivity',
    'extent_weighted_node_distributivity',
]

print_lock = threading.Lock()


def slug(stem: str) -> str:
    '''Name of a context's drawings, as in line_diagrams/*/generate.py.'''
    return stem.lower().replace('-', '_')


def drawn_contexts() -> list[tuple[str, str, Path]]:
    '''(dataset, lattice, context path) for every context that every
    algorithm under graphml/ has drawn.'''
    algorithm_dirs = sorted(d for d in GRAPHML_ROOT.iterdir() if d.is_dir())
    if not algorithm_dirs:
        sys.exit(f'no algorithm subdirectories found under {GRAPHML_ROOT}')
    contexts = []
    for dataset, contexts_dir in CONTEXT_DIRS.items():
        for cxt_path in sorted(contexts_dir.glob('*.cxt')):
            lattice = slug(cxt_path.stem)
            if all((d / dataset / f'{lattice}.graphml').exists() for d in algorithm_dirs):
                contexts.append((dataset, lattice, cxt_path))
    return contexts


def conexp_classpath(conexp_dir: Path) -> str:
    result = subprocess.run(
        ['lein', 'classpath'], cwd=conexp_dir, capture_output=True, text=True, check=True,
    )
    return result.stdout.strip().splitlines()[-1]


def compute(task: tuple[str, str, Path], classpath: str, timeout: float) -> tuple[dict, list[str]]:
    '''Run the worker on one context; returns the CSV row and its failures.'''
    dataset, lattice, cxt_path = task
    row = {'dataset': dataset, 'lattice': lattice, 'context': cxt_path.relative_to(REPO_ROOT).as_posix()}
    failures = []
    process = subprocess.Popen(
        ['java', '-cp', classpath, 'clojure.main', str(WORKER), str(cxt_path)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    timed_out = False
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        process.kill()
        stdout, stderr = process.communicate()
        timed_out = True
        failures.append(f'timeout after {timeout:g}s')
    for line in stdout.splitlines():
        name, _, value = line.partition('\t')
        if name not in METRICS:
            continue
        if value.startswith('ERROR: '):
            failures.append(f'{name}: {value[len("ERROR: "):]}')
        elif value:
            row[name] = value
    if process.returncode != 0 and not timed_out:
        failures.append(f'exit code {process.returncode}: {" ".join(stderr.strip().splitlines()[-1:])}')
    missing = [name for name in METRICS if name not in row]
    if missing and not failures:
        failures.append(f'no value for {", ".join(missing)}')
    return row, failures


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--conexp-dir', type=Path, default=REPO_ROOT.parent / 'conexp-clj',
                        help='conexp-clj checkout (default: ../conexp-clj)')
    parser.add_argument('--out', type=Path, default=REPO_ROOT / 'lattice_properties.csv',
                        help='CSV output path (default: lattice_properties.csv)')
    parser.add_argument('--jobs', type=int, default=max(1, (os.cpu_count() or 2) // 2),
                        help='contexts computed in parallel (default: half the CPUs)')
    parser.add_argument('--timeout', type=float, default=7200,
                        help='seconds per context before its remaining metrics are given up (default: 7200)')
    args = parser.parse_args(argv)

    tasks = drawn_contexts()
    classpath = conexp_classpath(args.conexp_dir)
    print(f'{len(tasks)} drawn contexts, {args.jobs} jobs', flush=True)

    results = {}
    done = 0

    def run(task):
        nonlocal done
        row, failures = compute(task, classpath, args.timeout)
        with print_lock:
            done += 1
            status = 'ok' if not failures else '; '.join(failures)
            print(f'[{done}/{len(tasks)}] {task[0]}/{task[1]}: {status}', flush=True)
        results[task] = (row, failures)

    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        list(pool.map(run, tasks))

    with open(args.out, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['dataset', 'lattice', 'context', *METRICS])
        writer.writeheader()
        for task in tasks:
            writer.writerow(results[task][0])

    failed = [(task, failures) for task, (_, failures) in results.items() if failures]
    print(f'\nwrote {len(tasks)} contexts to {args.out}')
    if failed:
        print(f'{len(failed)} contexts with missing metrics:')
        for (dataset, lattice, _), failures in sorted(failed):
            print(f'  {dataset}/{lattice}: {"; ".join(failures)}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
