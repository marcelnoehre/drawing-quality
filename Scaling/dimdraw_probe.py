"""Where does DimDraw's time actually go: the published examples, or our contexts?

The algorithm's author reports about a second; we measured 600 s without
completion at 46 concepts. This times the same odis call on the lattices the
DimDraw and ReDraw papers use, alongside ours, and records what distinguishes them.
"""
import sys, time
from pathlib import Path
import odis

BUDGET_MS = 30_000

def poset_stats(concepts):
    exts = [frozenset(c.extent.to_frozenset()) for c in concepts]
    n = len(exts)
    incomparable = sum(1 for i in range(n) for j in range(i + 1, n)
                       if not (exts[i] <= exts[j] or exts[j] <= exts[i]))
    return n, incomparable

def main() -> None:
    for path in [Path(p) for p in sys.argv[1:]]:
        try:
            context = odis.FormalContext.from_file(str(path))
            n_concepts, incomparable = poset_stats(list(context.concepts()))
            started = time.perf_counter()
            context.draw("dimdraw", BUDGET_MS)
            elapsed = time.perf_counter() - started
            hit = elapsed > BUDGET_MS / 1000 * 0.95
            print(f"{path.name:34s} "
                  f"{len(context.objects):4d}x{len(context.attributes):<3d} "
                  f"{n_concepts:5d} concepts {incomparable:7d} incomparable pairs "
                  f"{elapsed:8.2f}s {'HIT BUDGET' if hit else ''}", flush=True)
        except Exception as exc:
            print(f"{path.name:34s} failed: {type(exc).__name__}: {exc}", flush=True)


if __name__ == "__main__":
    main()
