# Running our scales through the drawing pipeline

Working notes on connecting our scale contexts to the eight drawing algorithms in
the repository. Written as the work happens, step by step.

Skip ahead to Methods section for the implementation. 

---

## does a .graphml say which concept a node is?

**The question.** We compare where an algorithm puts *the same concept* in two
different scales. That requires matching nodes across files by extent. If a node
carries only an index, node 7 in `venue.graphml` and node 7 in
`venue-equipment.graphml` are unrelated concepts and no post-processing repairs
it. Matching by position in a canonical concept ordering is **not** a fallback: it
looks right and is silently wrong, because two scales have different concept sets.

**The answer: none of the eight carry the extent.** Every generator declares
exactly two graphml keys, `x` and `y`, and writes nodes as bare integers:

```xml
<key id="y" for="node" attr.name="y" attr.type="double" />
<key id="x" for="node" attr.name="x" attr.type="double" />
<node id="0">
  <data key="x">-2.7474600603916333</data>
  <data key="y">14.677246968371236</data>
</node>
```

That was checked in the source of all eight generators and against the graphml
files already in the repository. There is no label, no extent, no intent.

**But the extent is in hand at the moment of writing, for seven of the eight.**
The integer written as the node id is an index into a structure that holds the
extent under real object names:

| Algorithm | Node id is | Extent reachable at write time as | Patch |
|---|---|---|---|
| `aeschlimann_schmid` | index into `self.concepts` | `self._extents[i]`, from `odis` | three lines |
| `cole_ducrou_eklund` | index into `self.concepts` | `self._extents[i]`, from `odis` | three lines |
| `fdp` | index into `self.concepts` | `self._extents[i]`, from `odis` | three lines |
| `freese` | index into `self.concepts` | `self._extents[i]`, from `odis` | three lines |
| `dimdraw` | `node.index` | `node.concept.extent`, from `odis` | three lines |
| `sugiyama` | `node.index` | `node.concept.extent`, from `odis` | three lines |
| `redraw` | position in a sorted node list | the node itself is `(extent, intent)` | three lines |
| `dimflux` | index into `vars.concepts` | `vars.extents[i]`, **but relabelled** | see below |

The patch is the same shape in each: declare one more key and write one more data
element.

```python
SubElement(root, 'key', {'id': 'extent', 'for': 'node',
                         'attr.name': 'extent', 'attr.type': 'string'})
...
extent_el = SubElement(node_el, 'data', {'key': 'extent'})
extent_el.text = '|'.join(sorted(extent_for(concept)))
```

**`dimflux` is the exception, and not for a trivial reason.** Its wrapper hands
the work to the `dim-flux` package, which *clarifies and reduces the context and
renames every object*. On our instruments context it reports 58 objects and 38
attributes where the file has 64 and 42, and calls them `g_1, g_2, …`. The lattice
is unaffected, 576 concepts either way, but the extents it exposes are sets of
`g_i` over a reduced object set, so they cannot be compared with another scale's
extents without first reconstructing the reduction. Options, in order of
preference:

1. patch `line_diagrams/dimflux/dimflux.py` to keep the mapping from reduced
   objects back to original ones and expose real extents;
2. reconstruct the reduction on our side, which depends on undocumented behaviour
   of a third-party package and is fragile;

**Unrelated blocker for `redraw`:** it imports an external checkout from
`REPO_ROOT.parent / 'redraw'`, or `$REDRAW_ROOT`, which is not present here.
It cannot run until that checkout exists.

**Status:** None of the eight emits an extent, so this needs the
collaborator's agreement, and `dimflux` needs a real decision
rather than a patch we can make alone.


---

## Can we recover the mapping ourselves?

If the node id can be mapped back to a concept on our side, no patch to his code
is needed and the harness can be built this week. `check_node_mapping.py` tests
that properly rather than assuming it.

For each algorithm it imports the generator, replaces `write_graphml` **in memory
only**, and records which extent each node id stood for at the moment of writing.
Nothing in the repository is edited. It then rebuilds the same mapping from the
.cxt alone and compares elementwise as sets of object names, and finally repeats
the capture in fresh processes under `PYTHONHASHSEED` 0, 1 and random. That last
test is the one that catches an ordering which comes out of set or dict iteration:
stable within a run, different between runs, wrong with no error raised.

| Algorithm | Reconstructs | Ordering | Hash-stable | Needs a patch |
|---|---|---|---|---|
| `aeschlimann_schmid` | yes, exactly | lectic, from `odis` | yes | no |
| `cole_ducrou_eklund` | yes, exactly | lectic, from `odis` | yes | no |
| `fdp` | yes, exactly | lectic, from `odis` | yes | no |
| `freese` | yes, exactly | lectic, from `odis` | yes | no |
| `dimdraw` | yes, exactly | lectic, from `odis` | yes | no |
| `sugiyama` | yes, exactly | lectic, from `odis` | yes | no |
| `redraw` | yes, exactly | explicit sort by extent size, then extent, then intent | yes | no |
| `dimflux` | not applicable | — | — | excluded until the upstream object mapping lands |

**The ordering is principled, not incidental.** Six of the seven number their
concepts in the order `odis` enumerates them, and that order is exactly the lectic
order an independent implementation produces: ConceptFlow's NextClosure gives the
identical sequence, element for element, while its Close-by-One gives a different
one. Two unrelated implementations agreeing on the sequence is what makes it safe
to rely on. `redraw` does not depend on any enumeration order at all: it sorts its
nodes explicitly before numbering them.

So **no patches are needed for the seven**, and the mapping belongs in one loader
rather than scattered through the consistency code.

### Two things found while testing

**`cole_ducrou_eklund` declines some contexts.** On `family-excitation` it reported
"no satisfactory layer diagram found within the candidate offset pool", which is
the algorithm giving up rather than failing. The harness must treat a missing
drawing as data, not as an error: some scales will have fewer than seven drawings.

**Superseded upstream.** As of `712d498` the generator runs up to three fallback
passes, each widening the candidate offset pool, and `family-excitation` now draws.
The design point stands — a generator may still refuse, and the harness must record
that rather than error — but this particular refusal is gone, and declines are now
rarer than the note below assumes.

**Attribute names with `∧` are read without complaint.** The conjunction names in
our scale files, which are UTF-8 and long, parse and draw fine.

## Setting up redraw

`redraw` is called out of process and needs two things that are now in place:

