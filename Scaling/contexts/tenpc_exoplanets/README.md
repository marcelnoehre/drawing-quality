# Confirmed exoplanets within 10 parsecs

`tenpc_exoplanets.cxt` — 85 exoplanets described by 16 binary attributes, density
0.476. Rebuilt by `build_contexts.py` from
`Datasets/stars_exoplanets/tenpc_exoplanets_source.csv` and verified identical to
the context produced by the original pipeline.

## Sources

The object list comes from the same catalogue as the companion star context:
**Reylé, C., Jardine, K., Fouqué, P., Caballero, J. A., Smart, R. L., Sozzetti, A.
2021, "The 10 parsec sample in the Gaia era", A&A 650, A201**, updated in **Reylé
et al. 2022, 21st Cambridge Workshop on Cool Stars, Zenodo
doi:10.5281/zenodo.7669746, arXiv:2302.02810**, catalogue version 2, CDS
`J/A+A/650/A201`.

The planet *parameters* come from elsewhere, in a fixed order of priority: the
**NASA Exoplanet Archive** Planetary Systems Composite Parameters table (2026
snapshot; **Akeson et al. 2013, PASP 125, 989**, table doi:10.26133/NEA13) for 80
planets, the **Open Exoplanet Catalogue** (**Rein 2012, arXiv:1211.7121**) for four,
and the literature for one, GJ 752 A b (**Kaminski et al. 2018, A&A 618, A115**).
Every value's source is recorded in the accompanying source table.

## Why these objects

The 85 planets are exactly the confirmed planets that the 10 pc catalogue lists for
the hosts in `../tenpc_stars/`. The selection is therefore made entirely by **host
distance**, and by no property of the planets themselves.

That is the point of using this set. Planet samples assembled from surveys inherit
the selection function of the detection method, so mass, period and multiplicity
distributions reflect the instrument as much as the population. Here the frame is
volume-limited by host, which keeps the object set closed in the sense formal
concept analysis needs: the extent of a concept answers "which planets within 10 pc
have these properties" completely.

The price is a small sample that leans heavily towards radial-velocity discoveries
around M dwarfs, 78 of 85 and 71 of 85 respectively, which is what the solar
neighbourhood actually contains and how it has been surveyed.

## How the data were collected

Object list first, then parameters, then rules:

- **Objects** are the planets of the reconstructed version 2 catalogue, including
  the eight planets added between version 1 and version 2.
- **Parameters** were assembled per planet in the priority order above. Host
  effective temperature and radius were filled in the same order, including from a
  sibling planet of the same host where a host lacked its own entry.
- **Instellation** is the NASA value where given, otherwise computed from the host
  radius and temperature and the semi-major axis, in units of Earth's instellation.
- **Habitable-zone edges** are computed per host from its effective temperature
  using the conservative limits of **Kopparapu et al. 2014, ApJL 787, L29**: the
  runaway greenhouse limit for one Earth mass as the inner edge, the maximum
  greenhouse limit as the outer edge. The two instellation attributes below form an
  ordinal pair, so a planet in the conservative habitable zone is one that has
  attribute 5 but not attribute 6. There are 13 such planets, among them Proxima
  Cen b, Teegarden's Star c and GJ 1061 d.
- **The transit flag** is set only when the Open Exoplanet Catalogue marks a planet
  as transiting *and* gives it a measured radius. This deliberately excludes
  GJ 686 b, which is flagged as transiting but is a radial-velocity planet without a
  radius. The remaining 11 are the known transiting systems within 10 pc.
- **Host attributes** are copied from the host's row in the star context, so the two
  contexts cannot disagree.

`Datasets/stars_exoplanets/README.md` is the fuller account, including the per-case
treatment of the five planets outside the NASA table and the Kopparapu coefficients
as used.

## Attributes, in the order they appear in the context

The count is the number of planets having the attribute.

### Mass regime, ordinal

| # | Attribute | Rule | Count |
|---|---|---|---|
| 1 | mass > 2.04 Earth (above Terran regime) | above the Terran–Neptunian transition of Chen & Kipping (2017) | 67 |
| 2 | mass > 0.414 Jupiter (Jovian regime) | above the Neptunian–Jovian transition of Chen & Kipping (2017) | 9 |
| 3 | only minimum mass (m sin i) known | the mass provenance is m sin i rather than a true mass | 55 |

### Orbit and irradiation

| # | Attribute | Rule | Count |
|---|---|---|---|
| 4 | ultra-short period (P < 1 d) | orbital period under one day (Sanchis-Ojeda et al. 2014) | 1 |
| 5 | instellation above HZ outer edge | above the maximum-greenhouse limit for its host | 66 |
| 6 | instellation above HZ inner edge | above the runaway-greenhouse limit for its host | 53 |

