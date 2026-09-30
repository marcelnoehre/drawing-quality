# Olympic disciplines, 2024 to 2028

`olympics.cxt` — 70 Olympic disciplines described by 38 binary attributes, density
0.402. Built by `build_contexts.py` from
`Datasets/olympic_disciplines_2024_2026_2028_complete_matrix.csv` and its codebook.

## What this data set is

Each object is a *discipline*, the unit the International Olympic Committee uses
between a sport and an event. Aquatics is a sport; swimming, diving, water polo,
artistic swimming and marathon swimming are its disciplines; the 100 m freestyle is
an event. Disciplines are the right grain here because they are what the programme
of a Games actually lists, and because properties such as venue, equipment or
scoring are constant within a discipline and vary between them.

Each attribute is a property of the discipline as contested at the Olympics, stated
as a one-sentence rule in the codebook and answered yes or no for every discipline.
Where a property holds for some events of a discipline but not all, the codebook
resolves it explicitly: *Team events* and *Individual events*, for instance, are
separate attributes and a discipline can carry both, because most disciplines have
events of both kinds.

## Why this object set is closed
The object set is not a
selection of interesting sports; it is exactly the union of the official discipline
programmes of three consecutive Games:

- **Paris 2024** (Summer), including the additions of that cycle, among them
  breaking, sport climbing, skateboarding and surfing;
- **Milano-Cortina 2026** (Winter), including ski mountaineering, new for that
  edition;
- **Los Angeles 2028** (Summer), whose programme adds baseball, softball, cricket,
  flag football, squash and lacrosse sixes.

That gives 54 summer and 16 winter disciplines, 70 in total. Nothing was added
because it seemed interesting and nothing was dropped because it was awkward: the
IOC's programme decisions fix the boundary, and any other compiler starting from the
same three programmes would arrive at the same list.

The frame is a union across three Games rather than a single Games, so two edge
cases follow. Breaking appears because it was contested in 2024, although it is not
on the 2028 programme. Disciplines are counted once even when they appear in all
three. The attribute *Women's event in the frame* likewise means at least one
women's event somewhere in those three programmes, which is true of all but three
disciplines.

## How the data were collected

The matrix was assembled by hand for this project. The codebook was written first,
fixing all 38 attributes as definitions precise enough to be answered consistently,
and the disciplines were then scored against those definitions from the published
programmes and the governing bodies' competition rules. The source table also keeps
two descriptive columns, the governing sport and whether the discipline is summer or
winter; they are *not* attributes of the context, since including "Summer" as an
attribute would split the lattice trivially into two halves. They are kept in the
source file because they are useful for grouping later.

As with any hand-scored table, the values encode descriptions rather than
measurements, and some of them are judgements: *Major spectator sport* and
*Professional circuit* are the clearest cases. The codebook is what makes those
judgements inspectable.

## Attributes, in the order they appear in the context

The count is the number of disciplines having the attribute.

### Competition structure

| # | Attribute | Meaning | Count |
|---|---|---|---|
| 1 | Team events | The frame includes events in which two or more competitors share a single result. | 48 |
| 2 | Individual events | The frame includes events contested by single competitors. | 53 |
| 3 | Head to head | Opponents compete at the same time in the same space and can directly affect each other's performance. | 55 |
| 4 | Judged | The result depends on officials' assessment of execution, difficulty or style. | 19 |
| 5 | Measured | The result is settled by time, distance, weight or an equivalent objective measurement. | 29 |
| 6 | Physical contact | Deliberate bodily contact with an opponent is a normal part of play. | 14 |

### Equipment