- a checkout of <https://github.com/domduerr/redraw> at the path its generator
  expects, which is the sibling of the drawing-quality repository;
- a conexp-clj REST API on `127.0.0.1:8080`, since redraw asks it for the concept
  lattice. The standalone jar of conexp-clj 3.1.0 is in `../../tools/` and is
  started with:

```bash
( sleep infinity | java -jar tools/conexp-clj.jar --api --port 8080 & )
```

The `sleep infinity` matters: the API reads its console, and with stdin closed it
exits immediately with "Bye for now!".


---

## Pinned versions

We import the generators directly rather than going through their command line, so
a change to `generate()` or to `write_graphml()` breaks us **silently**: the code
still runs, the node identification is simply wrong. The versions everything above
was verified against:

| Repository | Commit | Date |
|---|---|---|
| `marcelnoehre/drawing-quality` | `712d49805e8766d8f817c87e8f676a965d92ba5a` | 2026-09-30 |
| `domduerr/redraw` | `80f62a97a5ff41d173b61113cc90f80864f49f41` | 2021-02-04 |
| conexp-clj | 3.1.0 standalone, openjdk 25 | release v3.1.0 |
| `odis-python` | 2026.9.1 | pinned by his `pyproject.toml` |

After pulling the repository, rerun `check_node_mapping.py` before trusting any
drawing. `graphml_loader.py` also checks the concept order on every load and
raises `EnumerationOrderError` rather than returning a plausible mapping.

---

## The harness

`run_harness.py` does three passes, each idempotent, each writing one long-format
CSV into this directory.

| File | One row per | What it carries |
|---|---|---|
| `scales.csv` | scale | kind, chain membership, attributes, concepts, width, height, drawable |
| `drawings.csv` | scale x algorithm | status, runtime, and the metric scores |
| `consistency.csv` | nested pair x algorithm | Kendall tau on x-ranks, rank drift, overlap |

Long format, never wide. Contexts have different numbers of scales, so a column
per scale breaks the first time a context is added; here that is just a different
number of rows, and anything else is a join on `(context, scale)`. No combined
results file is maintained by hand; it can be generated from these three.

Drawings go to `graphml/<algorithm>/<context>/<scale>.graphml` and
`drawings/<algorithm>/<context>/<scale>.pdf`, beside `contexts/` rather than into
his tree. A drawing that already exists is not redrawn.

Current scope: 25 drawable scales across two contexts, 7 algorithms, so 175
drawings and 329 (nested pair, algorithm) comparisons.

### Declines are recorded, not swallowed

`cole_ducrou_eklund` refuses contexts where its search finds no satisfactory layer
diagram, and any algorithm may fail on a particular structure. Every attempt gets
a row in `drawings.csv` with a `status` of `drawn`, `cached`, `declined` or
`error`, and a `note` carrying the reason. Two reasons this matters: the design
becomes visibly unbalanced, so the mixed model can be told about it rather than
quietly losing rows, and which structures an algorithm refuses may itself say
something.

### The metric names changed under us

The refactor renamed the metrics. `evaluate_all` now returns seventeen scores:
`edge_crossing`, `crossing_angle`, `crossing_angle_min`, `slope_harmony`,
`slope_standard`, `slope_verticality`, `edge_length_uniformity`,
`layer_consistency`, `visual_chain_linearity`, `vertical_axis_balance`,
`nested_suitability`, and the six conflict scores for node-node, node-edge and
edge-edge, each in a mean and a minimum form. The older abbreviations of the plan,
EC, CA, SH, SC, LA, CL, CD, NCD, no longer map one to one, so `drawings.csv` uses
the current names.

### Seeds

No generator exposes a seed, so a run cannot be pinned. What can be done is to
rerun and measure the spread, which is what `profile_algorithms.py` does.

## The consistency score

`consistency.py` implements the measure and refuses to be trusted before its
fixtures pass:

```
python consistency.py --self-test
all fixtures pass: identical -> tau 1, mirrored -> tau -1,
non-shared moved -> tau 1 exactly, thin overlaps flagged
```

The fixtures earned their keep immediately. scipy's `kendalltau` returns
0.9999999999999999 for two identical rankings, because it normalises in floating
point, so the exactness the third fixture demands was not there. The statistic is
now counted in integers, concordant minus discordant over an integer denominator,
which returns exactly 1 and exactly -1 in the cases where that is the true answer;
scipy is still used for the p-value, and the two are cross-checked to 1e-9.

Rank drift is reported separately and is not charged to the algorithm: each shared
concept is ranked by height in both drawings and the mean absolute change of that
rank is normalised to [0, 1]. Refining a scale inserts concepts and pushes the
others up or down whatever the algorithm does.


---

## dimdraw's budget: what it means and what it costs us

DimDraw is an anytime algorithm:
when its budget expires odis returns the best layout the search has reached, which
is a legitimate drawing rather than a broken one.

The author reports about a second; we measured six hundred without completion.
Both are true, and the probe shows why.

| Context | Size | Concepts | Incomparable pairs | Time (30 s budget) |
|---|---|---|---|---|
| `ganter` (published) | 11x11 | 11 | 21 | 0.00 s |
| `bodiesofwater` (published) | 17x5 | 12 | 21 | 0.00 s |
| `triangles` (published) | 7x7 | 18 | 68 | 0.01 s |
| `living_beings_and_water` (published) | 8x9 | 19 | 91 | 0.01 s |
| `Cn5` (published) | 5x5 | 32 | 285 | consumed the budget |
| our `capability` | 64x5 | 13 | 24 | 0.00 s |
| our `excitation` | 64x13 | 21 | 154 | 3.70 s |
| our `family-excitation` | 64x19 | 27 | 260 | 0.41 s |
| our `playing-mechanism` | 64x19 | 35 | 465 | consumed the budget |

**What drives the cost is incomparability, not concept count**, which is what a
two-dimension extension would predict, since the work is in orienting incomparable
pairs. Our scales are not pathological; they are simply wider. And the author's own
test data contains the same behaviour: `Cn5`, a contranominal scale from the
DimDraw data set, consumes the budget at 32 concepts.

### What we do about it

dimdraw stays in, and is run on everything. The problem is a confound that is ours
to handle, not his. The plan is to ask whether quality improves as lattices shrink. A larger
lattice gets less search per concept, so dimdraw's quality could fall with size for
two reasons at once, genuine difficulty and a truncated search, and after the fact
the two cannot be separated. Every other algorithm's size trend is clean.

