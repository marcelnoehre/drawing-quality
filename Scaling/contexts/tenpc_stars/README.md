# Stars, brown dwarfs and white dwarfs within 10 parsecs

`tenpc_stars.cxt` — 456 objects described by 35 binary attributes, density 0.236.
Rebuilt by `build_contexts.py` from
`Datasets/stars_exoplanets/tenpc_stars_source.csv` and verified identical to the
context produced by the original pipeline.

## Source

**Reylé, C., Jardine, K., Fouqué, P., Caballero, J. A., Smart, R. L., Sozzetti, A.
2021, "The 10 parsec sample in the Gaia era", A&A 650, A201**, with the update
**Reylé et al. 2022, 21st Cambridge Workshop on Cool Stars, Zenodo
doi:10.5281/zenodo.7669746, arXiv:2302.02810**. The object list is catalogue
version 2, CDS `J/A+A/650/A201`, as updated in August 2023.

## Why these objects

Membership is decided by one criterion: a parallax of at least 100 mas, that is a
distance of at most 10 parsecs. The 456 objects are every known star, brown dwarf
and white dwarf in that volume, at that catalogue version, and the planets of those
same hosts form the companion context in `../tenpc_exoplanets/`.

Three reasons for taking this particular volume:

- **It is curated object by object.** Multiplicity, companions, spectral types and
  planets were compiled deliberately rather than joined automatically, which is what
  makes the system-level attributes trustworthy.
- **It is as complete as any published census.** The sample was built as a
  quality-assurance test for the Gaia Catalogue of Nearby Stars, and the CNS5
  authors (**Golovin et al. 2023, A&A 670, A19**) describe it as the most complete
  of the catalogues they reviewed.
- **10 pc rather than the 25 pc of CNS5.** Completeness for cool brown dwarfs
  degrades with distance, and the closed-world reading needs attributes that are
  decided for every object. 10 pc is the largest published volume where that holds.

The sample is dominated by objects invisible to the naked eye: 329 of the 456 are
of spectral type M or later, and 85 are brown dwarfs. That is a property of a
distance-limited sample and not a selection made here.

## How the data were collected

The published version 2 table could not be downloaded in full, so the object list
was reconstructed from the complete version 1 table plus the explicit change list in
the version 2 paper: 10 entries removed, 11 added, and a handful of renamings and
class corrections. The reconstruction reproduces the published version 2 totals
exactly, 541 entries in 336 systems, and agrees with all 342 version 2 rows that
were available as a cross-check.

Every attribute is then a deterministic rule on the catalogue fields:

- **Spectral types** are mapped to a position on the OBAFGKMLTY sequence, so the
  temperature attributes form an ordinal chain rather than one attribute per class.
  White-dwarf types, which start with D, take no position on that sequence and are
  described by their own attributes instead.
- **System attributes** come from the catalogue's own system grouping: how many
  bodies share a system, which of them is brightest in Gaia G, and what kinds of
  companion are present.
- **Planet attributes** come from the companion exoplanet context, so *hosts
  transiting planet* and *hosts planet in conservative HZ* are consistent between
  the two contexts by construction.
- **Variability** is restricted to the 17 objects the version 2 paper reports as
  variable in Gaia DR3. Well-known flare stars such as Proxima are not among them,
  because the attribute is about Gaia DR3 and not about activity in general.

`Datasets/stars_exoplanets/README.md` is the fuller account: the complete version 1
to version 2 change list, the treatment of two brown dwarfs whose spectral types had
to be assigned, and the provenance of every planet parameter.

## Attributes, in the order they appear in the context

The count is the number of objects having the attribute.

### Physical nature

| # | Attribute | Rule | Count |
|---|---|---|---|
| 1 | hydrogen-burning star | catalogue class `*`, `LM` or `LM?` | 350 |
| 2 | brown dwarf | class `BD` or `BD?` | 85 |
| 3 | white dwarf | class `WD` or `WD?` | 21 |
| 4 | class unconfirmed (candidate) | the class ends in `?` | 37 |

### Temperature sequence, ordinal

| # | Attribute | Rule | Count |
|---|---|---|---|
| 5 | SpT on OBAFGKMLTY sequence | has a non-white-dwarf spectral type | 397 |
| 6 | SpT G or later | G0 or cooler | 385 |
| 7 | SpT K or later | K0 or cooler | 367 |
| 8 | SpT M or later | M0 or cooler | 329 |
| 9 | SpT M3.5 or later (fully convective) | approximate onset of full convection near 0.35 solar masses (Chabrier & Baraffe 1997) | 240 |
| 10 | SpT M7 or later (ultracool) | standard definition of ultracool dwarfs (Kirkpatrick, Henry & Irwin 1997) | 103 |
| 11 | SpT L or later | L0 or cooler | 82 |
| 12 | SpT T or later | T0 or cooler | 63 |
| 13 | SpT Y | class Y | 19 |

