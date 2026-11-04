"""Draw again, under a budget of seven days, every drawing that timed out.

    python rerun_timeouts.py --dry-run                    # list what would run
    python rerun_timeouts.py                              # run them, 8 at a time, 7 days each
    python rerun_timeouts.py --stop                       # end a run early, from another shell
    python rerun_timeouts.py --hours 24                   # another budget per drawing
    python rerun_timeouts.py --algorithm redraw

Only drawings recorded in `drawings.csv` as `timeout` under a smaller budget are
attempted. Every other outcome -- a drawing, a decline, an invalid layout, a known
non-termination -- does not depend on the budget and is left as it is.

Eight drawings run at a time (`--jobs`), and each gets the full budget from the
moment it starts. They start in this order: DimFlux first and ReDraw last, the
other algorithms between them by how few drawings they have to redo, and within
each algorithm the smallest lattice first, so that quick drawings finish early. A
drawing still running at the budget is killed and recorded as a timeout, a
failure. The run ends by itself when the last drawing has finished or reached the
budget; `--stop` ends it earlier, killing every drawing still running and
recording it as a timeout with the time it ran as its budget. A drawing not yet
started keeps its old record.

Each attempt goes through `run_harness.drawing_row`, so it is drawn, checked and
recorded exactly as in a normal run: in its own process, with its extents recorded
and diverged or collapsed output marked `invalid`. Each outcome, with how long it
ran, is merged into `drawings.csv` the moment it finishes and logged to
`logs/rerun_timeouts.csv`. The log says when each drawing starts, and every hour
how long the run has gone, how many drawings are running and waiting, and the
latest progress of each running one. That progress comes from
`logs/progress/<algorithm>/<scale>.log`, which every drawing writes while it runs:
each main step of its algorithm as it starts and ends, its iteration counts, and
every ten minutes which of its functions it is in (`progress.py`). A drawing that has finished, or timed out
under the budget asked for, is not attempted again; one killed by `--stop` is, from
the beginning, when the run is started again.

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
import os
import signal
import subprocess
import sys
import time
from collections import Counter
from concurrent.futures import FIRST_COMPLETED, CancelledError, ThreadPoolExecutor, wait
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import progress  # noqa: E402
import run_harness  # noqa: E402
from node_extents import sidecar  # noqa: E402
from run_harness import (ALGORITHMS, EnvironmentFault, conexp_reachable,  # noqa: E402
                         drawing_row, graphml_path, load_generator, manifests, merge_csv,
                         read_csv)

DEFAULT_CONEXP_JAR = HERE.parent.parent / "tools" / "conexp-clj.jar"
DRAWINGS_CSV = HERE / "drawings.csv"
LOG = HERE / "logs" / "rerun_timeouts.csv"
PID_FILE = HERE / "logs" / "rerun_timeouts.pid"
PROGRESS = HERE / "logs" / "progress"

DEFAULT_HOURS = 7 * 24
DEFAULT_JOBS = 8
# How often the log says how far the run has got, in seconds.
HEARTBEAT_S = 3600


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
    # DimFlux first and ReDraw last; the others by how few drawings they have to
    # redo; within an algorithm the smallest lattice first.
    count = Counter(a for _, a in todo)
    place = {"dimflux": 0, "redraw": 2}
    return sorted(todo, key=lambda job: (place.get(job[1], 1), count[job[1]], job[1],
                                         int(job[0]["concepts"]), job[0]["scale"]))


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


def record(row: dict, stopped: bool, finished: int, killed: int, log_state: dict,
           total: int) -> tuple[int, int]:
    """Write one outcome to drawings.csv and the log; return the updated counts."""
    if stopped and row["status"] == "error" and "code -9" in row.get("note", ""):
        # Killed by --stop mid-run: whatever it had written is not a drawing.
        ran = float(row["runtime_s"])
        partial = graphml_path(row["algorithm"], row["context"], row["scale"])
        partial.unlink(missing_ok=True)
        sidecar(partial).unlink(missing_ok=True)
        row.update(status="timeout", wall_budget_s=round(ran),
                   note=f"still running when the run was stopped after {ran / 3600:.2f} h; killed")
        killed += 1
    elif row["status"] == "timeout":
        killed += 1
    else:
        finished += 1
    merge_csv(DRAWINGS_CSV, [row], ("context", "scale", "algorithm"))
    if log_state["writer"] is None:
        log_state["writer"] = csv.DictWriter(log_state["file"], fieldnames=["finished", *row])
        if log_state["header"]:
            log_state["writer"].writeheader()
    log_state["writer"].writerow({"finished": time.strftime("%Y-%m-%d %H:%M"), **row})
    log_state["file"].flush()
    print(f"  [{finished + killed:3d}/{total}] {row['algorithm']:20s} {row['scale']:45s} "
          f"{row['status']:14s} {row.get('runtime_s', '')} s", flush=True)
    return finished, killed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--hours", type=float, default=DEFAULT_HOURS,
                        help=f"wall-clock budget per drawing, in hours (default: {DEFAULT_HOURS}, "
                             f"seven days)")
    parser.add_argument("--algorithm", choices=ALGORITHMS, help="only this algorithm")
    parser.add_argument("--jobs", type=int, default=DEFAULT_JOBS,
                        help=f"drawings at a time (default: {DEFAULT_JOBS})")
    parser.add_argument("--conexp-jar", type=Path, default=DEFAULT_CONEXP_JAR)
    parser.add_argument("--dry-run", action="store_true", help="list the drawings and stop")
    parser.add_argument("--stop", action="store_true",
                        help="end the run in progress, recording what is still running")
    args = parser.parse_args()
    if args.stop:
        return stop_run()

    budget_s = int(args.hours * 3600)
    if budget_s <= run_harness.WALL_BUDGET_S:
        raise SystemExit(f"--hours must exceed the {run_harness.WALL_BUDGET_S // 60}-minute "
                         f"budget the timeouts were recorded under")
    todo = timed_out(budget_s, args.algorithm)
    jobs = max(1, min(args.jobs, len(todo)))
    print(f"{len(todo)} timed-out drawings, {jobs} at a time, {args.hours:g} h budget each, "
          f"in this order:")
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
    run_harness.WALL_BUDGET_S = budget_s
    # Each drawing's worker inherits this and writes its progress there.
    os.environ[progress.ENV] = str(PROGRESS)
    previous = {(r["context"], r["scale"], r["algorithm"]): r for r in read_csv(DRAWINGS_CSV)}
    LOG.parent.mkdir(exist_ok=True)
    PID_FILE.write_text(str(os.getpid()))
    new_log = not LOG.exists()
    started = time.time()
    stopping = {"at": None}
    futures: dict = {}

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

    def attempt(spec, algorithm):
        print(f"  started {algorithm} on {spec['scale']} ({spec['concepts']} concepts)",
              flush=True)
        return drawing_row(spec, algorithm, previous, False)

    finished = killed = 0
    try:
        with ThreadPoolExecutor(max_workers=jobs) as pool, LOG.open("a", newline="") as log:
            log_state = {"file": log, "writer": None, "header": new_log}
            futures.update({pool.submit(attempt, spec, algorithm): (algorithm, spec["scale"])
                            for spec, algorithm in todo})
            pending, next_beat = set(futures), started + HEARTBEAT_S
            while pending:
                done, pending = wait(pending, timeout=max(0.0, next_beat - time.time()),
                                     return_when=FIRST_COMPLETED)
                if time.time() >= next_beat and pending:
                    next_beat += HEARTBEAT_S
                    running = Counter(futures[f][0] for f in pending if f.running())
                    waiting = sum(not f.running() for f in pending)
                    print(f"{time.strftime('%Y-%m-%d %H:%M')}, after "
                          f"{(time.time() - started) / 3600:.1f} h: {finished} finished, "
                          f"{killed} timed out, {waiting} waiting, running: "
                          + ", ".join(f"{a} {n}" for a, n in running.most_common()), flush=True)
                    for f in pending:
                        if f.running():
                            algorithm, scale = futures[f]
                            print(f"    {algorithm:20s} {scale:40s} "
                                  f"{progress.latest(PROGRESS, algorithm, scale)}", flush=True)
                for future in done:
                    try:
                        row = future.result()  # a fault on our side stops the run
                    except CancelledError:
                        continue               # never started; its old record stands
                    finished, killed = record(row, stopping["at"] is not None, finished,
                                              killed, log_state, len(todo))
    except EnvironmentFault as exc:
        print(f"stopped: {exc}", file=sys.stderr)
        return 1
    finally:
        if server is not None:
            server.kill()
        PID_FILE.unlink(missing_ok=True)
    hours = ((stopping["at"] or time.time()) - started) / 3600
    print(f"done after {hours:.2f} h: {finished} finished, {killed} recorded as timeouts, "
          f"{len(todo) - finished - killed} not started")
    return 0


if __name__ == "__main__":
    sys.exit(main())