### Detection and knowledge status

| # | Attribute | Rule | Count |
|---|---|---|---|
| 7 | discovered by radial velocity | discovery method is radial velocity | 78 |
| 8 | transits its host | flagged as transiting with a measured radius | 11 |

### Architecture

| # | Attribute | Rule | Count |
|---|---|---|---|
| 9 | in multi-planet system | its host has at least two of the listed planets | 63 |
| 10 | host in multiple-star system | copied from the host's row in the star context | 15 |

### Host star

| # | Attribute | Rule | Count |
|---|---|---|---|
| 11 | host SpT M | the host is M0 or cooler | 71 |
| 12 | host fully convective (M3.5 or later) | the host is M3.5 or cooler | 29 |
| 13 | host SpT has emission-line flag (e) | the host's catalogue spectral type carries `e` | 13 |
| 14 | host within 5 pc | the host is at most 5 pc away | 33 |

### Archive status

| # | Attribute | Rule | Count |
|---|---|---|---|
| 15 | in NASA Exoplanet Archive composite (2026) | listed in the 2026 table | 80 |
| 16 | flagged controversial in NASA archive | the archive's controversy flag is set: GJ 15 A b, GJ 229 A b and c, HD 219134 f | 4 |

## Why the mass boundaries are 2.04 Earth masses and 0.414 Jupiter masses

Both come from one paper, **Chen, J. & Kipping, D. 2017, ApJ 834, 17**, which fits
the mass–radius relation of planets as a broken power law and finds where its slope
changes. Those breaks are treated as the boundaries between classes of planet: the
Terran to Neptunian transition at 2.04 M⊕, and the Neptunian to Jovian transition at
0.414 M_J. They are fitted transitions in a population, not round numbers chosen for
convenience, which is the reason for using them rather than, say, "ten Earth masses".

The two units differ only because that is how the paper reports them, each regime in
the unit natural to it. There is one underlying quantity and one scale: the build
script converts the second boundary to the same units as the first, so the context
is really "mass above 2.04 M⊕" and "mass above 131.6 M⊕", the two thresholds of a
three-band ordinal scale. Renaming the second attribute in Earth masses would make
that plainer at the cost of hiding the citation; the numbers in
`tenpc_exoplanets_manyvalued.csv` are in Earth masses throughout.

The same band problem applies here as in the white-dwarf context. The middle class,
Neptunian planets, has no attribute of its own, and its 58 members close up to the
67 planets above 2.04 M⊕. The conservative habitable zone is the case that matters
most: it is defined as above the outer edge but not above the inner one, and those
13 planets close up to the 48 above the outer edge. So the context can define the
habitable zone but a diagram of it has no node for it, unless the scale is made
interordinal by adding the complementary attributes.

## Caveats

- **Minimum masses are one-sided.** A minimum mass above a threshold proves the true
  mass is above it; a minimum mass below the threshold proves nothing. For the 55
  m-sin-i planets, a dot on attributes 1 and 2 means "not shown to be above", which
  is why attribute 3 exists.
- **Two kinds of attribute share one table.** Attributes 1 to 6 are about the
  planet, 7, 8, 15 and 16 are about what is known of it and by whom. The second kind
  describes the state of knowledge rather than the object, which is worth keeping in
  mind when reading a concept that mixes them.
- **Parameters and object list have different vintages.** The object list is frozen
  at catalogue version 2 of August 2023, while the parameters come from a 2026
  table. Planets discovered after the catalogue snapshot are absent even if the 2026
  table has them.
- **The NASA table came from a third-party mirror.** For a citable version, download
  the `pscomppars` table directly from the archive and rerun the original pipeline.

## References

Reylé et al. 2021, A&A 650, A201 · Reylé et al. 2022, Zenodo
doi:10.5281/zenodo.7669746 · Akeson et al. 2013, PASP 125, 989 · Rein 2012,
arXiv:1211.7121 · Chen & Kipping 2017, ApJ 834, 17 · Kopparapu et al. 2013, ApJ 765,
131 · Kopparapu et al. 2014, ApJL 787, L29 · Sanchis-Ojeda et al. 2014, ApJ 787, 47
· Kaminski et al. 2018, A&A 618, A115.

# Scales of this context

Ten scale-measures, built by `../build_scales.py` and verified by
`../verify_scale.py`. The groupings, with the reason for each and the candidates
rejected, are in `groupings.md` beside this file, fixed before any drawing. The
machine-readable summaries are `manifest.csv` and `nesting.csv`.