| # | Attribute | Meaning | Count |
|---|---|---|---|
| 7 | Ball | Play uses a ball. | 19 |
| 8 | Handheld implement | A bat, racket, club, stick, bow, blade, rifle, oar, pole or ski pole is held and used. | 28 |
| 9 | Net or goal | A net or goal acts as a target or as a divider between sides. | 15 |
| 10 | Vehicle board or runner | Competitors ride a bike, boat, board, sled, pair of skis or pair of skates. | 27 |
| 11 | Helmet or head protection | A helmet, mask or comparable head protection is standard competition equipment. | 29 |
| 12 | Animal | An animal takes part in the competition. | 4 |

### Venue

| # | Attribute | Meaning | Count |
|---|---|---|---|
| 13 | Grass or turf | Normally contested on natural grass or an equivalent turf surface. | 13 |
| 14 | Indoor venue | The standard competition venue is indoors. | 29 |
| 15 | Ice or snow | Contested on ice or snow. | 16 |
| 16 | Water | Contested in or on water. | 12 |
| 17 | Outdoor venue | Normally contested in the open air. | 42 |
| 18 | Fixed marked area | Contested inside a pitch, court, rink, ring, arena or lane of standardised dimensions. | 35 |

### Physical demands

| # | Attribute | Meaning | Count |
|---|---|---|---|
| 19 | Endurance | Sustained aerobic endurance is a principal physical demand. | 34 |
| 20 | Explosive power | Short bursts of maximal power are a principal physical demand. | 50 |
| 21 | Aim | Accuracy at a target, gate or hole is a central skill. | 18 |
| 22 | Running | Sustained running is a main activity. | 15 |
| 23 | Jumping | Jumping or aerial elements are a major scored or tactical component. | 23 |
| 24 | Weight classes | Competitors are divided into weight categories in at least one event in the frame. | 7 |

### Format and scoring

| # | Attribute | Meaning | Count |
|---|---|---|---|
| 25 | Clock | Play or a run is bounded by a fixed clock duration. | 26 |
| 26 | Fixed attempts | Contested over a predetermined number of rounds, attempts, ends, holes, innings, sets, heats or runs. | 51 |
| 27 | Points accumulate | The winner is the side that accumulates more points or goals. | 47 |
| 28 | Draw possible | A tie is a legitimate final result under standard rules. | 11 |
| 29 | Turn taking | Competitors act in turn rather than simultaneously. | 35 |

### Institutional profile

| # | Attribute | Meaning | Count |
|---|---|---|---|
| 30 | Olympic debut before 1950 | The discipline was first contested at an Olympic Games before 1950. | 39 |
| 31 | Professional circuit | Supports full-time professional athletes through leagues, tours or prize circuits. | 43 |
| 32 | Major spectator sport | Regularly draws mass television or stadium audiences outside the Olympics. | 22 |
| 33 | School sport | Commonly played in school physical education or school competition. | 19 |

### Origins and participation

| # | Attribute | Meaning | Count |
|---|---|---|---|
| 34 | British or Irish origin | The modern codified form originated in Britain or Ireland. | 17 |
| 35 | American origin | The modern codified form originated in North or South America. | 20 |
| 36 | Asian origin | The modern codified form originated in Asia. | 2 |
| 37 | Codified before 1900 | The modern rules of the discipline were codified before 1900. | 36 |
| 38 | Women's event in the frame | At least one women's event in this discipline appears in the frame. | 67 |

## Objects

**Summer, Paris 2024 programme (48):** Swimming, Marathon swimming, Diving,
Artistic swimming, Water polo, Archery, Athletics, Badminton, Basketball, 3x3
basketball, Boxing, Breaking, Canoe sprint, Canoe slalom, Road cycling, Track
cycling, Mountain biking, BMX racing, BMX freestyle, Dressage, Eventing, Jumping,
Fencing, Football, Golf, Artistic gymnastics, Rhythmic gymnastics, Trampoline,
Handball, Field hockey, Judo, Modern pentathlon, Rowing, Rugby sevens, Sailing,
Shooting, Skateboarding, Sport climbing, Surfing, Table tennis, Taekwondo, Tennis,
Triathlon, Volleyball, Beach volleyball, Weightlifting, Freestyle wrestling,
Greco-Roman wrestling.

