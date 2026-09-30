# White dwarfs within 40 parsecs

`wd40pc.cxt` — 1078 white dwarfs described by 28 binary attributes, density 0.226.
Rebuilt by `build_contexts.py` from `Datasets/white_dwarfs/wd40pc_source.csv` and
verified identical to the context produced by the original pipeline.

## Source

**O'Brien, M. W., Tremblay, P.-E., Klein, B. L., et al. 2024, "The 40 pc sample of
white dwarfs from Gaia", MNRAS 527, 8687**, distributed as CDS catalogue
`J/MNRAS/527/8687`. The objects are table A1 of that catalogue, in its version of
14 November 2024; the binarity attributes come from its table A6. The parent
selection is the Gaia white-dwarf candidate catalogue of **Gentile Fusillo et al.
2021, MNRAS 508, 3877**, and the astrometry and photometry are Gaia DR3 (**Gaia
Collaboration, Vallenari et al. 2023, A&A 674, A1**).

## Why these objects

Every confirmed white dwarf in table A1 is an object here, all 1078 of them; none
were added and none removed. The sample is worth using for three reasons that the
paper establishes:

- **It is volume-limited.** Membership is decided by distance, 40 pc, and not by
  brightness or by how interesting an object is. The Gaia selection at that distance
  is about 97 per cent complete.
- **It is spectroscopically complete.** The authors report medium-resolution optical
  spectroscopy for 99.3 per cent of the Gaia candidates within 40 pc. This is what
  makes the closed-world reading defensible: when an object lacks *hydrogen lines*,
  a spectrum was taken and the lines are absent, rather than nobody having looked.
- **Its parameters are uniform.** Mass, temperature and cooling age come from one
  fit to Gaia photometry and astrometry for every object, so a threshold means the
  same thing across the sample.

The catalogue version matters: the paper's abstract quotes 1073 or 1076 confirmed
white dwarfs depending on the version, while the CDS table used here holds 1078
records.

## How the data were collected

The pipeline that produced the source table read the CDS files unmodified, using the
byte positions given in the catalogue ReadMe, and derived every attribute as an
explicit rule on catalogue columns:

- **Spectral features** come from the spectral-type string under the standard
  classification of **Sion et al. 1983, ApJ 269, 253**. Qualifiers such as `pec`,
  `:` and `(warm)` are stripped, then the letters after the leading D are read; the
  first is the dominant feature and the rest are secondary.
- **Physical parameters** are the values *after* the low-mass correction that the
  paper adopts for cool white dwarfs, not the raw fit.
- **Binarity** comes from matching table A6 to table A1 by Gaia DR3 source
  identifier. Unresolved binaries are read from the catalogue comment column, which
  flags double and triple degenerates and Gaia non-single-star orbits.
- **27 objects have no Gaia fit** and a further two have no cooling age. They take
  no mass, temperature or age attributes; the attribute *Gaia parameters available*
  is what distinguishes "measured and below the threshold" from "not measured".

The thresholds are conventional boundaries from the literature rather than sharp
physical transitions, and each is sourced in the table below.

`Datasets/white_dwarfs/README.md` is the fuller account: it lists the input files,
the exact treatment of missing parameters, the nine A6 systems whose white dwarf
falls outside A1, and a comparison against the 10 pc sample.

## Attributes, in the order they appear in the context

The count is the number of white dwarfs having the attribute.

### Spectral features

| # | Attribute | Rule | Count |
|---|---|---|---|
| 1 | hydrogen lines (A) | letter A anywhere in the spectral type | 681 |
| 2 | helium lines (B) | letter B anywhere | 18 |
| 3 | featureless spectrum (DC) | primary letter C | 290 |
| 4 | carbon features (Q) | letter Q anywhere | 50 |
| 5 | metal lines (Z, polluted) | letter Z anywhere; metals indicate accreted planetary material | 119 |
| 6 | magnetic (H or P) | secondary letter H (Zeeman splitting) or P (polarisation) | 107 |
| 7 | emission lines (e) | the type ends in `e` | 4 |
| 8 | peculiar, warm or uncertain type | `pec`, `(warm)`, `:`, or primary X | 17 |

### Atmosphere and fit

| # | Attribute | Rule | Count |
|---|---|---|---|
| 9 | hydrogen-dominated atmosphere (fit) | adopted fit composition is H rather than He | 833 |
| 10 | Gaia parameters available | a corrected temperature and mass exist | 1051 |
| 11 | IR-faint (collision-induced absorption) | catalogue comment reports an IR-faint white dwarf | 22 |

### Mass, corrected mass in solar masses

One threshold cuts from below and two from above; see *Why these thresholds* below
for what that costs.

| # | Attribute | Threshold and motivation | Count |
|---|---|---|---|
| 12 | mass < 0.45 Msun (low mass) | single-star evolution cannot produce these within the age of the Galaxy, so binary interaction is implied (Kilic, Stanek & Pinsonneault 2007) | 43 |
| 13 | mass > 0.9 Msun (massive) | common threshold for massive white dwarfs, where merger products become frequent (Jewett et al. 2024) | 64 |
| 14 | mass > 1.1 Msun (ultramassive) | expected to have oxygen–neon cores (Camisassa et al. 2019) | 19 |

### Temperature, ordinal, corrected effective temperature

| # | Attribute | Threshold and motivation | Count |
|---|---|---|---|
| 15 | Teff > 5000 K | below about this, hydrogen lines become undetectable even in hydrogen atmospheres | 891 |
| 16 | Teff > 10500 K | approximate cool edge of the ZZ Ceti instability strip (Gianninas, Bergeron & Ruiz 2011) | 153 |
| 17 | Teff > 12500 K | approximate hot edge; above 10500 but not 12500 places an object inside the strip | 109 |

