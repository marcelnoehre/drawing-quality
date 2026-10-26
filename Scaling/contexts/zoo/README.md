# Zoo

`zoo.cxt` — 101 animals described by 43 attributes: sixteen traits and the
animal's zoological class, each variable nominally scaled into its values. Imported
from the surrounding repository, `contexts/real-world/original/zoo.cxt` (see
`.imported-from`), **with its attribute labels corrected on import**; every
incidence is unchanged.

## Source

The file came without documentation. It is the *Zoo* data set of the UCI Machine
Learning Repository (Forsyth, 1990): 101 animals, fifteen Boolean traits, the number
of legs, and a class from 1 to 7 (mammal, bird, reptile, fish, amphibian, insect,
invertebrate). The UCI file also has an animal-name column, which here became the
object names.

## The label correction

In the file as it is in the surrounding repository, **the first eleven yes/no
variables carry the label of the variable before them**, and the label "venomous"
is missing. It is not a format problem: the file is standard Burmeister, and both
readers used here, odis and ConceptFlow, parse it identically. The labels
themselves are wrong, and checking them against the animals settles it:

- `[hair 1]` held exactly the 20 birds, so it is feathers;
- `[eggs 1]` held exactly the 41 mammals, so it is milk;
- `[breathes 1]` held frog, honeybee, pit viper, scorpion, sea snake, sea wasp,
  stingray and wasp, so it is venomous;
- no fish had `[backbone 1]`, so it is breathes;
- `[animal-name 1]` held the leopard, the girl and the honeybee but not the termite,
  the carp or the chicken, so it is hair.

fins, legs, tail, domestic, catsize and type were correct.

| Label in the source | Corrected to |
|---|---|
| `animal-name` | **hair** |
| `hair` | **feathers** |
| `feathers` | **eggs** |
| `eggs` | **milk** |
| `milk` | **airborne** |
| `airborne` | **aquatic** |
| `aquatic` | **predator** |
| `predator` | **toothed** |
| `toothed` | **backbone** |
| `backbone` | **breathes** |
| `breathes` | **venomous** |

The correction is part of `../import_standard_contexts.py` (`LABEL_CORRECTIONS`), so
re-importing reproduces it rather than undoing it. Only labels change: the objects,
the incidences and therefore the lattice are exactly those of the source. The
surrounding repository's drawings and metrics are unaffected, since they never read
a label. The defect is described under *Defects found in the generators* in
`../../pipeline.md`.

The two equivalent attribute pairs earlier found in this context, `[hair 1]` with
`[type 2]` and `[eggs 1]` with `[type 1]`, were this mislabelling seen from another
side: they are feathers with bird and milk with mammal, facts of zoology.

## Attributes, by what they describe

The count is the number of animals having the attribute.

### Anatomy

| Attribute | Count |
|---|---|
| `[hair 0]` | 58 |
| `[hair 1]` | 43 |
| `[feathers 0]` | 81 |
| `[feathers 1]` | 20 |
| `[toothed 0]` | 40 |
| `[toothed 1]` | 61 |
| `[backbone 0]` | 18 |
| `[backbone 1]` | 83 |
| `[fins 0]` | 84 |
| `[fins 1]` | 17 |
| `[leg 0]` | 23 |
| `[leg 2]` | 27 |
| `[leg 4]` | 38 |
| `[leg 5]` | 1 |
| `[leg 6]` | 10 |
| `[leg 8]` | 2 |
| `[tail 0]` | 26 |
| `[tail 1]` | 75 |

### Physiology

| Attribute | Count |
|---|---|
| `[eggs 0]` | 42 |
| `[eggs 1]` | 59 |
| `[milk 0]` | 60 |
| `[milk 1]` | 41 |
| `[breathes 0]` | 21 |
| `[breathes 1]` | 80 |
| `[venomous 0]` | 93 |
| `[venomous 1]` | 8 |

### Ecology

| Attribute | Count |
|---|---|
| `[airborne 0]` | 77 |
| `[airborne 1]` | 24 |
| `[aquatic 0]` | 65 |
| `[aquatic 1]` | 36 |
| `[predator 0]` | 45 |
| `[predator 1]` | 56 |
| `[domestic 0]` | 88 |
| `[domestic 1]` | 13 |
| `[catsize 0]` | 57 |
| `[catsize 1]` | 44 |