So:

- every drawing records `budget_s`, `runtime_s` and `completed_within_budget`,
  for every algorithm that carries a budget, not only dimdraw;
- dimdraw's quality-against-lattice-size trend is reported **separately**, split by
  whether the budget was consumed, and never pooled with the others as if it were
  comparable;
- the write-up says plainly that above the completion threshold its trend is
  confounded by the budget.

Budgets currently in force: `dimdraw` 60 s of wall clock, anytime; `fdp` 60 s,
keeping its best iterate — but see *fdp's 48 minutes* below: it bounds the optimiser
only, and on some contexts fdp never reaches the optimiser at all; `cole_ducrou_eklund` a search budget rather than a clock,
n1=5, n2=3, max_solutions=5000, which makes it decline rather than return
something partial; the rest unbounded.

### The sensitivity check came out clean

`dimdraw_sensitivity.py` drew three mid-size scales at 60 s and again at 600 s and
scored both:

| Scale | Concepts | 60 s | 600 s | Scores |
|---|---|---|---|---|
| `playing-mechanism` | 35 | consumed | consumed | all seventeen identical |
| `practice` | 46 | consumed | consumed | all seventeen identical |
| `family-making` | 39 | consumed | consumed | all seventeen identical |

Ten times the budget changed nothing at all. The anytime search reaches its answer
well inside sixty seconds and then keeps looking without improving on it, so the
drawings we score are not truncated in any way that shows. **The confound is real
in principle and not measurable here**, which is the better outcome: dimdraw's size
trend can be read alongside the others rather than quarantined.

Two cautions. Identical scores show that more time does not change the returned
layout; they do not show that the layout is optimal. And this was measured at 35 to
46 concepts, so the check should be repeated if dimdraw is ever run on something
much larger. The split by `completed_within_budget` stays in the analysis either
way, because it costs nothing and makes the claim checkable.

### Incomparable pairs, recorded for every scale

`scales.csv` and the per-context manifests now carry `incomparable_pairs`, the
number of concept pairs where neither extent contains the other. It is quadratic to
compute, so it is recorded for every scale inside the measurement limit and left
empty above it, exactly as width and height are.

Three uses:

- **It predicts dimdraw's completion from structure** rather than discovering it
  run by run. Once the sweep exists, `completed_within_budget` can be plotted
  against it and a threshold reported, which says something more useful than a flag.
- **It is a cheap stand-in for order dimension.** Dimension through the Ferrers
  formulation is NP-hard; this is quadratic and directly related, since the work in
  a two-dimension extension is orienting incomparable pairs. Where both can be
  computed, report their correlation; if dimension proves infeasible at our sizes,
  this stands in for it as the measure of how structurally hard a lattice is to
  draw.
- **It is a finding in its own right.** For the current corpus: 24 incomparable
  pairs for `capability`, 260 for `family-excitation`, 465 for `playing-mechanism`,
  44818 for `capability-practice-making`, 153192 for the full instruments lattice.

`tests/test_dimdraw_cost.py` keeps the claim checkable. It pins `Cn5`, from
DimDraw's own data set, at 32 concepts and 285 incomparable pairs consuming its
budget, against `family-excitation` at 27 concepts and 260 pairs finishing at once.
Two lattices of almost the same size, opposite costs.

### What to discuss

Not that the drawings are wrong, because they are not. The ask is that results are
budget-dependent, so the budget belongs in the reported parameters alongside the
scores, and any size trend involving dimdraw is confounded by it. Concretely: it
would help if odis signalled in its output whether the budget was consumed, since
at present a converged layout and an interrupted one are indistinguishable in the
file.

Worth adding, because it is useful to a reader of his paper: **DimDraw's cost is
driven by incomparable pairs, not by lattice size.** Eleven to nineteen concepts
with twenty to ninety incomparable pairs finish instantly; thirty-odd concepts with
several hundred consume any budget. That tells a reader when DimDraw is usable,
which a table of lattice sizes does not. It came out of comparing several scales of
one data set rather than single lattices, which is a small argument for the scale
families themselves.


---

## A rule for cross-scale figures

When a figure follows the same concepts across several panels, the criterion is
that **the followed set recurs in every panel**, which means every column must
contain the followed scale. Spanning the size range is secondary.

The worked example is the first gate ladder, which was chosen to span the sizes:
`capability` at 13 concepts, `practice` at 46, `capability-practice-making` at 319,
the full context at 576. It looked reasonable and was useless, because `capability`
and `practice` share only two concepts, the top and the bottom, so the first panel
marked nothing worth looking at.

The ladder that works is `practice`, `family-practice`,
`capability-practice-making`, `instruments`, at 46, 107, 319 and 576 concepts.
`practice` nests into all three of the others, so its 46 concepts appear in every
panel and the eye can follow them as the lattice grows more than twelvefold around
them.

This will recur for every cross-scale figure in the paper, so check the nesting
matrix before choosing panels, not after drawing them.


---

## Telling a mirror from a scramble: tau within rank strata

A global tau cannot say *how* an algorithm loses the order. Three patterns produce
different global numbers but need different words:

| Pattern | Per-stratum taus | Sign agreement | Mean \|tau\| |
|---|---|---|---|
| a sub-branch flips | some near +1, some near -1 | low | high |
| the whole drawing mirrors | one sign throughout | 1.0 | high |
| the order is scrambled | near zero everywhere | meaningless | low |

`consistency.py` now computes tau within each rank stratum as well as globally, and
`consistency_strata.csv` records one row per stratum. The summary columns in
`consistency.csv` are `n_strata`, `n_strata_compared`, `frac_strata_strong`,
`frac_strata_inverted`, `strata_bimodality`, which is the mean absolute tau, and
`strata_sign_agreement`.

On the first algorithm measured, aeschlimann_schmid over the instruments scales,
the answer is **not** branch flips. Where the effect is strong the signs are
uniform:

```
family-making -> instruments        strata: -0.25  -0.72  -0.74  -0.60
making -> family-making             strata: +0.33  +0.87  +1.00  +1.00
```

Every stratum agrees on a direction, so this reads as a partial global reflection
rather than a flipped branch, and the magnitude, mean |tau| 0.58 against a
theoretical 1.0 for a pure mirror, says there is real rearrangement on top of it.
That is a mechanism worth naming in the write-up, and it is not the one the
hypothesis predicted.

