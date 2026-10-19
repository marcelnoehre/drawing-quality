# Groupings

Every grouping used to build a scale, with the reason it was chosen, written
**before any drawing**. Nothing here may be revised after drawing results are
seen. We choose the scales and then evaluate drawings on them, so this file is
what separates a considered choice from one tuned to the answer.

Scale attributes are original attributes or conjunctions of them, never
disjunctions or negations.

---

## seasoning_planner

Recorded 2026-10-16T09:25:39+02:00, from `contexts/seasoning_planner/seasoning_planner.cxt`,
56 objects and 37 attributes, imported unchanged from the surrounding repository.
Proposed on 15 October and approved before this record was written. No scale of
this context had been drawn.

The groups follow the standard culinary split: **herbs** are the leaves of a plant,
and **spices** are every other part (seed, fruit, bark, flower, root, bulb). Spices
are split further by plant part. Seeds and fruits form one group. Bark, flower
parts, roots and bulbs are too few to stand alone, so they are merged into one
group, as small groups were merged in the exoplanet context. This grouping rests on
botany, not on a judgement of flavour.

### Groups

| Group | Attributes | Count |
|---|---|---|
| herbs (leaves) | basil, mugwort, savory, tarragon, bay leaves, marjoram, oregano, rosemary, thyme | 9 |
| seeds and fruits | anise, coriander, caraway, white pepper, black pepper, allspice, juniper, nutmeg, vanilla, cayenne, sweet paprika, hot paprika | 12 |
| other parts | cinnamon (bark), cloves (bud), saffron (stigma), ginger and turmeric (rhizome), garlic (bulb), curry | 7 |
| dish | the nine categories: vegetables, meat, poultry, fish, potatoes, rice, sauces, pastry and desserts, miscellaneous | 9 |

Three placements needed a judgement:
- **Curry** (*Curry gemahlen*) is curry powder, a blend. It is not curry leaves,
  which are sold whole and named *Curryblätter*. It is a spice, so it goes with the
  other spices.
- **Mugwort, rosemary and bay** are sold ground or whole here rather than rubbed.
  They are leaves all the same, so they are herbs.
- **Nutmeg** is a seed and **vanilla** a fruit pod, and they are grouped that way.

"Spices" below means seeds and fruits together with the other parts. Every dish is
in exactly one category.

### Scales

| Scale | Groups | Concepts | The view, in one sentence | Drawn |
|---|---|---|---|---|
| `seasoning_planner_dish` | dish | 11 | The dish categories alone. | no, below 12 |
| `seasoning_planner_herbs` | herbs | 39 | Which herbs go on the same dishes. | yes |
| `seasoning_planner_seeds` | seeds and fruits | 80 | Which seed and fruit spices go on the same dishes. | yes |
| `seasoning_planner_other` | other parts | 37 | Which bark, flower, root and bulb spices go on the same dishes. | yes |
| `seasoning_planner_spices` | seeds + other | 219 | The spices, with the herbs set aside. | yes |
| `seasoning_planner_herbs_dish` | herbs + dish | 84 | Which herbs go with which kind of dish. | yes |
| `seasoning_planner_spices_dish` | spices + dish | 304 | Which spices go with which kind of dish. | yes |
| `seasoning_planner_seasonings` | herbs + spices | 421 | The whole seasoning chart, without the dish categories. | yes |
| `seasoning_planner` | all | 532 | The data themselves. | yes |

### No refinement chain

Each dish category is a block of dishes, so a conjunction like "thyme ∧ meat" is the
meet of two attributes that are both already in `herbs_dish`. It adds nothing that
scale does not already have.

### Rejected

| Candidate | Why not |
|---|---|
| seeds + dish (154), other + dish (78) | they split "which spices for which dish" by plant part, which no cook asks about; `spices_dish` covers the question |
| herbs + seeds (237), herbs + other (113) | halves of `seasonings` with no question of their own |
| Hanika and Hirth's published scales (vegetables + desserts; meat) | object-side scales, and the shipped data differ from the papers' data, so they would not reproduce |
| grouping by flavour (hot, sweet, aromatic) | a judgement with no source |

### Result

Nine scales, eight of them drawable. There are 20 nested pairs, of which 17 are
usable (both scales drawn). No scale has two equivalent attributes, so fdp should
not hang on any of them. No object shares a name with an attribute.

The papers report 421 concepts for this context, and the shipped file gives 532.
`seasonings`, which is the shipped file without the dish categories, has exactly
421. That suggests the papers may have counted the seasonings alone. We note this as
a coincidence, not a claim.
