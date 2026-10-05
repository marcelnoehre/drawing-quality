'''
Draw every context with every drawing algorithm under line_diagrams/.

Each (algorithm, context) drawing is independent and runs as its own process
(`generate.py --dataset D --context C`), up to --jobs at a time. Every process
gets a fresh temporary working directory, since some algorithms write
temporary files (e.g. dimflux's input.cxt) into the working directory. The
pending contexts are taken from each algorithm's `generate.py --list`, so
contexts that already have a .graphml are skipped, as are the (dataset,
context) pairs listed in unsupported_drawings.txt. As soon as one algorithm
fails on a context, that context is appended to unsupported_drawings.txt and
its not yet started drawings with the other algorithms are skipped, so every
context is drawn either by all algorithms or by none (later runs skip it until
it is removed from the file again). Failures are listed at the end.

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
UNSUPPORTED_DRAWINGS = Path(__file__).resolve().parent / 'unsupported_drawings.txt'

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


def unsupported_contexts() -> set[tuple[str, str]]:
    '''(dataset, context file name) pairs listed in UNSUPPORTED_DRAWINGS, one
    whitespace-separated pair per line; anything after a # is a comment.'''
    unsupported = set()
    if not UNSUPPORTED_DRAWINGS.exists():
        return unsupported
    for line in UNSUPPORTED_DRAWINGS.read_text().splitlines():
        line = line.split('#', 1)[0].strip()
        if line:
            dataset, name = line.split()
            unsupported.add((dataset, name))
    return unsupported


# contexts on which some algorithm failed during this run
failed_contexts: set[tuple[str, str]] = set()
failed_contexts_lock = threading.Lock()


def record_unsupported(task: tuple[str, str, str], reason: str) -> None:
    '''Mark the task's context as failed for this run and append it to
    UNSUPPORTED_DRAWINGS, unless another algorithm already failed on it.'''
    algorithm, dataset, cxt_path = task
    context = (dataset, Path(cxt_path).name)
    with failed_contexts_lock:
        if context in failed_contexts:
            return
        failed_contexts.add(context)
        with UNSUPPORTED_DRAWINGS.open('a') as f:
            f.write(f'{dataset} {context[1]}  # {algorithm}: {reason}\n')


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
    unsupported = unsupported_contexts()
    tasks = []
    skipped = 0
    for line in result.stdout.splitlines():
        if '\t' in line:
            dataset, cxt_path = line.split('\t', 1)
            if (dataset, Path(cxt_path).name) in unsupported:
                skipped += 1
            else:
                tasks.append((algorithm, dataset, cxt_path))
        else:
            log(algorithm, line)
    if skipped:
        log(algorithm, f'skipped {skipped} contexts listed in {UNSUPPORTED_DRAWINGS.name}')
    return tasks


def run_task(task: tuple[str, str, str]) -> str:
    '''Draw one context with one algorithm; returns 'ok', 'failed', or
    'skipped' if another algorithm already failed on the context.'''
    algorithm, dataset, cxt_path = task
    with failed_contexts_lock:
        if (dataset, Path(cxt_path).name) in failed_contexts:
            return 'skipped'
    result = run_script(algorithm, ['--dataset', dataset, '--context', cxt_path])
    log(algorithm, result.stdout)
    if result.returncode != 0:
        log(algorithm, f'{Path(cxt_path).name} failed with exit code {result.returncode}')
        record_unsupported(task, f'exit code {result.returncode}')
        return 'failed'
    return 'ok'


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
        outcomes = list(executor.map(run_task, tasks))

    failed = [task for task, outcome in zip(tasks, outcomes) if outcome == 'failed']
    skipped = outcomes.count('skipped')
    print(f'\n{outcomes.count("ok")}/{len(tasks)} drawings finished, {skipped} skipped')
    if failed:
        print(f'failed (contexts appended to {UNSUPPORTED_DRAWINGS.name}):')
        for algorithm, dataset, cxt_path in failed:
            print(f'  {algorithm} {dataset} {Path(cxt_path).name}')
        sys.exit(1)


if __name__ == '__main__':
    main()