## p-values are bounds when nothing exceeds the observation

With 2000 draws, "p = 0.0005" means no permutation reached the observed tau, which
is a bound of 1/(draws+1) rather than an estimate. `consistency.csv` carries
`tau_p_is_bound` and `n_null_extreme` so this is visible; report such cases as
p < 0.0005 and raise the draws for a specific pair if a tighter bound is needed.

## Feasibility is per algorithm, not per lattice

`drawable` in the scale manifests says whether a lattice is worth drawing at all.
It does not say who can draw it. Measured:

| Algorithm | 46 | 107 | 139 | 319 | 576 |
|---|---|---|---|---|---|
| `aeschlimann_schmid` | 0.09 s | 0.21 s | | 0.78 s | 1.27 s |
| `sugiyama` | 0.07 s | 0.21 s | | 0.78 s | drawn |
| `fdp` | 0.19 s | 1.43 s | 2.49 s | **no return**, then 9.81 s | |
| `freese` | 1.78 s | | | 464 s | |
| `cole_ducrou_eklund` | 4.93 s | | | | |
| `dimdraw` | 60 s, anytime | | | | |

`FEASIBLE_MAX_CONCEPTS` in `run_harness.py` records this, and a scale beyond an
algorithm's range is recorded as `skipped` with the reason rather than attempted,
so a sweep cannot hang on one cell.

### fdp's 48 minutes were not a size cliff. They were an infinite loop

**This supersedes what this file said earlier.** The reading was that fdp has a
cliff between 139 and 319 concepts, and that its `{'timeout_s': 60.0}` failed to
bound some unidentified phase. The first half was wrong.

Tracing the phases showed the process was never in the optimiser at all. It sat in
`_initialize_vectors`, before it, in the `while queue:` loop at `fdp.py:268`. That
loop places each non-coatom attribute once every attribute implied by it already
has a position. Two attributes that imply each other — equal extents, an
unclarified context — each wait for the other, neither ever becomes placeable, and
the queue cycles forever. It is non-termination, not slowness, and no budget can
help, because `timeout_s` is consulted only in the optimiser's callback, which is
never reached.

`capability-practice-making` has exactly one such pair: `Requires electricity` and
`Electrical sound` hold of the same instruments. **Remove one of the two and fdp
draws all 319 concepts in 9.81 seconds.** Reproduced downwards as well: fdp also
fails to return on `making`, which has 17 concepts and the same pair, and on a
four-object, three-concept fixture built to contain one. Pinned in
`tests/test_fdp_termination.py`.

Eleven of the 39 contexts and scales here contain an equivalent pair, four of them
imported unchanged from the collection. The real-world contexts are drawn
*reduced*, which is why this has not caused problems: reduction clarifies, so the bug is
invisible on the corpus that is tested on. Full table below.

Consequences here. fdp's entry in `FEASIBLE_MAX_CONCEPTS` is now `None`, since its
limit was never size; the harness instead checks the context itself
(`REQUIRES_CLARIFIED`, `equivalent_attributes()`) and records a skip naming the
pair. **The budget point survives in weaker form**: `timeout_s` is checked once per
CG iteration, so it bounds the optimiser at iteration granularity and nothing
before it, and `completed_within_budget` would have called that 48-minute run fine.

### Decided: we do not clarify the scales

Clarifying would make fdp usable everywhere and changes no extent, hence no
lattice, no concept and no cross-scale comparison. It is still the wrong move.

The attribute set **is** the view we chose. `Electrical sound` and `Requires
electricity` are two distinct attributes of the data that happen to hold of the
same instruments, and dropping one because of that edits the view silently — it
would show up in every figure label and in the conjunctive normal form we report.
That the lattice is unchanged is not the point. Modifying our inputs to accommodate
a defect in one algorithm is backwards, and this defect is reproduced on a
three-concept fixture and can be fixed in his code.

So the exclusion stands, with the pairs named, and it is recorded rather than
worked around. **Eleven of the 39 contexts and scales here contain an equivalent
pair**:

| Context or scale | Concepts | Equivalent attributes |
|---|---|---|
| `zoo/zoo` | 4579 | `[hair 1]` == `[type 2]`, and one more |
| `instruments/instruments` | 576 | `Requires electricity` == `Electrical sound` |
| `instruments/capability-practice-making` | 319 | `Requires electricity` == `Electrical sound` |
| `dolphins/dolphins` | 282 | `A_5` == `A_12`, and one more |
| `music/music` | 163 | `well-rounded` == `well-balanced` |
| `southern_woman/southern_woman` | 65 | `E14` == `E13` |
| `olympics/decision-structure-format` | 64 | `Measured` == `Measured ∧ Individual events` |
| `instruments/family-making` | 39 | `Requires electricity` == `Electrical sound` |
| `olympics/decision-structure` | 35 | `Measured` == `Measured ∧ Individual events` |
| `instruments/family-excitation-mechanism` | 33 | `Chordophone ∧ Hammered strings` == the same with `Keyboard`, and two more |
| `instruments/making` | 17 | `Requires electricity` == `Electrical sound` |

Seven are ours. The other four — `zoo`, `dolphins`, `music`, `southern_woman` — are
**four of the ten contexts imported from the real-world collection**, in their
original form.

That count is itself a finding worth keeping: coextensive attributes are ordinary
in real data, common enough to hit four of ten published contexts. They are
invisible in his pipeline only because `contexts/real-world/reduced` is what it
draws, and reduction clarifies. Clarifying our scales would erase exactly that
observation, which is a second reason not to.


---

# Method

Everything below is what the code does, stated once, so that nothing has to be
re-derived from the investigation above.

## Scale construction

A scale-measure is a coarser view of one context: the same objects, fewer
distinctions. A scale attribute is either an original attribute kept unchanged or
a **conjunction** of original attributes, never a disjunction and never a negation.

The reason is guarantees, not taste. Attribute projections are scale-measures by
Cor. 22 of Hanika and Hirth, and conjunctions by their Cor. 17, unconditionally.
Prop. 16 gives no such guarantee for disjunction or negation: those are
scale-measures only when the resulting attribute extent happens to be an extent of
the original context, which has to be checked case by case and usually fails.

Three routes, and every scale is one of them:

