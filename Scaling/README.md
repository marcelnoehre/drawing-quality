# Scale-measures for lattice drawing evaluation

The scales part of evaluating line-diagram drawing algorithms. A
scale-measure is a coarser view of a formal context: the same objects, fewer
distinctions, hence a smaller lattice. Building families of them from one data set
gives a size ladder in which the levels are related rather than merely
similar-sized, which is what lets two questions be asked at once — whether drawing
quality improves as the lattice coarsens, and whether an algorithm places the same
concept consistently across levels.

This directory holds the data, the contexts and scales built from it, the pipeline
that draws and measures them, and the results.

## Layout

| Path | What it is |
|---|---|
| `../` | The drawing-quality repository: its own `contexts/`, `line_diagrams/`, `lattice_metrics/`, `drawings/` and `main.py`. |
| `pipeline.md` | **The working notes.** How everything works, what it found, and what is still open. Start at its *Method* section. |
| `contexts/` | **Everything about the contexts**, one folder each: the context, its scale-measures, its manifest and nesting matrix, its groupings and its README. |
| `Datasets/` | The raw material: matrices and codebooks for the two hand-built contexts, and source tables, original build scripts and provenance READMEs for the three astronomy contexts. |
| `graphml/`, `drawings/` | The drawings, by algorithm and context, and their PDF renders. Regenerable in principle but hours of compute. |
| `figures/` | The gate figures. |
| `tests/` | Regression tests, with the small contexts they pin. |
| `*.csv` | The results; see below. |

### Code

| File | What it does |
|---|---|
| `build_contexts.py` | Cleans the collected data and generates the five contexts built here. |
| `contexts/import_standard_contexts.py` | Measures the repository's own contexts and imports those large enough to scale. |
| `contexts/build_scales.py` | Builds the scales of a context, measures them, verifies each one. |
| `contexts/verify_scale.py` | Checks the scale-measure property per attribute and writes the nesting matrix. |
| `check_node_mapping.py` | Verifies that a drawing's node ids can be turned back into concepts, per algorithm, under three hash seeds. Nothing downstream is trustworthy without this. |
| `graphml_loader.py` | Loads a drawing as `extent -> (x, y)`, re-checking the enumeration order every time. |
| `consistency.py` | Kendall tau on x-ranks, rank drift, per-stratum tau. `--self-test` runs three adversarial fixtures. |
| `nulls.py` | The permutation null, restricted to rank strata. `--self-test`. |
| `run_harness.py` | Draws, scores, compares; writes the four result files. |
| `gate.py` | Renders algorithms × scales with one followed scale marked, for looking at. |
| `profile_algorithms.py`, `dimdraw_*.py` | Timing and determinism measurements. Their findings are written up in `pipeline.md`. |

### Results

All four are long format — one row per observation, never one column per level.

| File | One row per |
|---|---|
| `scales.csv` | scale: size, width, height, incomparable pairs, whether it is worth drawing |
| `drawings.csv` | (scale, algorithm): status, runtime, budget, and every metric score |
| `consistency.csv` | (nested pair, algorithm): tau, rank drift, the null, the stratum summary |
| `consistency_strata.csv` | (nested pair, algorithm, rank stratum): tau within that stratum |

Runs are incremental: a filtered run merges its rows into these files rather than
replacing them, and drawings already on disk are not recomputed.

## Setup

```bash
cd <repository>/Scaling
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

`requirements.txt` pins the exact versions the current results were produced with,
including the parts of the surrounding repository's stack that the harness imports.
The `odis` pin matters: node identification depends on the order in which it
enumerates concepts. `redraw` additionally needs conexp-clj 3.1.0 serving on :8080.

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

## Running the pipeline

```bash
.venv/bin/python consistency.py --self-test        # before trusting any number
.venv/bin/python nulls.py --self-test
.venv/bin/python tests/test_dimdraw_cost.py
.venv/bin/python tests/test_fdp_termination.py
.venv/bin/python check_node_mapping.py             # ~5 min

.venv/bin/python run_harness.py --context instruments --algorithm aeschlimann_schmid
.venv/bin/python gate.py --out gate        # writes into figures/
```

Without `--context` or `--algorithm` the harness sweeps everything, which takes
hours. It will not hang: a scale beyond an algorithm's measured range, or one whose
context an algorithm cannot handle, is recorded as skipped with the reason.

## State

Two contexts are scaled, instruments and olympics; the others are collected and
unscaled. `aeschlimann_schmid` has been measured on all 17 nested pairs of
instruments and `fdp` on the two it can draw. Everything else — the full sweep,
the remaining nulls, order dimension — is listed at the end of `pipeline.md`, under
*Limitations* and *Open questions*.
