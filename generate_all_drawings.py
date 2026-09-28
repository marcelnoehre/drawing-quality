'''
Draw every context with every drawing algorithm under line_diagrams/.

Each (algorithm, context) drawing is independent and runs as its own process
(`generate.py --dataset D --context C`), up to --jobs at a time. Every process
gets a fresh temporary working directory, since some algorithms write
temporary files (e.g. dimflux's input.cxt) into the working directory. The
pending contexts are taken from each algorithm's `generate.py --list`, so
contexts that already have a .graphml are skipped. A failing drawing does not
stop the others; failures are listed at the end.

Usage:
    python generate_all_drawings.py
    python generate_all_drawings.py freese sugiyama
    python generate_all_drawings.py --jobs 4
'''
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

LINE_DIAGRAMS_DIR = Path(__file__).resolve().parent / 'line_diagrams'

# one core per drawing process: keep numerical libraries from spawning
# their own thread pools on top of the process pool
SINGLE_THREAD_ENV = {
    'OMP_NUM_THREADS': '1',
    'OPENBLAS_NUM_THREADS': '1',
    'MKL_NUM_THREADS': '1',
    'NUMEXPR_NUM_THREADS': '1',
}

print_lock = threading.Lock()


def available_algorithms() -> list[str]:
    return sorted(
        path.parent.name for path in LINE_DIAGRAMS_DIR.glob('*/generate.py')
    )


def log(tag: str, text: str) -> None:
    with print_lock:
        for line in text.splitlines():
            if line.strip():
                print(f'[{tag}] {line}', flush=True)


def run_script(algorithm: str, args: list[str]) -> subprocess.CompletedProcess:
    with tempfile.TemporaryDirectory(prefix=f'{algorithm}_') as cwd:
        return subprocess.run(
            [sys.executable, str(LINE_DIAGRAMS_DIR / algorithm / 'generate.py'), *args],
            cwd=cwd,
            env={**os.environ, **SINGLE_THREAD_ENV},
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )


def pending_tasks(algorithm: str) -> list[tuple[str, str, str]]:
    result = run_script(algorithm, ['--list'])
    if result.returncode != 0:
        log(algorithm, result.stdout)
        log(algorithm, f'listing contexts failed with exit code {result.returncode}')
        return []
    tasks = []
    for line in result.stdout.splitlines():
        if '\t' in line:
            dataset, cxt_path = line.split('\t', 1)
            tasks.append((algorithm, dataset, cxt_path))
        else:
            log(algorithm, line)
    return tasks


def run_task(task: tuple[str, str, str]) -> bool:
    algorithm, dataset, cxt_path = task
    result = run_script(algorithm, ['--dataset', dataset, '--context', cxt_path])
    log(algorithm, result.stdout)
    if result.returncode != 0:
        log(algorithm, f'{Path(cxt_path).name} failed with exit code {result.returncode}')
        return False
    return True


def main() -> None:
    algorithms = available_algorithms()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        'algorithms', nargs='*', choices=algorithms, metavar='algorithm',
        help=f'algorithms to run (default: all of {", ".join(algorithms)})',
    )
    parser.add_argument(
        '-j', '--jobs', type=int, default=8,
        help='number of drawings computed in parallel (default: 8)',
    )
    args = parser.parse_args()
    selected = args.algorithms or algorithms

    with ThreadPoolExecutor(max_workers=args.jobs) as executor:
        tasks = [task for tasks in executor.map(pending_tasks, selected) for task in tasks]
        print(f'{len(tasks)} drawings to compute with {args.jobs} jobs', flush=True)
        succeeded = list(executor.map(run_task, tasks))

    failed = [task for task, ok in zip(tasks, succeeded) if not ok]
    print(f'\n{len(tasks) - len(failed)}/{len(tasks)} drawings finished')
    if failed:
        print('failed:')
        for algorithm, dataset, cxt_path in failed:
            print(f'  {algorithm} {dataset} {Path(cxt_path).name}')
        sys.exit(1)


if __name__ == '__main__':
    main()