| Kind | Construction |
|---|---|
| **facet** | a plain subset of the attributes, one coherent lens |
| **chain step** | a facet refined by conjoining its attributes with attributes from *outside* the scale |
| **apposition** | two or more facets side by side |

Two rules constrain which of these are worth building.

**A conjunction only refines if it reaches outside the scale.** A scale's extents
are already all the intersections of its attribute extents, so conjoining
attributes that are both in the scale adds nothing. Refining the venue facet by
conjoining indoor and outdoor with the surfaces gave 18 concepts, exactly what the
facet already had.

**An apposition needs a one-sentence description that is not a list.** "The rules
of the contest: how it is run and how it is decided" earns its place; "structure
and format and demands" does not. Combinations that fail the test are recorded in
the groupings file as rejected, with the reason.

## Nesting: finer levels add attributes, never replace them

For cross-scale comparison the coarser view's extents must all be extents of the
finer one. That holds when a refinement **adds** attributes and keeps the ones it
refines, and breaks when it swaps them out.

Demonstrated on Living Beings and Water: replacing the general attribute with its
two refinements gives 10 concepts and nesting fails; retaining the general
attribute alongside them gives 12 and nesting holds. Twelve is the figure in Hanika
and Hirth's published scale of that context, so their own construction keeps both.

## Node identification: which concept is node 7?

The generators write `<node id="0">` with an x and a y and nothing else, so a
drawing does not say which concept a node is. Matching by position in some
canonical ordering is not an option, because two scales have different concept
sets. Matching is by **extent**.

The mapping is recoverable because the integer is an index into a reproducible
list. Six of the seven algorithms number concepts in the order `odis` enumerates
them, and `redraw` sorts its nodes explicitly by extent size, then extent, then
intent, before numbering.

That the odis order is *lectic* was not assumed. It is exactly ConceptFlow's
NextClosure, element for element, while ConceptFlow's Close-by-One gives a
different sequence: two unrelated implementations agreeing is what makes relying on
it safe.

`check_node_mapping.py` verifies the claim per algorithm by capturing ground truth,
replacing `write_graphml` in memory only so nothing in his tree is edited,
recording which extent each id stood for at the moment of writing, rebuilding the
same mapping from the .cxt alone, and comparing elementwise as sets of object
names. It repeats the capture in fresh processes under `PYTHONHASHSEED` 0, 1 and
random, which is what would catch an ordering that comes from set or dict
iteration: stable within a run, different between runs, wrong with no error raised.

`graphml_loader.py` does not trust any of this at use time. On every load it
re-derives the order from odis, checks it against an independent NextClosure
enumeration, and raises `EnumerationOrderError` rather than returning a plausible
mapping. It also refuses when the node count and concept count disagree, or when
two nodes map to one extent.

## Consistency

For each nested pair and each algorithm, over the concepts present in both
drawings:

- **Kendall tau on x-ranks.** Ordinal, never geometric: two runs on related inputs
  do not produce comparable coordinates, since the origin and scale are arbitrary,
  so any distance-based statistic would measure those as much as the placement.
  Ranks are invariant under translation, scaling and any monotone rescaling of x.
  The statistic is counted in integers so that its exact cases come out exact;
  scipy supplies the p-value and the two are cross-checked.
- **Rank drift**, reported separately and never charged to the algorithm: each
  shared concept is ranked by its vertical position in each drawing and the mean
  absolute change of that rank is normalised to [0, 1]. Refining a scale inserts concepts and moves
  the others vertically whatever the algorithm does.
- **Tau within each rank stratum**, which separates three patterns a global tau
  cannot: a flipped sub-branch gives mixed signs with high magnitudes, a mirrored
  drawing gives one sign throughout with high magnitudes, and a scramble gives low
  magnitudes everywhere. Summarised by `strata_sign_agreement` and
  `strata_bimodality`, which is the mean absolute tau, with one row per stratum in
  `consistency_strata.csv`.

Three fixtures run before any of this touches data, and they have already earned
their keep by catching that scipy returns 0.9999999999999999 for two identical
rankings: identical drawings give tau exactly 1, mirror images exactly -1, and
moving only non-shared nodes exactly 1.

## The permutation null

A raw tau is uninterpretable. How much agreement is surprising depends on how many
concepts are shared and how much freedom the order leaves, so every observation is
standardised.

Keep the finer drawing exactly as it is and permute which shared concept sits at
which of its positions, **restricted to rank strata**: a concept may only take the
position of another at the same height. Unrestricted shuffling would compare
against a null that violates the order constraint every drawing must satisfy, and
would flatter every algorithm. 2000 draws give a distribution, and the observation
becomes a z-score and a two-sided p-value.

When no draw reaches the observed value the p-value is a **bound**, 1/(draws+1),
not an estimate; `tau_p_is_bound` and `n_null_extreme` record that.
`null_free_positions` records how much freedom the null actually had, since a null
built of singleton strata is not a null.

The other two nulls are not built. The **rerun null** is likely trivial, because
every algorithm measured so far is deterministic, in which case it is tau = 1 and
the comparison reduces to whether the cross-scale tau falls short of 1; seeded
machinery is only worth building for algorithms that are genuinely
non-deterministic. The **random-valid null** gives an absolute floor and is the
least informative of the three.

## Reading the numbers

The terms above, and what a value of each one means.

**Shared concepts.** Those present in both drawings of a nested pair, matched by
extent — by which objects the concept contains — never by node id or position.
Everything is computed over these.

**x-rank.** A concept's position from the left, 1st, 2nd, 3rd, replacing its x
coordinate. Ranks because a drawing's origin, units and scale are arbitrary.

**Rank stratum.** A set of concepts at the same height in the lattice, height being
the longest chain below a concept. Computed from the extents, not from the picture.
It matters because the vertical order is forced — a concept must be drawn above
everything below it — while within a stratum nothing forces an order, so the
left-to-right arrangement there is entirely the algorithm's choice.

