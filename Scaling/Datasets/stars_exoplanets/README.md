# Formal contexts of the solar neighbourhood (10 pc sample)

Two binary formal contexts in Burmeister (`.cxt`) format, plus the attribute groupings ("scales")
needed for scale-measure / conceptual-scaling work, the many-valued source tables they were derived
from, and a pipeline that regenerates everything from the input data.

| Context | Objects | Attributes | Formal concepts |
|---|---|---|---|
| `tenpc_stars.cxt` | 456 stars, brown dwarfs and white dwarfs within 10 pc | 35 | 732 |
| `tenpc_exoplanets.cxt` | 85 confirmed exoplanets orbiting those objects | 16 | 371 |

---

## 1. File inventory

### Main deliverables (top level)

| File | What it is |
|---|---|
| `tenpc_stars.cxt` | Formal context 1. Rows are the 456 non-planetary objects of the 10 pc sample (v2), columns are 35 binary attributes (Section 5). Loadable in ConExp, ConImp, FCA tools that read Burmeister format. |
| `tenpc_exoplanets.cxt` | Formal context 2. Rows are the 85 confirmed exoplanets of the 10 pc sample (v2), columns are 16 binary attributes (Section 6). |
| `tenpc_scales.txt` | The attribute groups (scales) and meta-groups for both contexts, with the number of formal concepts of each scale's subcontext. |
| `tenpc_stars_source.csv` | The many-valued data behind context 1: object, system, catalogue class, spectral type, Gaia G (measured or estimated), distance, number of bodies in its system, planets it hosts. |
| `tenpc_exoplanets_source.csv` | The many-valued data behind context 2: planet, host, mass and mass type, period, semi-major axis, instellation, host Teff, habitable-zone edges, discovery method, transit flag, NASA-archive status, and which source each value came from. |
| `README.md` | This file. |

### Pipeline (`pipeline/`)

Run in this order from inside `pipeline/`; the last step reproduces the top-level files byte for byte
(checked).

| Script | Role |
|---|---|
| `reconstruct_v2.py` | Builds the v2 object list from v1 plus the published change list (Section 3) and cross-checks it against the v2 rows available. Writes `tenpc_v2_reconstructed.json`. |
| `oec_extract.py` | Pulls planet and host parameters from the Open Exoplanet Catalogue (fallback source). Writes `planets_oec.json`. |
| `planet_params.py` | Assembles planet parameters with source priority NASA archive, then OEC, then literature; fills host parameters; computes instellation where missing. Writes `planet_params.json`. |
| `build_contexts.py` | Defines every attribute as an explicit rule and writes both `.cxt` files and both `*_source.csv` files. |
| `scales.py` | Defines scales and meta-groups, checks every attribute is covered, counts concepts, writes `tenpc_scales.txt`. |
| `fca_check.py` | Helper: parses a `.cxt` file, validates it, counts formal concepts. |

### Input data (`pipeline/data/`)

| File | Content and origin |
|---|---|
| `tenpc_v1.csv` | The complete 10 pc sample **v1** (540 entries, 339 systems), key columns only: running numbers, system name, catalogue class, object name, spectral type, SIMBAD name, common name, Gaia G, estimated G, distance. Transcribed from K. Jardine's supplement file (gruze.org/10pc_supplement), which copies these columns from the catalogue. |
| `tenpc_v2_head.psv` | Catalogue class, name and spectral type of the first 343 rows of the **v2** catalogue (gruze.org/10pc/The10pcSample_v2.csv). Only used as a cross-check (the download was truncated at row 343). One row (2MASS J00345157+0523050) was accidentally omitted during transcription; the cross-check reports it and it is present in the reconstructed list. |
| `PSCompPars_2026.csv` | NASA Exoplanet Archive "Planetary Systems Composite Parameters" table (default columns, 6324 planets), obtained from a GitHub mirror (github.com/tatidurao/pscomppars_exoplanetas) because the archive itself was not reachable from my environment. See Section 8. |
| `pscomppars.csv` | An older copy of the same table from the same mirror (5926 planets). Only used to record whether a planet was listed there; it does not feed any attribute. |
| `oec.xml.gz` | Open Exoplanet Catalogue, full XML (github.com/OpenExoplanetCatalogue/oec_gzip). |

---

## 2. Why this sample

