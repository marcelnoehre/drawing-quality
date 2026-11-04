"""Progress of one drawing while it runs, written to a file of its own.

A long drawing gives no sign of life until it ends, which under a budget of days is
too long to wait. When `DRAW_PROGRESS_DIR` is set, the drawing's worker process
writes `<dir>/<algorithm>/<scale>.log`:

* a line when each main step of the algorithm starts and when it finishes, with
  how long it took (`PHASES` names the steps of every generator);
* a count of the algorithm's iterations, where one function runs once per
  iteration (`COUNTED`);
* every `INTERVAL_S`, how long the drawing has run, which of the algorithm's
  functions it is in at that moment, and the counts so far;
* whatever the generator prints, such as redraw's "Dimension 4:".

Nothing here changes what an algorithm computes: each wrapped function is called
with its own arguments and returns its own result. `rerun_timeouts.py` sets the
variable; a normal run of `run_harness.py` does not, and writes nothing.
"""

from __future__ import annotations

import functools
import importlib
import os
import sys
import threading
import time
from pathlib import Path

ENV = "DRAW_PROGRESS_DIR"
# How often a running drawing says where it is, in seconds (overridable for tests).
INTERVAL_S = float(os.environ.get("DRAW_PROGRESS_INTERVAL_S", 600))

# (module, class, method, label): a main step, logged when it starts and ends.
PHASES = {
    "dimflux": [("dim_flux.core.realizer", "Realizer", "__init__", "realizer"),
                ("dim_flux.fdp.forces", "ForceDirectedPlacement", "__init__", "force placement")],
    "redraw": [("util", "Order", "__init__", "lattice from conexp and setup"),
               ("algorithm", None, "round", "force round"),
               ("util", "Order", "dimension_stepdown", "dimension step-down")],
    "freese": [("freese", "Freese", m, m.strip("_").replace("_", " "))
               for m in ("_build_order", "_rank_function", "_comparability",
                         "_initialize_points", "_force_iteration", "_project")],
    "fdp": [("fdp", "FDP_Additive_Features", m, m.strip("_").replace("_", " "))
            for m in ("_build_cover_relations", "_sup_inf_distance", "_initialize_vectors",
                      "_optimize_layout")],
    "cole_ducrou_eklund": [("cole_ducrou_eklund", "ColeDucrouEklund", m,
                            m.strip("_").replace("_", " "))
                           for m in ("_structural_precomputation", "_order_attributes",
                                     "_build_offsets", "_build_subcontexts", "_search", "_rank")],
}
# Every generator renders a PDF of its drawing at the end, with the draw_graphml it
# imported under that name; module None stands for the generator's own module.
COMMON = [(None, None, "draw_graphml", "rendering the PDF")]

# (module, class, method, label): a function called once per iteration, counted.
COUNTED = {
    # Up to 1000 node steps and 1000 line steps per round, four rounds (dimensions 5 to 2).
    "redraw": [("util", "Order", "apply_forces", "force iterations (at most 2000 per round, 4 rounds)")],
    "freese": [("freese", "Freese", "_forces", "force iterations")],
    "fdp": [("fdp", "FDP_Additive_Features", "_total_energy_and_gradient",
             "energy evaluations")],
    "cole_ducrou_eklund": [("cole_ducrou_eklund", "ColeDucrouEklund", "_satisfactory",
                            "candidate layouts tested")],
}


class _Log:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.file = path.open("a", encoding="utf-8")
        self.started = time.time()
        self.counts: dict[str, int] = {}
        self.lock = threading.Lock()

    def line(self, text: str) -> None:
        with self.lock:
            elapsed = (time.time() - self.started) / 3600
            self.file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}  +{elapsed:6.2f} h  {text}\n")
            self.file.flush()

    def counts_text(self) -> str:
        return ", ".join(f"{n} {label}" for label, n in self.counts.items() if n)