| Column | Meaning | Values |
|---|---|---|
| `n_shared` | how many concepts the two drawings have in common | for a nested pair, all of the coarser lattice |
| `tau_x` | Kendall tau-b on x-ranks: over every pair of shared concepts, does the finer drawing keep their left-to-right order | +1 identical order, 0 unrelated, −1 exactly reversed |
| `rank_drift` | total absolute change of vertical rank, over the largest a permutation could give | 0 nothing moved relative to the others, 1 the vertical order exactly reversed. A baseline, not a score |
| `tau_z` | the observed tau in standard deviations of the null: (tau − null mean) / null sd | \|z\| < 2 unremarkable, 2–3 notable, > 3 hard to get by chance. Sign follows tau |
| `p_value` | scipy's classical Kendall p-value, whose null is independent random rankings | the textbook number, and the looser test; see below |
| `tau_p` | two-sided p-value from our 2000 stratum-restricted permutations | **the one to report**; see `tau_p_is_bound` |
| `tau_p_is_bound` | true when no draw reached the observed tau | then p is the bound 1/(draws+1) ≈ 0.0005, not an estimate; report as p < 0.0005 |
| `null_free_positions` | how many concepts the null could actually move | strata of one cannot be permuted, so a small number means the null had little freedom and the z means little |
| `n_strata` / `n_strata_compared` | heights spanned, and how many had ≥ 2 concepts to compare | a stratum of one has no pair to agree about |
| `frac_strata_strong` | fraction of compared strata with \|tau\| > 0.5 | held or flipped decisively, either direction |
| `frac_strata_inverted` | fraction with tau < −0.5 | decisively reversed |
| `strata_bimodality` | mean \|tau\| over strata: how decisive strata are, ignoring direction | near 1 every stratum held or flipped, near 0 none did. The name is poor; it measures decisiveness |
| `strata_sign_agreement` | fraction of compared strata sharing the majority sign | 0.5 evenly split, 1.0 one direction throughout |

**On the two p-values.** A p-value is the probability of a result at least this
extreme if the null were true: how surprising, never how large. The two here differ
in what they call chance. `p_value` allows any left-to-right order, including orders
no line diagram could have, since it ignores that a concept must be drawn above
everything below it; `tau_p` permutes only within rank strata, so its null is chance
among drawings that are actually legal. `tau_p` is therefore the stricter and the
honest one, and `tau_z` is the same comparison expressed as a distance rather than a
probability, which is what makes it comparable across pairs of very different size.

### The equations, and where each one comes from

Nothing here is a scikit-learn object; scikit-learn is only a transitive dependency
of ConceptFlow. The statistics are scipy plus two functions of our own.

Write `n` for the number of shared concepts, `a` for the coarser drawing and `b`
for the finer one, and let `x_a(i)` be concept `i`'s rank from the left in `a`.

**Kendall tau-b**, `tau_x` and every per-stratum tau. Over all `n(n-1)/2` pairs
`i < j`, with `C` the pairs ordered the same way in both drawings, `D` the pairs
ordered oppositely, `T_a` and `T_b` the pairs tied in `a` and in `b`:

```
tau_b = (C - D) / sqrt((P - T_a) * (P - T_b)),    P = n(n-1)/2
```

With no ties this is just `(C - D) / P`. Implemented as `kendall_tau_b` in
`consistency.py` rather than taken from scipy, counting `C`, `D`, `T_a`, `T_b` as
integers and dividing once at the end, because scipy returns 0.9999999999999999 for
two identical rankings and the fixtures require an exact 1. Quadratic in `n`, which
is why the null draws use scipy's instead.

**Rank drift.** With `y_a(i)` the rank of concept `i` by vertical position in `a`:

```
drift = sum_i |y_a(i) - y_b(i)| / floor(n^2 / 2)
```

`floor(n^2 / 2)` is the maximum of `sum |i - s(i)|` over permutations `s`, attained
by the reversal, so drift is 0 for an unchanged vertical order and 1 for a reversed
one at any `n`. Implemented as `rank_drift` in `consistency.py`.

**Stratum summary**, over the strata that had at least two shared concepts:

```
strata_bimodality     = mean |tau_s|
strata_sign_agreement = max(#{tau_s > 0}, #{tau_s < 0}) / #strata compared
frac_strata_strong    = #{|tau_s| > 0.5}  / #strata compared
frac_strata_inverted  = #{ tau_s  < -0.5} / #strata compared
```

Implemented as `stratum_summary` in `consistency.py`.

**The permutation null.** For each of `K = 2000` draws, permute the shared
concepts' positions within their strata and recompute tau, giving `tau_1 … tau_K`:

```
tau_z = (tau_obs - mean(tau_k)) / sd(tau_k)
tau_p = (#{|tau_k| >= |tau_obs|} + 1) / (K + 1)
```

`sd` is the population standard deviation. The `+1` in `tau_p` keeps it from ever
being exactly zero; when the numerator's count is 0 the result is the bound
`1/(K+1)`, which `tau_p_is_bound` marks. Implemented as `permutation_null` in
`nulls.py`, seeded at 20260929 so a rerun reproduces the same draws.

| Step | Comes from |
|---|---|
| ranking x and y | `scipy.stats.rankdata`, default `average` method, so tied values share their mean rank |
| `tau_x`, per-stratum tau | `kendall_tau_b` in `consistency.py` |
| `p_value` | `scipy.stats.kendalltau(...).pvalue` |
| `rank_drift`, the stratum summary | `rank_drift`, `stratum_summary` in `consistency.py` |
| rank strata | `rank_strata` in `nulls.py`: longest chain below each extent |
| shuffling a draw | `random.Random(20260929).shuffle`, within strata |
| tau of each draw | `scipy.stats.kendalltau`, `n log n`, cross-checked against ours to 1e-9 |
| `tau_z`, `tau_p` | `permutation_null` in `nulls.py`; `statistics.mean`, `statistics.pstdev` |

The last two stratum columns are read together, which is the point of computing
them:

| Mean \|tau\| | Sign agreement | Reading |
|---|---|---|
| high | ≈ 1.0 | the whole drawing mirrored |
| high | ≈ 0.5–0.7 | a sub-branch flipped, the rest held |
| low | anything | scrambled; the sign carries no information |

---

# Results so far

**Preliminary. Two algorithms, one context, and one of them on two pairs only.**
These are the numbers the pipeline currently produces, not findings about drawing
algorithms.

## Consistency, instruments, aeschlimann_schmid, 17 nested pairs

The `p` column is `tau_p`, the permutation p-value, not scipy's.

