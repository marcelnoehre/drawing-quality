# Groupings

Every grouping used to build a scale, with the reason it was chosen, written
**before any drawing**. Nothing here may be revised after drawing results are
seen. We choose the scales and then evaluate drawings on them, so this file is
what separates a considered choice from one tuned to the answer.

Scale attributes are original attributes or conjunctions of them, never
disjunctions or negations.

---

## zoo

Recorded 2026-10-15T16:10:15+02:00, from `contexts/zoo/zoo.cxt`, 101 objects and 43
attributes, imported from the surrounding repository with its attribute labels
corrected (see the README). Reviewed and approved before this record was written; no
scale of this context had been drawn. Every grouping below is by the corrected
labels.

### Groups

| Group | Variables | What it describes |
|---|---|---|
| anatomy | hair, feathers, toothed, backbone, fins, legs, tail | how the animal is built |
| physiology | eggs, milk, breathes, venomous | how its body works |
| ecology | airborne, aquatic, predator, domestic, catsize | how it lives |
| class | type: mammal, bird, reptile, fish, amphibian, insect, invertebrate | which class it belongs to |

Each variable is taken whole, with all its values.

### Scales

| Scale | Groups | Concepts | The view, in one sentence | Drawn |
|---|---|---|---|---|
| `zoo_class` | class | 9 | Which zoological class it belongs to. | no, below 12 |
| `zoo_physiology` | physiology | 32 | How its body works: reproduction, breathing, venom. | yes |
| `zoo_class_physiology` | class + physiology | 56 | How each class reproduces, breathes and defends itself. | yes |
| `zoo_anatomy` | anatomy | 132 | How the animal is built. | yes |
| `zoo_ecology` | ecology | 135 | How it lives: whether it flies or swims, hunts, is kept by people, how big it is. | yes |
| `zoo_class_anatomy` | class + anatomy | 152 | How each class of animal is built. | yes |
| `zoo_class_ecology` | class + ecology | 268 | Where and how each class of animal lives. | yes |
| `zoo_anatomy_physiology` | anatomy + physiology | 492 | The animal itself, inside and out, setting aside how it lives. | yes |
| `zoo_physiology_ecology` | physiology + ecology | 781 | How its body's workings fit its way of life: breathing in water, venom for hunting. | yes |
| `zoo` | all | 4579 | The data themselves. | no, above 1000 |

### No refinement chain

Class is a single level in this data, never refined into orders or families.

### Rejected

| Candidate | Why not |
|---|---|
| anatomy + ecology (1927 concepts) | the most natural view of adaptation, but above the drawable limit; physiology + ecology asks the same question and is drawn |
| anatomy + physiology + ecology (4569) | above the drawable limit |
| class alone (9) | below 12 concepts |

### Result

Ten scales, eight of them drawable, 19 nested pairs of which 7 are usable. fdp is
expected to fail on `class_physiology` and `class_anatomy`, which hold the equivalent
pairs milk and mammal, feathers and bird. No object shares a name with an attribute.
