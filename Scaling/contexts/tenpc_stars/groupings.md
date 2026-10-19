# Groupings

Every grouping used to build a scale, with the reason it was chosen, written
**before any drawing**. Nothing here may be revised after drawing results are
seen. We choose the scales and then evaluate drawings on them, so this file is
what separates a considered choice from one tuned to the answer.

Scale attributes are original attributes or conjunctions of them, never
disjunctions or negations.

---

## tenpc_stars

Recorded 2026-10-15T15:40:58+02:00, from `contexts/tenpc_stars/tenpc_stars.cxt`,
456 objects and 35 attributes. Reviewed and approved before this record was
written; no scale of this context had been drawn.

The groups follow the README's own sorting of the attributes, with one principle
carried over from the companion exoplanet context: facts about how an object is
catalogued or seen are kept apart from facts about the object. The README's own
caveats ask for this. It departs from the README's grouping in four places:

- the **emission-line flag** is, in the README's words, "about the catalogue, not
  the star", so it moves from *metallicity and activity* to knowledge;
- the **candidate flag** records that a classification is unconfirmed, not a
  property of the object, so it moves from *physical nature* to knowledge;
- the **Gaia variability flag** says an object was reported as variable in Gaia DR3,
  a catalogue statement, so it moves to knowledge;
- the **subdwarf flag** (metal-poor population) says what kind of object it is, so
  it joins *nature*.

**Distance.** "Within 5 pc" is in knowledge. It says where an object is relative to
us, not what kind of object it is, and in a distance-limited sample it is what
decides how well an object is seen. The README files it under *observational*,
which is the same judgement.

### Groups

| Group | Attributes | What it is about |
|---|---|---|
| nature | hydrogen-burning star; brown dwarf; white dwarf; subdwarf | what kind of object it is |
| spectral | on the OBAFGKMLTY sequence; G, K, M, M3.5 (fully convective), M7 (ultracool), L, T or later; Y | where it sits in the temperature sequence |
| wd | WD type known; DA; metal lines (Z); carbon features (Q); featureless (DC); magnetic | the white-dwarf classes |
| company | member of multiple system; of a system with three or more bodies; primary of it; has a hydrogen-burning, brown-dwarf or white-dwarf companion | the system it belongs to |
| planets | hosts a planet; two or more; a transiting one; one in the conservative HZ; member of a planet-hosting system | its planets |
| knowledge | class unconfirmed; emission-line flag; Gaia DR3 variable; within 5 pc; Gaia G measured | what the catalogue records about how it is seen |

### Refinement chain: the classification

The one hierarchy here that is genuinely parent and child: what kind of object,
then its spectral type, which classifies everything but white dwarfs, then the
white dwarfs by their own classes (Sion et al. 1983). Each step keeps everything
before it.

| Step | Scale | Concepts | Why |
|---|---|---|---|
| 1 | `tenpc_stars_nature` | 8 | the classification's first division; below the drawable minimum, recorded only |
| 2 | `tenpc_stars_nature_spectral` | 26 | each kind of object placed on the temperature sequence |
| 3 | `tenpc_stars_nature_spectral_wd` | 35 | and the white dwarfs split into their classes |

Steps 2 to 3 grow only 1.35 times, flagged in the manifest as a shallow transition,
as instruments' 27 to 33 is: only 21 objects are white dwarfs.

### Facet scales

| Scale | Concepts | Drawn | Why |
|---|---|---|---|
| `tenpc_stars_spectral` | 10 | no | the temperature sequence alone is a pure chain, width 1: every type contains the next, so there is nothing to lay out |
| `tenpc_stars_wd` | 11 | no | below 12 concepts |
| `tenpc_stars_planets` | 9 | no | below 12 concepts |
| `tenpc_stars_company` | 20 | yes | the system it belongs to: how many bodies, its role, its companions |
| `tenpc_stars_knowledge` | 14 | yes | what the catalogue records about how it is seen |

### Appositions, each a view someone would ask for

| Scale | Groups | Concepts | The view, in one sentence |
|---|---|---|---|
| `tenpc_stars_spectral_planets` | spectral + planets | 36 | Which kinds of stars host planets. |
| `tenpc_stars_spectral_knowledge` | spectral + knowledge | 57 | How completely each kind of object is catalogued. |
| `tenpc_stars_company_planets` | company + planets | 60 | The system an object lives in: its companions and its planets. |
| `tenpc_stars_spectral_company` | spectral + company | 109 | Which kinds of objects come in company, and with what: multiplicity along the temperature sequence. |
| `tenpc_stars_physical` | nature + spectral + wd + company + planets | 311 | Everything about the object and its system, setting aside how it is catalogued. |

`physical` is the mid-range root, as `capability_practice_making` (319) is for
instruments: every drawable physical view nests into it, and it nests into the full
context. It is named by its idea rather than by the list of its five groups.

### Rejected

| Candidate | Why not |
|---|---|
| spectral + company + planets (192 concepts) | the physical view with two groups left out; no question of its own |
| nature + spectral + company + planets (298) | the same, without the white-dwarf classes |
| knowledge + company, knowledge + planets | no question beyond "how we know things about systems like these"; fails the one-sentence test |
| the spectral sequence, drawn | width 1 |

### Result

Fourteen scales, ten of them drawable, 37 nested pairs of which 19 are usable (both
scales drawn). No drawable scale has two equivalent attributes, so fdp is not
expected to fail on any of them, and no object shares a name with an attribute.
For the ladder figure, `company` (20) nests into `company_planets` (60),
`physical` (311) and the full context (732).
