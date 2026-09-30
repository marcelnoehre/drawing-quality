# Formal context of the 40 pc white-dwarf sample

A binary formal context in Burmeister (`.cxt`) format of every confirmed white dwarf within 40 pc
of the Sun. It comes with the attribute groupings (scales and meta-groups) for scale-measure work,
the many-valued source table the context was derived from, and a pipeline that regenerates
everything from the original catalogue files.

| Context | Objects | Attributes | Formal concepts |
|---|---|---|---|
| `wd40pc.cxt` | 1078 white dwarfs within 40 pc | 28 | 728 |

This is the third context in the series, after `tenpc_stars.cxt` and `tenpc_exoplanets.cxt`
(10 pc sample). It is built on the same principles: a published, volume-limited object list;
attributes defined as explicit rules on catalogue columns; ordinal thresholds with a physical
motivation instead of long lists of nominal classes.

---

## 1. File inventory

### Main deliverables (this folder)

| File | What it is |
|---|---|
| `wd40pc.cxt` | The formal context. Rows are the 1078 white dwarfs of table A1 (named by their WDJ designation), columns are the 28 binary attributes of Section 4. Loadable in ConExp, ConImp and other tools that read Burmeister format. |
| `wd40pc_scales.txt` | The scales (attribute groups) and meta-groups, with the number of formal concepts of each scale's subcontext. |
| `wd40pc_source.csv` | The many-valued data behind every X and "." in the context. It gives, per white dwarf: name, Gaia DR3 ID, parallax, distance, absolute G, BP−RP colour, spectral type, fitted atmospheric composition, corrected Teff, corrected mass, cooling age, kinds of wide companions, size of the wide system, and the catalogue comment. |
| `README.md` | This file. |

### Pipeline (`pipeline/`)

Run from inside `pipeline/`. The pipeline reproduces the deliverables byte for byte (checked).

    python3 build_wd_context.py data    # writes wd40pc.cxt and wd40pc_source.csv
    python3 scales_wd.py                # writes wd40pc_scales.txt (uses fca_check.py)

| Script | Role |
|---|---|
| `parse.py` | Reads the fixed-width CDS tables using the byte positions given in the catalogue `ReadMe`. |
| `build_wd_context.py` | Defines every attribute as an explicit rule and writes the context and the source table. |
| `scales_wd.py` | Defines scales and meta-groups, checks that every attribute is covered, and counts concepts. |
| `fca_check.py` | Helper: parses and validates a `.cxt` file and counts its formal concepts. |

### Input data (`pipeline/data/`)

These are the original files of CDS catalogue J/MNRAS/527/8687, unmodified, as downloaded from
VizieR by the user.

| File | Content |
|---|---|
| `ReadMe` | The CDS description of the catalogue, including the byte-by-byte column format. |
| `tablea1.dat` | Table A1: all confirmed white dwarfs within 40 pc (1078 records, updated version of 14 November 2024). |
| `tablea6.dat` | Table A6: all wide binaries within 40 pc that contain at least one white dwarf (129 systems). |

---

## 2. Why this sample

**Reference catalogue.** The object list comes from O'Brien et al. (2024), "The 40 pc sample of
white dwarfs from Gaia". The sample is built on the Gaia white-dwarf candidate catalogue of
Gentile Fusillo et al. (2021). The authors report that 99.3 per cent of the Gaia candidates within
40 pc have medium-resolution optical spectroscopy. It is the largest volume-limited white-dwarf
sample with essentially complete spectroscopic follow-up.

**Why it suits FCA.** Because practically every object has a spectrum, the spectral-type attributes
are decided for every object. A "." means the feature is absent from the spectrum, not that
nobody looked. The physical parameters (mass, temperature, cooling age) come from one uniform fit
to Gaia DR3 photometry and astrometry, so thresholds on them mean the same thing for every object.
Completeness of the Gaia selection itself at 40 pc is estimated at about 97 per cent.

**Size.** With 1078 objects, the context sits in the requested range of 1000–2000.

**Snapshot.** The context uses table A1 in its version of 14 November 2024. The paper's abstract
quotes 1073 or 1076 confirmed white dwarfs depending on version, while the CDS table used here has
1078 records.

---

## 3. What was used and what was changed

Nothing in the input files was edited. The pipeline reads them as distributed.

- **Objects:** all 1078 records of table A1. Nothing was added or removed.
- **Physical parameters:** the columns *after* the low-mass correction (`Teffc`, `Massc`, `Agec`)
  are used. They are the values the paper adopts for cool white dwarfs, correcting the known
  "low-mass problem" of photometric fits below about 6000 K.
- **Missing parameters:** 27 objects have no Gaia fit. Most are IR-faint white dwarfs with multiple
  solutions, and some are objects whose photometry is contaminated or whose C₂ bands prevented a
  fit. Two further objects have a mass and temperature but no cooling age. These objects receive
  "." on all threshold attributes. The attribute "Gaia parameters available" makes this explicit;
  it is the top element of the mass, temperature and age scales.
