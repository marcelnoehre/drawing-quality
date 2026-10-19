# The scaling pipeline

How the scales of each context are drawn by the line-diagram algorithms of this
repository, how the drawings are scored, how consistently each algorithm places the
same concepts as a view grows, and how the algorithms are ranked on both. Each
section says what is done and why. `README.md` explains the layout and how to run
everything; `contexts/README.md` and each context's README and `groupings.md`
explain the data and the scales.

1. [Overview](#overview)
2. [Scales](#scales)
3. [Drawing](#drawing)
4. [Quality](#quality)
5. [Consistency](#consistency)
6. [The permutation null](#the-permutation-null)
7. [Ranking](#ranking)
8. [Across contexts: is the ranking more than chance?](#across-contexts-is-the-ranking-more-than-chance)
9. [Reading the output files](#reading-the-output-files)
10. [The equations](#the-equations)
11. [Ladder figures](#ladder-figures)
12. [Results](#results)
13. [What the algorithms do, measured](#what-the-algorithms-do-measured)
14. [Limitations](#limitations)
15. [Defects found in the generators](#defects-found-in-the-generators)
16. [Open questions](#open-questions)

---

# Overview

A **context** is a table of objects and attributes. A **scale** of it is a coarser
view: the same objects, fewer distinctions. When one scale's concepts are all
concepts of another, the two are **nested**, and every concept of the coarser one
appears in the drawings of both. The same algorithm then draws the same concept
twice, with no memory between the two runs, and the two placements can be compared.
No metric of a single drawing can say whether an algorithm keeps a reader's picture
intact as the view grows; this can.

`run_harness.py` runs four passes, each one incremental:

| Pass | Does | Writes |
|---|---|---|
| 1. draw | every algorithm draws every drawable scale, under a time budget | `drawings.csv`, `graphml/`, `drawings/` |
| 2. score | every drawing is scored on the 13 quality metrics of the repository's analysis | `quality.csv` |
| 3. compare | for every usable nested pair, how far each algorithm kept the coarser scale's concepts in their left-to-right order | `consistency.csv`, `consistency_strata.csv` |
| 4. rank | the algorithms on quality, on consistency and on both, per context and across contexts, with a significance test | `ranking.csv`, `sensitivity.csv`, `profile.csv`, `friedman.csv` |

---

# Scales

## What a scale is

A scale-measure, in the sense of Hanika and Hirth, keeps the objects and coarsens
the distinctions. Every scale here has the same objects as its context, and each of
its attributes is either an original attribute or a **conjunction** of original
attributes -- never a disjunction, never a negation.

The restriction is about guarantees. Attribute projections are scale-measures by
Hanika and Hirth's Cor. 22, and conjunctions by their Cor. 17, unconditionally.
Disjunctions and negations are scale-measures only when the resulting extent
happens to be an extent of the original context, which has to be checked case by
case and usually fails.

Every scale is one of three kinds:

| Kind | Construction |
|---|---|
| **facet** | a subset of the attributes, one coherent lens on the data |
| **chain step** | a scale refined by conjoining its attributes with attributes from *outside* it |
| **apposition** | two or more facets side by side |

Two rules decide which are worth building:

- **A conjunction refines only if it reaches outside the scale.** A scale's
  extents already include every intersection of its attribute extents, so
  conjoining two attributes that are both in the scale adds no concept.
- **An apposition needs a one-sentence description that is not a list.** "The
  rules of the contest: how it is run and how it is decided" earns its place;
  "structure and format and demands" does not.

## Groupings are by meaning, and recorded before anything is drawn

Attributes are grouped by what they mean, using the context's codebook or
documented source, never by structure or at random. A context whose attributes carry
no recoverable meaning is not scaled. Each context's `groupings.md` records the
groups, every scale built from them with its one-sentence view, the candidates
rejected and why, with a timestamp, **before any of its scales is drawn**, and is
not revised after drawing results are seen. Because the scales are chosen by hand
and then used to evaluate drawings, this record is what separates a considered
choice from one tuned to the answer.

## Nesting

For two scales to be compared, every extent of the coarser one must be an extent of
the finer one. That holds when a refinement **adds** attributes and keeps the ones it
refines, and fails when it replaces them: on Living Beings and Water, replacing a
general attribute by its two refinements gives 10 concepts and breaks nesting;
keeping it beside them gives 12, the size of Hanika and Hirth's published scale of
that context, and nesting holds.

| Term | Definition |
|---|---|
| **drawable** | between 12 and 1000 concepts, and width (largest antichain) at least 3. Below 12 every algorithm draws nearly the same picture; width 1 or 2 leaves almost no horizontal choice; above 1000 a diagram is no longer readable |
| **nested** | every extent of the coarser scale is an extent of the finer one |
| **usable** | nested, both scales drawable, and at least 8 shared concepts |

The overlap rule only matters for pairs that involve a scale outside the drawable
band: a nested pair of drawable scales shares every concept of the coarser scale,
which has at least 12.

## Checking the scales

`build_scales.py` builds every scale and checks it as it writes it, and
`verify_scale.py` checks again and writes the nesting matrix. Because a scale keeps
the objects unchanged, Hanika and Hirth's Prop. 20 makes a scale a scale-measure
exactly when each of its attributes is one, so the check is one closure per
attribute: its extent must be closed in the full context. Nesting is checked by
enumerating both extent sets. Each context's `manifest.csv` lists its scales with
their size, width, height and number of incomparable concept pairs, and
`nesting.csv` holds the pairwise nesting.

## Names and column order

A scale's file is `<context>_<name>.cxt`, lowercase with underscores only; the full
context keeps its own name. The same id is used for the drawing and in every CSV.
The manifest's `context` and `short_name` columns are the source of truth; nothing
parses an id.

**Every scale of a context lists its attributes in one canonical order**: by the
positions of their parts in the full context, compared as a sorted tuple. Two
attributes that occur in two scales are then in the same relative order in both,
so the only difference between the files of two nested scales is what the
refinement adds. **The objects keep one order too**: every scale lists them exactly
as the full context does. Both matter because the algorithms respond to the order
of columns, and some to the order of rows (see *What the algorithms do, measured*):
with an arbitrary order, a change between two drawings would mix the response to
refinement with the response to a reordered file. The order changes how a file is
written, never what it holds.

---

# Drawing

## Eight algorithms, every scale, one budget

`run_harness.py` asks each of the eight generators of the repository --
aeschlimann_schmid, cole_ducrou_eklund, dimdraw, dimflux, fdp, freese, redraw,
sugiyama -- to draw every drawable scale. Each drawing runs in its own process and
working directory, eight at a time, under a **wall-clock budget of 30 minutes**,
the same for every algorithm. The process group is killed at the limit and any
partial output deleted.

Thirty minutes is long enough that an algorithm which works at these sizes is not
turned into a failure for being slow, and short enough that a full run stays
practical. A timeout counts as a failure, so the budget is a parameter of the
results, not a detail. Every runtime is recorded, so its effect can be checked: see
*Results*, *Failures*.

Only a timeout depends on the budget. When the budget grows, recorded timeouts are
attempted again under the new one; drawings, declines and errors are kept, since a
drawing finished within the smaller budget finishes within the larger one too, and
`wall_budget_s` records the budget each outcome was obtained under.

Three algorithms also have **internal budgets** that are part of the algorithm:
dimdraw (60 s, an anytime search that returns its best layout so far), fdp (60 s,
bounding its optimiser only) and dimflux (60 s, bounding its force phase only).
These return a drawing rather than fail; `used_internal_budget` records where that
can be inferred from the runtime (dimdraw and fdp).

## Outcomes

| Status | Meaning |
|---|---|
| `drawn`, `cached` | a drawing exists, with its node identification recorded |
| `declined` | the generator said it could not draw this lattice |
| `timeout` | still running at the wall-clock budget, so killed |
| `error` | the generator raised, or its process died |
| `nonterminating` | a known non-termination, not run because it could only time out: fdp on a context with two attributes of equal extent (see *Defects*) |
| `invalid` | output was written but is not a usable drawing: a coordinate is not finite or exceeds 10⁹ in magnitude (the layout diverged), or every node lies on one vertical or one horizontal line (the layout collapsed) |

**Why `invalid` is a failure.** A diverged or collapsed layout is not a line diagram
a reader could use, and scoring it would reward it: with every node on one vertical
line, every edge is vertical and several quality metrics give their best score. The
bound is not delicate. Every valid drawing in the corpus stays within a few hundred
units, and the diverged ones reach 10⁴⁰ to 10⁸⁴, so any bound between 10³ and 10⁴⁰
classifies them identically. A few coinciding nodes do not make a drawing invalid;
that is a poor drawing, which the clearance metrics penalise.

**Nothing is dropped.** Every algorithm is asked to draw every drawable scale, and
an algorithm that does not produce a drawing has a failure recorded, with its
reason, which counts against it in the ranking. Dropping every lattice that some
algorithm cannot draw would keep the design balanced and lose exactly the
information that matters: which algorithm fails, and where.

**Contexts are not altered to suit an algorithm.** fdp cannot draw a context with
two coextensive attributes, which is common in real data; such a context is not
clarified to let fdp through. The attribute set is the chosen view, and removing a
label because it is coextensive with another would change every figure label and
the conjunctive description of the scale.

**A fault on our side never becomes an algorithm's result.** The run stops, with a
message saying what to fix, when: the conexp-clj server redraw needs is down before
a redraw drawing or after one fails; a generator cannot be loaded; a generator
returns without a drawing and without a reason; or recording the node
identification fails. Everything computed before the stop is kept.

## Caching

Drawing is the expensive part, so nothing is redone without a reason.

- **A drawing belongs to one exact file.** Each records the sha256 of the `.cxt` it
  was drawn from, and is reused, scored, compared and loaded only while that file is
  unchanged. The lattice alone cannot tell a stale drawing from a current one:
  reordering a scale's columns leaves its lattice unchanged and changes most
  drawings.
- **A recorded failure** is reused only for the same file under the same budget,
  and is attempted again with `--retry-failed`.
- **Every score and comparison** carries a fingerprint of the files it was computed
  from and of the code that computed it, and is recomputed only when that changes.
- Every row is saved as soon as it is computed, so an interrupted run loses only
  the drawings in progress.

## Which concept is node 7?

The generators write each node as `<node id="7">` with an x and a y and nothing
else. Comparing two drawings needs to know which concept each node is, and matching
by position in some ordering is not an option, because two scales have different
concepts. Nodes are matched by **extent**: by which objects the concept contains.

The identification is **recorded while the drawing is written, never rebuilt**
afterwards. `node_extents.py` wraps each generator's `write_graphml` in memory -- no
generator is edited -- reads from the object being written which extent each node
id stands for, and saves that table beside the drawing as `<scale>.extents.json`.
Rebuilding the numbering after the fact would depend on reproducing each
generator's internal ordering exactly, and fails silently when it does not.

`graphml_loader.py` checks the table on every load and raises rather than return a
plausible mapping:

1. the drawing was made from exactly this `.cxt`;
2. the table's ids are exactly the drawing's node ids;
3. its extents are exactly the extents of the lattice;
4. every drawn edge joins a concept to one of its lower covers.

The fourth check catches a table that names the right concepts for the wrong nodes,
since such a swap almost always breaks an edge. It cannot catch a swap of two
concepts with the same upper and the same lower covers, like the two middle
elements of a diamond, because the drawn edges are then the same either way. Such
pairs are rare (21 across all drawable scales, all in four instruments scales), and
since the table is read from the generators' own objects rather than inferred, no
mechanism for such a swap is known.

## Setting up redraw

redraw runs out of process and needs a checkout of
<https://github.com/domduerr/redraw> beside this repository and a conexp-clj REST
API on `127.0.0.1:8080`. `run_unattended.sh` starts the API from
`tools/conexp-clj.jar` if it is not running. To start it by hand:

```bash
( sleep infinity | java -jar tools/conexp-clj.jar --api --port 8080 & )
```

The `sleep infinity` matters: the API reads its console, and exits at once if
stdin is closed.

## Pinned versions

The generators are imported directly, so a change in one of them can change the
node identification without an error. The versions everything was verified
against:

| Component | Version |
|---|---|
| `drawing-quality` (this repository's generators and metrics) | `d552419be28e2d278b16e38ef0a3b98863ca7688` |
| `domduerr/redraw` | `80f62a97a5ff41d173b61113cc90f80864f49f41` |
| conexp-clj | 3.1.0 standalone, OpenJDK 25 |
| `odis-python` | 2026.9.1 |
| `dim-flux` | 1.0.11 |
| Python | 3.14.4; packages in `requirements.txt` |

After updating any generator, redraw rather than reuse cached drawings.

---

# Quality

Every drawing is scored on the **13 metrics** the repository's own analysis uses
(`analysis/results.ipynb`), in its four families:

| Family | Metrics |
|---|---|
| Crossings | `edge_crossing`, `crossing_angle` |
| Layering | `layer_consistency`, `vertical_axis_balance` |
| Slopes | `slope_verticality`, `slope_harmony`, `edge_length_uniformity`, `slope_standard`, `visual_chain_linearity` |
| Clearance | `node_edge_conflict`, `node_node_conflict`, `edge_edge_conflict`, `nested_suitability` |

Each score lies in [0, 1], 1 best. A score that is missing, not a number or outside
that range stops the run when the drawing is scored, naming the drawing and the
metric, rather than being discovered later by the ranking.

Quality is ranked exactly as that analysis ranks it: on each lattice the
algorithms are ranked on each metric, the metric ranks are averaged within each
family, and the families are averaged with equal weight, so that no aspect counts
more for having more metrics. The one addition is failures: a failed drawing is
ranked last on every metric of its scale.

---

# Consistency

For each usable nested pair and each algorithm, over the concepts present in both
drawings (for a nested pair, all concepts of the coarser scale):

## Kendall tau on x-ranks

Each shared concept is replaced by its position from the left, 1st, 2nd, 3rd, in
each drawing, and the two orders are compared with Kendall's tau-b: over every pair
of shared concepts, does the finer drawing keep them in the same left-to-right
order? +1 is the identical order, 0 no relation, −1 the exact reverse.

**Ranks, never coordinates.** Two runs on related inputs do not produce comparable
coordinates: the origin, the units and the scale are arbitrary, so any distance
between placements measures those as much as the placement. Ranks are invariant
under translation, scaling and any monotone rescaling of x.

**A mirror image is not an inconsistency.** Mirroring a whole drawing negates every
x, which reverses every left-to-right relation and leaves every other relation
intact: tau changes sign and nothing else. A drawing that keeps the shared concepts'
arrangement exactly, the other way round, has kept the arrangement a reader has
learned. So the ranked statistic is **|tau|**, the order kept one way round or the
other. It does not forgive everything:

- **A flipped branch still counts against.** If one sub-branch flips and the rest
  holds, the pairs within the branch reverse while the pairs across it do not, and
  |tau| falls. Only a mirror of the whole shared arrangement is free.
- **Weak anti-correlation is weak consistency.** |−0.3| = 0.3: mirrored, the drawing
  would correlate at +0.3, no more.

The signed tau is kept beside it in every file and ranked beside it, so the effect
of this choice is always visible.

**Undefined tau.** If a drawing gives every shared concept the same x, there is no
order to compare and tau-b is undefined. That keeps no order at all, so it is
recorded as tau = 0 with `tau_undefined` set.

## Rank drift

Each shared concept is also ranked by its vertical position in each drawing, and the
total change of those ranks, over the largest any reordering could produce, gives a
number from 0 (no concept changed height relative to the others) to 1 (the vertical
order reversed). It is reported, never charged to the algorithm: refining a scale
inserts concepts into chains and moves the others up or down whatever the
algorithm does.

## Tau within each rank stratum

A concept's height is the length of the longest chain below it; a **rank stratum**
is a set of concepts at the same height. Within a stratum nothing in the order forces
a left-to-right arrangement, so it is entirely the algorithm's choice. Tau computed
within each stratum separates three patterns that one global tau cannot:

| Mean \|tau\| over strata | Sign agreement | Reading |
|---|---|---|
| high | ≈ 1.0 | the whole drawing mirrored |
| high | ≈ 0.5–0.7 | a sub-branch flipped, the rest held |
| low | anything | scrambled; the sign carries no information |

Strata of one concept have nothing to compare. Strata of two are left out of the
mean |tau|, since two concepts are always either in order or reversed and would
make a scramble look decisive; their sign still counts towards the agreement.

## Fixtures

`consistency.py --self-test` must pass before any number is trusted: identical
drawings give tau exactly 1, mirror images exactly −1, and moving only concepts
that are not shared leaves tau exactly 1. Tau-b is counted in integers so that these
come out exact; scipy's floating-point version returns 0.9999999999999999 for two
identical rankings.

---

# The permutation null

A raw tau says little on its own: how much agreement is surprising depends on how
many concepts are shared and how much freedom the order leaves. So every
observation is compared with a null in which the algorithm's placement carries no
information.

**Keep the finer drawing exactly as it is and permute which shared concept sits at
which position, only within rank strata**: a concept may take the position of
another at the same height, nothing else. Unrestricted shuffling would compare
against placements no line diagram could have, since a concept must be drawn above
everything below it, and would flatter every algorithm. 2000 permutations give a
distribution, and the observation is tested two ways against it:

- **|tau|, the headline** (`tau_abs_z`, `tau_abs_p`): is the order kept, one way
  round or the other, more than placement within strata keeps it by chance?
  One-sided, against the distribution of |tau| over the permutations.
- **Signed tau** (`tau_z`, `tau_p`): two-sided, **centred on the null mean**.
  Restricting permutations to strata keeps pairs across strata in place, so the null
  is generally not centred on zero, and a two-sided test must measure how far the
  observation lies from the null's own centre.

A significant *negative* signed tau means the order is kept **reversed** -- a mirror
-- not that it is lost.

When no permutation reaches the observation, the p-value is a bound,
1/(permutations + 1), not an estimate; the `_is_bound` columns mark this, and it is
reported as p < 0.0005. `null_free_positions` records how much freedom the null
had, since strata of one cannot be permuted.

**What the null does not do.** The structure of a lattice alone favours some
arrangements -- children tend to sit under their parents -- so "beyond chance" means
beyond placement within strata, not beyond what the structure implies. A null of
random valid drawings would separate the two; it is not built (see *Open
questions*). A null of repeated runs is not needed: the algorithms are
deterministic for a given input file, with the caveat that an anytime result
depends on how far its search got within its budget.

scipy's classical Kendall p-value (`p_value`) is also recorded. Its null allows any
left-to-right order, including impossible ones, so it is the looser test; the
permutation tests are the ones to report.

---

# Ranking

`ranking.py` ranks the algorithms on quality, on consistency and on both, within
each context and across contexts.

## Why average ranks

A tau over 13 shared concepts and one over 319 are not the same kind of number, and
neither are a crossing score and a slope score. Within one comparison -- one lattice
for quality, one nested pair for consistency -- every algorithm is judged on the
same thing, so ranks there are comparable, and nowhere else. Averaging ranks over
comparisons is the method Demšar (2006) recommends for comparing many algorithms
over many test cases whose scores are not on a common scale, and the one the
repository's own analysis uses. A failure needs no invented penalty value: it is
simply last.

## Failed, not attempted, not scored

| Case | What it means | How the ranking treats it |
|---|---|---|
| **Failed** (`declined`, `timeout`, `error`, `nonterminating`) | the algorithm was asked to draw the scale and did not produce a drawing | **penalised**: last place, shared with the other failures, on all 13 metrics of that scale and on every usable pair the scale is part of, weighted by the size of the scale (below) |
| **Not attempted** | the algorithm has not been run on that scale | the context is **not ranked** until it has been; never treated as a failure, and never a reason to drop the algorithm |
| **Drawn but not scored** | a drawing exists but its scores are missing or not numbers | **an error that stops the ranking**: the gap is in the pipeline, not the algorithm's |

The penalty is deliberately not absolute: an algorithm that fails the largest
views is pushed down, and it can still finish above one that draws everything badly.

## Views are weighted by log₂ of their size

Within every measure, each scale counts in proportion to **log₂ of its number of
concepts**. A failure belongs to a view -- the algorithm is already last on every
measure of that view -- so only the weight of the view can make failing a large
lattice cost more than failing a small one, which is the claim that matters:
automatic layout is most needed where drawing by hand is impractical. The logarithm
keeps this gentle: a 576-concept view counts 2.5 times a 13-concept one, where
linear weights would make it count 44 times and let one lattice decide everything.
log₂|L| is also the size measure the repository's analysis uses. The ranking with
every view counting equally is reported beside it.

## Consistency, per context

1. Each usable nested pair ranks the algorithms by |tau|, 1 = best, ties sharing the
   average rank; an algorithm that failed either drawing shares the last places.
2. The pairs ending in the same finer scale share that scale's weight, so a scale
   that many others nest into does not count many times.
3. The pair ranks are averaged with those weights.

## Combined: consistency as a fifth family

Consistency alone rewards an algorithm that hardly moves anything because it barely
lays anything out; the most stable layouts are not the best ones. This is the
stability-quality trade-off known from dynamic graph drawing (Misue et al. 1995;
Brandes and Mader 2011). So consistency is combined with quality, by the rule the
repository's analysis already applies to quality: each aspect of a drawing counts
equally. Consistency is one more aspect, so the **combined** rank is the mean of
five family ranks -- the four quality families and consistency -- and quality
carries four fifths, consistency one fifth.

Reported beside it, so that the conclusion's dependence on the weighting is visible
rather than assumed:

| Reported | What it shows |
|---|---|
| `combined` | the headline |
| `combined_half` | quality and consistency weighted half and half |
| `sensitivity.csv` | the ranking for every weight on consistency from 0 to 1, and where first place changes hands |
| `equal` view weighting | every scale counting the same |
| `consistency_signed`, `combined_signed` | the same with signed tau, mirrors counted against |
| `profile.csv` | where each algorithm draws and where it fails, in absolute terms |

## Contexts

Per-context mean ranks are averaged over contexts with equal weight. **A context
is ranked only when it is complete**: every algorithm has an outcome on every
drawable scale of its manifest and on every usable pair of its nesting matrix. An
overall ranking over fewer than all contexts is labelled PARTIAL in `ranking.csv`,
`sensitivity.csv` and `friedman.csv` (`corpus`, `corpus_complete`), and the files
are rewritten in full on every run, so nothing from an earlier run lingers.

A score or tau that is not a finite number, or an unknown status, stops the
ranking rather than being ranked.

---

# Across contexts: is the ranking more than chance?

**What it is.** Average ranks say which algorithm came out ahead, not whether the
difference is larger than chance. Demšar (2006), whose average ranks the ranking
follows, pairs them with a test across data sets: the **Friedman test** asks whether
the algorithms differ at all, and a **post-hoc test** then says which differences
are large enough. `ranking.py` computes both and writes `friedman.csv`; the formulas
are checked against Demšar's own worked example in `tests/test_ranking.py`.

**Why contexts are the cases.** A test needs independent cases. The scales and
pairs of one context are not independent: they are nested views of the same data,
and every pair into the full lattice shares one drawing. Different contexts are
different data sets, collected separately. So each context is one case (a *block*,
in Friedman's terms), and within it the algorithms are ranked 1 to k by their score
for that context: the combined mean rank, or the quality or consistency mean rank.
This is Demšar's setting, with contexts in place of data sets.

**Why a rank test.** The per-context scores of different contexts are not on a
common scale -- a context with more scales or more failures spreads its mean ranks
differently -- so only their order within a context is compared. The Friedman test
needs nothing else: no normality, no common scale, no equal variances.

**The formulas.** With N contexts, k algorithms and R_j algorithm j's average rank
over the contexts (each context ranking the algorithms 1..k, ties averaged):

```
chi2_F = 12N / (k(k+1)) * ( sum_j R_j^2  -  k(k+1)^2 / 4 )        Friedman (1937, 1940)
F_F    = (N-1) chi2_F / ( N(k-1) - chi2_F ),   F with k-1 and (k-1)(N-1) df
                                                                  Iman & Davenport (1980)
CD     = q_alpha * sqrt( k(k+1) / (6N) )                          Nemenyi (1963)
z_j    = (R_j - R_best) / sqrt( k(k+1) / (6N) ),  p two-sided normal, Holm (1979)
```

F_F is reported beside chi2_F because the chi-square approximation is conservative
for small N, and Demšar recommends it. q_alpha is the studentized range statistic
divided by √2 (`scipy.stats.studentized_range`, infinite degrees of freedom); for
k = 8 it is 3.031 at α = 0.05, Demšar's table value.

**Two post-hoc views, for two questions.**

- **Nemenyi, all pairs.** Two algorithms differ significantly when their average
  ranks differ by at least CD. With N = 11 contexts and k = 8 algorithms,
  CD = 3.17. This is the test behind the usual critical-difference diagram, and it
  is conservative: it controls the error over all 28 pairs.
- **Holm, each algorithm against the best.** The narrower question -- is the
  first-placed algorithm better than each of the others? -- is answered by comparing
  against a control, with Holm's step-down correction over the k − 1 comparisons,
  as Demšar recommends. It is more powerful than Nemenyi for that question.

Both are run on the combined ranking, and on quality and consistency separately,
so that it is clear which of the two carries a difference.

**What it can and cannot say.** A significant Friedman test says the algorithms do
not all perform alike across contexts; a significant Holm comparison says the best
algorithm beats that one by more than chance would, across contexts. A
non-significant result says the data cannot tell them apart, not that they are
equal: with 11 contexts the test has little power, and only large, consistent
differences will pass. It says nothing about any single context.

**Assumptions, and their limits.**

- *Contexts are independent.* True of the data; but three contexts are astronomy
  built on one template (properties of the object against the state of knowledge),
  so their rankings may be more alike than independent data sets would be. Repeating
  the test with the three counted as one shows whether that matters.
- *Every algorithm has a score in every context.* Guaranteed: only complete
  contexts are ranked.
- *The approximations need enough cases.* Demšar's rule of thumb, N > 10 and k > 5,
  holds at N = 11 and k = 8, but only just; `approximation_ok` records it. Over fewer
  contexts the numbers are printed but marked, and are not a result.
- *Post-hoc tests on mean ranks depend on which algorithms are compared.* Benavoli,
  Corani and Mangili (2016) show that whether A beats B can change when a third
  algorithm is added or removed, because every algorithm's rank moves. The
  algorithm set here is fixed, so this is a caveat to state; their recommended
  alternative, pairwise Wilcoxon signed-rank tests on the per-context scores with
  Holm's correction, is a robustness check.
- *Living Beings and Water is one of the contexts.* It is a 19-concept published
  example with one usable pair, so its ranking carries the least information;
  repeating the test without it shows whether it matters.

**Suggested wording:** *"To test whether the differences between algorithms exceed
chance, we follow Demšar (2006): each context is an independent case, within which
the algorithms are ranked by their combined score. A Friedman test (with the
Iman–Davenport correction) tests whether the algorithms differ at all; post hoc, the
best-ranked algorithm is compared with each other using Holm's procedure, and all
pairs with the Nemenyi critical difference (CD = 3.17 for 11 contexts and 8
algorithms at α = 0.05)."*

**References.** Demšar, J. (2006), Statistical comparisons of classifiers over
multiple data sets, *JMLR* 7, 1–30. Friedman, M. (1937), *JASA* 32, 675–701, and
(1940), *Ann. Math. Statist.* 11, 86–92. Iman, R. L. and Davenport, J. M. (1980),
*Commun. Statist. A* 9, 571–595. Nemenyi, P. B. (1963), *Distribution-free multiple
comparisons*, PhD thesis, Princeton. Holm, S. (1979), *Scand. J. Statist.* 6,
65–70. Benavoli, A., Corani, G. and Mangili, F. (2016), Should we really use
post-hoc tests based on mean-ranks?, *JMLR* 17(5), 1–10.

---

# Reading the output files

**Shared concepts.** Those present in both drawings of a nested pair, matched by
extent, never by node id or position. **x-rank**: a concept's position from the
left. **Rank stratum**: concepts at the same height in the lattice.

## consistency.csv

| Column | Meaning | Values |
|---|---|---|
| `n_shared` | concepts the two drawings have in common | for a nested pair, all of the coarser lattice |
| `tau_x` | Kendall tau-b on x-ranks | +1 same order, 0 unrelated, −1 reversed (a mirror image) |
| `tau_abs` | \|tau_x\|, the order kept either way round; **what is ranked** | 1 identical or mirrored, 0 unrelated |
| `tau_undefined` | every shared concept at one x in a drawing; tau recorded as 0 | |
| `tau_abs_z`, `tau_abs_p` | \|tau\| against the null distribution of \|tau\| | **the ones to report** |
| `tau_abs_p_is_bound` | no permutation reached the observed \|tau\| | report as p < 1/(permutations + 1) |
| `tau_z`, `tau_p` | the signed tau against its null, centred on the null mean, two-sided | \|z\| < 2 unremarkable, > 3 hard to get by chance; a significant negative value is a kept reversal |
| `tau_p_is_bound` | no permutation reached the observed tau | as above |
| `null_mean`, `null_sd`, `null_abs_mean`, `null_abs_sd` | the null distributions of tau and of \|tau\| | |
| `null_free_positions` | concepts the null could actually move | small means the null had little freedom |
| `p_value` | scipy's classical Kendall p-value, unconstrained null | the looser test |
| `rank_drift` | vertical rank change, normalised | 0 none, 1 reversed; a baseline, not a score |
| `n_strata`, `n_strata_compared` | heights spanned, and how many had two or more concepts | |
| `frac_strata_strong`, `frac_strata_inverted` | share of compared strata with \|tau\| > 0.5, and with tau < −0.5 | |
| `strata_decisiveness` | mean \|tau\| over strata of three or more | near 1 every stratum held or flipped, near 0 none did |
| `strata_sign_agreement` | share of compared strata with the majority sign | 0.5 split, 1.0 one direction throughout |
| `usable`, `status`, `note` | whether the pair is usable; `ok`, or `failed` with the drawing that is missing | |
| `fingerprint` | what the row was computed from | |

`consistency_strata.csv` has one row per stratum with its own tau.

## The other files

| File | Column | Meaning |
|---|---|---|
| `scales.csv` | | every scale of every context, from the manifests |
| `drawings.csv` | `status`, `note` | the outcome and, for a failure, its reason in the generator's words where it gave one |
| | `runtime_s`, `wall_budget_s` | seconds for the whole drawing, and the budget it ran under, in seconds |
| | `internal_budget_s`, `used_internal_budget` | the algorithm's own budget, and whether the drawing used all of it, where that can be inferred |
| | `source_sha256` | the exact `.cxt` drawn |
| `quality.csv` | the 13 metrics | scores of one drawing, each in [0, 1], 1 best |
| `ranking.csv` | `measure` | `crossings`, `layering`, `slopes`, `clearance`, `quality` (their mean), `consistency` (by \|tau\|), `combined`, `combined_half`, `consistency_signed`, `combined_signed` |
| | `view_weighting` | `log2`, the ranking, or `equal` |
| | `mean_rank` | 1 best on every comparison; with k algorithms, k last everywhere |
| | `context`, `corpus`, `corpus_complete` | a context or `all`; which contexts a row covers; false unless all |
| `sensitivity.csv` | `weight_on_consistency`, `position` | the ranking for every weight w on consistency and 1 − w on quality |
| `profile.csv` | `drawn`, `failed_*`, `largest_drawn`, `smallest_failed` | what each algorithm drew and where it failed |
| | `coverage`, `median_abs_tau`, `median_tau`, `complete` | share of usable pairs measured; descriptive medians; whether the context is ranked |
| `friedman.csv` | `friedman_mean_rank` | average over contexts of the rank 1..k within each context (not `mean_rank`) |
| | `chi2_F`, `p_chi2_F`, `F_F`, `p_F_F` | the Friedman test and its Iman–Davenport form |
| | `q_alpha`, `cd_nemenyi`, `approximation_ok` | the Nemenyi critical value and difference at 0.05; whether N > 10 and k > 5 |
| | `control`, `z_vs_control`, `p_vs_control`, `p_holm`, `significant_holm` | each algorithm against the best-ranked, raw and Holm-adjusted |

---

# The equations

Write `n` for the number of shared concepts, `a` for the coarser drawing and `b`
for the finer one, and `x_a(i)`, `y_a(i)` for concept `i`'s rank from the left and
by height in `a`. All statistics are scipy plus functions in this directory.

**Kendall tau-b**, `tau_x` and every per-stratum tau. Over all `P = n(n−1)/2` pairs,
with `C` the pairs ordered the same way in both drawings, `D` those ordered
oppositely, and `T_a`, `T_b` the pairs tied in `a` and in `b`:

```
tau_b = (C - D) / sqrt((P - T_a) * (P - T_b))
```

`kendall_tau_b` in `consistency.py`, counted in integers.

**Rank drift.**

```
drift = sum_i |y_a(i) - y_b(i)| / floor(n^2 / 2)
```

`floor(n²/2)` is the largest value of `sum |i − s(i)|` over all permutations `s`,
reached by the reversal, so drift lies in [0, 1] at any n. `rank_drift` in
`consistency.py`.

**Stratum summary**, over strata with at least two shared concepts:

```
strata_decisiveness   = mean |tau_s|, over strata with at least three concepts
strata_sign_agreement = max(#{tau_s > 0}, #{tau_s < 0}) / #strata compared
frac_strata_strong    = #{|tau_s| > 0.5} / #strata compared
frac_strata_inverted  = #{tau_s < -0.5}  / #strata compared
```

**The permutation null.** For each of `K = 2000` permutations within strata, the
tau `tau_k`:

```
m         = mean(tau_k)
tau_z     = (tau_obs - m) / sd(tau_k)
tau_p     = (#{|tau_k - m| >= |tau_obs - m|} + 1) / (K + 1)
tau_abs_z = (|tau_obs| - mean(|tau_k|)) / sd(|tau_k|)
tau_abs_p = (#{|tau_k| >= |tau_obs|} + 1) / (K + 1)
```

`sd` is the population standard deviation; a permutation within 1e-9 of the
observation counts as reaching it. `permutation_null` and `null_summary` in
`nulls.py`, with a fixed seed so a rerun reproduces the same permutations.

**Mean rank of algorithm a in one context**, consistency. With `P` the usable
pairs, `fine(p)` the finer scale of pair `p`, `n_fine(p)` the number of usable pairs
ending in it, `w` = log₂ of its number of concepts (or 1, for the equal weighting),
and `rank_p(a)` the rank of `a` by |tau| on `p` (the average of the last places if
it failed either drawing):

```
mean_rank(a) = sum_p w(fine(p)) / n_fine(p) * rank_p(a)  /  sum_p w(fine(p)) / n_fine(p)
```

Quality is the same with scales in place of pairs and the family rank in place of
`rank_p`. `rank_context` and `quality_context` in `ranking.py`.

| Step | Implemented by |
|---|---|
| ranking x, y and scores | `scipy.stats.rankdata`, method `average` |
| tau-b, per-stratum tau | `kendall_tau_b` in `consistency.py` |
| `p_value` | `scipy.stats.kendalltau(...).pvalue` |
| rank strata | `rank_strata` in `nulls.py`: longest chain below each extent |
| tau of each permutation | `scipy.stats.kendalltau`, cross-checked against `kendall_tau_b` |
| the null tests | `null_summary` in `nulls.py` |
| Friedman, Nemenyi, Holm | `friedman_from_ranks`, `holm_against_control` in `ranking.py`; `scipy.stats` `chi2`, `f`, `norm`, `studentized_range` |

---

# Ladder figures

A ladder figure shows the best and the worst algorithm of a context, by its
combined ranking, among those that draw every scale of the ladder: one row each, one
panel per scale, from a small scale up to the largest drawable one. The concepts of
the first scale appear in every panel, coloured by their left-to-right position in
that algorithm's first panel (purple leftmost, yellow rightmost); an algorithm that
keeps the order keeps the colours running left to right as the lattice grows. Each
panel gives |tau| against the first, marked "mirrored" where the order is kept the
other way round.

**The followed concepts must recur in every panel**, so the first scale must nest
into every other. Spanning the size range is not enough on its own: two scales that
share only the top and the bottom concept make a figure with nothing to follow.

**The ladder is chosen by a rule that does not look at results**
(`choose_ladder` in `ladder_figure.py`), so that no ladder is picked because its
picture fits a conclusion. It ends at the context's largest drawable scale, and its
first scale nests into every panel; among those ladders it prefers, in order:

1. as many panels as possible, up to four;
2. as many steps as possible where each panel nests into the next, a true
   refinement;
3. the smallest first scale, since its concepts are the ones followed by eye;
4. alphabetical order, so the choice is unique.

| Context | Ladder (concepts) | Refinement steps |
|---|---|---|
| diagnosis | upper (18) → upper_diagnosis (36) → symptoms (78) → diagnosis (88) | 2 of 3 |
| instruments | making (17) → family_making (39) → capability_practice_making (319) → instruments (576) | 2 of 3 |
| living_beings_and_water | taxa (12) → living_beings_and_water (19) | 1 of 1 |
| music | motion (12) → motion_character (42) → motion_form (53) → music (163) | 2 of 3 |
| olympic_disciplines | competitors (17) → sport_competitors (57) → discipline_competitors (122) → olympic_disciplines (529) | 3 of 3 |
| olympics | equipment (21) → equipment_medium (53) → venue_equipment (98) → venue_equipment_demands (444) | 3 of 3 |
| seasoning_planner | other (37) → spices (219) → seasonings (421) → seasoning_planner (532) | 3 of 3 |
| tenpc_exoplanets | host_system (15) → planet_host_system (79) → tenpc_exoplanets (371) | 2 of 2 |
| tenpc_stars | company (20) → company_planets (60) → physical (311) → tenpc_stars (732) | 3 of 3 |
| wd40pc | binarity (13) → mass_binarity (23) → parameters_binarity (112) → wd40pc (728) | 3 of 3 |
| zoo | physiology (32) → class_physiology (56) → anatomy_physiology (492) → physiology_ecology (781) | 1 of 3 |

```bash
python ladder_figure.py --all                # every ranked context, into figures/
python ladder_figure.py --context wd40pc     # one context
python ladder_figure.py --followed instruments_practice --out ladder_instruments_practice \
    --scales instruments_family_practice instruments_capability_practice_making instruments
```

A context's figure is drawn once the context is ranked. Any other ladder can be
drawn by naming its scales, as in the last line, which draws the second instruments
ladder that runs to the full lattice through four scales.

# Results

The complete run: 11 contexts, 91 drawable scales, 8 algorithms, 728 drawings, 151
usable nested pairs and 1208 comparisons, under a 30-minute budget per drawing.
Mean ranks, 1 = best; views weighted by log₂ of their size; contexts weighted
equally. All numbers are in `ranking.csv`, `friedman.csv`, `sensitivity.csv` and
`profile.csv`.

## The ranking

| Algorithm | Crossings | Layering | Slopes | Clearance | **Quality** | **Consistency** | **Combined** | Half and half | Every view equal | Consistency, signed |
|---|---|---|---|---|---|---|---|---|---|---|
| dimdraw | 2.22 | 3.39 | 2.86 | 3.58 | **3.01** | **3.23** | **3.06** | 3.12 | 3.18 | 4.11 |
| dimflux | 2.93 | 4.63 | 4.82 | 2.74 | **3.78** | **3.43** | **3.71** | 3.61 | 3.77 | 4.14 |
| sugiyama | 4.65 | 3.82 | 4.18 | 4.28 | **4.23** | **3.46** | **4.08** | 3.85 | 4.13 | 3.25 |
| freese | 5.23 | 2.81 | 4.48 | 5.23 | **4.44** | **5.07** | **4.56** | 4.75 | 4.44 | 5.45 |
| fdp | 3.71 | 6.05 | 4.19 | 4.83 | **4.70** | **4.12** | **4.58** | 4.41 | 4.68 | 3.68 |
| aeschlimann_schmid | 5.49 | 3.58 | 4.56 | 4.76 | **4.60** | **4.56** | **4.59** | 4.58 | 4.73 | 3.40 |
| cole_ducrou_eklund | 5.40 | 5.15 | 4.89 | 4.16 | **4.90** | **5.46** | **5.01** | 5.18 | 4.82 | 5.42 |
| redraw | 6.37 | 6.56 | 6.01 | 6.41 | **6.34** | **6.67** | **6.40** | 6.50 | 6.26 | 6.56 |

- **dimdraw is first in every one of the 11 contexts**, and first overall for every
  weight on consistency from 0 to 1 (`sensitivity.csv`), with every view counting
  equally, and with signed tau.
- **dimflux is second**; sugiyama, freese, fdp and aeschlimann_schmid lie within
  half a rank of one another, so their order among themselves is not settled;
  cole_ducrou_eklund and redraw are last.
- **Consistency by |tau| and by signed tau rank the algorithms differently**:
  sugiyama, aeschlimann_schmid and fdp keep much of their order *mirrored*, so
  signed tau ranks them as the most consistent and |tau| does not. dimdraw is the
  most consistent by |tau|.

Per context, combined:

| Context | First | Second | Third | Last |
|---|---|---|---|---|
| diagnosis | dimdraw 3.32 | freese 3.65 | dimflux 3.86 | redraw 6.39 |
| instruments | dimdraw 2.86 | dimflux 3.76 | sugiyama 3.82 | fdp 5.99 |
| living_beings_and_water | dimdraw 3.50 | dimflux 3.90 | cole_ducrou_eklund 3.98 | fdp 5.40 |
| music | dimdraw 3.22 | dimflux 3.41 | freese 3.76 | redraw 6.50 |
| olympic_disciplines | dimdraw 3.14 | dimflux 3.60 | fdp 3.81 | redraw 6.89 |
| olympics | dimdraw 3.36 | dimflux 3.83 | freese 3.85 | redraw 6.42 |
| seasoning_planner | dimdraw 2.46 | dimflux 3.19 | fdp 3.51 | redraw 6.95 |
| tenpc_exoplanets | dimdraw 3.24 | fdp 3.41 | dimflux 3.62 | redraw 6.83 |
| tenpc_stars | dimdraw 3.13 | sugiyama 3.66 | aeschlimann_schmid 4.17 | redraw 6.21 |
| wd40pc | dimdraw 2.80 | fdp 3.87 | dimflux 3.91 | redraw 6.60 |
| zoo | dimdraw 2.57 | dimflux 3.48 | sugiyama 3.64 | redraw 6.82 |

## Across contexts

Each context ranks the algorithms 1 to 8 by its combined score; the mean of those
ranks over the 11 contexts, and each algorithm against dimdraw with Holm's
correction:

| Algorithm | Mean rank over contexts | Holm-adjusted p against dimdraw |
|---|---|---|
| dimdraw | 1.00 | -- |
| dimflux | 2.45 | 0.16 |
| sugiyama | 4.00 | 0.008 |
| fdp | 4.91 | < 0.001 |
| freese | 4.91 | < 0.001 |
| aeschlimann_schmid | 5.36 | < 0.001 |
| cole_ducrou_eklund | 5.55 | < 0.001 |
| redraw | 7.82 | < 0.001 |

The Friedman test rejects that the algorithms perform alike (χ²_F = 54.8, F_F = 24.6
with 7 and 70 degrees of freedom, p < 10⁻⁶). dimdraw is better than six of the
seven others beyond chance; dimflux is not distinguishable from it at α = 0.05. By
the Nemenyi critical difference, 3.17, dimdraw differs from fdp, freese,
aeschlimann_schmid, cole_ducrou_eklund and redraw. On quality alone the picture is
the same. On consistency alone dimdraw, sugiyama and dimflux cannot be told apart,
and only cole_ducrou_eklund, freese and redraw are worse than dimdraw beyond chance.

**Robustness** (`robustness.py`, `robustness.csv`). The test was repeated three
ways:

| Variant | Cases | Combined: best, and worse than it beyond chance |
|---|---|---|
| all contexts (the test above) | 11 | dimdraw; all except dimflux |
| without Living Beings and Water | 10 | dimdraw; all except dimflux |
| the three astronomy contexts as one case | 9 | dimdraw; all except dimflux |
| pairwise Wilcoxon signed-rank tests, Holm-adjusted | 11 | dimdraw; all seven, dimflux included (p = 0.007 each) |

On the combined score the Friedman test rejects equal performance in every variant (p < 10⁻¹³). The
Wilcoxon tests are the stronger result because dimdraw is first in every context,
so every difference has the same sign. On quality alone every variant agrees with
the combined ranking. On consistency alone the best-ranked algorithm alternates
between dimdraw and sugiyama across the variants, and only redraw is worse than the
best in all of them: consistency does not single out one algorithm.

## Consistency

Of the 832 comparisons with both drawings present, 557 keep the shared concepts'
left-to-right order, one way round or the other, beyond chance (`tau_abs_p` < 0.05).
Median |tau| per algorithm lies between 0.28 (aeschlimann_schmid) and 0.56 (fdp,
redraw over the few pairs redraw completes): no algorithm keeps the order closely
as the view grows. 165 comparisons have tau below −0.5, so near-mirrors are common.

## Failures

| Algorithm | Drawn (of 91) | Failures |
|---|---|---|
| aeschlimann_schmid | 91 | none |
| dimdraw | 91 | none |
| sugiyama | 91 | none |
| dimflux | 89 | 2 timeouts, on the largest lattices |
| fdp | 78 | 12 non-terminating on coextensive attributes, 1 timeout |
| freese | 74 | 11 timeouts, 6 invalid (diverged or collapsed layouts) |
| cole_ducrou_eklund | 69 | 21 declined, 1 timeout |
| redraw | 52 | 39 timeouts |

The longest successful drawing took 28 minutes (redraw). Ten drawings needed more
than 15 minutes; counting them as timeouts, as a 15-minute budget would, leaves the
order of the algorithms unchanged, and redraw, which gains most from the longer
budget, stays last.

## Ladder figures

`figures/ladder_<context>.png` for every context, rows chosen as described under
*Ladder figures*.

---

# What the algorithms do, measured

## They respond to the order of the columns, and some to the order of the rows

Shuffling the attribute columns, or the object rows, of a `.cxt` changes nothing
about the context, the lattice or any concept. It changed the drawings anyway.
`column_order.py` draws four instruments scales of 13 to 46 concepts under four
column shuffles and four row shuffles each, with all eight algorithms, and compares
every drawing with the drawing of the same scale in canonical order, concept by
concept (`column_order.csv`; fdp is not run on the one scale with coextensive
attributes). Consistency is read as everywhere else: |tau| of the left-to-right
order, so a mirror image counts as order kept.

| Algorithm | Unchanged by a column shuffle | Median \|tau\| | Lowest \|tau\| | Exact mirror | Heights change | Unchanged by a row shuffle |
|---|---|---|---|---|---|---|
| cole_ducrou_eklund | 75% | 1.00 | 0.67 | 0% | 0% | 100% |
| aeschlimann_schmid | 44% | 0.94 | 0.25 | 6% | 0% | 100% |
| dimdraw | 12% | 0.88 | 0.16 | 12% | 75% | 100% |
| redraw | 0% | 0.86 | 0.65 | 0% | 50% | 0% |
| dimflux | 0% | 0.85 | 0.12 | 12% | 81% | 0% |
| freese | 6% | 0.57 | 0.21 | 0% | 0% | 100% |
| fdp | 0% | 0.56 | 0.03 | 0% | 100% | 0% |
| sugiyama | 6% | 0.41 | 0.01 | 0% | 0% | 100% |

The columns are statistics over the 16 column-shuffled drawings of each algorithm
(12 for fdp); "lowest |tau|" is the shuffle that disturbed the order most, and an
exact mirror, tau = −1, counts as |tau| = 1. Every algorithm except
cole_ducrou_eklund changes most drawings when only the columns are reordered, some
of them nearly to a scramble. redraw, dimflux and fdp change them when only the
rows are reordered, too, and not by rounding: nodes move by up to the width of the
drawing.

The algorithms are deterministic for a given *file*, not for a given *lattice*.
This is why every scale of a context lists its attributes in one canonical order
and its objects in the full context's order. `figures/column-order-demo.png`
(`column_order.py --figure`) shows one scale, `instruments_excitation`, in
canonical and in shuffled column order for all eight algorithms; the scale and the
shuffle are fixed by rule, not chosen by their look.

## DimDraw's cost is driven by incomparable pairs, not lattice size

| Context | Concepts | Incomparable pairs | Time, 30 s budget |
|---|---|---|---|
| `ganter`, published | 11 | 21 | 0.00 s |
| `triangles`, published | 18 | 68 | 0.01 s |
| `living_beings_and_water`, published | 19 | 91 | 0.01 s |
| `Cn5`, published | 32 | 285 | used the whole budget |
| `instruments_capability` | 13 | 24 | 0.00 s |
| `instruments_excitation` | 21 | 154 | 3.70 s |
| `instruments_family_excitation` | 27 | 260 | 0.41 s |
| `instruments_playing_mechanism` | 35 | 465 | used the whole budget |

A two-dimensional extension orients incomparable pairs, so that is what the work
grows with. `Cn5`, a contranominal scale from DimDraw's own data set, uses any
budget at 32 concepts, while `instruments_family_excitation` at 27 concepts and 260
incomparable pairs finishes in 0.41 s. This tells a reader when DimDraw is usable,
which lattice size alone does not. Every manifest records `incomparable_pairs`;
`tests/test_dimdraw_cost.py` pins the comparison.

Above a few hundred incomparable pairs DimDraw returns an anytime result. Ten times
the budget (600 s instead of 60 s) gave identical drawings on the three mid-size
scales tested (35 to 46 concepts), so within that range the drawings are not
truncated in any way that shows.

## fdp does not terminate on a context with coextensive attributes

What looks like a size limit is non-termination: two attributes with equal extents
make fdp's initialisation cycle forever, at 17 concepts as readily as at 319, and
its time budget cannot stop it because it bounds only the later optimiser. Remove
one attribute of the pair and the 319-concept scale draws in under ten seconds.
Coextensive attributes are ordinary in real data; reduced contexts do not show the
problem because reduction clarifies. Details under *Defects*.

---

# Limitations

- **The algorithm set is what the repository provides.** dimflux is the only
  genuinely additive layout; dimdraw is order-dimension-driven and anytime above
  about thirty concepts. A contrast between additive and force-directed families
  rests on few members.
- **The results hold for one canonical order of columns and rows.** The canonical order removes
  the order of columns and rows from the comparison between nested scales, but an order-sensitive
  algorithm could rank differently under another fixed order.
- **Quality is the repository's metrics, as its analysis aggregates them.** The
  quality ranks depend on which metrics and families are defined. Some metrics give
  their best score to degenerate output, which is why such output is classified as
  invalid before scoring. Equal family
  weights are nominal: a family whose metrics disagree averages towards the middle,
  so a family with a wider spread of ranks moves the combined rank more.
- **Weights are choices**: one fifth on consistency, log₂ view weights. The sweep
  over the weight on consistency and the equal-view ranking are reported for that
  reason.
- **Within a context the ranking is a description, not a test.** Nested scales of
  one context are not independent cases; the test is across contexts, and with 11
  contexts it has little power.
- **Comparisons within a context share drawings.** Every pair into the full lattice
  uses the same drawing of it, and nesting is transitive, so a context's pairs are
  not independent. The pair weights stop a finer scale from counting more than
  once, not a coarser one.
- **"Beyond chance" means beyond placement within strata**, not beyond what the
  lattice structure implies, and the p-values are per comparison, not corrected for
  the number made.
- **Node identification is checked up to concepts with identical covers**, which no
  check on the drawn edges can tell apart.
- **The 30-minute budget can change the ranking**, because a timeout counts as a
  failure, and runs execute in parallel, so time-limited results can depend on
  machine load. Every runtime is kept.
- **fdp cannot draw a context with coextensive attributes**, and such contexts are
  not altered for it; those scales are its recorded failures.
- **Internal budgets are inferred from runtimes.** dimdraw does not report whether
  its search finished; fdp's budget bounds only its optimiser; dimflux's only its
  force phase.
- **The scales are chosen by hand.** The groupings are recorded before anything is
  drawn and never revised after results are seen, with the rejected alternatives,
  so the choice can be inspected.
- **No human validation.** Consistency of placement is a proxy for how easily a
  reader carries a picture from one view to the next.

---

# Defects found in the generators

Found while connecting the scales to the generators. Paths are relative to the
repository root.

## 1. fdp never returns on a context that is not attribute-clarified

Two attributes with equal extents -- each implies the other -- make
`FDP_Additive_Features.__init__` loop forever, at any lattice size. In
`line_diagrams/fdp/fdp.py`, `_initialize_vectors` places a non-coatom attribute only
once every attribute implied by it already has a position:

```python
elif all(up in self.vectors for up in upper[m]):
    ...
else:
    queue.append(m)
```

With `a` and `b` equivalent, `upper[a]` contains `b` and `upper[b]` contains `a`, so
neither is ever placed and the queue cycles. `{'timeout_s': ...}` cannot stop it: it
is consulted only in the optimiser's callback, which this never reaches. Four
objects and three attributes reproduce it (`tests/data/equivalent-attributes.cxt`,
pinned in `tests/test_fdp_termination.py`):

```
B

4
3

g1
g2
g3
g4
x
a
b
XXX
XXX
X..
...
```

```python
import odis
from fdp import FDP_Additive_Features
FDP_Additive_Features(odis.FormalContext.from_file('equivalent-attributes.cxt'),
                      {'timeout_s': 5.0})     # never returns
```

It is invisible on the reduced contexts, because reduction clarifies, and appears
as soon as anything unreduced is drawn: in the original real-world collection,
`zoo`, `dolphins`, `music` and `southern_woman` all contain such a pair.

## 2. The output file name is slugged, and nothing tells the caller

Every `generate.py` writes `{slug(cxt_path.stem)}.graphml`, where `slug` lowercases
and turns hyphens into underscores, and `generate()` returns `None`. A caller that
forms the expected path from the `.cxt` name gets a wrong path for any hyphenated
name, silently. Returning the path from `generate()` would fix it. (The scale names
here are chosen so that `slug` leaves them unchanged.)

## 3. `skipped` means four different things

| Message | Meaning |
|---|---|
| `skipped {name}: {path} already exists` | cached, i.e. success |
| `skipped {name}: no drawing found` (dimdraw) | the algorithm declined |
| `skipped {name}: {e}` (cole_ducrou_eklund) | the algorithm declined |
| `skipped {dataset}: directory not found` | misconfiguration |

They can only be told apart by substring. A distinct word for the cache hit, or a
status in the return value, would settle it.

## 4. fdp divides by zero when two attribute vectors coincide

`fdp.py` emits `RuntimeWarning: invalid value encountered in scalar divide` when
`np.linalg.norm(n_i - n_j)` is zero, and the resulting `nan` enters the gradient.
Reproducible on the fixture above with the equivalent pair removed; the layout
still comes out.

## 5. dim-flux crashed when an object and an attribute shared a name

In the `dim-flux` package, up to version 1.0.10: objects and attributes were indexed
by name in one map, so an object and an attribute with the same name (the olympics
data has a discipline and a demand both called "Jumping") received the same sympy
symbol, and sympy refused the duplicate. Fixed in 1.0.11, which this pipeline
requires.

## 6. The zoo context's attribute labels are shifted

In `contexts/real-world/original/zoo.cxt`, the first eleven yes/no variables carry
the label of the variable before them in the UCI Zoo order, and "venomous" is
missing: `[animal-name …]` is really hair, `[hair …]` feathers, `[feathers …]` eggs,
`[eggs …]` milk, `[milk …]` airborne, `[airborne …]` aquatic, `[aquatic …]`
predator, `[predator …]` toothed, `[toothed …]` backbone, `[backbone …]` breathes and
`[breathes …]` venomous. Easy check: `[hair 1]` holds exactly the 20 birds and
`[eggs 1]` exactly the 41 mammals. Drawings and metrics are unaffected, since
nothing reads a label, but any concept read off this context means something other
than its label says. The copy in `contexts/zoo/` is corrected on import.

## 7. freese's layout can diverge numerically

On six of the larger scales (219 to 319 concepts) freese returns coordinates of
10⁴⁰ to 10⁸⁴. In three of them every node ends on one vertical line; in the other
three the drawing is about 10⁷⁹ units wide and under 30 high. Both are recorded as
`invalid`. The quality metrics cannot detect this and score the collapsed ones as
perfectly vertical; a bound on the coordinates, or a check that the layout has
converged, would catch it at the source.

## Worth knowing

dimdraw's internal budget is honoured but invisible: `context.draw('dimdraw',
60000)` returns the same kind of result whether the search converged or was cut
off. If odis exposed it, every drawing above about thirty concepts would become
interpretable.

---

# Open questions

- **Robustness under a second column order.** Rerun once with a different fixed
  order and report whether the ranking holds.
- **A null of random valid drawings**, which would separate consistency an
  algorithm achieves from consistency the lattice structure forces.
- **Order or localisation?** Tau measures order. Shared concepts might also spread
  across the width in small drawings and cluster to one side in large ones; the
  spread of their x-ranks within the finer drawing would measure that.
- **More contexts**, grouped by meaning, each adding power to the test across
  contexts.
