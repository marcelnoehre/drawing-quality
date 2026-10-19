# Living Beings and Water

`living_beings_and_water.cxt` — 8 living beings described by 9 attributes,
19 concepts. Imported unchanged from the surrounding repository,
`contexts/real-world/original/living_beings_and_water.cxt` (see `.imported-from`).

## Source

The standard textbook example of formal concept analysis (Ganter and Wille), and the
running example of Hanika and Hirth's work on scale-measures, which publishes a
scale-measure of it. That makes it this project's **baseline**: the one context where
a scale chosen by someone else can be reproduced and checked.

## The context

| | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|---|---|---|---|---|---|---|---|---|---|
| Leech | × | × |  |  |  |  | × |  |  |
| Bream | × | × |  |  |  |  | × | × |  |
| Frog | × | × | × |  |  |  | × | × |  |
| Dog | × |  | × |  |  |  | × | × | × |
| Spike - weed | × | × |  | × |  | × |  |  |  |
| Reed | × | × | × | × |  | × |  |  |  |
| Bean | × |  | × | × | × |  |  |  |  |
| Maize | × |  | × | × |  | × |  |  |  |

| # | Attribute | Count |
|---|---|---|
| 1 | needs water to live | 8 |
| 2 | lives in water | 5 |
| 3 | lives on land | 5 |
| 4 | needs chlorophyll to produce food | 4 |
| 5 | two seed leaves | 1 |
| 6 | one seed leaf | 3 |
| 7 | can move around | 4 |
| 8 | has limbs | 3 |
| 9 | suckles its offspring | 1 |

# Scales of this context

| Scale | Kind | One sentence | Attributes | Concepts | Width | Height | Drawn |
|---|---|---|---|---|---|---|---|
| `living_beings_and_water_taxa` | apposition | plants and animals by where they live, and the mammals: Hanika and Hirth's published scale | 9 | 12 | 4 | 5 | yes |
| `living_beings_and_water` | full | the data themselves, the identity scale-measure | 9 | 19 | 6 | 6 | yes |

## The published scale, reproduced

`living_beings_and_water_taxa` is the scale-measure of Hanika and Hirth (the
"scale measures" paper, Fig. 2), built attribute for attribute. Its attributes are
original attributes or conjunctions of them, which they name as follows:

| Their name | Definition | Here |
|---|---|---|
| W | needs water to live | `needs water to live` |
| LW | lives in water | `lives in water` |
| plants | needs chlorophyll | `needs chlorophyll to produce food` |
| animals | can move around | `can move around` |
| land plants | lives on land ∧ plant | `lives on land ∧ needs chlorophyll to produce food` |
| water plants | lives in water ∧ plant | `lives in water ∧ needs chlorophyll to produce food` |
| land animal | lives on land ∧ animal | `lives on land ∧ can move around` |
| water animal | lives in water ∧ animal | `lives in water ∧ can move around` |
| mammal | animal ∧ suckles its offspring | `can move around ∧ suckles its offspring` |

The paper states that this scale reflects twelve of the nineteen concepts of the
context. Built here, it has **exactly 12 concepts**, is verified as a scale-measure,
and nests into the full context. That agreement is the end-to-end check this
context was kept for: the construction used throughout this project reproduces a
published expert scale on the authors' own example.

"Needs water to live" holds of all eight beings, so it adds no concept; it is kept
because the published scale includes it.

## Why only this scale

The baseline's job is to check the method, not to supply evidence: reproducing a
scale someone else published is the strongest check there is, and a scale devised
here would add nothing to it. At 12 to 19 concepts, every algorithm draws nearly the
same picture, so further views would add little to the ranking. Two were considered
and not built -- habitat with the plant attributes, and habitat with the animal
attributes, 12 concepts each -- since they overlap the published scale's idea at the
size where algorithms do not differ; and kingdom with habitat without conjunctions,
13 concepts, is a coarser copy of the published scale.

## Nesting

One nested pair, usable: the published scale into the full context.

## What is computed from these scales

Of the 2 scales above, **2 are drawable** -- between 12 and 1000 concepts, with width
at least 3 -- at 12 and 19 concepts. Of 1 nested pair, **1 is usable**: both scales
drawable, and sharing at least 8 concepts. From these, `../../run_harness.py`
computes:

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
