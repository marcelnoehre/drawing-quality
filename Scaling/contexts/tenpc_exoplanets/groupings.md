# Groupings

Every grouping used to build a scale, with the reason it was chosen, written
**before any drawing**. Nothing here may be revised after drawing results are
seen. We choose the scales and then evaluate drawings on them, so this file is
what separates a considered choice from one tuned to the answer.

Scale attributes are original attributes or conjunctions of them, never
disjunctions or negations.

---

## tenpc_exoplanets

Recorded 2026-10-15T15:18:54+02:00, from
`contexts/tenpc_exoplanets/tenpc_exoplanets.cxt`, 85 objects and 16 attributes.
Reviewed and approved before this record was written; no scale of this context had
been drawn. **Amended at 15:43 the same day, still before any drawing: distance moved
from host to knowledge.** The amendment at the end of this file gives the reason and
the resulting scales; the tables below are kept as first recorded.

The four groups are the ones the context's README already sorts the attributes
into, merged where a group is too small to stand alone. One choice departs from
the README's order on purpose: the minimum-mass flag (`only minimum mass (m sin i)
known`) is listed there under *mass regime*, but it says how a mass is known, not
what it is, so it belongs with knowledge. The README's own caveat -- that some
attributes "describe the state of knowledge rather than the object" -- is the
reason for keeping knowledge apart from the planet throughout.

### Groups

| Group | Attributes | What it is about |
|---|---|---|
| planet | mass > 2.04 Earth; mass > 0.414 Jupiter; ultra-short period; instellation above HZ outer edge; instellation above HZ inner edge | the planet itself: its mass band and how strongly it is irradiated |
| host | host SpT M; host fully convective; host SpT has emission-line flag; host within 5 pc | the star it orbits |
| system | in multi-planet system; host in multiple-star system | its company |
| knowledge | only minimum mass known; discovered by radial velocity; transits its host; in NASA Exoplanet Archive composite (2026); flagged controversial | what is known of it, and by whom |

### Facet scales, each a plain attribute projection — recorded, not drawn

| Scale | Concepts | Why it exists |
|---|---|---|
| `tenpc_exoplanets_planet` | 10 | the view of the planet alone |
| `tenpc_exoplanets_host` | 10 | the view of the host alone |
| `tenpc_exoplanets_system` | 4 | the view of its company alone |
| `tenpc_exoplanets_knowledge` | 11 | the view of the state of knowledge alone |

All four are below the drawable minimum of 12 concepts, where every algorithm draws
almost the same picture. They are kept in the manifest as the views they are, as
the full olympics lattice is, and never drawn.

### Appositions, each a view someone would ask for

| Scale | Groups | Concepts | The view, in one sentence |
|---|---|---|---|
| `tenpc_exoplanets_host_system` | host + system | 25 | The planetary system as a whole: what star, how many planets, how many stars. |
| `tenpc_exoplanets_planet_system` | planet + system | 30 | Whether planets of a given kind come alone or in company. |
| `tenpc_exoplanets_planet_knowledge` | planet + knowledge | 48 | How well each kind of planet is known, and by which method: the detection bias made visible. |
| `tenpc_exoplanets_planet_host` | planet + host | 55 | Which kinds of planets orbit which kinds of stars. |
| `tenpc_exoplanets_planet_host_system` | planet + host + system | 114 | Everything about the planet and where it lives, setting aside how we know it. |

`planet_host_system` is the mid-range root: the three smaller physical views nest
into it, and it nests into the full context, so it plays the part
`capability_practice_making` plays for instruments. Knowledge is joined only to the
planet, in `planet_knowledge`, where the question is precisely how the state of
knowledge depends on the kind of planet.

### No refinement chain

A chain refines a scale by conjoining its attributes with attributes from outside
it, and needs a hierarchy that is genuinely parent and child. The hierarchies in
this data are already built into the attributes as ordinal pairs: the mass bands
(Terran, Neptunian, Jovian), the two instellation edges, and M dwarf containing
fully convective. The one typology that suggests itself, planet classes by mass and
irradiation ("hot Jupiter", "temperate super-Earth"), lies entirely inside the
planet group, and a conjunction of attributes that are both in the scale adds
nothing to it. So no chain is built.

### Rejected

| Candidate | Why not |
|---|---|
| knowledge + host | no question beyond "how we know things about planets around these stars"; fails the one-sentence test |
| knowledge + system | the same |
| the four facets, drawn | below 12 concepts |

### Result

Ten scales, six of them drawable, 23 nested pairs of which 8 are usable (both
scales drawn): the three small physical views into `planet_host_system`, and every
drawable scale into the full context. No drawable scale has two equivalent
attributes, so fdp is not expected to fail on any of them, and no object shares a
name with an attribute.

---

### Amendment 2026-10-15T15:43:12+02:00 — distance is knowledge

Made before any scale of this context was drawn, so it is a design correction, not
a revision after results.

`host within 5 pc` moves from **host** to **knowledge**. Building the companion star
context showed that the two contexts filed the same fact differently: that context's
README puts distance under *observational*, this one under *host star*. It is the
same fact about the same systems, so it should sit in the same group in both. It
belongs with knowledge because it says where a system is relative to us, not what
kind of star the host is, and in a distance-limited sample it is what decides how
well a system is seen -- which is exactly the question the knowledge views ask.

| Group | Attributes now |
|---|---|
| host | host SpT M; host fully convective; host SpT has emission-line flag |
| knowledge | only minimum mass known; discovered by radial velocity; transits its host; host within 5 pc; in NASA Exoplanet Archive composite (2026); flagged controversial |

planet and system are unchanged. The scales keep their names and their one-sentence
views; their sizes change:

| Scale | Concepts before | Concepts now | Drawn |
|---|---|---|---|
| `tenpc_exoplanets_planet` | 10 | 10 | no |
| `tenpc_exoplanets_host` | 10 | 5 | no |
| `tenpc_exoplanets_system` | 4 | 4 | no |
| `tenpc_exoplanets_knowledge` | 11 | 16 | yes |
| `tenpc_exoplanets_host_system` | 25 | 15 | yes |
| `tenpc_exoplanets_planet_system` | 30 | 30 | yes |
| `tenpc_exoplanets_planet_knowledge` | 48 | 73 | yes |
| `tenpc_exoplanets_planet_host` | 55 | 34 | yes |
| `tenpc_exoplanets_planet_host_system` | 114 | 79 | yes |
| `tenpc_exoplanets` | 371 | 371 | yes |

The knowledge facet, now 16 concepts, becomes drawable. Seven scales are drawable,
with 10 usable nested pairs instead of 8. No drawable scale has two equivalent
attributes, and no object shares a name with an attribute.