| Coarser → finer | Shared | tau | z | p |
|---|---|---|---|---|
| making → family-making | 17 | +0.82 | 3.39 | < 0.0005 |
| making → capability-practice-making | 17 | +0.73 | 3.14 | 0.0010 |
| family-making → instruments | 39 | −0.59 | −4.78 | < 0.0005 |
| family-practice → instruments | 107 | −0.28 | −3.97 | 0.0010 |
| family-excitation → family-excitation-mechanism | 27 | −0.46 | −2.77 | 0.0020 |
| capability-practice-making → instruments | 319 | −0.08 | −1.71 | 0.0505 |

The null is doing the work it was built for: **−0.08 over 319 shared concepts
(z = −1.71) is a stronger signal than +0.82 over 17 (z = 3.39) is weak**, and the
raw taus rank the pairs quite differently from the z-scores. Negative values
dominate the refinements into the full lattice.

## The first cross-algorithm comparison, on two pairs

fdp draws six of the eleven instruments scales; the rest have equivalent attributes
and are skipped, so only two nested pairs have both ends. On one of them the two
algorithms disagree sharply:

| Pair | Shared | `aeschlimann_schmid` | `fdp` |
|---|---|---|---|
| excitation → playing-mechanism | 21 | +0.27 (z +1.64) | +0.36 (z +1.83) |
| practice → family-practice | 46 | +0.11 (z **+1.07**) | −0.65 (z **−5.53**) |

Same two lattices, same shared concepts, same null: one algorithm reproduces the
coarser order about as well as chance, the other reverses it strongly and with
uniform per-stratum signs (sign agreement 1.0, mean |tau| 0.71 against 0.22). That
is the first evidence that the measure separates **algorithms** and not just
scales, which is what it has to do if it is to say anything about drawing at all.
Two pairs, so it is an encouraging sign and nothing more.

## The mechanism is not a flipped branch

Per-stratum taus are not bimodal. Where the effect is strong the signs are uniform:

```
family-making -> instruments     strata: -0.25  -0.72  -0.74  -0.60
making -> family-making          strata: +0.33  +0.87  +1.00  +1.00
```

Every stratum agrees on a direction, so this reads as a **partial global
reflection with rearrangement on top**, not a flipped sub-branch. Mean absolute tau
of 0.58, against 1.0 for a pure mirror, is what fixes the "partial". This is not
the mechanism the hypothesis predicted.

## DimDraw's cost is driven by incomparable pairs, not lattice size

It tells a reader when DimDraw is
usable, which a table of lattice sizes does not, and it came out of comparing
several scales of one data set rather than single lattices.

| Context | Concepts | Incomparable pairs | Time, 30 s budget |
|---|---|---|---|
| `ganter`, published | 11 | 21 | 0.00 s |
| `triangles`, published | 18 | 68 | 0.01 s |
| `living_beings_and_water`, published | 19 | 91 | 0.01 s |
| `Cn5`, published | 32 | 285 | consumed |
| our `capability` | 13 | 24 | 0.00 s |
| our `excitation` | 21 | 154 | 3.70 s |
| our `family-excitation` | 27 | 260 | 0.41 s |
| our `playing-mechanism` | 35 | 465 | consumed |

`Cn5` is the anchor: a contranominal scale from DimDraw's own data set, 32
concepts, consuming any budget, while our `family-excitation` at 27 concepts and
260 incomparable pairs finishes in 0.41 s. Pinned in `tests/test_dimdraw_cost.py`.

## The dimdraw budget confound is real in principle and unmeasurable here

Three mid-size scales drawn at 60 s and at 600 s, all seventeen metric scores
identical each time. Ten times the budget changed nothing, so the anytime search
reaches its answer well inside a minute. Measured at 35 to 46 concepts only; repeat
if dimdraw is ever run on something much larger.

## fdp does not terminate on an unclarified context

Not a size limit, which is what it looked like at first: two attributes with equal
extents make `_initialize_vectors` cycle forever, at 17 concepts as readily as at
319, and `timeout_s` cannot stop it because the optimiser is never reached. Remove
one attribute of the pair and the 319-concept scale draws in 9.81 s. Eleven of the
39 contexts and scales here contain such a pair, seven of them ours, so this decides
where fdp can be used. We do not clarify to work around it; the reasoning and the
pairs are under *Decided: we do not clarify the scales*.

## The gate

Two figures in `figures/`, reproducible with:

```bash
# figures/gate.png    — the practice ladder, 46 concepts followed through 576
python gate.py --algorithms sugiyama aeschlimann_schmid --out gate
# figures/gate-strongest.png — the making ladder, the strongest measured effect
python gate.py --algorithms sugiyama aeschlimann_schmid --out gate-strongest \
    --scales making family-making capability-practice-making instruments \
    --followed making
```

The effect is visible where density allows: in `gate-strongest.png` the 17 marked
concepts span the width at 17 and 39 concepts and cluster to one side by 576. At 319
and 576 concepts the panels are too dense to judge order by eye, so the low-density
panels are the ones to read. The gate is a feasibility check and produces no
result.

---

# Limitations

- **Two contexts**, instruments and olympics. More are collected but unscaled.
- **The additive family is empty.** `zschalig`, `lessink` and `autolayout` do not
  exist in the repository, there is no simple baseline, and `dimflux` is excluded
  until his object-mapping patch lands. `dimdraw` is order-dimension-driven rather
  than additive, and is usable only on small, low-incomparability scales. So the
  predicted split — additive layouts staying consistent as the scale is refined,
  force-directed ones scrambling — **has no clean test yet**. Consistency is still
  measured across the seven available algorithms; what is missing is the contrast
  between the two families.
- **dimdraw** completes only up to roughly thirty concepts, or a few hundred
  incomparable pairs, and above that returns an anytime result. Its size trend is
  confounded by the budget in principle, though not measurably at the sizes tested.
- **fdp** cannot be run on an unclarified context at all, which is seven of our
  contexts and scales, so its coverage is partial — and partial in a way that has
  nothing to do with size. We will not clarify to work around it, for the reasons
  recorded under *Decided: we do not clarify the scales*; the pairs are named there
  and every skip carries the pair that caused it.
- **cole_ducrou_eklund may decline a scale outright**, which makes the design
  unbalanced, so the model has to handle missing cells rather than dropping rows.
  Which structures it refuses may itself be informative. How often this happens is
  currently unknown: the one case we had, `family-excitation`, draws as of upstream
  `712d498`, which added fallback passes, and we have not measured cole since.
