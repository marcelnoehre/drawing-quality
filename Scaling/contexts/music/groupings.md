# Groupings

Every grouping used to build a scale, with the reason it was chosen, written
**before any drawing**. Nothing here may be revised after drawing results are
seen. We choose the scales and then evaluate drawings on them, so this file is
what separates a considered choice from one tuned to the answer.

Scale attributes are original attributes or conjunctions of them, never
disjunctions or negations.

---

## music

Recorded 2026-10-15T15:58:38+02:00, from `contexts/music/music.cxt`, 31 objects and 11
attributes, imported unchanged from the surrounding repository. Reviewed and
approved before this record was written; no scale of this context had been drawn.

### Groups

| Group | Adjectives | What it describes |
|---|---|---|
| motion | fast, lively, sprightly, rhythmizing | how the piece moves: tempo and rhythm |
| form | well-rounded, well-balanced, structured thoroughly, transparent | how it is built: proportion, craft, clarity of texture |
| character | dramatic, strong, playful | what it expresses |

*Playful* is a mood, so character; *sprightly* is the energy of the movement, so
motion. Well-rounded and well-balanced hold of the same 15 pieces and are kept
apart, as the data has them.

### Scales

| Scale | Groups | Concepts | The view, in one sentence | Drawn |
|---|---|---|---|---|
| `music_motion` | motion | 12 | How the piece moves: its tempo and rhythm. | yes |
| `music_form` | form | 5 | How it is built. | no, below 12 |
| `music_character` | character | 6 | What it expresses. | no, below 12 |
| `music_form_character` | form + character | 27 | How it is built against what it expresses. | yes |
| `music_motion_character` | motion + character | 42 | Its temperament: how it moves and what it expresses. | yes |
| `music_motion_form` | motion + form | 53 | How it moves against how it is built. | yes |
| `music` | all | 163 | The data themselves. | yes |

### No refinement chain

No adjective is a kind of another.

### Rejected

| Candidate | Why not |
|---|---|
| an energy grouping: strong, lively, fast, sprightly | mixes tempo with expression, so each view would answer two questions |
| merging well-rounded and well-balanced | edits the data to suit one algorithm |

### Result

Seven scales, five of them drawable, 12 nested pairs of which 6 are usable. fdp is
expected to fail on the three drawable scales containing the form group, which have
two equivalent attributes. No object shares a name with an attribute.