### Metallicity and activity

| # | Attribute | Rule | Count |
|---|---|---|---|
| 14 | subdwarf (sd/esd, metal-poor) | spectral type prefixed `sd` or `esd` | 3 |
| 15 | emission-line flag (e) in SpT | the catalogue spectral type carries the `e` suffix | 53 |
| 16 | Gaia DR3 variable (Reyle+2022) | one of the 17 objects reported as variable in Gaia DR3 | 17 |

### White-dwarf spectral features

| # | Attribute | Rule | Count |
|---|---|---|---|
| 17 | WD spectral type known | the spectral type starts with D | 20 |
| 18 | WD hydrogen atmosphere (DA) | primary letter A (Sion et al. 1983) | 9 |
| 19 | WD metal lines (Z) | letter Z anywhere | 5 |
| 20 | WD carbon features (Q) | letter Q anywhere | 5 |
| 21 | WD featureless (DC) | primary letter C | 2 |
| 22 | WD magnetic (P/H) | suffix P or H | 4 |

### Multiplicity and role

| # | Attribute | Rule | Count |
|---|---|---|---|
| 23 | member of multiple system | its system has at least 2 non-planetary bodies | 209 |
| 24 | member of system with >=3 bodies | at least 3 bodies | 79 |
| 25 | primary (brightest) of multiple system | brightest member by Gaia G, measured where available, ties broken by earlier spectral type | 89 |

### Companion types

| # | Attribute | Rule | Count |
|---|---|---|---|
| 26 | has hydrogen-burning companion | another star in the same system | 185 |
| 27 | has brown-dwarf companion | a brown dwarf in the same system | 31 |
| 28 | has white-dwarf companion | a white dwarf in the same system | 9 |

### Planet hosting

| # | Attribute | Rule | Count |
|---|---|---|---|
| 29 | hosts confirmed planet | at least one of the 85 planets orbits it | 48 |
| 30 | hosts >=2 confirmed planets | at least two | 26 |
| 31 | hosts transiting planet | one of its planets transits | 8 |
| 32 | hosts planet in conservative HZ | one of its planets lies in the conservative habitable zone | 12 |
| 33 | member of planet-hosting system | any body of its system hosts a planet | 64 |

### Observational

| # | Attribute | Rule | Count |
|---|---|---|---|
| 34 | within 5 pc | distance at most 5 pc, that is parallax at least 200 mas | 72 |
| 35 | G magnitude measured by Gaia | a measured Gaia G exists; false for stars too bright for Gaia, for the faintest Y and late-T dwarfs, and for unresolved companions | 343 |

## Caveats

- **The emission flag is about the catalogue, not the star.** A dot means the
  spectral type carries no `e`, which depends on the source of the classification.
- **Fully convective at M3.5** is a spectral-type stand-in for a mass boundary.
- **Candidate classes stay candidates.** Attribute 4 marks them rather than
  promoting or dropping them, so the object count is not quietly changed.
- **The snapshot is fixed at catalogue version 2.** Later discoveries, such as the
  Barnard's Star planets of 2024 and 2025, are not present, though planet
  *parameters* in the companion context come from a 2026 table.

## References

Reylé et al. 2021, A&A 650, A201 · Reylé et al. 2022, Zenodo
doi:10.5281/zenodo.7669746 · Golovin et al. 2023, A&A 670, A19 · Chabrier & Baraffe
1997, A&A 327, 1039 · Kirkpatrick, Henry & Irwin 1997, AJ 113, 1421 · Kirkpatrick
2005, ARA&A 43, 195 · Cushing et al. 2011, ApJ 743, 50 · Sion et al. 1983, ApJ 269,
253 · Eyer et al. 2023, A&A 674, A13.

# Scales of this context

Fourteen scale-measures, built by `../build_scales.py` and verified by
`../verify_scale.py`. The groupings, with the reason for each and the candidates
rejected, are in `groupings.md` beside this file, fixed before any drawing. The
machine-readable summaries are `manifest.csv` and `nesting.csv`.