- **Binarity:** table A6 was matched to table A1 by Gaia DR3 source ID. 120 of the 129 A6
  systems have their white dwarf in A1. The other 9 involve white dwarfs outside the main A1
  selection (e.g. a white dwarf within 1σ of the 40 pc boundary, white dwarfs without separate Gaia
  proper motions, or white dwarfs missing from the Gentile Fusillo et al. catalogue). They do not
  change the object list. Where both white dwarfs of a WD+WD pair are in A1, both receive the
  companion attributes.
- **Unresolved binaries:** these are taken from the catalogue comment column. It flags "double
  degenerate" (confirmed or candidate), "triple degenerate" and "Gaia non-single-star" orbits.

---

## 4. Attributes

Each attribute is a deterministic rule on the catalogue columns (see `build_wd_context.py`). The
counts give the number of white dwarfs having the attribute.

### Spectral features

These come from the spectral-type letters of the standard scheme (Sion et al. 1983). The first
letter after "D" is the dominant feature, and further letters are secondary features. Qualifiers
such as `pec`, `:` and `(warm)` are removed before the letters are read.

| Attribute | Rule | Count |
|---|---|---|
| hydrogen lines (A) | letter A anywhere (DA, DAZ, DZA, DBA …) | 681 |
| helium lines (B) | letter B anywhere | 18 |
| featureless spectrum (DC) | primary letter C | 290 |
| carbon features (Q) | letter Q anywhere | 50 |
| metal lines (Z, polluted) | letter Z anywhere; metals in a white-dwarf atmosphere indicate accreted planetary material | 119 |
| magnetic (H or P) | secondary letter H (Zeeman splitting) or P (polarisation) | 107 |
| emission lines (e) | type ends in "e" (DAe, DAHe) | 4 |
| peculiar, warm or uncertain type | `pec`, `(warm)`, `:` (uncertain), or primary X (unclassifiable) | 17 |

### Atmosphere and fit

| Attribute | Rule | Count |
|---|---|---|
| hydrogen-dominated atmosphere (fit) | adopted fit composition = H (the alternative is He) | 833 |
| Gaia parameters available | corrected Teff and mass exist | 1051 |
| IR-faint (collision-induced absorption) | catalogue comment "IR-faint white dwarf with collision-induced absorption" | 22 |

### Mass (interordinal; corrected mass, in solar masses)

| Attribute | Threshold and motivation | Count |
|---|---|---|
| mass < 0.45 Msun (low mass) | Single-star evolution cannot produce white dwarfs below about 0.45 M☉ within the age of the Galaxy, so these are expected to come from binary interaction (Kilic, Stanek & Pinsonneault 2007) | 43 |
| mass > 0.9 Msun (massive) | Common threshold for "massive" white dwarfs, where merger products become frequent (e.g. Jewett et al. 2024) | 64 |
| mass > 1.1 Msun (ultramassive) | Common threshold for ultramassive white dwarfs, expected to have oxygen–neon cores (Camisassa et al. 2019) | 19 |

### Temperature (ordinal; corrected Teff)

| Attribute | Threshold and motivation | Count |
|---|---|---|
| Teff > 5000 K | Below about 5000 K hydrogen lines become undetectable even in hydrogen atmospheres, so cool DA white dwarfs appear as DC | 891 |
| Teff > 10500 K | Approximate cool edge of the ZZ Ceti (DAV) instability strip (Gianninas, Bergeron & Ruiz 2011) | 153 |
| Teff > 12500 K | Approximate hot edge of the ZZ Ceti strip; "Teff > 10500 K but not > 12500 K" places an object inside the strip | 109 |

### Cooling age (ordinal; decades)

| Attribute | Threshold and motivation | Count |
|---|---|---|
| cooling age > 0.1 Gyr | Order-of-magnitude bins in log age | 1029 |
| cooling age > 1 Gyr | " | 822 |
| cooling age > 10 Gyr | Comparable to the age of the Galactic disc; the oldest white dwarfs in the volume | 5 |

### Binarity (from table A6 and the comment column)

| Attribute | Rule | Count |
|---|---|---|
| in wide binary or multiple (A6) | white dwarf appears in table A6 | 135 |
| wide main-sequence companion | its A6 system contains an MS star | 99 |
| wide white-dwarf companion | its A6 system contains another white dwarf | 33 |
| wide brown-dwarf companion | its A6 system contains a brown dwarf | 5 |
| wide system with >=3 members | A6 system type has three or more components | 13 |
| unresolved binary evidence (DD or Gaia orbit) | comment reports a double/triple degenerate (confirmed or candidate) or a Gaia non-single-star orbit | 59 |

### Observational

| Attribute | Rule | Count |
|---|---|---|
| within 20 pc | parallax ≥ 50 mas. The 20 pc white-dwarf sample is a long-standing reference volume (Holberg et al. 2016; Hollands et al. 2018) | 143 |
| within 10 pc | parallax ≥ 100 mas; links to the 10 pc context | 19 |

---