class Tee:
    """Write what the generator prints both where it went before and to the log."""

    def __init__(self, stream, log: _Log):
        self.stream, self.log, self.pending = stream, log, ""

    def write(self, text: str) -> int:
        self.pending += text
        *lines, self.pending = self.pending.split("\n")
        for line in lines:
            if line.strip():
                self.log.line(f"printed: {line.strip()[:200]}")
        return self.stream.write(text)

    def flush(self) -> None:
        self.stream.flush()


def _resolve(module: str, cls: str | None):
    owner = importlib.import_module(module)
    return getattr(owner, cls) if cls else owner


def _wrap_phase(log: _Log, owner, name: str, label: str) -> None:
    original = getattr(owner, name)
    seen = {"n": 0}

    @functools.wraps(original)
    def phase(*args, **kwargs):
        seen["n"] += 1
        which = f"{label} {seen['n']}" if seen["n"] > 1 or label == "force round" else label
        log.line(f"start {which}")
        began = time.time()
        try:
            result = original(*args, **kwargs)
        except BaseException as exc:
            log.line(f"failed in {which} after {(time.time() - began) / 60:.1f} min: "
                     f"{type(exc).__name__}")
            raise
        counts = f" ({log.counts_text()})" if log.counts_text() else ""
        log.line(f"done  {which} in {(time.time() - began) / 60:.1f} min{counts}")
        return result

    setattr(owner, name, phase)


def _wrap_count(log: _Log, owner, name: str, label: str) -> None:
    original = getattr(owner, name)
    log.counts[label] = 0

    @functools.wraps(original)
    def counted(*args, **kwargs):
        log.counts[label] += 1
        return original(*args, **kwargs)

    setattr(owner, name, counted)


def _where(main_ident: int) -> str:
    """The algorithm's own functions on the main thread's stack, outermost first."""
    frame = sys._current_frames().get(main_ident)
    names = []
    while frame is not None:
        code = frame.f_code
        path = code.co_filename
        if "line_diagrams" in path or "dim_flux" in path or "redraw" in path:
            names.append(f"{code.co_name} ({Path(path).name}:{frame.f_lineno})")
        frame = frame.f_back
    return " > ".join(reversed(names[:4])) or "outside the algorithm's code"


def install(algorithm: str, context: str, scale: str, generator) -> _Log | None:
    """Start logging this drawing's progress, if `DRAW_PROGRESS_DIR` is set."""
    root = os.environ.get(ENV)
    if not root:
        return None
    log = _Log(Path(root) / algorithm / f"{scale}.log")
    log.line(f"started {algorithm} on {context}/{scale}")
    for module, cls, name, label in PHASES.get(algorithm, []) + COMMON:
        try:
            _wrap_phase(log, generator if module is None else _resolve(module, cls), name, label)
        except (ImportError, AttributeError) as exc:
            log.line(f"(no marker for {label}: {type(exc).__name__})")
    for module, cls, name, label in COUNTED.get(algorithm, []):
        try:
            _wrap_count(log, _resolve(module, cls), name, label)
        except (ImportError, AttributeError) as exc:
            log.line(f"(no counter for {label}: {type(exc).__name__})")

    main_ident = threading.main_thread().ident

    def sample():
        while True:
            time.sleep(INTERVAL_S)
            counts = f"; {log.counts_text()}" if log.counts_text() else ""
            log.line(f"running, in {_where(main_ident)}{counts}")

    threading.Thread(target=sample, daemon=True).start()
    return log


def latest(root: Path, algorithm: str, scale: str) -> str:
    """The last line a drawing's progress file holds, for the run's hourly summary."""
    path = root / algorithm / f"{scale}.log"
    try:
        with path.open("rb") as f:
            f.seek(max(0, path.stat().st_size - 2000))
            lines = f.read().decode("utf-8", "replace").strip().splitlines()
        return lines[-1] if lines else "(no progress yet)"
    except OSError:
        return "(no progress file)"