**Added for Los Angeles 2028 (6):** Baseball, Softball, Cricket, Flag football,
Squash, Lacrosse sixes.

**Winter, Milano-Cortina 2026 programme (16):** Biathlon, Bobsleigh, Skeleton,
Curling, Ice hockey, Luge, Figure skating, Speed skating, Short track speed skating,
Alpine skiing, Cross-country skiing, Freestyle skiing, Nordic combined, Ski jumping,
Snowboarding, Ski mountaineering.

## Caveats

- **One pair shares an identical attribute set**: BMX freestyle and skateboarding.
  Both are judged, board- or bike-based, outdoor, explosive disciplines, and nothing
  in this codebook separates them. They remain distinct objects in one concept.
- **Discipline boundaries follow the IOC, not common usage.** Bobsleigh and skeleton
  are separate disciplines of one sport; dressage, eventing and jumping are three
  disciplines of equestrian.
- **Frame-level attributes read "in at least one event".** Weight classes, team and
  individual events, and women's events are all of this kind, so a cross does not
  mean every event of the discipline has the property.
- **Institutional attributes are judgements about the present day**, and *Major
  spectator sport* in particular depends on which country one is standing in.

---

# Scales of this context

Fifteen scale-measures, built by `../build_scales.py` and verified by
`../verify_scale.py`. The groupings, with the reason for each and the candidates
rejected, are in `groupings.md` beside this file, fixed before any drawing. The
machine-readable summaries are `manifest.csv` and `nesting.csv`.

These are not one cumulative chain. Each is a view answering a single question,
plus two refinement chains where the hierarchy is real and four appositions where
the combined view is one somebody would ask for. The seven facets are the
codebook's own groups, used unchanged: every one of them clears the floor on its
own, so none had to be merged.

| Scale | Kind | One sentence | Attributes | Concepts | Width | Height | Drawable |
|---|---|---|---|---|---|---|---|
| `origins` | facet | where the modern form was codified, and whether women contest it | 5 | 12 | 4 | 5 | yes |
| `institution` | facet | its standing: age, professionalism, audience, schools | 4 | 16 | 6 | 5 | yes |
| `venue` | facet | where it is contested and on what surface | 6 | 18 | 7 | 5 | yes |
| `format` | facet | how play is bounded and scored | 5 | 18 | 5 | 6 | yes |
| `equipment` | facet | what is carried, ridden or played with | 6 | 21 | 7 | 6 | yes |
| `structure` | facet | how the contest is organised and how a winner is settled | 6 | 28 | 8 | 7 | yes |
| `demands` | facet | what the discipline asks of the body | 6 | 35 | 12 | 6 | yes |
| `decision-structure` | chain, step 1 | how the result is settled, each way split by who contests it | 12 | 35 | 10 | 8 | yes |
| `equipment-medium` | chain, step 2 | equipment split by the medium it is used in | 15 | 53 | 18 | 7 | yes |
| `decision-structure-format` | chain, step 2 | those branches split again by how play is bounded | 18 | 64 | 15 | 11 | yes |
| `institution-origins` | apposition | where the discipline came from and what standing it has now | 9 | 81 | 20 | 9 | yes |
| `venue-equipment` | apposition | what the ground you play on requires you to carry or ride | 12 | 98 | 31 | 9 | yes |
| `structure-format` | apposition | the rules of the contest: how it is run and how it is decided | 11 | 139 | 33 | 11 | yes |
| `venue-equipment-demands` | apposition | the physical side of competing: the surface underfoot, the gear in hand and the effort required | 18 | 444 | 126 | 11 | yes |
| `olympics` | full | the data themselves | 38 | 10463 | – | – | **no** |

## The full lattice: motivation, not material

