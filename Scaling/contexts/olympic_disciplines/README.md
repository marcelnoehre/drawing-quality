# Olympic disciplines

`olympic_disciplines.cxt` — 50 Olympic disciplines described by 19 binary
attributes about their place in the Olympic programme. Imported unchanged from the
surrounding repository, `contexts/real-world/original/olympic_disciplines.cxt` (see
`.imported-from`).

## Source

The file came without documentation, and none was found in the surrounding
repository. What follows is read from the file itself. The objects are 50
disciplines named "Sport - Discipline"; the presence of karate, surfing,
skateboarding, sport climbing, 3x3 basketball and baseball/softball, and the absence
of breaking and of every winter discipline, matches the Summer programme of Tokyo
2020. That is an inference from the object list, not a documented fact. The
thresholds on the number of Games and of events are taken as given.

## How it relates to `olympics`

Our own `olympics` context describes nearly the same disciplines -- 48 of these 50,
36 under the same name and 12 worded differently ("Cycling - Track" against "track
cycling"); only karate, kata and kumite, is absent from ours -- but asks something
else. Ours describes what a sport *is*: its equipment, the physical
demands, how a result is settled, where it came from. This one describes the
discipline's **place in the programme**: which genders compete, how many medal
events it carries, how many Games it has been part of, whether it has a Paralympic
counterpart. Only individual or team competition and indoor or outdoor venue appear
in both. The two are complementary descriptions of a similar set of objects, not
duplicates, and are scaled independently.

## Attributes, by what they are about

The count is the number of disciplines having the attribute.

### Who may compete

| # | Attribute | Count |
|---|---|---|
| 1 | female only events | 46 |
| 4 | male only events | 45 |
| 3 | mixed events | 10 |
| 7 | open events | 3 |

### Competition format

| # | Attribute | Count |
|---|---|---|
| 6 | individual competition | 39 |
| 15 | team competition | 31 |

### Venue

| # | Attribute | Count |
|---|---|---|
| 2 | indoor events | 24 |
| 10 | outdoor events | 26 |

### Kind of sport

| # | Attribute | Count |
|---|---|---|
| 11 | water sport | 12 |
| 12 | ball game | 13 |
| 17 | combat sport | 11 |
| 18 | athletic sport | 43 |

### Olympic history, ordinal

| # | Attribute | Count |
|---|---|---|
| 16 | part of >= 8 olympics | 33 |
| 8 | part of >= 16 olympics | 25 |
| 14 | part of >= 24 olympics | 21 |

### Size of the programme, ordinal

| # | Attribute | Count |
|---|---|---|
| 13 | >= 5 events | 21 |
| 9 | >= 10 events | 13 |
| 19 | >= 20 events | 2 |

### Paralympics

| # | Attribute | Count |
|---|---|---|
| 5 | has paralympic equivalent | 20 |

## Objects

Judo - Judo, Aquatics - Swimming, Sport Climbing - Sport Climbing, Cycling - Track, Golf - Golf, Handball - Handball, Rugby - Rugby Sevens, Volleyball - Volleyball, Baseball/Softball - Baseball/Softball, Cycling - Mountain Bike, Karate - Kumite, Cycling - BMX Racing, Modern Pentathlon - Modern Pentathlon, Fencing - Fencing, Aquatics - Diving, Aquatics - Water Polo, Table Tennis - Table Tennis, Gymnastics - Rhythmic, Aquatics - Artistic Swimming, Volleyball - Beach Volleyball, Surfing - Surfing, Equestrian - Dressage, Equestrian - Jumping, Basketball - Basketball, Aquatics - Marathon Swimming, Gymnastics - Artistic, Tennis - Tennis, Boxing - Boxing, Rowing - Rowing, Taekwondo - Taekwondo, Karate - Kata, Canoe - Slalom, Wrestling - Freestyle, Shooting - Shooting, Sailing - Sailing, Football - Football, Triathlon - Triathlon, Archery - Archery, Equestrian - Eventing, Badminton - Badminton, Weightlifting - Weightlifting, Cycling - Road, Skateboarding - Skateboarding, Wrestling - Greco Roman, Athletics - Athletics, Basketball - 3x3, Gymnastics - Trampoline, Hockey - Hockey, Cycling - BMX Freestyle, Canoe - Sprint.

# Scales of this context

Eight scale-measures, built by `../build_scales.py` and verified by
`../verify_scale.py`. The groupings, with the reason for each and the candidates
rejected, are in `groupings.md` beside this file, fixed before any drawing. The
machine-readable summaries are `manifest.csv` and `nesting.csv`.

| Scale | Kind | One sentence | Attributes | Concepts | Width | Height | Drawn |
|---|---|---|---|---|---|---|---|
| `olympic_disciplines_competitors` | apposition | who competes: which genders may enter, and whether alone or in a team | 6 | 17 | 5 | 7 | yes |
| `olympic_disciplines_standing` | apposition | its place in the Games: how long on the programme, how many medal events, a Paralympic counterpart | 7 | 22 | 5 | 8 | yes |
| `olympic_disciplines_discipline` | apposition | what kind of sport it is and where it is contested | 6 | 25 | 9 | 6 | yes |
| `olympic_disciplines_sport_competitors` | apposition | which kinds of sport are contested by whom, alone or in teams | 10 | 57 | 13 | 9 | yes |
| `olympic_disciplines_sport_standing` | apposition | which kinds of sport hold what place in the programme | 11 | 103 | 22 | 11 | yes |
| `olympic_disciplines_competitors_standing` | apposition | how far the programme opens each discipline to women, men and mixed teams, against how established and large it is | 13 | 113 | 19 | 14 | yes |
| `olympic_disciplines_discipline_competitors` | apposition | the discipline as it is contested, setting aside its place in the Games | 12 | 122 | 24 | 10 | yes |
| `olympic_disciplines` | full | the data themselves, the identity scale-measure | 19 | 529 | 88 | 15 | yes |

## Why these scales

**The groups are by what an attribute is about**: who may enter, alone or in a team,
where, what kind of sport, and how established the discipline is in the Games. No
single group can be drawn on its own: entry and sport have 7 and 11 concepts, and
the number-of-Games and number-of-events bands are ordinal, chains of width 1 with
nothing to lay out. So the scales are combinations, each answering one question.

**Standing merges three small groups** -- the history bands, the programme-size
bands and the Paralympic flag -- because together they answer one question: how
established the discipline is in the Olympic movement.

**`competitors_standing` is the view this data is best placed for.** How far the
programme opens each discipline to women, men and mixed teams, against how long
and how large it has been, is a live question: mixed events are recent additions,
and the newer disciplines carry most of them.

**`discipline_competitors` is the mid-range root**, everything about the discipline
as it is contested, setting aside its place in the Games.

**There is no refinement chain.** The bands are hierarchies already built into the
attributes, and the one natural hierarchy, sport into discipline ("Cycling - Track",
"Cycling - Road"), exists only in the object names, never in an attribute.

## Nesting

14 nested pairs, every one usable. For a ladder figure, `competitors` (17) nests into
`sport_competitors` (57), `discipline_competitors` (122) and the full context (529).

## What is computed from these scales

Of the 8 scales above, **8 are drawable** -- between 12 and 1000 concepts, with
width at least 3 -- from 17 to 529 concepts. Of 14 nested pairs, **14 are usable**:
both scales drawable, and sharing at least 8 concepts. From these,
`../../run_harness.py` computes:

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
