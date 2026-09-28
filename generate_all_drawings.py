'''
Run every drawing algorithm's generate.py under line_diagrams/.

Each script is run as its own process from inside its algorithm directory,
since the scripts import their sibling modules directly and some write
temporary files into the working directory. A failing algorithm does not
stop the others; failures are listed at the end.

Usage:
    python generate_all_drawings.py
    python generate_all_drawings.py freese sugiyama
'''
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

LINE_DIAGRAMS_DIR = Path(__file__).resolve().parent / 'line_diagrams'


def available_algorithms() -> list[str]:
    return sorted(
        path.parent.name for path in LINE_DIAGRAMS_DIR.glob('*/generate.py')
    )


def main() -> None:
    algorithms = available_algorithms()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        'algorithms', nargs='*', choices=algorithms, metavar='algorithm',
        help=f'algorithms to run (default: all of {", ".join(algorithms)})',
    )
    selected = parser.parse_args().algorithms or algorithms

    failed = []
    for algorithm in selected:
        algorithm_dir = LINE_DIAGRAMS_DIR / algorithm
        print(f'\n===== {algorithm} =====', flush=True)
        result = subprocess.run(
            [sys.executable, 'generate.py'], cwd=algorithm_dir,
        )
        if result.returncode != 0:
            print(f'{algorithm} failed with exit code {result.returncode}')
            failed.append(algorithm)

    print(f'\n{len(selected) - len(failed)}/{len(selected)} algorithms finished')
    if failed:
        print(f'failed: {", ".join(failed)}')
        sys.exit(1)


if __name__ == '__main__':
    main()