**Reference catalogue.** The object set is the "10 parsec sample in the Gaia era"
(Reylé et al. 2021; updated in Reylé et al. 2022). It is a curated, volume-limited census of every
known star, brown dwarf and confirmed exoplanet with parallax ≥ 100 mas (distance ≤ 10 pc). It was
compiled as a quality-assurance test for the Gaia Catalogue of Nearby Stars, and the CNS5 authors
(Golovin et al. 2023) describe it as having the highest completeness among the catalogues they
reviewed. Its completeness has since been confirmed independently.

**Why 10 pc and not the 25 pc of CNS5.** CNS5 (5931 objects to 25 pc) is the larger reference, but
(a) completeness for cool brown dwarfs degrades with distance, and (b) for FCA the closed-world
reading ("." means *absent*, not *unknown*) needs attributes that are actually measured for every
object. The 10 pc sample is the largest published volume where the catalogue itself was curated
object by object (multiplicity, companions, spectral types, exoplanets).

**Exoplanets.** The planet context contains exactly the confirmed planets listed in the catalogue.
The planet set is therefore selected by host distance only, not by any planet property, which keeps
it volume-limited by host and avoids the detection-method selection effects of survey-based samples.

**Snapshot.** The object lists are frozen at catalogue v2 (CDS J/A+A/650/A201, updated
August 2023). Discoveries after that (for example the Barnard's Star planets of 2024–2025) are not
included. Planet *parameters*, by contrast, come from the 2026 NASA table (best current values).

---

## 3. What was changed: v1 → v2 reconstruction

The full v2 table could not be downloaded (the web fetch truncated it at row 343), but the complete
v1 table and the explicit change list in the v2 paper (Reylé et al. 2022, Sect. 2) were available.
`reconstruct_v2.py` applies exactly those changes:

**Removed (10 entries)**
- 2MASS J16471580+5632057 (better parallax places it beyond 10 pc)
- 2MASS J07584037+3247245 (better Gaia EDR3 parallax)
- CFBDS J213926+022023 A and B (actually a single object, beyond 10 pc)
- 41 Ara Ab = GJ 666 Ab (companion wrongly attributed to A)
- GJ 748 A and B (Hubble parallax places the pair beyond 10 pc)
- SZ UMa B = GJ 424 B (companion not confirmed)
- UPM J0815−2344 B (background object)
- WISE J081117.81−805141.3 (moved to the candidate list)

**Added (11 entries)**
- CWISEP J225628.97+400227.3 (Y dwarf, new system)
- CWISEP J181006.00−101001.1 (metal-poor brown dwarf, new system)
- 41 Ara Bb: the unseen companion of GJ 666 B found from its Gaia DR3 astrometric orbit
  (0.17–0.73 solar masses; class "LM?"). The name "41 Ara Bb", and renaming "41 Ara B" to
  "41 Ara Ba", are my labels.
- 8 planets: GJ 411 c (= HD 95735 c), LTT 1445 A c, GJ 393 b (= BD+01 2447 b),
  GJ 514 b (= BD+11 2576 b), GJ 367 b (host CD−45 5378), HD 260655 b and c, Wolf 1069 b

**Other edits**
- "Lalande 21185 b" renamed "HD 95735 b" (v2 naming).
- GJ 1230 C and GJ 867 C changed from "LM?" to "LM": the v2 paper states that their Gaia DR3
  orbital solutions confirm their low-mass-star nature.
- Spectral types of the two added brown dwarfs are not in the rows I had, so I assigned:
  "Y?" for CWISEP J2256+4002 (the v2 paper calls it a Y dwarf) and "esdT0" for CWISE J1810−1010
  (discovery classification, Schneider et al. 2020). Note that later work gives esdT3 and reports
  no methane in its spectrum (Burgasser et al. 2024; Lodieu et al. 2022). Distances of these two
  (9.5 and 8.9 pc) are approximate and only enter the "within 5 pc" attribute, where they make no
  difference.

**Verification**
- Result: 541 entries = 456 bodies (371 stars including 21 white dwarfs, 85 brown dwarfs) + 85
  planets, in 336 systems. This matches the totals published for v2 exactly.
- All 342 transcribed v2 rows agree with the reconstruction in name, catalogue class and spectral
  type (differences such as "F5" vs "F5.0" treated as equal).

---

## 4. Planet parameters

Priority per planet: **NASA composite table (2026)** → **Open Exoplanet Catalogue** →
**literature**. Host Teff and radius are filled in the same order, including from a sibling planet
of the same host. The source of every value is recorded in `tenpc_exoplanets_source.csv`.

| Case | Planets | Treatment |
|---|---|---|
| NASA 2026 table | 80 | Mass (with provenance Mass / Msini / Msin(i)/sin(i)), period, semi-major axis, instellation, host Teff and radius, discovery method, controversy flag. |
| Not in NASA 2026 but in OEC | GJ 9066 b, GJ 832 c, HD 102365 A b, GJ 176 b | OEC values; host parameters from a NASA sibling planet where available. HD 102365: host radius 0.96 R☉ adopted (the classification "hotter than the habitable zone" holds for any radius above about 0.4 R☉). |
| In neither | GJ 752 A b | Literature values: m sin i = 12.2 M⊕, P = 105.915 d, a = 0.3357 AU; host Teff 3558 K, R 0.47 R☉ (Kaminski et al. 2018). Its habitable-zone classification depends on these values. |

`planet_params.py` also contains a literature entry for GJ 3512 c; it is unused because the NASA
table has that planet.

**Transit flag:** true only when OEC marks the planet as transiting *and* gives a measured radius.
This excludes GJ 686 b, which OEC flags as transiting without a radius (it is an RV-only planet).
The resulting 11 transiting planets are the known transiting systems within 10 pc.

**Instellation:** NASA value where given; otherwise S = (R★/R☉)² (Teff/5772 K)⁴ / a², in units of
Earth's instellation.

---

## 5. Attributes of the star context (`tenpc_stars.cxt`)

Every attribute is a deterministic rule on the catalogue fields (see `build_contexts.py`). Counts are
the number of objects having the attribute.

| Attribute | Rule | Count |
|---|---|---|
| hydrogen-burning star | catalogue class `*`, `LM` or `LM?` | 350 |
| brown dwarf | class `BD` or `BD?` | 85 |
| white dwarf | class `WD` or `WD?` | 21 |
| class unconfirmed (candidate) | class ends in `?` (e.g. suspected M-dwarf companion without spectrum) | 37 |
| SpT on OBAFGKMLTY sequence | has a non-white-dwarf spectral type | 397 |
| SpT G or later | spectral type G0 or cooler | 385 |
| SpT K or later | K0 or cooler | 367 |
| SpT M or later | M0 or cooler | 329 |
| SpT M3.5 or later (fully convective) | M3.5 or cooler; approximate onset of full convection near 0.35 M☉ (Chabrier & Baraffe 1997) | 240 |
| SpT M7 or later (ultracool) | M7 or cooler; standard definition of ultracool dwarfs (Kirkpatrick, Henry & Irwin 1997) | 103 |
| SpT L or later | L0 or cooler | 82 |
| SpT T or later | T0 or cooler | 63 |
| SpT Y | Y class | 19 |
| subdwarf (sd/esd, metal-poor) | spectral type prefixed `sd` or `esd` | 3 |
| emission-line flag (e) in SpT | catalogue spectral type carries the `e` suffix | 53 |
| Gaia DR3 variable (Reyle+2022) | one of the 17 objects the v2 paper (Sect. 3.2) reports as variable in Gaia DR3 (solar-like, short-timescale or rotational modulation); GJ 15 A/B excluded because they appear in the tables only through GAPS photometry | 17 |
| WD spectral type known | spectral type starts with `D` | 20 |
| WD hydrogen atmosphere (DA) | primary letter A (Sion et al. 1983 scheme) | 9 |
| WD metal lines (Z) | letter Z anywhere | 5 |
| WD carbon features (Q) | letter Q anywhere | 5 |
| WD featureless (DC) | primary letter C | 2 |
| WD magnetic (P/H) | suffix P or H | 4 |
| member of multiple system | its system has ≥ 2 non-planetary bodies | 209 |
| member of system with >=3 bodies | ≥ 3 bodies | 79 |
| primary (brightest) of multiple system | brightest member by G (measured, else estimated); ties broken by earlier spectral type | 89 |
| has hydrogen-burning companion | another star in the same system | 185 |
| has brown-dwarf companion | a brown dwarf in the same system | 31 |
| has white-dwarf companion | a white dwarf in the same system | 9 |
| hosts confirmed planet | ≥ 1 of the 85 planets orbits it | 48 |
| hosts >=2 confirmed planets | ≥ 2 planets | 26 |
| hosts transiting planet | one of its planets transits | 8 |
| hosts planet in conservative HZ | one of its planets lies in the conservative habitable zone (Section 6) | 12 |
| member of planet-hosting system | any body of its system hosts a planet | 64 |
| within 5 pc | distance ≤ 5 pc (parallax ≥ 200 mas) | 72 |
| G magnitude measured by Gaia | a measured Gaia G exists; false for stars too bright for Gaia, for Y/late-T dwarfs too faint, and for unresolved companions | 343 |

---

## 6. Attributes of the exoplanet context (`tenpc_exoplanets.cxt`)

| Attribute | Rule | Count |
|---|---|---|
| mass > 2.04 Earth (above Terran regime) | mass (or m sin i) > 2.04 M⊕, the Terran–Neptunian transition of Chen & Kipping (2017) | 67 |
| mass > 0.414 Jupiter (Jovian regime) | > 0.414 M_J, the Neptunian–Jovian transition of Chen & Kipping (2017) | 9 |
| only minimum mass (m sin i) known | mass provenance is m sin i | 55 |
| ultra-short period (P < 1 d) | orbital period < 1 day (Sanchis-Ojeda et al. 2014) | 1 |
| instellation above HZ outer edge | S > maximum-greenhouse limit (Kopparapu et al. 2014), computed for the host's Teff | 66 |
| instellation above HZ inner edge | S > runaway-greenhouse limit for 1 M⊕ (Kopparapu et al. 2014) | 53 |
| discovered by radial velocity | discovery method RV | 78 |
| transits its host | see Section 4 | 11 |
| in multi-planet system | host has ≥ 2 of the listed planets | 63 |
| host in multiple-star system | copied from the host's row in context 1 | 15 |
| host SpT M | host is M0 or cooler | 71 |
| host fully convective (M3.5 or later) | host M3.5 or cooler | 29 |
| host SpT has emission-line flag (e) | host's catalogue spectral type carries `e` | 13 |
| host within 5 pc | host distance ≤ 5 pc | 33 |
| in NASA Exoplanet Archive composite (2026) | listed in the 2026 table | 80 |
| flagged controversial in NASA archive | `pl_controv_flag` = 1 (GJ 15 A b, GJ 229 A b and c, HD 219134 f) | 4 |

The two instellation attributes form an ordinal scale. A planet in the conservative habitable zone
has the first but not the second (13 planets: Proxima Cen b, GJ 1061 d, Teegarden's Star c,
GJ 687 b, GJ 876 b and c, GJ 682 b, GJ 752 A b, GJ 667 C c, BD+11 2576 b, GJ 433 d, GJ 357 d,
Wolf 1069 b). Kopparapu et al. (2014) coefficients used:
runaway greenhouse S₀ = 1.107, a = 1.332e−4, b = 1.580e−8, c = −8.308e−12, d = −1.931e−15;
maximum greenhouse S₀ = 0.356, a = 6.171e−5, b = 1.698e−9, c = −3.198e−12, d = −5.575e−16;
S_eff = S₀ + aT + bT² + cT³ + dT⁴ with T = Teff − 5780 K.

---

## 7. Scales and meta-groups

Full membership lists and concept counts are in `tenpc_scales.txt`.

**Star context:** S1 Physical nature · S2 Temperature sequence (ordinal) · S3 Metallicity and
activity · S4 White-dwarf spectral features · S5 Multiplicity (ordinal) and role · S6 Companion
types · S7 Planet hosting · S8 Observational. Overlapping cross-cutting scales: X1 Stellar/substellar
boundary, X2 Degenerate companions.
Meta-groups: M1 Intrinsic physics (S1, S2, S3, S4, X1) · M2 System architecture (S5, S6, S7, X2) ·
M3 Observation and selection (S8, S1, S3).

**Exoplanet context:** P1 Mass regime (ordinal) · P2 Orbit and irradiation (ordinal) · P3 Detection
and knowledge status · P4 Architecture · P5 Host star. "Only minimum mass known" belongs to both P1
and P3.
Meta-groups: Q1 Planet intrinsic (P1, P2) · Q2 Epistemic / observational (P3, P1) ·
Q3 System and host (P4, P5).

---

## 8. Caveats and how to read "."

- **Mass thresholds with m sin i.** A minimum mass above a threshold proves the true mass is above
  it; a minimum mass below it does not prove the opposite. For m-sin-i planets, "." on the mass
  attributes means "not shown to be above".
- **Emission flag.** "." means the catalogue spectral type has no `e`; it does not mean the star is
  inactive (flags depend on the spectral-typing source).
- **Gaia DR3 variable.** Relative to Gaia DR3 only; famous flare stars such as Proxima are not in
  that list.
- **"Fully convective" at M3.5** is an approximation to a mass boundary.
- **NASA table provenance.** The 2026 table comes from a third-party GitHub mirror. For a citable
  version, download table `pscomppars` (default columns) directly from the NASA Exoplanet Archive,
  save it as `pipeline/data/PSCompPars_2026.csv`, and rerun the pipeline.
- **Transcription.** `tenpc_v1.csv` and `tenpc_v2_head.psv` were transcribed from the fetched web
  files. The reconstruction reproduces the published v2 totals exactly and matches all available
  v2 rows, which checks the transcription of those columns.
- **Supplement disclaimer.** The gruze.org supplement marks its *derived* columns (distance,
  absolute magnitude, Galactic coordinates) "not for scientific use". Only its distance column is
  used, and only for "within 5 pc", which is equivalent to parallax ≥ 200 mas.

---

## 9. Differences from the earlier contexts (Almagest-based, 200 attributes)

- **Objects.** The earlier contexts had 97 objects (Sun, Moon, 5 planets, 48 constellations,
  42 named stars) and 146 objects (7 classical bodies + 139 identified Almagest stars). They were a
  naked-eye, brightness-selected sample. Here the sample is distance-selected, so it is dominated
  by M dwarfs and brown dwarfs, which are invisible to the eye.
- **Attribute values.** Earlier values were assigned case by case from general knowledge. Here each
  attribute is a stated rule applied to catalogue or archive data, so the table is reproducible.
- **Attributes.** Dropped from the 200: everything about galaxies, nebulae, comets, small bodies,
  moons, catalogue designations (Messier/NGC), hemisphere visibility, and attributes that cannot be
  decided for all objects (naked-eye visibility, subgiant status, GCVS names). Kept in spirit and
  redefined precisely: multiplicity, white dwarf, variability, exoplanet hosting, habitable zone,
  discovery method, measured mass. New: the ordinal temperature chain, ultracool/fully convective
  boundaries, white-dwarf atmosphere classes, companion types, mass regimes, instellation
  thresholds, knowledge-status attributes.
- **Scaling.** Many-valued quantities (spectral type, multiplicity, mass, instellation) are scaled
  ordinally with physically motivated thresholds instead of one nominal attribute per class.

---

## 10. References

**Catalogues and data**
- Reylé, C., Jardine, K., Fouqué, P., Caballero, J. A., Smart, R. L., Sozzetti, A. 2021,
  *The 10 parsec sample in the Gaia era*, A&A 650, A201.
- Reylé, C., Jardine, K., Fouqué, P., Caballero, J. A., Smart, R. L., Sozzetti, A. 2022,
  *The 10 parsec sample in the Gaia era: first update*, 21st Cambridge Workshop on Cool Stars,
  Zenodo, doi:10.5281/zenodo.7669746; arXiv:2302.02810.
- CDS catalogue J/A+A/650/A201 (v2, August 2023); data also at gruze.org/10pc and
  dc.zah.uni-heidelberg.de/10pcsample.
- Golovin, A., Reffert, S., Just, A., et al. 2023, *The Fifth Catalogue of Nearby Stars (CNS5)*,
  A&A 670, A19.
- Akeson, R. L., et al. 2013, *The NASA Exoplanet Archive*, PASP 125, 989; Planetary Systems
  Composite Parameters table, doi:10.26133/NEA13.
- Rein, H. 2012, *A proposal for community driven and decentralized astronomical databases and
  the Open Exoplanet Catalogue*, arXiv:1211.7121.

**Thresholds and classification schemes**
- Chabrier, G., Baraffe, I. 1997, A&A 327, 1039 (fully convective boundary).
- Kirkpatrick, J. D., Henry, T. J., Irwin, M. J. 1997, AJ 113, 1421 (ultracool dwarfs, M7 and later).
- Kirkpatrick, J. D. 2005, ARA&A 43, 195 (L and T classes); Cushing, M. C., et al. 2011, ApJ 743, 50 (Y class).
- Sion, E. M., et al. 1983, ApJ 269, 253 (white-dwarf spectral classification).
- Chen, J., Kipping, D. 2017, ApJ 834, 17 (mass regimes).
- Kopparapu, R. K., et al. 2013, ApJ 765, 131; Kopparapu, R. K., et al. 2014, ApJL 787, L29 (habitable zone).
- Sanchis-Ojeda, R., et al. 2014, ApJ 787, 47 (ultra-short-period planets).

**Individual objects**
- Schneider, A. C., et al. 2020, ApJ 898, 77; Lodieu, N., et al. 2022, A&A 663, A84;
  Burgasser, A. J., et al. 2024 (CWISE J1810−1010).
- Kaminski, A., et al. 2018, A&A 618, A115 (GJ 752 A b = HD 180617 b).
- Gaia DR3 variability as summarised in Reylé et al. 2022, Sect. 3.2 (Eyer, L., et al. 2023, A&A 674, A13).