| Scale | Kind | One sentence | Attributes | Concepts | Width | Height | Drawn |
|---|---|---|---|---|---|---|---|
| `tenpc_stars_nature` | facet, step 1 | what kind of object it is | 4 | 8 | 4 | 4 | no |
| `tenpc_stars_nature_spectral` | chain, step 2 | each kind of object placed on the temperature sequence | 13 | 26 | 5 | 12 | yes |
| `tenpc_stars_nature_spectral_wd` | chain, step 3 | and the white dwarfs split into their classes | 19 | 35 | 9 | 12 | yes |
| `tenpc_stars_spectral` | facet | where it sits on the temperature sequence | 9 | 10 | 1 | 10 | no |
| `tenpc_stars_wd` | facet | the white-dwarf classes | 6 | 11 | 5 | 5 | no |
| `tenpc_stars_planets` | facet | its planets | 5 | 9 | 3 | 6 | no |
| `tenpc_stars_company` | facet | the system it belongs to | 6 | 20 | 6 | 7 | yes |
| `tenpc_stars_knowledge` | facet | what the catalogue records about how it is seen | 5 | 14 | 5 | 5 | yes |
| `tenpc_stars_spectral_planets` | apposition | which kinds of stars host planets | 14 | 36 | 7 | 11 | yes |
| `tenpc_stars_spectral_knowledge` | apposition | how completely each kind of object is catalogued | 14 | 57 | 10 | 12 | yes |
| `tenpc_stars_company_planets` | apposition | its companions and its planets | 11 | 60 | 16 | 9 | yes |
| `tenpc_stars_spectral_company` | apposition | multiplicity along the temperature sequence | 15 | 109 | 16 | 14 | yes |
| `tenpc_stars_physical` | apposition | everything about the object and its system, setting aside how it is catalogued | 30 | 311 | 54 | 15 | yes |
| `tenpc_stars` | full | the data themselves, the identity scale-measure | 35 | 732 | 130 | 16 | yes |

## Why these scales

**The groups are the README's own**, with catalogue facts kept apart from the
object, as the Caveats above ask. The emission-line flag is "about the catalogue,
not the star", the candidate flag says a class is unconfirmed, the Gaia variability
flag says what Gaia DR3 reported, and distance and Gaia photometry say how an
object is seen from here; together they form *knowledge*. The subdwarf flag says
what kind of object it is and joins *nature*. Distance is treated the same way in
the companion exoplanet context, since it is the same fact about the same systems.

**There is one real hierarchy, built as a chain.** Classification goes from what
kind of object it is, to its spectral type, which covers everything but white
dwarfs, to the white dwarfs' own classes. Each step keeps everything before it. The
first step has only 8 concepts and is recorded but not drawn; the last step grows
only 1.35 times, because only 21 objects are white dwarfs, and is flagged as a
shallow transition.

**The spectral sequence alone is never drawn.** Every spectral class contains the
next (G or later contains K or later, and so on), so its lattice is a chain of
width 1: there is nothing for a layout algorithm to arrange. It enters the
drawable scales in combination with something else.

**Every apposition answers one question**, written as one sentence in the table.
`physical` is the mid-range root: every drawable physical view nests into it, and
it nests into the full context, as `capability_practice_making` does for
instruments. Two broader combinations were rejected as the physical view with
groups left out, with no question of their own, and knowledge joined to company or
to planets failed the one-sentence test.

## Nesting

37 nested pairs, of which 19 have both scales drawn: the classification chain
(26 into 35), every drawable physical view into `physical`, and every drawable
scale into the full context. `knowledge` nests into `spectral_knowledge` and the full
context only, as the one group that is not physical. For a ladder figure, `company`
(20) nests into `company_planets` (60), `physical` (311) and the full context (732).

## Two things to know when reading results

- **No drawable scale has two equivalent attributes**, so fdp is expected to draw
  all of them, and no object shares a name with an attribute.
- **The two smallest drawable scales are knowledge (14) and company (20).** A
  comparison from one of them carries little information when the scale it nests
  into is large; the permutation null accounts for that, and the ranking compares
  algorithms only on the same pair.

## What is computed from these scales

Of the 14 scales above, **10 are drawable** -- between 12 and 1000 concepts, with
width at least 3 -- from 14 to 732 concepts; the others are recorded and never
drawn. Of 37 nested pairs, **19 are usable**: both scales drawable, and sharing at
least 8 concepts. From these, `../../run_harness.py` computes:

- **a drawing of every drawable scale by each of the eight algorithms**, under a
  30-minute budget per drawing; one that does not happen is recorded as a failure,
  with its reason, and counted against the algorithm;
- **the quality of every drawing**, on the 14 metrics of the drawing-quality
  analysis;
- **the consistency of every usable pair**: whether each algorithm keeps the
  left-to-right order of the coarser scale's concepts in its drawing of the finer
  one, as Kendall tau against a permutation null;
- **this context's ranking of the algorithms**, which enters the overall ranking
  with the same weight as every other context.

The definitions are in `../README.md`, *Drawable and usable*; the results in
`../../drawings.csv`, `quality.csv`, `consistency.csv` and `ranking.csv`.

