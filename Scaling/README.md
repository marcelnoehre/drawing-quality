# Scale-measures for lattice drawing evaluation

The scales part of evaluating line-diagram drawing algorithms. A
scale-measure is a coarser view of a formal context: the same objects, fewer
distinctions, hence a smaller lattice. Building families of them from one data set
gives a size ladder in which the levels are related rather than merely
similar-sized. That is what lets the question here be asked: whether an algorithm
places the same concept consistently as the view is refined. Consistency is ranked
together with drawing quality, using the surrounding repository's metrics, because
an algorithm can be stable simply by drawing badly; a level an algorithm cannot draw
counts against it on both.

This directory holds the data, the contexts and scales built from it, the pipeline
that draws and measures them, and the results.

## Layout

| Path | What it is |
|---|---|
| `../` | The drawing-quality repository: its own `contexts/`, `line_diagrams/`, `lattice_metrics/`, `drawings/` and `main.py`. |
| `pipeline.md` | **How the pipeline works and why**: scales, drawing, quality, consistency, the null, the ranking, the test across contexts, the output files, the equations, the ladder figures, limitations and open questions. |
| `contexts/` | **Everything about the contexts**, one folder each: the context, its scale-measures, its manifest and nesting matrix, its groupings and its README. |
| `Datasets/` | The raw material: matrices and codebooks for the two hand-built contexts, and source tables, original build scripts and provenance READMEs for the three astronomy contexts. |
| `graphml/`, `drawings/` | The drawings, by algorithm and context, and their PDF renders. Regenerable in principle but hours of compute. |
| `figures/` | `ladder_instruments.png`, `ladder_olympics.png` (best and worst algorithm on one ladder of scales per context) and `column-order-demo.png` (one lattice, two column orders, two drawings). |
| `tests/` | Regression tests, with the small contexts they pin. |
| `*.csv` | The results; see below. |

### Code

