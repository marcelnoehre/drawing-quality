# Groupings — olympic disciplines

Every grouping used to build a scale of this context, with the reason it was
chosen, written **before any drawing**. Nothing here may be revised after drawing
results are seen. We choose the scales and then evaluate drawings on them, so this
file is what separates a considered choice from one tuned to the answer.

Scale attributes are original attributes or conjunctions of them, never
disjunctions or negations.

Recorded 2026-09-29T09:39:26+02:00, from `olympics.cxt`, 70 disciplines and 38
attributes. The facets are the seven groups of the codebook, used unchanged:
unlike the instruments context, every one of them is large enough to be a view on
its own, so none had to be merged.

## Facet scales, each a plain attribute projection

| Scale | Grouping | Why |
|---|---|---|
| `structure` | the 6 competition-structure attributes | How a contest is organised and how a winner is settled is the first thing anyone asks about a sport. |
| `demands` | the 6 physical-demand attributes | What the discipline asks of the body is the sport-science lens, and it cuts across every other grouping. |
| `equipment` | the 6 equipment attributes | What is carried, ridden or played with is what a spectator sees first and what a governing body regulates most. |
| `venue` | the 6 venue attributes | Where a discipline is contested and on what surface. |
| `format` | the 5 format-and-scoring attributes | How play is bounded and scored, which is what makes a contest finish. |
| `institution` | the 4 institutional-profile attributes | The discipline's standing: how old it is at the Games, whether it supports professionals, whether anyone watches, whether it is taught at school. |
| `origins` | the 5 origins-and-participation attributes | Where the modern form was codified, and whether women contest it in the frame. |

## Refinement chains

Built only where the parent-child relation is real.

### `typology`: how the result is settled, then by whom, then by the clock

The standard typology of sport: results are settled by judging, by measurement or
by accumulating points, and each of those divides by who contests it. Combat
appears as head-to-head with physical contact.

| Step | Scale | Grouping | Why |
|---|---|---|---|
| 1 | `decision-structure` | the three decision attributes, plus each conjoined with individual, team or head-to-head, plus head-to-head with physical contact | This is the classification sport science actually uses: judged, measured and game sports, each split by whether one person or a side competes. |
| 2 | `decision-structure-format` | step 1, plus each branch conjoined with the format that defines it | Timed races, fixed-attempt competitions and clocked team games are the real subdivisions within each branch. |

A decision-only level was **not** emitted: three attributes give 8 concepts, below
the floor of 10 to 12, so it would not be a drawing problem.

### `equipment-medium`: equipment, then what it is used on

| Step | Scale | Grouping | Why |
|---|---|---|---|
| 1 | `equipment` | the equipment facet, which doubles as the root of this chain | |
| 2 | `equipment-medium` | each equipment attribute conjoined with the surface or medium it is used in | The same six equipment attributes describe very different sports depending on the medium: a runner on ice, a boat on water and a ball on grass have nothing else in common. |

## Appositions

Built only where the combined view has a one-sentence description that is not
just the two facets listed.

| Scale | Grouping | Why |
|---|---|---|
| `structure-format` | structure together with format | The rules of the contest: how it is run and how it is decided are one subject, and splitting them is an artefact of the codebook. |
| `institution-origins` | institution together with origins | Where a discipline came from and what standing it now has are one question about its place in the world rather than its play. |
| `venue-equipment` | venue together with equipment | What the ground you play on requires you to carry or ride. Skates and sleds on ice, boats and oars on water, studs on grass. |
| `venue-equipment-demands` | venue, equipment and demands | The physical side of competing: the surface underfoot, the gear in hand and the effort required, as against the rules and the institution. Built deliberately at the top of the drawable range. |

## Rejected

| Candidate | Why not |
|---|---|
| a decision-only level | 8 concepts, under the floor. |
| refining `venue` by surface within venue type | Adds nothing: 18 concepts before and 18 after. See the construction rule below. |
| `structure-format-demands` and similar triples | 559 concepts and valid, but over the drawable ceiling and no better a sentence than the triple that fits. |
| summer against winter as an attribute | Not in the context by design; it would split the lattice trivially in two. |

## Construction rule learned here

Conjoining attributes that are **already in the same scale** can never add a
concept: a scale's extents are exactly the intersections of its attribute extents,
so such a conjunction is already among them. A refinement step must bring in a
conjunct from outside the scale. The venue chain was dropped for exactly this
reason, and both surviving chains cross facets.

## Note on the venue facet

`Ice or snow` stands in for the winter programme, which is deliberately not an
attribute of this context. It will dominate the venue scale and anything
appositioned with it, splitting sixteen winter disciplines from fifty-four summer
ones. That is expected rather than a fault, but it should be said when the
diagrams are read.

## Exact conjunctions

`decision-structure` adds, to Judged, Measured and Points accumulate:

    Judged ∧ Individual events            Points accumulate ∧ Team events
    Judged ∧ Team events                  Points accumulate ∧ Individual events
    Measured ∧ Individual events          Points accumulate ∧ Head to head
    Measured ∧ Team events                Head to head ∧ Physical contact
    Measured ∧ Head to head

`decision-structure-format` adds, on top of those:

    Judged ∧ Individual events ∧ Fixed attempts      Points accumulate ∧ Team events ∧ Clock
    Measured ∧ Individual events ∧ Clock             Points accumulate ∧ Team events ∧ Draw possible
    Measured ∧ Individual events ∧ Fixed attempts    Points accumulate ∧ Individual events ∧ Turn taking

`equipment-medium` adds, to the six equipment attributes:

    Vehicle board or runner ∧ Ice or snow     Ball ∧ Grass or turf
    Vehicle board or runner ∧ Water           Ball ∧ Indoor venue
    Vehicle board or runner ∧ Outdoor venue   Handheld implement ∧ Ice or snow
    Animal ∧ Grass or turf                    Handheld implement ∧ Water
                                              Handheld implement ∧ Indoor venue

No other conjunctions are used. The facet and apposition scales carry original
attributes unchanged.
