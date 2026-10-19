# Groupings

Every grouping used to build a scale, with the reason it was chosen, written
**before any drawing**. Nothing here may be revised after drawing results are
seen. We choose the scales and then evaluate drawings on them, so this file is
what separates a considered choice from one tuned to the answer.

Scale attributes are original attributes or conjunctions of them, never
disjunctions or negations.

---

## olympic_disciplines

Recorded 2026-10-15T15:55:25+02:00, from
`contexts/olympic_disciplines/olympic_disciplines.cxt`, 50 objects and 19 attributes,
imported unchanged from the surrounding repository. Reviewed and approved before
this record was written; no scale of this context had been drawn.

The attributes describe a discipline's place in the Olympic programme, unlike our
own `olympics` context, which describes what a sport is. The groups follow what
each attribute is about.

### Groups

| Group | Attributes | What it is about |
|---|---|---|
| entry | female only, male only, mixed, open events | who may compete |
| format | individual, team competition | alone or in a team |
| venue | indoor, outdoor events | where |
| sport | water sport, ball game, combat sport, athletic sport | what kind of sport |
| standing | part of at least 8, 16, 24 Olympics; at least 5, 10, 20 events; has a Paralympic equivalent | how established it is in the Games |

Standing merges three small groups that answer one question. Its parts alone are
ordinal bands, chains of width 1.

### Scales, each a view someone would ask for

| Scale | Groups | Concepts | The view, in one sentence |
|---|---|---|---|
| `olympic_disciplines_competitors` | entry + format | 17 | Who competes: which genders may enter, and whether alone or in a team. |
| `olympic_disciplines_standing` | standing | 22 | Its place in the Games: how long it has been on the programme, how many medal events it has, whether it has a Paralympic counterpart. |
| `olympic_disciplines_discipline` | sport + venue | 25 | What kind of sport it is and where it is contested. |
| `olympic_disciplines_sport_competitors` | sport + entry + format | 57 | Which kinds of sport are contested by whom, alone or in teams. |
| `olympic_disciplines_sport_standing` | sport + standing | 103 | Which kinds of sport hold what place in the programme. |
| `olympic_disciplines_competitors_standing` | entry + format + standing | 113 | How far the programme opens each discipline to women, men and mixed teams, against how established and large it is. |
| `olympic_disciplines_discipline_competitors` | sport + venue + entry + format | 122 | The discipline as it is contested -- what sport, where, by whom -- setting aside its place in the Games. |
| `olympic_disciplines` | all | 529 | The data themselves. |

`discipline_competitors` is the mid-range root.

### No refinement chain

The bands are already built into the attributes, and sport into discipline exists
only in the object names, never in an attribute.

### Rejected

| Candidate | Why not |
|---|---|
| sport + venue + format (63 concepts) | separates team or individual from who may enter, giving a list rather than a view |
| entry, sport, history or programme alone | 7 to 11 concepts, or chains of width 1 |

### Result

Eight scales, all drawable, 14 nested pairs, all usable. No scale has two equivalent
attributes, and no object shares a name with an attribute.