### Class (UCI type: 1 mammal, 2 bird, 3 reptile, 4 fish, 5 amphibian, 6 insect, 7 invertebrate)

| Attribute | Count |
|---|---|
| `[type 1]` | 41 |
| `[type 2]` | 20 |
| `[type 3]` | 5 |
| `[type 4]` | 13 |
| `[type 5]` | 4 |
| `[type 6]` | 8 |
| `[type 7]` | 10 |

# Scales of this context

Ten scale-measures, built by `../build_scales.py` and verified by
`../verify_scale.py`. The groupings, with the reason for each and the candidates
rejected, are in `groupings.md` beside this file, fixed before any drawing. The
machine-readable summaries are `manifest.csv` and `nesting.csv`.

| Scale | Kind | One sentence | Attributes | Concepts | Width | Height | Drawn |
|---|---|---|---|---|---|---|---|
| `zoo_class` | facet | which zoological class it belongs to | 7 | 9 | 7 | 3 | no |
| `zoo_physiology` | facet | how its body works: reproduction, breathing, venom | 8 | 32 | 10 | 6 | yes |
| `zoo_class_physiology` | apposition | how each class reproduces, breathes and defends itself | 15 | 56 | 17 | 7 | yes |
| `zoo_anatomy` | facet | how the animal is built | 18 | 132 | 33 | 9 | yes |
| `zoo_ecology` | facet | how it lives: whether it flies or swims, hunts, is kept by people, how big it is | 10 | 135 | 42 | 7 | yes |
| `zoo_class_anatomy` | apposition | how each class of animal is built | 25 | 152 | 34 | 10 | yes |
| `zoo_class_ecology` | apposition | where and how each class of animal lives | 17 | 268 | 69 | 8 | yes |
| `zoo_anatomy_physiology` | apposition | the animal itself, inside and out, setting aside how it lives | 26 | 492 | 95 | 13 | yes |
| `zoo_physiology_ecology` | apposition | how its body's workings fit its way of life: breathing in water, venom for hunting | 18 | 781 | 157 | 11 | yes |
| `zoo` | full | the data themselves, the identity scale-measure | 43 | 4579 | — | — | no |

## Why these scales

**The groups are by what a trait describes**: how the animal is built, how its body
works, how it lives, and which class it belongs to. Each variable is taken whole,
with all its values.

**The full context is never drawn.** At 4579 concepts it is far beyond the drawable
limit, as the full olympics lattice is, so every drawn scale here is a view.

**Class adds little to anatomy**, 132 to 152 concepts: an animal's build largely
tells its class. That is a fact about animals, and the scales show it.

**The most natural view of adaptation is too large to draw.** Anatomy with ecology --
how an animal's build fits its way of life, fins for swimming, feathers for flying --
has 1927 concepts. Physiology with ecology, at 781, is the drawable view of the same
question, and the one built.

**There is no refinement chain**: class is a single level in this data, never
refined into orders or families.

## Nesting

19 nested pairs, of which 7 have both scales drawn. `physiology` (32) nests into
`class_physiology` (56), `anatomy_physiology` (492) and `physiology_ecology` (781), the
ladder for a figure; `anatomy` (132) into `class_anatomy` and `anatomy_physiology`;
`ecology` (135) into `class_ecology` and `physiology_ecology`. No drawn scale nests
into the full context, since it is not drawn.

## Two things to know when reading results

- **fdp fails on `class_physiology` and `class_anatomy`**, which contain the
  equivalent pairs milk and mammal, feathers and bird.
- **These are the largest drawn scales so far**, 492 and 781 concepts. The slower
  algorithms are expected to time out on them, which the budget records as
  failures.

## What is computed from these scales

Of the 10 scales above, **8 are drawable** -- between 12 and 1000 concepts, with width
at least 3 -- from 32 to 781 concepts; the others are recorded and never drawn. Of
19 nested pairs, **7 are usable**: both scales drawable, and sharing at least 8
concepts. From these, `../../run_harness.py` computes:

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
