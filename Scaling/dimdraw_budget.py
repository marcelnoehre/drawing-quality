"""Is dimdraw slow because of its time budget, or because the problem is hard?

Its generator asks odis for a drawing with a 60 second budget:
``context.draw('dimdraw', 60000)``. Three runs at 46 concepts each returned in
60.07 s, which is what a binding budget looks like rather than a measurement.
DimDraw computes a two-dimension extension, which is NP-hard, so the alternative
is that the problem is genuinely intractable at that size.

The two have opposite consequences. If the cap is the problem, raise it and
dimdraw may reach the middle of our range. If the problem is intractable, dimdraw
is unusable above roughly fifty concepts, and with zschalig and lessink absent and
dimflux excluded, no structure-driven algorithm is left for RQ2 to contrast.

**Answered, and neither alternative as stated.** The cost tracks incomparable
pairs rather than concept count: `Cn5` from DimDraw's own data set consumes any
budget at 32 concepts, while our `family-excitation` finishes in 0.41 s at 27 with
260 incomparable pairs. So there is no single concept count above which it is
unusable, and the sensitivity check found identical scores at 60 s and 600 s on
three mid-size scales. dimdraw stays in: it is anytime, and a capped result is a
legitimate drawing, recorded with its budget. See pipeline.md.

    python dimdraw_budget.py --context contexts/instruments/practice.cxt --budget 600
"""
import argparse, time
from pathlib import Path
import odis

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--context', type=Path,
                        default=Path('contexts/instruments/practice.cxt'))
    parser.add_argument('--budget', type=float, default=600.0,
                        help='seconds given to odis')
    args = parser.parse_args()

    context = odis.FormalContext.from_file(str(args.context))
    n_concepts = len(list(context.concepts()))
    print(f'{args.context.name}: {n_concepts} concepts, budget {args.budget:.0f}s',
          flush=True)

    started = time.perf_counter()
    drawing = context.draw('dimdraw', int(args.budget * 1000))
    elapsed = time.perf_counter() - started
    print(f'returned after {elapsed:.2f}s with {len(list(drawing.nodes))} nodes')
    print('verdict:', 'the 60s cap was binding' if elapsed < args.budget * 0.95
          else 'ran to the budget: intractable at this size')


if __name__ == '__main__':
    main()
