"""Draw again, without a time limit or under a longer one, every drawing that timed out.

    python rerun_timeouts.py --dry-run                    # list what would run
    python rerun_timeouts.py                              # run them, no time limit
    python rerun_timeouts.py --stop                       # end a run, from another shell
    python rerun_timeouts.py --hours 24                   # or a fixed budget per drawing
    python rerun_timeouts.py --algorithm redraw --jobs 4

Only drawings recorded in `drawings.csv` as `timeout` under a smaller budget are
attempted. Every other outcome -- a drawing, a decline, an invalid layout, a known
non-termination -- does not depend on the budget and is left as it is.

**Without `--hours`** there is no time limit. Every drawing starts at once, so all
of them have been running for the same time whenever the run ends. `--stop` ends it:
every drawing still running is killed and recorded as a timeout, with the time it
ran as its budget, which is then the same for all of them. Drawings that finish are
recorded with the budget `inf`. With `--jobs` below the number of drawings, the
later ones start later and get less time, so the budgets differ.

**With `--hours`**, each drawing is killed at that budget, as in a normal run.

Each attempt goes through `run_harness.drawing_row`, so it is drawn, checked and
recorded exactly as in a normal run: in its own process, with its extents recorded
and diverged or collapsed output marked `invalid`. Each outcome is merged into
`drawings.csv` the moment it finishes and logged to `logs/rerun_timeouts.csv`. A
drawing that has finished, or timed out under the budget asked for, is not
attempted again; one killed by `--stop` is, when a run without a limit is started
again, from the beginning.

redraw needs a checkout of https://github.com/domduerr/redraw beside this
repository (or `REDRAW_ROOT` pointing at one) and the conexp-clj API on port 8080.
If the API is not running, it is started from `--conexp-jar` (by default
`tools/conexp-clj.jar` beside this repository) and stopped again at the end. Every
generator is loaded before anything is drawn, so a missing dependency stops the run
at once rather than hours in.

Afterwards, score, compare and rank with the new drawings:

    python run_harness.py --no-draw && python ranking.py && python robustness.py
"""

from __future__ import annotations

import argparse
import csv
import math
import os
import signal
import subprocess
import sys
import time
from concurrent.futures import CancelledError, ThreadPoolExecutor, as_completed
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import run_harness  # noqa: E402
from node_extents import sidecar  # noqa: E402
from run_harness import (ALGORITHMS, EnvironmentFault, conexp_reachable,  # noqa: E402
                         drawing_row, graphml_path, load_generator, manifests, merge_csv,
                         read_csv)

DEFAULT_CONEXP_JAR = HERE.parent.parent / "tools" / "conexp-clj.jar"
DRAWINGS_CSV = HERE / "drawings.csv"
LOG = HERE / "logs" / "rerun_timeouts.csv"
PID_FILE = HERE / "logs" / "rerun_timeouts.pid"

# The harness needs a number to wait for; without a limit it waits ten years, and
# the drawings that finish are recorded with the budget "inf".
NO_LIMIT_S = 10 * 365 * 24 * 3600


def timed_out(budget_s: float, algorithm: str | None) -> list[tuple[dict, str]]:
    """(manifest row, algorithm) of every drawing that timed out under a smaller budget."""
    specs = {(s["context"], s["scale"]): s for s in manifests() if s["drawable"] == "True"}
    todo = []
    for r in read_csv(DRAWINGS_CSV):
        if r["status"] != "timeout" or (algorithm and r["algorithm"] != algorithm):
            continue
        if float(r["wall_budget_s"] or 0) >= budget_s:
            continue                       # already timed out under this budget or more
        todo.append((specs[(r["context"], r["scale"])], r["algorithm"]))
    # Largest first, so with fewer jobs than drawings the long ones start first.
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


def children(keep: set[int]) -> list[int]:
    """The process ids whose parent is this process, except those in `keep`."""
    me, found = os.getpid(), []
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit() or int(entry.name) in keep:
            continue
        try:
            # The field after the parenthesised command name: state, then parent id.
            stat = (entry / "stat").read_text()
        except OSError:
            continue
        if int(stat.rsplit(")", 1)[1].split()[1]) == me:
            found.append(int(entry.name))
    return found