| File | What it does |
|---|---|
| `build_contexts.py` | Cleans the collected data and generates the five contexts built here. |
| `contexts/import_standard_contexts.py` | Measures the repository's own contexts and imports those large enough to scale. |
| `contexts/build_scales.py` | Builds the scales of a context, measures them, verifies each one. |
| `contexts/verify_scale.py` | Checks the scale-measure property per attribute and writes the nesting matrix. |
| | Both use [ConceptFlow](https://github.com/anuragxorma/conceptflow) for the FCA operations: `scale_measure` builds a scale, `scale_measure_problems` checks it, `refines` decides nesting, and `lattice_width`, `lattice_height` and `incomparable_pairs` measure it. |
| `node_extents.py` | Records which concept every node is while a drawing is written, as `<scale>.extents.json`. Nothing downstream is trustworthy without this. |
| `graphml_loader.py` | Loads a drawing as `extent -> (x, y)` from that record, checking it against the lattice and the drawn edges every time. |
| `consistency.py` | Kendall tau on x-ranks and its magnitude, rank drift, per-stratum tau. `--self-test` runs three adversarial fixtures. |
| `nulls.py` | The permutation null, restricted to rank strata. `--self-test`. |
| `run_harness.py` | Draws every scale with every algorithm under a 30-minute budget, scores the drawings, compares across scales, then ranks. Recomputes only what changed. |
| `rerun_timeouts.py` | Draws again, under a seven-day budget, every drawing recorded as a timeout, and records the outcomes and their runtimes in `drawings.csv`. |
| `ranking.py` | Ranks the algorithms on quality (the repository's 14 metrics in its four families), on consistency, and on both combined, penalising failed drawings and weighting each view by log₂ of its size; writes the weight sweep and the profile. |
| `ladder_figure.py` | The best and the worst algorithm drawing one ladder of nested scales, the followed concepts coloured by position. |
| `robustness.py` | Repeats the test across contexts without Living Beings and Water, with astronomy as one case, and with pairwise Wilcoxon tests; writes `robustness.csv`. |
| `column_order.py` | Draws four scales under shuffled columns and rows and compares with the canonical drawings; writes `column_order.csv`, and with `--figure` the column-order figure. |
| `profile_algorithms.py`, `dimdraw_*.py` | Timing and determinism measurements, written up in `pipeline.md` under *What the algorithms do, measured*. |

### Results

All are long format — one row per observation, never one column per level.

| File | One row per |
|---|---|
| `scales.csv` | scale: size, width, height, incomparable pairs, whether it is worth drawing |
| `drawings.csv` | (scale, algorithm): status — drawn, or how it failed and why — and runtime |
| `quality.csv` | (scale, algorithm): the 14 metric scores of the drawing |
| `consistency.csv` | (nested pair, algorithm): tau, rank drift, the null, the stratum summary |
| `consistency_strata.csv` | (nested pair, algorithm, rank stratum): tau within that stratum |
| `ranking.csv` | (context, view weighting, measure, algorithm): mean rank, 1 = best, for quality, consistency and combined |
| `sensitivity.csv` | (weight on consistency, algorithm): the ranking as that weight goes from 0 to 1 |
| `profile.csv` | (context, algorithm): what it drew, where it failed and how |
| `friedman.csv` | (measure, algorithm): across contexts, the Friedman test, Holm against the best and the Nemenyi critical difference (Demšar 2006) |

What every column means, and the equations behind them, is in `pipeline.md` under
*Reading the output files* and *The equations*.

Runs are incremental: a filtered run merges its rows into these files rather than
replacing them, and drawings already on disk are not recomputed.

## What is computed

From each context to a ranking of the drawing algorithms, in four filters and four
computations.

**The filters.**

| Term | Meaning |
|---|---|
| **scale** | every view of a context we build: a scale-measure written as its own `.cxt`, listed in the context's `manifest.csv`, chosen by hand and recorded in `groupings.md` before anything is drawn |
| **drawable** | a scale given to the drawing algorithms: 12 to 1000 concepts, with width at least 3. Smaller, every algorithm draws nearly the same picture; width 1 or 2 is essentially a chain with nothing to lay out; larger is impractical to draw. The rest are built and kept, never drawn |
| **nested pair** | two scales where every concept of the coarser is also a concept of the finer, so the coarser scale's concepts reappear in the finer drawing |
| **usable pair** | a nested pair of two drawable scales sharing at least 8 concepts: the comparisons consistency is measured on |

**The computations** (`run_harness.py`, then `ranking.py`):

1. **Draw** every drawable scale with each of the eight algorithms, under a
   30-minute budget per drawing. A drawing that does not happen is a failure --
   declined, timed out, crashed or known not to terminate -- recorded with its
   reason and counted against the algorithm, never dropped.
2. **Score** every drawing on the 14 metrics of the drawing-quality analysis, in its
   four families: crossings, layering, slopes, clearance.
3. **Compare** each usable pair: does the algorithm keep the left-to-right order of
   the coarser scale's concepts in its drawing of the finer one -- one way round or
   the other, since a mirror image of the whole drawing keeps every relation?
   |Kendall tau| on x-ranks, against a permutation null; the signed tau is kept
   beside it.
4. **Rank** the algorithms per context and overall: quality counts four fifths and
   consistency one fifth, each view weighted by log₂ of its size, a failure ranked
   last. A context is ranked only once all eight algorithms have an outcome on all
   of it, and an overall ranking over fewer than all contexts is marked PARTIAL.
   Across contexts, a Friedman test with post-hoc comparisons says which
   differences are larger than chance.

**What there is to compute on:**

| Context | Scales | Drawable | Nested pairs | Usable pairs | Drawn sizes (concepts) |
|---|---|---|---|---|---|
| `instruments` | 11 | 11 | 17 | 17 | 13–576 |
| `olympics` | 15 | 14 | 30 | 16 | 12–444 |
| `tenpc_exoplanets` | 10 | 7 | 23 | 10 | 15–371 |
| `tenpc_stars` | 14 | 10 | 37 | 19 | 14–732 |
| `wd40pc` | 17 | 12 | 61 | 35 | 13–728 |
| `olympic_disciplines` | 8 | 8 | 14 | 14 | 17–529 |
| `music` | 7 | 5 | 12 | 6 | 12–163 |
| `diagnosis` | 7 | 6 | 12 | 9 | 18–88 |
| `zoo` | 10 | 8 | 19 | 7 | 32–781 |
| `living_beings_and_water` | 2 | 2 | 1 | 1 | 12–19 |
| `seasoning_planner` | 9 | 8 | 20 | 17 | 37–532 |
| **all** | **110** | **91** | **246** | **151** | |

The usable pairs are the evidence for consistency, and the drawable scales for
quality. In the ranking every context counts the same, however many pairs it has:
more pairs make a context's result more precise, not more influential.

Every term, equation and choice is explained in `pipeline.md`.

## Setup

```bash
cd <repository>/Scaling
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

`requirements.txt` pins the exact versions the current results were produced with,
including the parts of the surrounding repository's stack that the harness imports.
Scales are built, checked and measured with ConceptFlow 0.6.0. The `dim-flux` pin matters: 1.0.10 is the first version that keeps the whole
context, so its drawings can be matched by extent at all. `redraw` additionally
needs conexp-clj 3.1.0 serving on :8080; the harness refuses to start without it.

## Building the contexts

```bash
.venv/bin/python build_contexts.py
```

This reads `Datasets/`, writes the five `.cxt` files into `contexts/`, and prints
the size and density of each. Nothing under `Datasets/` is written to.

For the three astronomy contexts the script does more than convert: it recomputes
all 28, 35 and 16 attributes from the many-valued source tables, applying the same
rules as the original pipelines, and then compares the result against the context
files those pipelines produced. The run currently reports all three as identical. A
mismatch means this script is wrong, not the data, and the run exits with a nonzero
status so it can be used as a check.

Expected output:

```
instruments           64 objects x  42 attributes   density 0.229
olympics              70 objects x  38 attributes   density 0.402
wd40pc              1078 objects x  28 attributes   density 0.226
tenpc_stars          456 objects x  35 attributes   density 0.236
tenpc_exoplanets      85 objects x  16 attributes   density 0.476
```

## Conventions

- **Scale files are named after their context**: `<context>_<name>.cxt`, lowercase
  with underscores only, e.g. `instruments_family_practice.cxt`; the full context
  keeps its own name. The same id is used for every drawing and every CSV row.
- **Every scale of a context lists its attributes in one fixed order.** The drawing
  algorithms respond to column order, so this keeps file order out of the
  comparison between levels.
- **Every drawing has its `.extents.json` beside it.** A drawing without one is
  redrawn, never guessed at.
- **Nothing is dropped.** A drawing that does not happen is recorded as `declined`,
  `timeout`, `error` or `nonterminating`, with its reason, and counts against the
  algorithm in the ranking.

## Running the pipeline

```bash
.venv/bin/python consistency.py --self-test        # before trusting any number
.venv/bin/python nulls.py --self-test
.venv/bin/python tests/test_ranking.py
.venv/bin/python tests/test_integrity.py
.venv/bin/python tests/test_dimdraw_cost.py
.venv/bin/python tests/test_fdp_termination.py

.venv/bin/python contexts/build_scales.py --context instruments   # rebuild scales
.venv/bin/python run_harness.py                                    # everything
.venv/bin/python run_harness.py --context instruments --algorithm freese
.venv/bin/python run_harness.py --no-draw                          # rescore, recompare, re-rank
.venv/bin/python ranking.py                                        # re-rank only
.venv/bin/python ladder_figure.py                                  # the ladder figure
```

The full sweep takes hours: every algorithm draws every drawable scale, eight at a
time, each under a 30-minute wall-clock budget. It cannot hang — a drawing still
running at the limit is killed and recorded as a timeout — and it is incremental:
finished drawings are reused while the `.cxt` they were drawn from is unchanged
(each drawing records its sha256), recorded failures are not attempted again for
the same file and budget unless `--retry-failed` is given, and every score and comparison carries a fingerprint of
what it was computed from, so it is only recomputed when that changes. With nothing
changed, a full run takes under a second.

To run it unattended -- overnight, or over a weekend with the lid closed:

```bash
./run_unattended.sh                       # takes the same options as run_harness.py
tail -f logs/unattended.log               # progress
kill -- -"$(cat logs/unattended.pgid)"    # stop
```

It returns at once and survives closing the editor and the terminal. While it runs
the laptop will not sleep, lid closed or not; when it ends, sleep is allowed again.
No system setting is changed. It starts redraw's conexp server if needed. Plug the
laptop in and leave it on a hard surface; every finished drawing is saved as it
happens, so an interruption costs only the drawings in progress.

## Rerunning the timeouts under a seven-day budget

`rerun_timeouts.py` draws again every drawing recorded in `drawings.csv` as a
timeout, with only the algorithm that timed out on it, and leaves every other
outcome as it is: a drawing, a decline, an invalid layout or a known
non-termination does not depend on the budget. It is meant for a server, from a
fresh clone:

```bash
git clone <this repository> drawing-quality
git clone https://github.com/domduerr/redraw            # beside it, for redraw
git -C redraw checkout 80f62a97a5ff41d173b61113cc90f80864f49f41
mkdir tools                                            # beside both: the conexp-clj
#   3.1.0 standalone jar as tools/conexp-clj.jar; redraw needs it, and Java

cd drawing-quality/Scaling
python3.14 -m venv .venv && .venv/bin/pip install -r requirements.txt

.venv/bin/python rerun_timeouts.py --dry-run              # what would run
mkdir -p logs
setsid nohup .venv/bin/python -u rerun_timeouts.py \
    > logs/rerun_timeouts.log 2>&1 < /dev/null &
tail -f logs/rerun_timeouts.log                           # progress
.venv/bin/python rerun_timeouts.py --stop                 # end it early, if needed
```

Every drawing gets seven days and all start at once, so all of them have been
running for the same time whenever the run ends. A drawing still running after
seven days is killed and recorded as a timeout, a failure. The run ends by itself
when the last drawing has finished or reached seven days. `--stop` ends it earlier:
every drawing still running is then killed and recorded as a timeout, with the
time it ran as its budget. Do not end it by killing the process, which records
nothing for the drawings still running. `--hours` sets another budget, and
`--algorithm` restricts the run to one algorithm.

Before drawing anything it loads every generator it needs, and it starts the
conexp-clj API for redraw if it is not running. Each outcome is written to
`drawings.csv` the moment it finishes, with how long it ran (`runtime_s`), and
every hour the log says how long the run has gone and how many drawings are still
running. The results can therefore be committed at any point, the drawings
finished so far included; when the run has ended, commit them once more:

```bash
git add drawings.csv graphml drawings
git commit -m "Scaling: timed-out drawings redrawn under a seven-day budget"
```

Scoring, comparing and ranking with them is then
`run_harness.py --no-draw`, `ranking.py` and `robustness.py`.

## State

Eleven contexts are scaled (`contexts/README.md`, *Scaled so far*).
`wood_properties` is not, until the meaning of its abbreviated attributes is
known. All eight algorithms are run on every drawable scale. The results are the
CSV files above; a ranking over fewer than all contexts is marked PARTIAL in them.
What is still open is listed in `pipeline.md` under *Limitations* and *Open
questions*.
