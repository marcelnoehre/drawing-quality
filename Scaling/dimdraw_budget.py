"""Is dimdraw slow because of its time budget, or because the problem is hard?

Its generator asks odis for a drawing with a 60 second budget:
``context.draw('dimdraw', 60000)``. Three runs at 46 concepts each returned in
60.07 s, which is what a binding budget looks like rather than a measurement.
DimDraw computes a two-dimension extension, which is NP-hard, so the alternative
is that the problem is genuinely intractable at that size.

The answer is neither alternative as stated: the cost tracks incomparable pairs
rather than concept count. `Cn5` from DimDraw's own data set consumes any budget at
32 concepts, while `instruments_family_excitation` finishes in 0.41 s at 27 with
260 incomparable pairs. There is no single concept count above which it is
unusable, and a capped result is a legitimate drawing, recorded with its budget.
See pipeline.md, *What the algorithms do, measured*.

    python dimdraw_budget.py --context contexts/instruments/instruments_practice.cxt --budget 600
"""
import argparse, time
from pathlib import Path
import odis

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--context', type=Path,
                        default=Path('contexts/instruments/instruments_practice.cxt'))
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
