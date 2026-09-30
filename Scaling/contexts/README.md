# Formal contexts

Binary formal contexts, one folder each, in Burmeister (`.cxt`) format. These are
the full contexts: the data as collected, before any scaling. Scale-measures are
built from them in a later step and are not part of this folder.

They come from two places. Five were **collected and built here**, and ten are
**standard examples imported** from the surrounding drawing-quality repository.

## Collected and built here

| Folder | Context | Objects | Attributes | Density | Concepts | Width |
|---|---|---|---|---|---|---|
| `instruments/` | musical instruments | 64 | 42 | 0.229 | 576 | 138 |
| `olympics/` | olympic disciplines 2024–2028 | 70 | 38 | 0.402 | 10463 | – |
| `wd40pc/` | white dwarfs within 40 pc | 1078 | 28 | 0.226 | 728 | – |
| `tenpc_stars/` | stars, brown dwarfs and white dwarfs within 10 pc | 456 | 35 | 0.236 | 732 | – |
| `tenpc_exoplanets/` | confirmed exoplanets of those stars | 85 | 16 | 0.476 | 371 | 74 |

Concepts are counted by enumerating extents with NextClosure; width, the largest
antichain, is computed by matching and only where that is affordable, which is why
the three largest lattices have no entry. The olympics context is an outlier at
10463 concepts: 70 disciplines against 38 fairly independent properties produce far
more combinations than the astronomy data, where thresholds on one quantity are
nested and constrain each other.

Each folder holds the context file and a README that says what the data set is, why
its object set is what it is, how the data were collected, and what every attribute
means, listed in the order the attributes appear in the context file.

A context folder also holds everything **derived** from that context: its
scale-measures as further `.cxt` files, the `manifest.csv` describing them, the
`nesting.csv` matrix, and the `groupings.md` recording why each scale was chosen.
Nothing about a context lives anywhere else. See *Scales* below.

Beside each context sits the data it came from. For the three astronomy contexts
that is the many-valued table, `*_manyvalued.csv`, holding the masses, temperatures,
ages, distances and spectral types that the threshold attributes were computed from.
The two hand-built contexts are natively binary and have no numeric counterpart, so
they carry their codebook instead, and the olympics folder additionally carries the
two descriptive columns, governing sport and summer or winter, that were deliberately
left out of the context.

## Standard examples imported from the repository

The remaining folders hold the textbook and benchmark contexts that come with the
drawing-quality repository, at `contexts/real-world/original` two levels up. The
*original* files are used rather than the *reduced* ones beside them, because only
the originals keep the real object and attribute names; the reduced variants relabel
everything to `g1`, `m1` and so on, which is useless for choosing groupings by hand.

`import_standard_contexts.py` in this folder measures all 42 of them and imports
only those comparable in size to the five above. A context qualifies on either of
two counts: a lattice of at least 60 concepts, which still allows three or four
coarsening steps above the floor of 10 to 12, or at least 100 objects plus
attributes, which makes it a comparable drawing problem even when its lattice is
smaller. Width must be at least 3 either way, since a chain offers nothing
horizontal to measure. Rather smaller than our own is allowed on purpose, so that
the classic two-mode network examples come in; the textbook contexts of a dozen
concepts do not, because a chain over them would be one or two levels of nearly
identical pictures.

Contexts holding the same data twice are imported once. Two tests catch that:
equality of the table, and agreement in shape, in row and column degrees and in
lattice size, which finds the same data under a relabelling. Each imported folder
carries a `.imported-from` marker naming its source, and the script only ever writes
to folders that have one, so the five contexts above are never touched. Rerunning it
with different thresholds removes imports that no longer qualify.

| Context | Objects | Attributes | Concepts | Width | Qualifies on |
|---|---|---|---|---|---|
| `zoo` | 101 | 43 | 4579 | – | both |
| `seasoning_planner` | 56 | 37 | 532 | 152 | concepts |
| `olympic_disciplines` | 50 | 19 | 529 | 88 | concepts |
| `wood_properties` | 29 | 28 | 315 | 91 | concepts |
| `dolphins` | 62 | 62 | 282 | 113 | both |
| `music` | 31 | 11 | 163 | 41 | concepts |
| `diagnosis` | 120 | 17 | 88 | 22 | both |
| `southern_woman` | 18 | 14 | 65 | 16 | concepts |
| `brunson_club` | 25 | 15 | 62 | 21 | concepts |
| `living_beings_and_water` | 8 | 9 | 19 | 6 | baseline |