- **Two budget parameters do not mean what the code implies, in opposite
  directions.** dimdraw's is honoured but its consumption is invisible in the
  output; fdp's is checked once per optimiser iteration and covers nothing before
  the optimiser, so a run that never reaches it is unbounded and would have been
  recorded as having completed within budget.
- **The scales are hand-picked by us**, so a reviewer may ask whether they were
  chosen to produce the result. The mitigation is the circularity guard: every
  grouping is written into the context's `groupings.md` with a timestamp and a
  reason **before anything is drawn**, and is never revised after results are seen.
  The rejected candidates are recorded there too.
- **Chain length varies by context**, so the covariate is `|L_i|`, the concept
  count, and never the level index.
- **No human validation.** Every metric is a proxy for readability, and the study
  measures proxies against proxies.
- **The gate is a feasibility check**, not a result, and was read by eye.

---

# Defects found in the generators

Four things found while wiring our scales into the main pipeline. The first costs us
correctness, the second cost us a day, the rest are small. All reproduce on the
repository as pinned, `712d498`. Paths are relative to its root.

## 1. `fdp` never returns on a context that is not attribute-clarified

Two attributes with equal extents — each implies the other — make
`FDP_Additive_Features.__init__` loop forever, at any lattice size. In
`line_diagrams/fdp/fdp.py:262-281`, `_initialize_vectors` places a non-coatom
attribute only once every attribute implied by it already has a position:

```python
elif all(up in self.vectors for up in upper[m]):
    ...
else:
    queue.append(m)      # fdp.py:281
```

With `a` and `b` equivalent, `upper[a]` contains `b` and `upper[b]` contains `a`,
so neither branch is ever taken for either and the queue cycles. The batching by
`same_upper` does not help: their upper sets differ, one containing `b` and the
other `a`.

`{'timeout_s': 60.0}` cannot stop it. That is consulted only in the callback passed
to `minimize` in `_optimize_layout`, which this never reaches, so a caller relying
on the budget hangs indefinitely.

Four objects and three attributes are enough. `x` holds of g1, g2, g3, and `a` and
`b` both hold of g1 and g2, so each implies the other and neither is a coatom:

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
                      {'timeout_s': 5.0})     # never returns; three concepts
```

Not visible on the corpus because `contexts/real-world/reduced` is what the
pipeline draws, and reduction clarifies. It appears as soon as anything unreduced
is drawn. Eleven of the 39 contexts and scales on our side contain an equivalent
pair, and four of them are the real world: `zoo`, `dolphins`, `music` and `southern_woman`, in
`contexts/real-world/original` — four of the ten contexts in that collection.

Coextensive attributes are ordinary in real data, so an unclarified context is a
legitimate input, and the current failure is a hang rather than an error. We are
not clarifying our contexts to route around it, so those scales stay out of fdp's
results until it is fixed.

That this looks like a size problem is worth flagging too: our 319-concept scale
ran 48 minutes without returning and we first recorded it as a scaling cliff.
Removing one attribute of the pair draws it in **9.81 s**. fdp is much faster than
the cliff suggested.

## 2. The output filename is slugged but nothing tells a caller

Every `generate.py` writes `{slug(cxt_path.stem)}.graphml`, where `slug` lowercases
and turns hyphens into underscores, while `generate()` returns `None`. A caller
scripting the generators has to reimplement `slug` to know what was written, and
one that instead forms the expected path from the `.cxt` stem gets a wrong path for
any hyphenated name.

That failure is silent and directional: the generator succeeds, the file is there
under the slugged name, the caller sees nothing at the name it expected, and, if it
treats a missing file as a decline the way ours did, every successful drawing of a
hyphenated context becomes a recorded refusal. Only the hyphenated ones, so it
biases rather than breaking.

One line fixes it: `return graphml_path` from `generate()`.

## 3. `skipped` means four different things on the same channel

Parsing generator output cannot distinguish them:

| Message | Meaning |
|---|---|
| `skipped {name}: {path} already exists` | cached, i.e. success |
| `skipped {name}: no drawing found` (`dimdraw`) | the algorithm declined |
| `skipped {name}: {e}` (`cole_ducrou_eklund`) | the algorithm declined |
| `skipped {dataset}: directory not found` | misconfiguration |

Ours currently tells them apart by substring, which is fragile. A distinct word for
the cache hit, or a status in the return value, would settle it. The same message
also goes to `stderr` in `pending_contexts()` and to `stdout` in `main()`.

## 4. `fdp` divides by zero when two attribute vectors coincide

`fdp.py:206` emits `RuntimeWarning: invalid value encountered in scalar divide`
whenever `np.linalg.norm(n_i - n_j)` is zero, and the resulting `nan` propagates
into the gradient. Reproducible on the four-object fixture above with the
equivalent pair removed; it does not appear at 319 concepts, so it looks specific
to small degenerate cases. Harmless in the cases seen, since the layout still comes
out, but it is a `nan` inside an optimiser.

## Not a defect, but worth knowing

`dimdraw`'s budget is honoured and invisible: `context.draw('dimdraw', 60000)`
returns the same thing whether the search converged or was cut off, so nothing
downstream can tell an optimal drawing from an anytime one. We infer it from wall
clock against the budget, which is a guess. If odis can expose it, every drawing
above about thirty concepts becomes interpretable.

---

# Open questions and next steps

**Is the visible effect order reversal or localisation?** These are different
claims and tau only measures the first. The gate figure appears to show the marked
set spanning the width at 17 and 39 concepts and clustering by 576, which is a
statement about *where* the shared concepts sit, not about their order. Proposed
measure: the spread of the shared set's x-ranks within the finer drawing,
normalised by the full range. Not implemented.

**Is the partial global reflection systematic or an artefact of arbitrary
orientation?** If an algorithm has no canonical left-right orientation it may pick
a different one each time, which would produce the same uniform-sign signature with
no meaning. Check whether the sign across all 17 pairs is systematic or balanced,
and whether it correlates with anything about the pair. Against a single consistent
reflection: the two gate figures cluster in different directions.

**The remaining nulls.** Confirm from the timing sweep which algorithms are
non-deterministic, then build the rerun null only for those; the random-valid null
last.

**Bring dimflux in once the object mapping is fixed.** It is excluded only because
its node ids cannot currently be turned back into concepts, which is a blocker for
us specifically and not a judgement on the algorithm.Nothing else in
the pipeline needs to change.

**More contexts**, and the full sweep across all seven algorithms.
