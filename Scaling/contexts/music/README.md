# Music

`music.cxt` — 31 pieces of Western art music described by 11 adjectives
about how they sound. Imported unchanged from the surrounding repository,
`contexts/real-world/original/music.cxt` (see `.imported-from`).

## Source

From Ganter, B., Wille, R. and Stumme, G. (eds., 2005), *Formal Concept Analysis:
Foundations and Applications*, LNCS 3626, Springer, p. 22, per the metadata of the
public FCA context repository (`fcatools/contexts`, `music_en`, "music and their
characteristics"). The adjectives are judgements of how each piece sounds, not
measurements; their German originals are *abgerundet, ausgewogen, dramatisch,
durchsichtig, gründlich gestaltet, kraftvoll, lebhaft, spritzig, rhythmisierend,
schnell, verspielt*.

## Attributes, by what they describe

The count is the number of pieces having the attribute.

### Motion

| # | Attribute | Count |
|---|---|---|
| 10 | fast | 16 |
| 7 | lively | 24 |
| 8 | sprightly | 11 |
| 9 | rhythmizing | 16 |

### Form

| # | Attribute | Count |
|---|---|---|
| 1 | well-rounded | 15 |
| 2 | well-balanced | 15 |
| 5 | structured thoroughly | 24 |
| 4 | transparent | 23 |

### Character

| # | Attribute | Count |
|---|---|---|
| 3 | dramatic | 14 |
| 6 | strong | 24 |
| 11 | playful | 15 |

**Well-rounded and well-balanced hold of exactly the same 15 pieces.** In this data
the two judgements never come apart, so every scale containing both has two
equivalent attributes. They are kept apart, as the data has them: merging them
would edit the data, and that they coincide is itself worth knowing.

## Objects

Beethoven: Romance for violin and orchestra F-major; Bach: Contrapunctus I; Chajkovskij: Piano concerto b flat minor, 1st movement; Mahler: 2nd Symphony, 2nd movement; Bartok: Concert for ochestra; Beethoven: 9th symphony, 4th movement (presto); Bach: WTP 1, prelude c minor; Bach: 3rd Brandenburg Concerto, 3rd movement; Ligeti: Continuum; Mahler: 9th symphony, 2nd movement (Ländler); Beethoven: Moonlight sonata, 3rd movement; Hindemith: Chamber music No.1, finale; Bizet: Suite arlesienne; Mozart: Figaro, overture; Schubert: Wayfarer fantasy; Beethoven: Spring sonata, 1st movement; Bach: WTP 1, fuge c minor; Shostakovich: 15th symphony, 1st movement; Wagner: Mastersinger, overture; Beethoven: String quartet op.131, final movement; Johann Strauß: Spring voice waltz; Mozart: Il Seragio, “O, how I will triumph ...”; Bach: Mathew's passion No.5 (choir); Brahms: Intermezzo op. 117, No.2; Wagner: Ride of the valkyries; Mozart: Magic flute, “The hell revenge rages ...”; Mendelsohn: 4th symphony, 4th movement; Brahms: 4th symphony, 4th movement; Beethoven: Great fuge op. 133; Goretzky: Lament symphony; Verdi: Requiem, dies irae.

# Scales of this context

Seven scale-measures, built by `../build_scales.py` and verified by
`../verify_scale.py`. The groupings, with the reason for each and the candidates
rejected, are in `groupings.md` beside this file, fixed before any drawing. The
machine-readable summaries are `manifest.csv` and `nesting.csv`.

| Scale | Kind | One sentence | Attributes | Concepts | Width | Height | Drawn |
|---|---|---|---|---|---|---|---|
| `music_motion` | facet | how the piece moves: its tempo and rhythm | 4 | 12 | 4 | 5 | yes |
| `music_form` | facet | how it is built: proportion, craft, clarity of texture | 4 | 5 | 2 | 4 | no |
| `music_character` | facet | what it expresses | 3 | 6 | 2 | 4 | no |
| `music_form_character` | apposition | how it is built against what it expresses | 7 | 27 | 7 | 7 | yes |
| `music_motion_character` | apposition | its temperament: how it moves and what it expresses | 7 | 42 | 11 | 8 | yes |
| `music_motion_form` | apposition | how it moves against how it is built | 8 | 53 | 15 | 8 | yes |
| `music` | full | the data themselves, the identity scale-measure | 11 | 163 | 41 | 10 | yes |

## Why these scales

**The groups are by what an adjective describes**: how the piece moves, how it is
built, and what it expresses. Two adjectives needed a judgement. *Playful*
(*verspielt*) names a mood, so it belongs to character, not to tempo. *Sprightly*
(*spritzig*) names the energy of the movement, so it belongs to motion.

**Form and character are recorded but not drawn**: with 5 and 6 concepts they are
below the drawable minimum. Motion, at 12, is drawn. Each pair of groups gives one
view, and the three pairs are the natural ones: temperament (motion and
character), and construction set against either.

**An "energy" grouping was rejected** -- strong, lively, fast and sprightly against
the rest -- because it mixes tempo with expression, so each view would answer two
questions at once.

**There is no refinement chain**: no adjective is a kind of another.

## Nesting

12 nested pairs, of which 6 have both scales drawn. `motion` (12) nests into
`motion_character` (42), `motion_form` (53) and the full context (163); each of the
three pairwise views nests into the full context. A ladder figure here has three
columns: `motion`, `motion_form`, `music`.

## Two things to know when reading results

- **fdp will fail on every scale containing the form group** -- `form_character`,
  `motion_form` and the full context -- because well-rounded and well-balanced are
  equivalent, and fdp never terminates on equivalent attributes. It is recorded
  and penalised like any other failure. fdp draws `motion` and `motion_character`.
- **This is the smallest scaled context**, with 6 usable pairs. It counts as much as
  any other context in the overall ranking, so its result is the least precise of
  the contexts that weigh equally.

## What is computed from these scales

Of the 7 scales above, **5 are drawable** -- between 12 and 1000 concepts, with width
at least 3 -- from 12 to 163 concepts; the others are recorded and never drawn. Of 12
nested pairs, **6 are usable**: both scales drawable, and sharing at least 8
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