| Scale | Kind | One sentence | Attributes | Concepts | Width | Height | Drawn |
|---|---|---|---|---|---|---|---|
| `tenpc_exoplanets_planet` | facet | what kind of planet it is | 5 | 10 | 3 | 5 | no |
| `tenpc_exoplanets_host` | facet | what kind of star it orbits | 3 | 5 | 2 | 4 | no |
| `tenpc_exoplanets_system` | facet | whether it has company | 2 | 4 | 2 | 3 | no |
| `tenpc_exoplanets_knowledge` | facet | how it is known, including how far away it is | 6 | 16 | 5 | 7 | yes |
| `tenpc_exoplanets_host_system` | apposition | the planetary system as a whole | 5 | 15 | 5 | 6 | yes |
| `tenpc_exoplanets_planet_system` | apposition | whether planets of a given kind come alone or in company | 7 | 30 | 10 | 7 | yes |
| `tenpc_exoplanets_planet_knowledge` | apposition | how well each kind of planet is known, and by which method | 11 | 73 | 18 | 10 | yes |
| `tenpc_exoplanets_planet_host` | apposition | which kinds of planets orbit which kinds of stars | 8 | 34 | 9 | 8 | yes |
| `tenpc_exoplanets_planet_host_system` | apposition | everything about the planet and where it lives, setting aside how we know it | 10 | 79 | 22 | 8 | yes |
| `tenpc_exoplanets` | full | the data themselves, the identity scale-measure | 16 | 371 | 74 | 12 | yes |

## Why these scales

**The groups are the README's own.** The attributes above are already sorted into
six groups: mass regime, orbit and irradiation, detection and knowledge,
architecture, host star, archive status. The scales use four, merged where a group
is too small to be a view on its own: *planet* (mass regime with orbit and
irradiation), *host*, *system* (architecture) and *knowledge* (detection with
archive status). Grouping by what an attribute is about, as the data's own
documentation already does, rather than by anything a drawing could show, is what
keeps the choice independent of the results.

**Knowledge is kept apart from the planet.** The Caveats above note that some
attributes "describe the state of knowledge rather than the object". A concept
mixing the two answers a muddled question, so the physical views -- planet, host,
system and their combinations -- never contain a knowledge attribute, and knowledge
is joined only to the planet, in `planet_knowledge`, where the question *is* how
the state of knowledge depends on the kind of planet. Two attributes are filed
differently from the attribute table above for that reason: the minimum-mass flag
says how a mass is known, not what it is, and **distance** (`host within 5 pc`)
says where a system is relative to us, not what kind of star the host is. In a
distance-limited sample, distance is what decides how well a system is seen. The
companion star context files distance the same way.

**Three facets are recorded but never drawn.** With two to five attributes each,
planet, host and system have 4 to 10 concepts, below the drawable minimum of 12,
where every algorithm draws almost the same picture. Knowledge, with six
attributes, has 16 and is drawn.

**Every apposition answers one question**, written as one sentence in the table.
Two candidates were rejected for failing that: knowledge joined to the host, and
knowledge joined to the system, each of which would only say "how we know things
about planets around these stars".

**There is no refinement chain.** A chain refines a scale with conjunctions that
reach outside it, along a genuine parent-child hierarchy. The hierarchies here --
the mass bands, the two instellation edges, M dwarf containing fully convective --
are already built into the attributes as ordinal pairs, and the planet-class
typology one might want ("hot Jupiter", "temperate super-Earth") lies wholly inside
the planet group, where a conjunction adds nothing.

## Nesting

`planet_host_system` is the mid-range root, as `capability_practice_making` is for
instruments: the three smaller physical views (15, 30 and 34 concepts) nest into it,
and it nests into the full context. With the knowledge facet nesting into
`planet_knowledge` and the full context, that gives 10 usable nested pairs, every
one of them with both scales drawn.

## Two things to know when reading results

- **No drawable scale has two equivalent attributes**, so fdp, which never
  terminates on such a context, is expected to draw all of them; and no object
  shares a name with an attribute.
- **The habitable zone has no node.** As explained above, a planet in the
  conservative habitable zone is one above the outer edge and not above the inner
  one, and a negation is never a scale attribute. The 13 such planets are
  therefore not a concept in any of these scales; they are visible only as the
  difference between two.

## What is computed from these scales

Of the 10 scales above, **7 are drawable** -- between 12 and 1000 concepts, with
width at least 3 -- from 15 to 371 concepts; the others are recorded and never
drawn. Of 23 nested pairs, **10 are usable**: both scales drawable, and sharing at
least 8 concepts. From these, `../../run_harness.py` computes:

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