## 5. Scales and meta-groups

Full membership lists and concept counts are in `wd40pc_scales.txt`.

**Scales**
- W1 Spectral features
- W2 Atmosphere and fit
- W3 Mass (interordinal)
- W4 Temperature (ordinal)
- W5 Cooling age (ordinal)
- W6 Binarity
- W7 Observational

"Gaia parameters available" is shared by W3–W5 as their top element.

**Overlapping, cross-cutting scales**
- **X1 Spectral evolution along the cooling sequence.** Spectral features, atmosphere composition
  and temperature thresholds together. This shows how white dwarfs change spectral class as they
  cool: DA to DC below about 5000 K, and carbon or metal features appearing in helium atmospheres.
- **X2 Binary-evolution and merger signatures.** Low mass, massive, ultramassive, magnetic,
  warm/peculiar DQ, unresolved-binary evidence and white-dwarf companions. These are properties
  associated in the literature with binary interaction and mergers.

**Meta-groups** (scales may recur)
- N1 Intrinsic properties: W1, W3, W4, W5, X1
- N2 Binarity and evolutionary history: W6, X2
- N3 Observation and measurement: W2, W7

---

## 6. Caveats and how to read "."

- **Spectral features** are decided by the spectrum, but detectability depends on temperature. A
  cool white dwarf with a hydrogen atmosphere can be DC because hydrogen lines vanish below about
  5000 K, not because hydrogen is absent. The two attributes "hydrogen lines (A)" and
  "hydrogen-dominated atmosphere (fit)" separate this deliberately.
- **Threshold attributes** are "." for the 27 objects without Gaia fits, which also lack
  "Gaia parameters available". For those, "." means "not known", which the scale structure
  makes visible.
- **Thresholds** 0.45, 0.9 and 1.1 M☉, and 10500 and 12500 K, are conventional boundaries from the
  literature, not sharp physical transitions. The ZZ Ceti edges in particular depend on mass.
- **Binarity:** absence of "in wide binary" means no wide companion in the A6 catalogue; close
  companions appear only through the "unresolved binary evidence" attribute, which is based on
  individual studies and is therefore incomplete.
- **Cooling age** is the time since the white dwarf formed, not the total age of the star.
- **Comparison with the 10 pc context:** 19 white dwarfs lie within 10 pc here, versus 21 in the
  10 pc sample. Procyon B (not a separate Gaia source) and the unresolved candidate G 203-47 B are
  not in table A1. Spectral types sometimes differ between the two catalogues because they cite
  different classifications, for example EGGR 372 (DQ9P in the 10 pc sample, DXP here) and
  LAWD 96 (DAP versus DA).

---

## 7. Possible extensions

- **Core crystallisation.** A crystallisation attribute (the Gaia "Q branch") could be added from
  mass and temperature using published cooling models (e.g. Tremblay et al. 2019). It was left out
  to avoid introducing model-dependent boundaries without the tabulated model grid.
- **Kinematics.** A disc/halo attribute would need radial velocities, which the catalogue does not
  provide.

---

## 8. References

**Catalogue**
- O'Brien, M. W., Tremblay, P.-E., Klein, B. L., et al. 2024, *The 40 pc sample of white dwarfs from
  Gaia*, MNRAS 527, 8687; CDS catalogue J/MNRAS/527/8687 (table A1 updated 14 November 2024).
- Gentile Fusillo, N. P., et al. 2021, MNRAS 508, 3877 (Gaia EDR3 white-dwarf catalogue, the parent
  selection).
- Earlier papers of the 40 pc series: Tremblay, P.-E., et al. 2020, MNRAS 497, 130;
  McCleery, J., et al. 2020, MNRAS 499, 1890; O'Brien, M. W., et al. 2023, MNRAS 518, 3055.
- Gaia Collaboration, Vallenari, A., et al. 2023, A&A 674, A1 (Gaia DR3).

**Classification and thresholds**
- Sion, E. M., et al. 1983, ApJ 269, 253 (white-dwarf spectral classification).
- Kilic, M., Stanek, K. Z., Pinsonneault, M. H. 2007, ApJ 671, 761 (low-mass white dwarfs from
  binary evolution).
- Jewett, G., et al. 2024, ApJ 974, 12 (massive white dwarfs above 0.9 M☉ in the 100 pc sample).
- Camisassa, M. E., et al. 2019, A&A 625, A87 (ultramassive oxygen–neon white dwarfs).
- Gianninas, A., Bergeron, P., Ruiz, M. T. 2011, ApJ 743, 138 (ZZ Ceti instability strip).
- Bergeron, P., Kilic, M., Blouin, S., et al. 2022, ApJ 934, 36 (IR-faint white dwarfs).
- Holberg, J. B., et al. 2016, MNRAS 462, 2295; Hollands, M. A., et al. 2018, MNRAS 480, 3942
  (20 pc white-dwarf sample).
- Tremblay, P.-E., et al. 2019, Nature 565, 202 (core crystallisation in Gaia white dwarfs).
