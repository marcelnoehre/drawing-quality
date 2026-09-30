# Musical instruments

`instruments.cxt` — 64 musical instruments described by 42 binary attributes,
density 0.229. Built by `build_contexts.py` from
`Datasets/musical_instruments_matrix.csv` and its codebook.

## What this data set is

Each object is a musical instrument, taken as a type rather than a specific
physical instrument: *Violin* means the violin as it is normally built and played,
not one violin. Each attribute is a property of that type, stated as a one-sentence
rule in the codebook and answered yes or no for every instrument.

The attributes cover nine facets: how the sound is produced, how the vibration is
excited, how pitch is controlled, what the instrument can do musically, whether it
is electric, where it is conventionally used, how it is held or carried, what it is
made of, and where and when it came from.

## Why these 64 instruments

The object set is chosen, not found; there is no catalogue of "all instruments" to
be volume-limited against. It was assembled so that the context is varied enough to
be interesting and small enough to be scaled by hand:

- **All four Hornbostel–Sachs families are present**, and not only as tokens: 15
  chordophones, 24 aerophones, 8 membranophones, 15 idiophones. Some instruments
  carry two family attributes, which is why the counts exceed 64.
- **The Western concert core is complete enough to be recognisable.** Every regular
  member of the symphony orchestra is present (28 instruments carry that attribute),
  which matters because several attributes, such as *Transposing* or *Symphony
  orchestra*, only make sense against that tradition.
- **Non-European instruments are included on purpose** (17 of them: sitar, erhu,
  shakuhachi, djembe, taiko, cajón, kalimba, steelpan, didgeridoo and others), so
  that the origin attributes separate real groups rather than marking a handful of
  exceptions.
- **Electric and electronic instruments are included** (theremin, synthesizer,
  Hammond organ, electric guitar, electric bass), so the electrification attributes
  are populated on both sides.
- **Near-duplicates were mostly avoided.** One saxophone stands for the family, one
  harmonica for free-reed mouth instruments. The few pairs that remain are
  deliberate: violin and viola, electric guitar and electric bass, snare and bass
  drum differ in register or size rather than in any property this codebook records.
- **Every attribute is non-trivial.** No attribute is true of all 64 instruments or
  of none, so no column is redundant in the lattice.

## How the data were collected

The matrix was assembled by hand for this project. There is no upstream catalogue:
the codebook was written first, fixing each of the 42 attributes as a definition
precise enough to be answered consistently, and the instruments were then scored
against those definitions from standard reference descriptions of each instrument.
The family attributes follow the Hornbostel–Sachs classification. The musical
capability attributes follow ordinary playing practice rather than extended
technique, and the convention attributes describe what is usual, not what is
possible.

Two consequences follow, and both matter when the results are read:

- The values encode **conventional descriptions**, not measurements. *Commonly used
  in jazz* or *Regular member of the standard symphony orchestra* are judgements
  that a different compiler might make differently at the margins.
- Because the attributes were written before the instruments were scored, the
  scoring could not be tuned to produce a convenient lattice. That is the reason the
  codebook exists as a separate file.

## Attributes, in the order they appear in the context

The count is the number of instruments having the attribute.

### Sound production family (Hornbostel–Sachs)

| # | Attribute | Meaning | Count |
|---|---|---|---|
| 1 | Chordophone | The sound-producing vibration comes from one or more stretched strings. | 15 |
| 2 | Aerophone | The sound-producing vibration is that of air itself, either an enclosed air column or a free reed. | 24 |
| 3 | Membranophone | The sound-producing vibration is that of a stretched membrane. | 8 |
| 4 | Idiophone | The body of the instrument itself vibrates to produce the sound. | 15 |

### Excitation method

| # | Attribute | Meaning | Count |
|---|---|---|---|
| 5 | Bowed | The strings are normally set in motion with a bow. | 5 |
| 6 | Plucked | The strings are normally set in motion by plucking or strumming, by fingers, plectrum or an internal quill mechanism. | 9 |
| 7 | Hammered strings | The strings are normally set in motion by hammers or beaters. | 1 |
| 8 | Single reed | Sound is excited by one or more beating single reeds under the player's control. | 4 |
| 9 | Double reed | Sound is excited by a double reed. | 4 |
| 10 | Free reed | Sound is produced by free reeds vibrating in a frame, with no associated air column. | 3 |
| 11 | Lip excited | Sound is excited by the player's buzzing lips. | 8 |
| 12 | Edge or fipple blown | Sound is excited by an air stream directed against a sharp edge or through a fipple, with no reed and no lip buzzing. | 6 |
| 13 | Mouth blown | The player supplies air directly with the mouth, into or across the instrument or a blowpipe. | 21 |
| 14 | Bellows or bag | Air is supplied by bellows, a blower or an air-reservoir bag rather than by the mouth alone. | 4 |
| 15 | Struck with implement | Normally sounded by striking with sticks, mallets or beaters. | 12 |
| 16 | Struck with hands | Normally sounded by striking with the bare hands or fingers. | 5 |
| 17 | Shaken or clashed | Normally sounded by shaking, or by clashing two parts of the instrument together. | 4 |