### Cooling age, ordinal, in decades of gigayears

| # | Attribute | Threshold and motivation | Count |
|---|---|---|---|
| 18 | cooling age > 0.1 Gyr | order-of-magnitude bins in log age | 1029 |
| 19 | cooling age > 1 Gyr | as above | 822 |
| 20 | cooling age > 10 Gyr | comparable to the age of the Galactic disc | 5 |

### Binarity

| # | Attribute | Rule | Count |
|---|---|---|---|
| 21 | in wide binary or multiple (A6) | the white dwarf appears in table A6 | 135 |
| 22 | wide main-sequence companion | its A6 system contains a main-sequence star | 99 |
| 23 | wide white-dwarf companion | its A6 system contains another white dwarf | 33 |
| 24 | wide brown-dwarf companion | its A6 system contains a brown dwarf | 5 |
| 25 | wide system with >=3 members | the A6 system has three or more components | 13 |
| 26 | unresolved binary evidence (DD or Gaia orbit) | the comment reports a double or triple degenerate, or a Gaia non-single-star orbit | 59 |

### Observational

| # | Attribute | Rule | Count |
|---|---|---|---|
| 27 | within 20 pc | parallax at least 50 mas; the 20 pc sample is a long-standing reference volume (Holberg et al. 2016; Hollands et al. 2018) | 143 |
| 28 | within 10 pc | parallax at least 100 mas; links this context to the 10 pc ones | 19 |

## Why these thresholds

None of the numbers were chosen here. Each is a convention taken from the
literature, and each is a boundary of a named class of object rather than a
statistical cut of this sample. The measured values they were applied to are in
`wd40pc_manyvalued.csv`, so any of them can be moved and the effect inspected.

**Mass.** The distribution of white-dwarf masses is strongly peaked; in this sample
the median is 0.633 M☉ and 944 of the 1051 objects with a fit lie between 0.45 and
0.9. The three thresholds mark the exceptions on either side of that peak, which is
why the low-mass one points the other way. 0.45 M☉ is the standard low-mass cut: a
star that would leave a lighter remnant has a main-sequence lifetime longer than the
age of the Galaxy, so such objects are taken to come from binary interaction rather
than single-star evolution (Kilic, Stanek & Pinsonneault 2007). 0.9 M☉ is the
conventional line for *massive* white dwarfs, above which merger products become
frequent (Jewett et al. 2024). 1.1 M☉ is the usual *ultramassive* cut, above which
oxygen–neon cores are expected (Camisassa et al. 2019); values of 1.05 and 1.1 both
appear in the literature.

**Temperature.** 5000 K is observational rather than structural: below it hydrogen
lines are undetectable even in a hydrogen atmosphere, so a DA white dwarf is
classified DC. It is the boundary that makes attributes 1 and 9 diverge. 10500 and
12500 K are the approximate cool and hot edges of the ZZ Ceti instability strip
(Gianninas, Bergeron & Ruiz 2011), where hydrogen-atmosphere white dwarfs pulsate.
Both edges depend on mass, so they are approximate by nature.

**Cooling age.** 0.1, 1 and 10 Gyr are decade boundaries in log age, chosen for
resolution rather than physics, with one exception: 10 Gyr is comparable to the age
of the Galactic disc, so the five objects above it are the oldest in the volume.

### What the thresholds cannot express

The three mass attributes leave the middle band, 0.45 to 0.9 M☉, without an
attribute of its own. That band is not lost, but it is not a concept either: its 944
objects close up to all 1051 objects with a Gaia fit, because no attribute of this
context separates them. The same holds for every band between thresholds, including
the one the temperature scale was built for: the 44 white dwarfs inside the ZZ Ceti
strip close up to the 153 above 10500 K. A diagram drawn from this context therefore
has no node for "typical mass" or "inside the instability strip".

Making those bands into concepts means making the scales interordinal, that is
adding the complementary attributes, mass at least 0.45, at most 0.9, at most 1.1,
temperature at most 12500 K, and so on. That is a change to the context and to every
lattice drawn from it, so it has not been applied. It is the sort of decision worth
making once, deliberately, and recording.

## Caveats

- **Detectability is temperature-dependent.** A cool hydrogen-atmosphere white dwarf
  can be classified DC because its lines have vanished. Attributes 1 and 9 separate
  the observed spectrum from the fitted atmosphere on purpose.
- **A dot on a threshold attribute has two readings.** For the 1051 objects with a
  Gaia fit it means "below the threshold"; for the other 27 it means "not known",
  and attribute 10 is what tells them apart.
- **Close binaries are under-represented.** Only wide companions are catalogued;
  attribute 26 reports unresolved binaries from individual studies and is therefore
  incomplete.
- **Cooling age is the time since the white dwarf formed**, not the age of the star.

## References

O'Brien et al. 2024, MNRAS 527, 8687 · Gentile Fusillo et al. 2021, MNRAS 508, 3877
· Gaia Collaboration 2023, A&A 674, A1 · Sion et al. 1983, ApJ 269, 253 · Kilic,
Stanek & Pinsonneault 2007, ApJ 671, 761 · Jewett et al. 2024, ApJ 974, 12 ·
Camisassa et al. 2019, A&A 625, A87 · Gianninas, Bergeron & Ruiz 2011, ApJ 743, 138
· Bergeron et al. 2022, ApJ 934, 36 · Holberg et al. 2016, MNRAS 462, 2295 ·
Hollands et al. 2018, MNRAS 480, 3942.