The lower end of that table is where the judgement sits. `diagnosis` has only 88
concepts but 120 objects, so as a drawing problem it is squarely in our range.
`southern_woman` and `brunson_club` are smaller again, at 65 and 62 concepts, and
are in because both are classic two-mode network data sets, the Davis Southern Women
study and a club membership network. They bring a kind of data the rest of the
corpus lacks, and at that size a chain still has three or four levels. Below them
the next candidate is `foundedness` at 57 concepts, where the examples become
textbook illustrations rather than data.

**Living Beings and Water is in for a different reason.** With 19 concepts it fails
the filter, and it is imported anyway because it is the published worked example
that the construction is validated against before anything larger is scaled. It is a
method check, not a member of the corpus.

**The three largest cannot be drawn at full size.** Zoo, the spices planner and the
olympic disciplines example have lattices of 4579, 532 and 529 concepts. They are
still worth scaling; their chains simply have to stop below the top rather than
terminating at the data.

**Duplicates were dropped.** `gewuerz_planer` is the same table as
`seasoning_planner`. `tealady` is the Southern Women data under first names and
numbered events, which `southern_woman` carries under the real names of the study,
and `futtertabelle` repeats `bird_diet`; all of those fall below the size filter in
any case.

**Do not confuse `olympic_disciplines` with `olympics`.** The first is the small
benchmark example that ships with the repository, 50 objects and 19 attributes. The
second is the context built here from the 2024 to 2028 programmes, 70 objects and 38
attributes. They are different data about the same subject.

As a side effect the measurement reproduces three published numbers exactly: 4579
concepts for zoo and 19 for Living Beings and Water, both as reported by Hanika and
Hirth, and 532 for the shipped spices file, which is the figure that differs from
the 421 quoted in their papers.

## How these files are produced

The five collected contexts are written by `build_contexts.py` in the parent
directory:

```bash
.venv/bin/python build_contexts.py
```

The script reads `Datasets/`, writes the five `.cxt` files here, and never modifies
anything it reads. For the three astronomy contexts it recomputes every attribute
from the many-valued source table and then compares the result against the context
file produced by the original pipeline; the run reports whether the two agree. They
currently agree exactly, so the files here are reproducible rather than copied.

The parent `README.md` covers the Python environment and how to install it.

## Reading the files

A Burmeister file lists the object count, the attribute count, then the object
names, then the attribute names, then one row of `X` and `.` per object. Two
contexts come from data tables where a value could in principle be unknown; both
are read in the closed-world sense used throughout formal concept analysis, so a
`.` means the attribute does not apply, not that nobody checked. Where that reading
needs care, the individual README says so. For the white dwarfs in particular, 27
objects have no fitted parameters, and the attribute *Gaia parameters available*
exists to make that visible instead of hiding it in the dots.

## Threshold attributes and the bands between them

Several attributes in the astronomy contexts are thresholds on a numeric quantity:
mass above 0.9 solar masses, temperature above 10500 K, instellation above the
habitable-zone outer edge. They are the result of conceptual scaling, the step that
turned a measured number into yes-or-no attributes, and the choice of scale has a
consequence that is easy to miss.

A threshold attribute gives a nested family of object sets, so the *band* between two
thresholds is a difference of two sets, not an intersection. Extents are closed under
intersection, so a band is generally **not** an extent, and the concept lattice has no
node for it. Measured on the contexts here:

| Band | Objects in it | Its closure |
|---|---|---|
| white dwarfs of typical mass, 0.45 to 0.9 M☉ | 944 | 1051, every object with a Gaia fit |
| white dwarfs inside the ZZ Ceti strip, 10500 to 12500 K | 44 | 153, every object above 10500 K |
| planets in the conservative habitable zone | 13 | 48, every planet above the outer edge |