### Pitch control mechanism

| # | Attribute | Meaning | Count |
|---|---|---|---|
| 18 | Frets | The fingerboard carries frets or comparable fixed stopping points. | 7 |
| 19 | Valves | Pitch is changed with piston or rotary valves. | 6 |
| 20 | Slide | Pitch is changed with a movable slide. | 1 |
| 21 | Finger holes | The instrument has tone holes closed by the fingers directly or by keys. | 11 |
| 22 | Keyboard | The instrument is played from a piano-style keyboard of keys. | 8 |
| 23 | Pedals | One or more foot pedals are part of normal playing technique. | 10 |

### Pitch and tonal capability

| # | Attribute | Meaning | Count |
|---|---|---|---|
| 24 | Definite pitch | Produces a clearly recognisable musical pitch rather than an indefinite-pitched sound. | 51 |
| 25 | Fully chromatic | All twelve semitones are available throughout the instrument's normal range in ordinary playing. | 45 |
| 26 | Three or more simultaneous pitches | A single player can sound at least three different pitches at the same moment. | 21 |
| 27 | Continuously variable pitch | Pitch can be varied smoothly across a wide span rather than only in fixed steps. | 9 |
| 28 | Sustaining | A note can be held at steady volume for as long as the player continues the exciting action. | 32 |

### Electrification

| # | Attribute | Meaning | Count |
|---|---|---|---|
| 29 | Requires electricity | The instrument cannot produce its normal sound without electrical power. | 5 |
| 30 | Electrical sound | The sound reaching the listener is generated or transduced electrically rather than radiated acoustically by the instrument itself. | 5 |

### Musical practice and convention

| # | Attribute | Meaning | Count |
|---|---|---|---|
| 31 | Symphony orchestra | A regular member of the standard symphony orchestra. | 28 |
| 32 | Concert or marching band | A regular member of the standard Western wind band. | 24 |
| 33 | Jazz | Commonly used in jazz ensembles. | 20 |
| 34 | Rock and pop | Commonly used in rock and popular-music bands. | 13 |
| 35 | Transposing | Music is conventionally written at a pitch other than it sounds, including octave transpositions. | 15 |

### Ergonomics and mobility

| # | Attribute | Meaning | Count |
|---|---|---|---|
| 36 | Played seated | The instrument's design or size normally requires or strongly favours playing while seated. | 25 |
| 37 | Marching or processional | Commonly played while marching or moving in procession. | 18 |

### Construction and materials

| # | Attribute | Meaning | Count |
|---|---|---|---|
| 38 | Wooden body | The body or main resonating structure is made primarily of wood, bamboo or cane. | 42 |
| 39 | Metal body | The body or main sounding structure is made primarily of metal. | 18 |
| 40 | Resonator | Has a hollow soundbox, shell, soundboard or tuned resonator that amplifies a separately vibrating element (false for aerophones). | 29 |

### Origin and history

| # | Attribute | Meaning | Count |
|---|---|---|---|
| 41 | Non European origin | The instrument in its recognised form developed in a tradition outside Europe. | 17 |
| 42 | Post 1900 | The instrument came into existence after 1900. | 7 |

## Objects

Violin, Viola, Cello, Double bass, Concert harp, Classical guitar, Electric guitar,
Electric bass guitar, Ukulele, Banjo, Mandolin, Sitar, Erhu, Piano, Harpsichord,
Celesta, Pipe organ, Hammond organ, Harmonium, Accordion, Diatonic harmonica,
Concert flute, Piccolo, Recorder, Panpipes, Shakuhachi, Oboe, English horn,
Bassoon, Clarinet, Bass clarinet, Alto saxophone, Highland bagpipes, Trumpet,
Flugelhorn, French horn, Trombone, Euphonium, Tuba, Sousaphone, Didgeridoo,
Timpani, Snare drum, Bass drum, Bongos, Congas, Djembe, Taiko, Cajon, Tambourine,
Triangle, Crash cymbals, Tam-tam, Maracas, Castanets, Xylophone, Marimba,
Vibraphone, Glockenspiel, Tubular bells, Steelpan, Kalimba, Theremin, Synthesizer.

## Caveats

- **Four pairs share an identical attribute set**: violin and viola, electric guitar
  and electric bass guitar, Hammond organ and synthesizer, snare drum and bass drum.
  They differ in register, size or sound-generation detail, none of which this
  codebook records. They remain distinct objects and sit in the same concept.
- **Convention attributes are period- and place-bound.** *Symphony orchestra*,
  *Concert or marching band*, *Jazz* and *Rock and pop* describe present-day Western
  practice and would have been scored differently a century ago.
- **Family attributes can overlap.** Instruments such as the steelpan or the piano
  raise classification questions, and an instrument may carry two family attributes
  where the standard classification genuinely splits.
- **Nothing here is measured.** A reviewer is entitled to disagree with individual
  cells; the codebook is what makes such disagreement specific rather than vague.

---

# Scales of this context

