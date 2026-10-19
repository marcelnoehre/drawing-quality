# Seasoning planner

`seasoning_planner.cxt` — 56 dishes and 37 attributes: 28 spices and herbs, and the
nine dish categories each dish belongs to ("…(Gruppierung)": vegetables, meat,
poultry, fish, potatoes, rice, sauces, pastry and desserts, miscellaneous). In
German. Imported unchanged from the surrounding repository, which took it from
conexp-clj's `testing-data/Seasoning-Planner.ctx`.

## Source

Two descriptions, which disagree on the origin:

- conexp-clj's context descriptions: "found in lecture notes of Gerd Stumme";
  "foods that are related to recommended seasonings based on a chart published by
  the spice company Fuchs Group" (https://github.com/tomhanika/conexp-clj/blob/master/testing-data/context-descriptions.org).
- the public FCA context repository, `fcatools/contexts`, `seasoningplanner_de`:
  Mahn, M. (2014), *Gewürze: Das Standardwerk*, Christian Verlag, München; "spices and
  herbs together and the meals they match".

The attributes need translation, not a codebook: they are spice names with their
form of sale (*gemahlen* ground, *gerebelt* rubbed, *ganz* whole) and the dish
categories. Hanika and Hirth use this context too, with 532 concepts in the shipped
file against 421 in their papers.

# Scales of this context

Nine scale-measures, built by `../build_scales.py` and verified by
`../verify_scale.py`. The groupings, with the reason for each and the candidates
rejected, are in `groupings.md` beside this file, fixed before any drawing. The
machine-readable summaries are `manifest.csv` and `nesting.csv`.

| Scale | Kind | One sentence | Attributes | Concepts | Width | Height | Drawn |
|---|---|---|---|---|---|---|---|
| `seasoning_planner_dish` | facet | the dish categories alone | 9 | 11 | 9 | 3 | no |
| `seasoning_planner_herbs` | facet | which herbs go on the same dishes | 9 | 39 | 13 | 7 | yes |
| `seasoning_planner_seeds` | facet | which seed and fruit spices go on the same dishes | 12 | 80 | 22 | 9 | yes |
| `seasoning_planner_other` | facet | which bark, flower, root and bulb spices go on the same dishes | 7 | 37 | 13 | 7 | yes |
| `seasoning_planner_spices` | apposition | the spices, with the herbs set aside | 19 | 219 | 61 | 10 | yes |
| `seasoning_planner_herbs_dish` | apposition | which herbs go with which kind of dish | 18 | 84 | 30 | 7 | yes |
| `seasoning_planner_spices_dish` | apposition | which spices go with which kind of dish | 28 | 304 | 89 | 11 | yes |
| `seasoning_planner_seasonings` | apposition | the whole seasoning chart, without the dish categories | 28 | 421 | 114 | 12 | yes |
| `seasoning_planner` | full | the data themselves, the identity scale-measure | 37 | 532 | 152 | 12 | yes |

## Why these scales

**The groups follow the culinary split between herbs and spices.** Herbs are the
leaves of a plant, and spices are every other part. Spices are then split by plant
part: seeds and fruits form one group, and bark, flower, root and bulb are merged
into another because each is too small to stand alone. This rests on botany, not on
a judgement of flavour. **Curry** here is curry powder, a blend rather than curry
leaves, so it goes with the spices. **The dish categories** form a group of their
own. With 11 concepts that group is below the drawable minimum, so it is recorded
but not drawn.

The appositions answer the questions a cook asks: which herbs, or which spices, go
with which kind of dish, and the whole seasoning chart with the categories set
aside. Splitting "which spices for which dish" by plant part was rejected, since no
cook asks it. **There is no refinement chain**: the dish categories partition the
dishes, so conjoining a seasoning with a category adds nothing to `herbs_dish` or
`spices_dish`.

## Nesting

20 nested pairs, of which 17 have both scales drawn. Two ladders run to the full
context: `herbs` (39) → `herbs_dish` (84) → `seasoning_planner` (532), and
`seeds` (80) → `spices` (219) → `spices_dish` (304) → `seasoning_planner`.

## Two things to know when reading results

- **No scale has two equivalent attributes**, so fdp is not expected to hang here.
- **`seasonings` has exactly 421 concepts**, the figure the papers give for this
  context, while the shipped file has 532. The papers may have counted the
  seasonings without the dish categories. This is a coincidence worth noting, not
  a claim.

## What is computed from these scales

Of the 9 scales above, **8 are drawable** -- between 12 and 1000 concepts, with width
at least 3 -- from 37 to 532 concepts; the other is recorded and never drawn. Of 20
nested pairs, **17 are usable**: both scales drawable, and sharing at least 8
concepts. From these, `../../run_harness.py` computes:

- **a drawing of every drawable scale by each of the eight algorithms**, under a
  30-minute budget per drawing; one that does not happen is recorded as a failure,
  with its reason, and counted against the algorithm;
- **the quality of every drawing**, on the 13 metrics of the drawing-quality
  analysis;
- **the consistency of every usable pair**: whether each algorithm keeps the
  left-to-right order of the coarser scale's concepts in its drawing of the finer
  one, as Kendall tau against a permutation null;
- **this context's ranking of the algorithms**, which enters the overall ranking
  with the same weight as every other context.

The definitions are in `../README.md`, *Drawable and usable*; the results in
`../../drawings.csv`, `quality.csv`, `consistency.csv` and `ranking.csv`.
