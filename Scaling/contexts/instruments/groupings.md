# Groupings

Every grouping used to build a scale, with the reason it was chosen, written
**before any drawing**. Nothing here may be revised after drawing results are
seen. We choose the scales and then evaluate drawings on them, so this file is
what separates a considered choice from one tuned to the answer.

Scale attributes are original attributes or conjunctions of them, never
disjunctions or negations.

---

## instruments

Recorded 2026-09-28T15:26:50+02:00, from
`contexts/instruments/instruments.cxt`, 64 objects and 42 attributes.
The facets below are the nine groups of the codebook, merged where a group is
too small to be a view on its own.

### Facet scales, each a plain attribute projection

| Scale | Grouping | Why |
|---|---|---|
| `excitation` | the 13 excitation-method attributes | How the sound is set going is the question an organologist asks first after the family, and it is the one facet that alone tells most instruments apart. |
| `capability` | the 5 pitch-and-tonal-capability attributes | What an instrument can play cuts across how it is built; a marimba and a piano meet here and nowhere else. |
| `practice` | the 5 musical-practice attributes plus the 2 ergonomics attributes | Where an instrument is played and how it is held are one question, that of the player's situation, and neither group is large enough to stand alone. |
| `making` | the 3 materials attributes, the 2 origin attributes, the 2 electrification attributes | What an instrument is made of, where it came from and whether it needs power are all questions about its physical provenance. |

### Refinement chain: the Hornbostel-Sachs taxonomy

The only hierarchy in this data that is genuinely a parent-child relation, so the
only one built as a chain. Each step adds a conjunct and keeps every ancestor.

| Step | Scale | Grouping | Why |
|---|---|---|---|
| 1 | `family-excitation` | the 4 families, plus each family conjoined with the excitation methods that occur in it | This is the classification's own structure: chordophones divide into bowed, plucked and struck, aerophones into reed, lip and edge, and so on. |
| 2 | `family-excitation-mechanism` | step 1, plus each branch conjoined with the mechanism it uses | The taxonomy keeps going: within lip-excited aerophones, valves and slide are the real division, and within plucked chordophones it is frets. |

A family-only scale was **not** emitted: four attributes give 7 concepts, below
the floor of 10 to 12, so it would not be a drawing problem. Family survives as
the root of this chain and inside two appositions.

### Appositions

Built only where the combined view has a one-sentence description that is not
just the two facets listed.

| Scale | Grouping | Why |
|---|---|---|
| `playing-mechanism` | excitation together with pitch control | The mechanics of playing are one subject: how the sound starts and how its pitch is chosen. It also carries pitch control, which gives only 9 concepts alone and so is not emitted on its own. |
| `family-making` | family together with making | Which families are built from which materials is where the woodwind and brass distinction actually lives, and it is a distinction with known awkward cases such as the saxophone. |
| `family-practice` | family together with practice | Which families populate the orchestra, the wind band, jazz and popular music is the orchestration question. |
| `capability-practice-making` | capability, practice and making | Everything about an instrument except how its sound is produced: what it can play, where it is played and what it is made of. One idea, the complement of the mechanism, rather than three facets listed. Built deliberately as the mid-range root, the largest view below the full lattice. |

### Rejected

| Candidate | Why not |
|---|---|
| family as a standalone scale | 7 concepts, under the floor. |
| pitch control as a standalone scale | 9 concepts, under the floor; kept inside `playing-mechanism`. |
| family conjoined with capability | Mostly degenerate: chordophone with definite pitch is every chordophone, aerophone with sustaining is every aerophone, and membranophone with fully chromatic, polyphonic or sustaining is empty. Capability is a facet, not a refinement of family. |
| capability together with practice | 132 concepts and a perfectly valid scale-measure, but its description is only the two facets joined, so it fails the test for an apposition. |
| family, capability, practice and making together | 414 concepts and a valid scale-measure, and it would have nested two more pairs, but adding family breaks the single idea: family *is* how the sound is produced, so the description falls back to a list. |
| one cumulative chain over all facets | Appositioning unrelated lenses produces valid scale-measures that nobody would describe in one sentence. Nesting is not a reason to build a view. |

### Provenance note on one nesting

The raw `excitation` scale is **not** nested under `family-excitation`, which is
why the chain begins at family rather than at excitation. The reason is in the
data: "Struck with implement" occurs in both the membranophone and the idiophone
branch, so its extent is the union of two conjunction extents, and a union need
not be an extent. This is a record of why the scales look the way they do, not a
result.

### Exact conjunctions

`family-excitation` adds, to the four family attributes:

    Chordophone ∧ Bowed          Aerophone ∧ Single reed        Membranophone ∧ Struck with implement
    Chordophone ∧ Plucked        Aerophone ∧ Double reed        Membranophone ∧ Struck with hands
    Chordophone ∧ Hammered strings   Aerophone ∧ Free reed      Idiophone ∧ Struck with implement
                                 Aerophone ∧ Lip excited        Idiophone ∧ Struck with hands
                                 Aerophone ∧ Edge or fipple blown   Idiophone ∧ Shaken or clashed
                                 Aerophone ∧ Mouth blown
                                 Aerophone ∧ Bellows or bag

`family-excitation-mechanism` adds, on top of those:

    Chordophone ∧ Plucked ∧ Frets            Aerophone ∧ Edge or fipple blown ∧ Finger holes
    Chordophone ∧ Plucked ∧ Pedals           Aerophone ∧ Single reed ∧ Finger holes
    Chordophone ∧ Hammered strings ∧ Keyboard    Aerophone ∧ Double reed ∧ Finger holes
    Aerophone ∧ Lip excited ∧ Valves         Aerophone ∧ Free reed ∧ Keyboard
    Aerophone ∧ Lip excited ∧ Slide          Idiophone ∧ Struck with implement ∧ Keyboard
                                             Idiophone ∧ Struck with implement ∧ Pedals

No other conjunctions are used. The facet and apposition scales carry original
attributes unchanged.