Eleven scale-measures, built by `../build_scales.py` and verified by
`../verify_scale.py`. The groupings, with the reason for each and the candidates
rejected, are in `groupings.md` beside this file, fixed before any drawing. The
machine-readable summaries are `manifest.csv` and `nesting.csv`.

These are not one cumulative chain. Each is a view answering a single question,
plus one refinement chain where the hierarchy is real and four appositions where
the combined view is one somebody would ask for. The largest of those,
`capability-practice-making`, is the mid-range root: at 319 concepts it is the
biggest view below the full lattice, and it is defined by one idea rather than a
list, everything about the instrument except how its sound is produced.

| Scale | Kind | One sentence | Attributes | Concepts | Width | Height |
|---|---|---|---|---|---|---|
| `excitation` | facet | how the sound is set going | 13 | 21 | 13 | 5 |
| `capability` | facet | what the instrument can play | 5 | 13 | 4 | 6 |
| `practice` | facet | where and how it is played, including posture and mobility | 7 | 46 | 16 | 8 |
| `making` | facet | what it is made of, where it came from, whether it needs power | 7 | 17 | 6 | 6 |
| `family-excitation` | chain, step 1 | each family split by how it is excited | 19 | 27 | 15 | 6 |
| `family-excitation-mechanism` | chain, step 2 | those branches split again by the pitch mechanism they use | 30 | 33 | 17 | 6 |
| `playing-mechanism` | apposition | the mechanics of playing: how sound starts and how pitch is chosen | 19 | 35 | 16 | 6 |
| `family-making` | apposition | which families are built from which materials | 11 | 39 | 14 | 6 |
| `family-practice` | apposition | which families populate which ensembles | 11 | 107 | 35 | 9 |
| `capability-practice-making` | apposition | the instrument as a musician meets it, setting aside how the sound is produced | 19 | 319 | 81 | 12 |
| `instruments` | full | the data themselves, the identity scale-measure | 42 | 576 | 138 | 14 |

Width is the largest antichain, by Dilworth's theorem the number of concepts
minus a maximum matching of the strict inclusion order over all comparable pairs.
It is not the size of the largest rank, which is a different and smaller number.

## What each scale keeps and drops

The facets are the codebook's own groups, merged where a group is too small to be
a view on its own, so each facet scale drops every attribute outside its group.
Nothing is dropped from the data as a whole: all 42 attributes appear in at least
one scale.

- **`excitation`** keeps the 13 excitation-method attributes.
- **`capability`** keeps definite pitch, fully chromatic, three or more
  simultaneous pitches, continuously variable pitch, sustaining.
- **`practice`** keeps the four ensemble attributes, transposing, played seated
  and marching or processional.
- **`making`** keeps wooden body, metal body, resonator, non European origin,
  post 1900, requires electricity, electrical sound.
- **`family-excitation`** keeps the four families and adds fifteen conjunctions,
  one per family-and-excitation pair that occurs.
- **`family-excitation-mechanism`** adds eleven further conjunctions of three
  attributes. All six pitch-control attributes appear, but only inside a branch:
  `Frets` only as `Chordophone ∧ Plucked ∧ Frets`, never alone.
- **`playing-mechanism`** keeps excitation and pitch control as plain attributes.
- **`family-making`** and **`family-practice`** keep the four families plus the
  seven attributes of the other facet.

The exact conjunctions are listed in `groupings.md`.

## Two things to know when reading results

**Pitch control and family are not scales of their own.** Alone they give 9 and 7
concepts, under the floor of 10 to 12 where every algorithm draws the same
picture. They survive inside the chain and the appositions.

**The second chain step is shallow**, 27 to 33 concepts, a ratio of 1.22, flagged
in the manifest as a low-ratio transition. It is kept deliberately: whether a
transition that shallow moves any drawing metric is something to measure, not to
assume.

## Nesting

Seventeen of the 110 ordered pairs nest, and all seventeen are usable: each shares
at least eight concepts and both sides are drawable, the full context included at
576 concepts. Ten have the full context on the finer side. The other seven come
from real relationships:

| Coarser | Finer | Concepts | Shared | Ratio |
|---|---|---|---|---|
| `family-excitation` | `family-excitation-mechanism` | 27 → 33 | 27 | 1.22 |
| `excitation` | `playing-mechanism` | 21 → 35 | 21 | 1.67 |
| `making` | `family-making` | 17 → 39 | 17 | 2.29 |
| `practice` | `family-practice` | 46 → 107 | 46 | 2.33 |
| `practice` | `capability-practice-making` | 46 → 319 | 46 | 6.94 |
| `making` | `capability-practice-making` | 17 → 319 | 17 | 18.77 |
| `capability` | `capability-practice-making` | 13 → 319 | 13 | 24.54 |

Because the levels nest, the shared concepts are exactly the coarser view's, so
each overlap equals its concept count. None falls below the floor of eight.

One nesting that might be expected does **not** hold: raw `excitation` is not
nested under `family-excitation`. "Struck with implement" spans the membranophone
and idiophone branches, so its extent is a union of two conjunction extents, and a
union need not be an extent. `groupings.md` records this as provenance for why the
chain starts at family.