def stop_run() -> int:
    try:
        pid = int(PID_FILE.read_text())
        os.kill(pid, signal.SIGTERM)
    except (OSError, ValueError):
        print(f"no run to stop: {PID_FILE.relative_to(HERE)} names no running process")
        return 1
    print(f"asked run {pid} to stop; it records every drawing still running as a "
          f"timeout and exits")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--hours", type=float,
                        help="wall-clock budget per drawing, in hours (default: no limit)")
    parser.add_argument("--algorithm", choices=ALGORITHMS, help="only this algorithm")
    parser.add_argument("--jobs", type=int,
                        help="drawings at a time (default: all of them without a limit, "
                             "at most half the cores with one)")
    parser.add_argument("--conexp-jar", type=Path, default=DEFAULT_CONEXP_JAR)
    parser.add_argument("--dry-run", action="store_true", help="list the drawings and stop")
    parser.add_argument("--stop", action="store_true",
                        help="end the run in progress, recording what is still running")
    args = parser.parse_args()
    if args.stop:
        return stop_run()

    limited = args.hours is not None
    if limited and args.hours * 3600 <= run_harness.WALL_BUDGET_S:
        raise SystemExit(f"--hours must exceed the {run_harness.WALL_BUDGET_S // 60}-minute "
                         f"budget the timeouts were recorded under")
    budget_s = int(args.hours * 3600) if limited else math.inf
    todo = timed_out(budget_s, args.algorithm)
    if args.jobs:
        jobs = args.jobs
    elif limited:
        jobs = max(1, min(len(todo), (os.cpu_count() or 2) // 2))
    else:
        jobs = max(1, len(todo))
    budget_text = f"{args.hours:g} h budget each" if limited else "no time limit"
    print(f"{len(todo)} timed-out drawings, {jobs} at a time, {budget_text}")
    if not limited and jobs < len(todo):
        print("  note: with fewer jobs than drawings, the later ones start later and "
              "get less time before a --stop")
    if jobs > (os.cpu_count() or 1):
        print(f"  note: {jobs} at a time on {os.cpu_count()} cores; they share the CPUs")
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
    run_harness.WALL_BUDGET_S = budget_s if limited else NO_LIMIT_S
    previous = {(r["context"], r["scale"], r["algorithm"]): r for r in read_csv(DRAWINGS_CSV)}
    LOG.parent.mkdir(exist_ok=True)
    PID_FILE.write_text(str(os.getpid()))
    new_log = not LOG.exists()
    started = time.time()
    stopping = {"at": None}
    futures = []

    def stop(_signum, _frame):
        # Kill every drawing in progress; each then returns as a killed process, which
        # is recorded below as a timeout. Drawings not yet started are not started.
        if stopping["at"] is None:
            stopping["at"] = time.time()
            print(f"stopping after {(stopping['at'] - started) / 3600:.2f} h", flush=True)
        for future in futures:
            future.cancel()
        for pid in children({server.pid} if server else set()):
            try:
                os.killpg(pid, signal.SIGKILL)      # each drawing is its own process group
            except OSError:
                pass

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)

    finished = killed = 0
    try:
        with ThreadPoolExecutor(max_workers=jobs) as pool, LOG.open("a", newline="") as log:
            writer = None
            futures.extend(pool.submit(drawing_row, spec, algorithm, previous, False)
                           for spec, algorithm in todo)
            for future in as_completed(futures):
                try:
                    row = future.result()      # a fault on our side stops the run
                except CancelledError:
                    continue                   # never started; its old record stands
                if stopping["at"] is not None and row["status"] == "error" \
                        and "code -9" in row.get("note", ""):
                    # Killed mid-run: whatever it had written is not a drawing.
                    ran = float(row["runtime_s"])
                    partial = graphml_path(row["algorithm"], row["context"], row["scale"])
                    partial.unlink(missing_ok=True)
                    sidecar(partial).unlink(missing_ok=True)
                    row.update(status="timeout", wall_budget_s=round(ran),
                               note=f"still running when the run was stopped after "
                                    f"{ran / 3600:.2f} h; killed")
                    killed += 1
                else:
                    finished += 1
                    if not limited and row.get("wall_budget_s") == NO_LIMIT_S:
                        row["wall_budget_s"] = "inf"
                merge_csv(DRAWINGS_CSV, [row], ("context", "scale", "algorithm"))
                if writer is None:
                    writer = csv.DictWriter(log, fieldnames=["finished", *row])
                    if new_log:
                        writer.writeheader()
                writer.writerow({"finished": time.strftime("%Y-%m-%d %H:%M"), **row})
                log.flush()
                print(f"  [{finished + killed:3d}/{len(todo)}] {row['algorithm']:20s} "
                      f"{row['scale']:45s} {row['status']:14s} {row.get('runtime_s', '')}",
                      flush=True)
    except EnvironmentFault as exc:
        print(f"stopped: {exc}", file=sys.stderr)
        return 1
    finally:
        if server is not None:
            server.kill()
        PID_FILE.unlink(missing_ok=True)
    hours = ((stopping["at"] or time.time()) - started) / 3600
    print(f"done after {hours:.2f} h: {finished} finished, {killed} still running and "
          f"recorded as timeouts, {len(todo) - finished - killed} not started")
    return 0


if __name__ == "__main__":
    sys.exit(main())
