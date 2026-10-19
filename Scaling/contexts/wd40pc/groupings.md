# Groupings

Every grouping used to build a scale, with the reason it was chosen, written
**before any drawing**. Nothing here may be revised after drawing results are
seen. We choose the scales and then evaluate drawings on them, so this file is
what separates a considered choice from one tuned to the answer.

Scale attributes are original attributes or conjunctions of them, never
disjunctions or negations.

---

## wd40pc

Recorded 2026-10-15T15:47:20+02:00, from `contexts/wd40pc/wd40pc.cxt`, 1078 objects
and 28 attributes. Reviewed and approved before this record was written; no scale of
this context had been drawn.

The groups follow the README's own sorting of the attributes, with the principle
used for both 10 pc contexts: facts about how an object is seen are kept apart from
facts about the object. Knowledge is whether a Gaia fit exists and which of the two
nearer reference volumes, 20 pc and 10 pc, the white dwarf lies in; distance is
knowledge in all three of our astronomical contexts, for the same reason: it says
where an object is relative to us, and in a distance-limited sample it decides how
well an object is seen. IR-faint stays physical, since collision-induced absorption
is a property of the atmosphere. "Peculiar, warm or uncertain type" bundles a
physical fact (peculiar) with a knowledge fact (uncertain) in one attribute; it
cannot be split, so it stays with the spectral features.

### Groups

| Group | Attributes | What it is about |
|---|---|---|
| spectral | hydrogen lines (A); helium lines (B); featureless (DC); carbon (Q); metal lines (Z); magnetic; emission lines; peculiar, warm or uncertain | what its spectrum shows |
| atmosphere | hydrogen-dominated (fit); IR-faint | what its atmosphere is made of |
| mass | below 0.45, above 0.9, above 1.1 solar masses | how heavy |
| temperature | above 5000, 10500, 12500 K | how hot |
| age | cooling age above 0.1, 1, 10 Gyr | how long it has been cooling |
| binarity | wide binary; main-sequence, white-dwarf or brown-dwarf companion; three or more members; unresolved binary evidence | its company |
| knowledge | Gaia parameters available; within 20 pc; within 10 pc | how it is seen |

### Scales

| Scale | Kind | One sentence | Attributes | Concepts | Width | Height | Drawn |
|---|---|---|---|---|---|---|---|
| `wd40pc_atmosphere` | facet | what its atmosphere is made of | 2 | 4 | 2 | 3 | no |
| `wd40pc_mass` | facet | how heavy it is | 3 | 5 | 2 | 4 | no |
| `wd40pc_temperature` | facet | how hot it is | 3 | 4 | 1 | 4 | no |
| `wd40pc_age` | facet | how long it has been cooling | 3 | 4 | 1 | 4 | no |
| `wd40pc_knowledge` | facet | how it is seen: whether a fit exists, which reference volume it is in | 3 | 6 | 2 | 4 | no |
| `wd40pc_binarity` | facet | the company it keeps | 6 | 13 | 5 | 6 | yes |
| `wd40pc_spectral` | facet | what its spectrum shows | 8 | 30 | 12 | 5 | yes |
| `wd40pc_cooling` | apposition | where it is on its cooling track: how hot it still is and how long it has been cooling | 6 | 14 | 4 | 7 | yes |
| `wd40pc_mass_binarity` | apposition | whether its mass points to a binary past: low-mass and massive white dwarfs against their company | 9 | 23 | 9 | 7 | yes |
| `wd40pc_parameters` | apposition | its fitted physical parameters: how heavy, how hot, how old | 9 | 46 | 12 | 9 | yes |
| `wd40pc_appearance` | apposition | what its spectrum shows and what its atmosphere is made of | 10 | 47 | 19 | 6 | yes |
| `wd40pc_spectral_knowledge` | apposition | how completely each spectral class is characterised, and how much of it lies in the nearest volumes | 11 | 83 | 25 | 7 | yes |
| `wd40pc_appearance_temperature` | apposition | why it looks the way it does: its spectrum against how hot it is | 13 | 97 | 30 | 8 | yes |
| `wd40pc_parameters_binarity` | apposition | how mass, temperature and age relate to the company it keeps | 15 | 112 | 28 | 9 | yes |
| `wd40pc_appearance_parameters` | apposition | everything about the white dwarf itself, setting aside its company and how it is catalogued | 19 | 319 | 74 | 11 | yes |
| `wd40pc_physical` | apposition | everything about the white dwarf and its company, setting aside how it is catalogued | 25 | 534 | 123 | 12 | yes |
| `wd40pc` | full | the data themselves, the identity scale-measure | 28 | 728 | 154 | 13 | yes |

### Why these

- **Five facets are recorded, not drawn.** Atmosphere, mass and knowledge have 4 to
  6 concepts, below the drawable minimum of 12. Temperature and age are pure
  chains of width 1 -- every band contains the next -- so there is nothing to lay
  out. They enter the drawable scales in combination.
- **`appearance_temperature`** is the spectral-evolution question. Below 5000 K
  hydrogen lines vanish even in a hydrogen atmosphere, so such a white dwarf is
  classified featureless: what the spectrum shows depends on how hot it is.
- **`mass_binarity`** puts together what the README links: a white dwarf under
  0.45 solar masses cannot come from a single star within the age of the Galaxy,
  so it implies a binary past, and massive ones are often merger products.
- **`appearance_parameters` and `physical`** are the two broad views: the white dwarf
  itself, and the white dwarf with its company, both setting aside how it is
  catalogued. `physical` is the mid-range root.
- **`spectral_knowledge`** is this context's knowledge view, as `planet_knowledge`
  and `spectral_knowledge` are for the 10 pc contexts.

### No refinement chain

The hierarchies here -- the mass, temperature and age bands, and the companion
types under "wide binary" -- are already built into the attributes. Spectral
evolution is a dependency of what is seen on temperature, not a parent-child
relation, so it is an apposition, not a chain.

### Rejected

| Candidate | Why not |
|---|---|
| parameters + knowledge (73 concepts) | the same question as `spectral_knowledge`, asked of the parameters instead of the spectral classes |
| the single-group facets, drawn | below 12 concepts, or width 1 |

### Result

Seventeen scales, twelve of them drawable, 61 nested pairs of which 35 are usable
(both scales drawn). No drawable scale has two equivalent attributes, and no object
shares a name with an attribute. Ladders for a figure: `spectral` (30) into
`appearance` (47), `appearance_temperature` (97), `appearance_parameters` (319) and
`physical` (534); or `binarity` (13) into `mass_binarity` (23),
`parameters_binarity` (112) and `physical`.

As with the habitable zone in the exoplanet context, two named bands have no
concept in any scale: the ZZ Ceti instability strip, 10500 to 12500 K, and the
typical-mass band, 0.45 to 0.9 solar masses. Each would need a negation. Making the
scales interordinal would be a change to the data, which the README leaves as a
deliberate decision not yet taken.