Each of those groups is still *definable* from the data, and each README names it,
but it cannot appear as a node of a diagram drawn from the context as it stands. The
standard remedy is an interordinal scale: add the complementary attributes, mass at
least 0.45, temperature at most 12500 K, and so on, so that a band becomes an
intersection of two attribute extents. That changes the context, and therefore every
lattice built from it, so it is left as a deliberate decision rather than applied
silently. The individual READMEs flag where it would bite.

## Scales

A scale-measure is a coarser view of one context: the same objects, fewer
distinctions. Scales live in the folder of the context they come from, so
`instruments/` holds `instruments.cxt` and, beside it, `excitation.cxt`,
`family-excitation.cxt` and the rest. The identity scale-measure is the context
file itself, which is why no copy of it is written.

| File in a context folder | What it is |
|---|---|
| `<scale>.cxt` | a scale, same objects as the context, listed in the manifest |
| `manifest.csv` | one row per scale: kind, chain membership, attributes, concepts, width, height, whether it is `drawable`, description, flags |
| `nesting.csv` | one row per ordered pair of scales: nested or not, both extent counts, the overlap, the ratio, whether the overlap is too thin, and whether the pair is `usable` |
| `groupings.md` | every grouping used, timestamped, with its rationale and the rejected candidates |

A scale attribute is either an original attribute kept unchanged, which is an
attribute projection and a scale-measure by Cor. 22 of Hanika and Hirth, or a
conjunction of original attributes, which is one by their Cor. 17,
unconditionally. Disjunction and negation are never used: those are scale-measures
only when the resulting extent happens to be an extent of the original, which is
not guaranteed.

Scales are not one cumulative chain. Each is a view answering a single question,
with refinement chains where the hierarchy is real and appositions where the
combination is a view someone would ask for. Every scale is nested under its
context by definition, so each gives one coarse-to-fine pair; chains and
appositions add more, and `nesting.csv` records which pairs those are.

### Drawable and usable

A scale is **drawable** when a layout algorithm can actually take it: between 12
and 1000 concepts, with width at least 3. Below that floor every algorithm produces
the same picture. The ceiling is provisional: it is not from the literature and not
from the colleague's data, and it is meant to be replaced once the ten algorithms
have been timed at a few sizes. It is set where it is so that the identity
scale-measure of the contexts we have is admitted without pretending we know where
the limit falls. A scale outside the band
is still built and still measured, because it says something about the data, but
the `drawable` column exists so that nothing downstream feeds it to a layout run by
accident. The olympics context is the case in point, at 10463 concepts.

A nested pair is **usable** for a cross-level comparison when it nests, shares at
least eight concepts, and both sides are drawable. Nesting is set inclusion and
costs nothing to compute, so pairs involving an undrawable scale stay in the matrix
and are marked unusable rather than dropped.

Nothing is asserted in prose. `build_scales.py` checks every scale as it writes
it, and `verify_scale.py` rechecks and regenerates the matrix:

```bash
.venv/bin/python contexts/build_scales.py --context instruments
.venv/bin/python contexts/verify_scale.py contexts/instruments/instruments.cxt \
    --dir contexts/instruments --matrix contexts/instruments/nesting.csv
```

Because the map is the identity on objects, Prop. 20 says a scale is a
scale-measure exactly when each of its attributes is one on its own, so the check
is one closure per attribute rather than an enumeration of the scale's extents.
Both commands exit non-zero on failure.

## Conventions

- Attribute names are the readable names, not codes. They are unique within a
  context and are the names that will appear in diagrams.
- Object names are the names used by the source catalogue or codebook.
- Object order and attribute order are fixed by the build script, so a row index
  means the same thing across regenerations.
- The two hand-built contexts each contain a few objects with identical attribute
  sets. That is expected and harmless: they are distinct objects sharing one
  concept. The individual READMEs list them.

## Where the raw material lives

`Datasets/` in the parent directory holds the sources: the matrices and codebooks
for the two hand-built contexts, and, for the astronomy contexts, the many-valued
source tables, the original build scripts and long provenance READMEs. Those
READMEs go further than the ones here on catalogue versions, individual objects and
thresholds, and are the right place to look before citing anything.