70 disciplines and 38 attributes produce **10463 concepts**. That is the argument
for scaling in one number, and a far better one than the 421-concept example the
literature uses: the data are ordinary, the attributes are all decidable, and the
lattice is still twenty times past anything that can be drawn.

It is therefore marked `drawable = False` in the manifest and **must never be fed
to a layout run**. Its width and height are left empty; at 10463 concepts a
Dilworth matching would need some 55 million pair comparisons, and it is not drawn,
so it does not need them. Enumerating its extents, which is what nesting requires,
takes under half a second.

`venue-equipment-demands` at 444 concepts is the drawable root that replaces it:
the largest view of this data that a layout algorithm can still take, and the one
where the algorithms are most stressed.

## Nesting

Thirty of the 210 ordered pairs nest. Fourteen of them have the full lattice on
the finer side and are therefore **not usable**: nesting is set inclusion and costs
nothing to compute, but nothing is ever drawn from a scale outside the band. That
leaves **16 usable pairs**, each nested, each sharing at least eight concepts, and
both sides drawable.

| Coarser | Finer | Concepts | Shared | Ratio |
|---|---|---|---|---|
| `decision-structure` | `decision-structure-format` | 35 → 64 | 35 | 1.83 |
| `equipment-medium` | `venue-equipment` | 53 → 98 | 53 | 1.85 |
| `decision-structure-format` | `structure-format` | 64 → 139 | 64 | 2.17 |
| `equipment` | `equipment-medium` | 21 → 53 | 21 | 2.52 |
| `decision-structure` | `structure-format` | 35 → 139 | 35 | 3.97 |
| `venue-equipment` | `venue-equipment-demands` | 98 → 444 | 98 | 4.53 |
| `equipment` | `venue-equipment` | 21 → 98 | 21 | 4.67 |
| `structure` | `structure-format` | 28 → 139 | 28 | 4.96 |
| `institution` | `institution-origins` | 16 → 81 | 16 | 5.06 |
| `venue` | `venue-equipment` | 18 → 98 | 18 | 5.44 |
| `origins` | `institution-origins` | 12 → 81 | 12 | 6.75 |
| `format` | `structure-format` | 18 → 139 | 18 | 7.72 |
| `equipment-medium` | `venue-equipment-demands` | 53 → 444 | 53 | 8.38 |
| `demands` | `venue-equipment-demands` | 35 → 444 | 35 | 12.69 |
| `equipment` | `venue-equipment-demands` | 21 → 444 | 21 | 21.14 |
| `venue` | `venue-equipment-demands` | 18 → 444 | 18 | 24.67 |

Because the levels nest, the shared concepts are exactly the coarser view's, so
each overlap equals its concept count. None falls below the floor of eight.

Two of those pairs are worth noticing in advance. `equipment-medium` nests inside
`venue-equipment` although one is a chain step and the other an apposition: the
conjunctions of the chain are intersections the apposition already has. And the
typology chain reaches `structure-format` from two directions, at ratios 2.17 and
3.97, which gives the same coarse view two different refinement routes.

## What each scale keeps and drops

The seven facets are the codebook's groups, so each facet scale drops every
attribute outside its own group; all 38 appear somewhere.

- **`decision-structure`** keeps only Judged, Measured and Points accumulate as
  plain attributes. Individual events, Team events, Head to head and Physical
  contact appear only inside conjunctions, never alone.
- **`decision-structure-format`** adds six three-way conjunctions. Clock, Fixed
  attempts, Draw possible and Turn taking likewise appear only inside them.
- **`equipment-medium`** keeps the six equipment attributes and adds nine
  conjunctions with a venue attribute; the venue attributes never appear alone.
- The four appositions keep their components' attributes unchanged.

## A note on the venue facet

`Ice or snow` is not the winter programme, which is deliberately not an attribute,
but it is very nearly the same split: sixteen disciplines against fifty-four. It
will dominate the venue scale and everything appositioned with it. That is
expected, and worth saying when the diagrams are read.
