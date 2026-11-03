"""Draw again, under a longer wall-clock budget, every drawing that timed out.

    python rerun_timeouts.py --hours 24 --dry-run         # list what would run
    python rerun_timeouts.py --hours 24                   # run them
    python rerun_timeouts.py --hours 24 --algorithm redraw --jobs 4

Only drawings recorded in `drawings.csv` as `timeout` under a smaller budget are
attempted. Every other outcome -- a drawing, a decline, an invalid layout, a known
non-termination -- does not depend on the budget and is left as it is.

Each attempt goes through `run_harness.drawing_row`, so it is drawn, checked and
recorded exactly as in a normal run: in its own process, killed at the budget,
with its extents recorded and diverged or collapsed output marked `invalid`. Each
outcome is merged into `drawings.csv` the moment it finishes, with the budget it
ran under, and logged to `logs/rerun_timeouts.csv`. An interrupted run picks up
where it left off: a drawing that has finished, or timed out under the new budget,
is not attempted again.

redraw needs a checkout of https://github.com/domduerr/redraw beside this
repository (or `REDRAW_ROOT` pointing at one) and the conexp-clj API on port 8080.
If the API is not running, it is started from `--conexp-jar` (by default
`tools/conexp-clj.jar` beside this repository) and stopped again at the end. Every
generator is loaded before anything is drawn, so a missing dependency stops the run
at once rather than hours in.

Afterwards, score, compare and rank with the new drawings:

    python run_harness.py --no-draw && python ranking.py && python robustness.py

To stop a run, kill its process group; drawings in progress are killed with it.
"""

from __future__ import annotations

import argparse
import csv
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import run_harness  # noqa: E402
from run_harness import (ALGORITHMS, EnvironmentFault, conexp_reachable,  # noqa: E402
                         drawing_row, load_generator, manifests, merge_csv, read_csv)

DEFAULT_CONEXP_JAR = HERE.parent.parent / "tools" / "conexp-clj.jar"
LOG = HERE / "logs" / "rerun_timeouts.csv"


def timed_out(budget_s: int, algorithm: str | None) -> list[tuple[dict, str]]:
    """(manifest row, algorithm) of every drawing that timed out under a smaller budget."""
    specs = {(s["context"], s["scale"]): s for s in manifests() if s["drawable"] == "True"}
    todo = []
    for r in read_csv(HERE / "drawings.csv"):
        if r["status"] != "timeout" or (algorithm and r["algorithm"] != algorithm):
            continue
        if float(r["wall_budget_s"] or 0) >= budget_s:
            continue                       # already timed out under this budget or more
        todo.append((specs[(r["context"], r["scale"])], r["algorithm"]))
    # Largest first, so the long ones are not left to run alone at the end.
    return sorted(todo, key=lambda job: -int(job[0]["concepts"]))


def start_conexp(jar: Path) -> subprocess.Popen:
    if not jar.exists():
        raise SystemExit(f"redraw needs the conexp-clj API, and {jar} does not exist. "
                         f"Download the conexp-clj 3.1.0 standalone jar to that path, pass "
                         f"--conexp-jar, or start the API on port 8080 yourself")
    (HERE / "logs").mkdir(exist_ok=True)
    # The API exits at once when its console is closed, so stdin is kept open.
    try:
        server = subprocess.Popen(["java", "-jar", str(jar), "--api", "--port", "8080"],
                                  stdin=subprocess.PIPE,
                                  stdout=open(HERE / "logs" / "conexp.log", "w"),
                                  stderr=subprocess.STDOUT, start_new_session=True)
    except FileNotFoundError:
        raise SystemExit("redraw needs the conexp-clj API, which needs Java; "
                         "`java` was not found") from None
    for _ in range(60):
        if conexp_reachable():
            print("conexp API started for redraw", flush=True)
            return server
        time.sleep(2)
    server.kill()
    raise SystemExit("the conexp API did not come up within two minutes; see logs/conexp.log")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--hours", type=float, required=True,
                        help="wall-clock budget per drawing, in hours")
    parser.add_argument("--algorithm", choices=ALGORITHMS, help="only this algorithm")
    parser.add_argument("--jobs", type=int,
                        help="drawings at a time (default: all of them, at most half the cores)")
    parser.add_argument("--conexp-jar", type=Path, default=DEFAULT_CONEXP_JAR)
    parser.add_argument("--dry-run", action="store_true", help="list the drawings and stop")
    args = parser.parse_args()

    budget_s = int(args.hours * 3600)
    if budget_s <= run_harness.WALL_BUDGET_S:
        raise SystemExit(f"--hours must exceed the {run_harness.WALL_BUDGET_S // 60}-minute "
                         f"budget the timeouts were recorded under")
    todo = timed_out(budget_s, args.algorithm)
    jobs = args.jobs or max(1, min(len(todo), (os.cpu_count() or 2) // 2))
    print(f"{len(todo)} timed-out drawings, {jobs} at a time, {args.hours:g} h budget each")
    for spec, algorithm in todo:
        print(f"  {algorithm:20s} {spec['scale']:45s} {spec['concepts']:>5s} concepts")
    if args.dry_run or not todo:
        return 0

    # Fail now, not hours in, if a generator cannot be loaded on this machine.
    for algorithm in sorted({a for _, a in todo}):
        try:
            load_generator(algorithm)
        except Exception as exc:
            raise SystemExit(f"{algorithm}: its generator could not be loaded "
                             f"({type(exc).__name__}: {exc})") from None

    server = None
    if any(a == "redraw" for _, a in todo) and not conexp_reachable():
        server = start_conexp(args.conexp_jar)

    # drawing_row and draw read the budget from the module when they run.
    run_harness.WALL_BUDGET_S = budget_s
    previous = {(r["context"], r["scale"], r["algorithm"]): r
                for r in read_csv(HERE / "drawings.csv")}
    LOG.parent.mkdir(exist_ok=True)
    new_log = not LOG.exists()
    try:
        with ThreadPoolExecutor(max_workers=jobs) as pool, LOG.open("a", newline="") as log:
            writer = None
            futures = [pool.submit(drawing_row, spec, algorithm, previous, False)
                       for spec, algorithm in todo]
            for done, future in enumerate(as_completed(futures), start=1):
                row = future.result()          # a fault on our side stops the run
                merge_csv(HERE / "drawings.csv", [row], ("context", "scale", "algorithm"))
                if writer is None:
                    writer = csv.DictWriter(log, fieldnames=["finished", *row])
                    if new_log:
                        writer.writeheader()
                writer.writerow({"finished": time.strftime("%Y-%m-%d %H:%M"), **row})
                log.flush()
                print(f"  [{done:3d}/{len(todo)}] {row['algorithm']:20s} {row['scale']:45s} "
                      f"{row['status']:14s} {row.get('runtime_s', '')}", flush=True)
    except EnvironmentFault as exc:
        print(f"stopped: {exc}", file=sys.stderr)
        return 1
    finally:
        if server is not None:
            server.kill()
    return 0


if __name__ == "__main__":
    sys.exit(main())
