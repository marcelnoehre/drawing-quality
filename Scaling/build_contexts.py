"""Clean the collected data sets and generate the five formal contexts.

Reads the material under ``Datasets/`` and writes one Burmeister ``.cxt`` file per
data set into ``contexts/<name>/<name>.cxt``.

Two of the contexts (musical instruments, olympic disciplines) are built from a
binary matrix plus a codebook, so this script only converts and renames.  The
three astronomy contexts are rebuilt from the many-valued source tables that
accompany them: every attribute is recomputed here from the same rule that the
original pipeline used, and the result is compared against the context file that
pipeline produced.  A mismatch is reported and is a bug in this script.

Usage:

    .venv/bin/python build_contexts.py            # build and verify
    .venv/bin/python build_contexts.py --quiet    # build, report only problems

Nothing under ``Datasets/`` is modified.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
DATASETS = ROOT / "Datasets"
CONTEXTS = ROOT / "contexts"


# --------------------------------------------------------------------------
# Burmeister format
# --------------------------------------------------------------------------

def write_cxt(path: Path, objects: list[str], attributes: list[str],
              incidence: list[list[bool]]) -> None:
    """Write a formal context in Burmeister (.cxt) format."""
    if len(set(objects)) != len(objects):
        raise ValueError(f"{path.name}: duplicate object names")
    if len(set(attributes)) != len(attributes):
        raise ValueError(f"{path.name}: duplicate attribute names")
    if len(incidence) != len(objects):
        raise ValueError(f"{path.name}: {len(incidence)} rows for {len(objects)} objects")
    if any(len(row) != len(attributes) for row in incidence):
        raise ValueError(f"{path.name}: row length does not match the attribute count")

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        f.write("B\n\n%d\n%d\n\n" % (len(objects), len(attributes)))
        for o in objects:
            f.write(o + "\n")
        for a in attributes:
            f.write(a + "\n")
        for row in incidence:
            f.write("".join("X" if v else "." for v in row) + "\n")


def read_cxt(path: Path) -> tuple[list[str], list[str], list[list[bool]]]:
    """Read a Burmeister .cxt file; used to verify against the published contexts."""
    lines = path.read_text().splitlines()
    if lines[0].strip() != "B":
        raise ValueError(f"{path}: not a Burmeister file")
    n_obj, n_att = int(lines[2]), int(lines[3])
    body = [l for l in lines[4:] if l != ""] if lines[4] == "" else lines[4:]
    objects = body[:n_obj]
    attributes = body[n_obj:n_obj + n_att]
    rows = body[n_obj + n_att:n_obj + n_att + n_obj]
    incidence = [[c == "X" for c in row] for row in rows]
    return objects, attributes, incidence


def read_table(path: Path) -> pd.DataFrame:
    """Read a CSV as plain strings, so that empty means empty and nothing is coerced."""
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def copy_table(source: Path, target: Path) -> None:
    """Copy a source table next to the context it explains, unchanged."""
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source.read_text())


def num(value: str):
    """Return the value as a float, or None when the field is empty."""
    value = (value or "").strip()
    if value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def incidence_from(records, rules) -> list[list[bool]]:
    return [[bool(rule(r)) for _, rule in rules] for r in records]


# --------------------------------------------------------------------------
# 1. Musical instruments
# --------------------------------------------------------------------------

def build_instruments():
    matrix = read_table(DATASETS / "musical_instruments_matrix.csv")
    codebook = read_table(DATASETS / "musical_instruments_codebook.csv")

    objects = matrix.iloc[:, 0].tolist()
    columns = list(matrix.columns[1:])
    names = dict(zip(codebook["Column_name_in_matrix"], codebook["Characteristic"]))
    missing = [c for c in columns if c not in names]
    if missing:
        raise ValueError(f"instruments: no codebook entry for {missing}")

    attributes = [names[c] for c in columns]
    incidence = [[matrix.at[i, c] == "1" for c in columns] for i in matrix.index]
    return "instruments", objects, attributes, incidence


# --------------------------------------------------------------------------
# 2. Olympic disciplines
# --------------------------------------------------------------------------

def build_olympics():
    matrix = read_table(DATASETS / "olympic_disciplines_2024_2026_2028_complete_matrix.csv")
    codebook = read_table(DATASETS / "olympic_disciplines_2024_2026_2028_complete_codebook.csv")

    # The first three columns are the object name and two descriptive fields that
    # are not attributes of the context.
    objects = matrix.iloc[:, 0].tolist()
    columns = [c for c in matrix.columns[1:] if c not in ("Governing_sport", "Games")]
    names = dict(zip(codebook["Column_name_in_matrix"], codebook["Characteristic"]))
    missing = [c for c in columns if c not in names]
    if missing:
        raise ValueError(f"olympics: no codebook entry for {missing}")

    attributes = [names[c] for c in columns]
    incidence = [[matrix.at[i, c] == "1" for c in columns] for i in matrix.index]
    return "olympics", objects, attributes, incidence


# --------------------------------------------------------------------------
# 3. White dwarfs within 40 pc
# --------------------------------------------------------------------------
# Attribute rules follow Datasets/white_dwarfs/build_wd_context.py, recomputed
# here from the many-valued table wd40pc_source.csv.

def _wd_letters(sp: str) -> str:
    core = sp.replace("pec", "").replace("(warm)", "").replace(":", "").strip()
    return core[1:] if core.startswith("D") else core


def _wd_primary(sp: str) -> str:
    return _wd_letters(sp)[:1]


def _wd_has(sp: str, ch: str) -> bool:
    return ch in re.sub(r"[^A-Z]", "", _wd_letters(sp))


def _wd_secondary_has(sp: str, ch: str) -> bool:
    return ch in re.sub(r"[^A-Z]", "", _wd_letters(sp))[1:]


WD_UNRESOLVED = re.compile(r"Double degenerate|triple degenerate|non-single-star", re.I)


def build_white_dwarfs():
    table = read_table(DATASETS / "white_dwarfs" / "wd40pc_source.csv")
    records = table.to_dict("records")

    def companions(r) -> set[str]:
        return {k for k in r["wide_companions"].split("+") if k}

    def system_size(r) -> int:
        return int(num(r["wide_system_size"]) or 0)

    def gt(r, key, x):
        v = num(r[key])
        return v is not None and v > x

    def lt(r, key, x):
        v = num(r[key])
        return v is not None and v < x

    rules = [
        # spectral features
        ("hydrogen lines (A)", lambda r: _wd_has(r["spectral_type"], "A")),
        ("helium lines (B)", lambda r: _wd_has(r["spectral_type"], "B")),
        ("featureless spectrum (DC)", lambda r: _wd_primary(r["spectral_type"]) == "C"),
        ("carbon features (Q)", lambda r: _wd_has(r["spectral_type"], "Q")),
        ("metal lines (Z, polluted)", lambda r: _wd_has(r["spectral_type"], "Z")),
        ("magnetic (H or P)", lambda r: _wd_secondary_has(r["spectral_type"], "H")
            or _wd_secondary_has(r["spectral_type"], "P")),
        ("emission lines (e)", lambda r: bool(re.search(r"e$", r["spectral_type"].replace("pec", "")))),
        ("peculiar, warm or uncertain type", lambda r: "pec" in r["spectral_type"]
            or ":" in r["spectral_type"] or _wd_primary(r["spectral_type"]) == "X"
            or "(warm)" in r["spectral_type"]),
        # atmosphere and fit
        ("hydrogen-dominated atmosphere (fit)", lambda r: r["fit_composition"] == "H"),
        ("Gaia parameters available", lambda r: num(r["mass_corrected_Msun"]) is not None
            and num(r["teff_corrected_K"]) is not None),
        ("IR-faint (collision-induced absorption)", lambda r: r["comment"].startswith("IR-faint")),
        # mass, interordinal
        ("mass < 0.45 Msun (low mass)", lambda r: lt(r, "mass_corrected_Msun", 0.45)),
        ("mass > 0.9 Msun (massive)", lambda r: gt(r, "mass_corrected_Msun", 0.9)),
        ("mass > 1.1 Msun (ultramassive)", lambda r: gt(r, "mass_corrected_Msun", 1.1)),
        # temperature, ordinal
        ("Teff > 5000 K", lambda r: gt(r, "teff_corrected_K", 5000)),
        ("Teff > 10500 K", lambda r: gt(r, "teff_corrected_K", 10500)),
        ("Teff > 12500 K", lambda r: gt(r, "teff_corrected_K", 12500)),
        # cooling age, ordinal
        ("cooling age > 0.1 Gyr", lambda r: gt(r, "cooling_age_Gyr", 0.1)),
        ("cooling age > 1 Gyr", lambda r: gt(r, "cooling_age_Gyr", 1.0)),
        ("cooling age > 10 Gyr", lambda r: gt(r, "cooling_age_Gyr", 10.0)),
        # binarity
        ("in wide binary or multiple (A6)", lambda r: system_size(r) > 0),
        ("wide main-sequence companion", lambda r: "MS" in companions(r)),
        ("wide white-dwarf companion", lambda r: "WD" in companions(r)),
        ("wide brown-dwarf companion", lambda r: "BD" in companions(r)),
        ("wide system with >=3 members", lambda r: system_size(r) >= 3),
        ("unresolved binary evidence (DD or Gaia orbit)",
            lambda r: bool(WD_UNRESOLVED.search(r["comment"]))),
        # observational
        ("within 20 pc", lambda r: (num(r["parallax_mas"]) or 0.0) >= 50.0),
        ("within 10 pc", lambda r: (num(r["parallax_mas"]) or 0.0) >= 100.0),
    ]

    objects = [r["name"] for r in records]
    return "wd40pc", objects, [n for n, _ in rules], incidence_from(records, rules)


# --------------------------------------------------------------------------
# 4 and 5. The 10 pc sample: stars and exoplanets
# --------------------------------------------------------------------------
# Attribute rules follow Datasets/stars_exoplanets/build_contexts.py, recomputed
# here from tenpc_stars_source.csv and tenpc_exoplanets_source.csv.

SPECTRAL_CLASSES = "OBAFGKMLTY"

# The 17 objects Reylé et al. (2022), Sect. 3.2, report as variable in Gaia DR3.
GAIA_VARIABLE = {
    "GJ 625", "AN Sex", "GJ 1151", "L 49-19", "G 19-7", "MCC 135", "BD+43 2796",
    "BD+16 2708 A", "HD 100623 B", "Ross 248", "DENIS J104814.6-395606", "GJ 643",
    "GJ 486", "L 173-19", "LP 655-48", "BD+61 195 B", "GJ 867 B",
}

JUPITER_IN_EARTH_MASSES = 317.828


def sptval(sp: str):
    """Position on the OBAFGKMLTY sequence (class * 10 + subtype); None for a white dwarf."""
    if not sp or sp.startswith("D"):
        return None
    m = re.search(r"([OBAFGKMLTY])\s*(\d+(?:\.\d+)?)?", sp.replace("esd", "").replace("sd", ""))
    if not m:
        return None
    return SPECTRAL_CLASSES.index(m.group(1)) * 10 + (float(m.group(2)) if m.group(2) else 0.0)


def _seff(teff: float, s0, a, b, c, d) -> float:
    t = teff - 5780.0
    return s0 + a * t + b * t ** 2 + c * t ** 3 + d * t ** 4


def hz_edges(teff: float) -> tuple[float, float]:
    """Conservative habitable zone of Kopparapu et al. (2014): runaway and maximum greenhouse."""
    inner = _seff(teff, 1.107, 1.332e-4, 1.580e-8, -8.308e-12, -1.931e-15)
    outer = _seff(teff, 0.356, 6.171e-5, 1.698e-9, -3.198e-12, -5.575e-16)
    return inner, outer


def _tenpc_tables():
    stars = read_table(DATASETS / "stars_exoplanets" / "tenpc_stars_source.csv").to_dict("records")
    planets = read_table(DATASETS / "stars_exoplanets" / "tenpc_exoplanets_source.csv").to_dict("records")

    by_system: dict[str, list[dict]] = {}
    for r in stars:
        by_system.setdefault(r["system"], []).append(r)
    for r in stars:
        if len(by_system[r["system"]]) != int(r["n_system_bodies"]):
            raise ValueError(
                f"tenpc: system '{r['system']}' has {len(by_system[r['system']])} rows but the "
                f"table says {r['n_system_bodies']} bodies; grouping by system name is unsafe")

    planets_of: dict[str, list[dict]] = {}
    for p in planets:
        planets_of.setdefault(p["host"], []).append(p)

    def in_hz(p) -> bool:
        inner, outer = hz_edges(float(p["host_Teff"]))
        s = float(p["instellation_Searth"])
        return s > outer and not s > inner

    return stars, planets, by_system, planets_of, in_hz


def build_tenpc():
    stars, planets, by_system, planets_of, in_hz = _tenpc_tables()

    def siblings(r):
        return [o for o in by_system[r["system"]] if o is not r]

    def magnitude(r):
        for key in ("G", "G_estimated"):
            v = num(r[key])
            if v is not None:
                return v
        return None

    def brightest(system: str):
        candidates = [o for o in by_system[system] if magnitude(o) is not None]
        if not candidates:
            return None
        return min(candidates, key=lambda o: (magnitude(o),
                                              sptval(o["spectral_type"]) if sptval(o["spectral_type"]) is not None else 99,
                                              o["object"]))

    def hosted(r):
        return planets_of.get(r["object"], [])

    def spt_at_least(r, threshold):
        v = sptval(r["spectral_type"])
        return (v if v is not None else -1) >= threshold

    def wd_letters(r):
        sp = r["spectral_type"] or ""
        return re.sub(r"[^A-Z]", "", sp[1:]) if sp.startswith("D") else ""

    star_rules = [
        ("hydrogen-burning star", lambda r: r["catalogue_class"] in ("*", "LM", "LM?")),
        ("brown dwarf", lambda r: r["catalogue_class"] in ("BD", "BD?")),
        ("white dwarf", lambda r: r["catalogue_class"] in ("WD", "WD?")),
        ("class unconfirmed (candidate)", lambda r: r["catalogue_class"].endswith("?")),
        ("SpT on OBAFGKMLTY sequence", lambda r: sptval(r["spectral_type"]) is not None),
        ("SpT G or later", lambda r: spt_at_least(r, 40)),
        ("SpT K or later", lambda r: spt_at_least(r, 50)),
        ("SpT M or later", lambda r: spt_at_least(r, 60)),
        ("SpT M3.5 or later (fully convective)", lambda r: spt_at_least(r, 63.5)),
        ("SpT M7 or later (ultracool)", lambda r: spt_at_least(r, 67)),
        ("SpT L or later", lambda r: spt_at_least(r, 70)),
        ("SpT T or later", lambda r: spt_at_least(r, 80)),
        ("SpT Y", lambda r: spt_at_least(r, 90)),
        ("subdwarf (sd/esd, metal-poor)", lambda r: bool(re.match(r"e?sd", r["spectral_type"] or ""))),
        ("emission-line flag (e) in SpT",
            lambda r: bool(re.search(r"[OBAFGKMLTY]\d*(\.\d+)?e", r["spectral_type"] or ""))),
        ("Gaia DR3 variable (Reyle+2022)", lambda r: r["object"] in GAIA_VARIABLE),
        ("WD spectral type known", lambda r: (r["spectral_type"] or "").startswith("D")),
        ("WD hydrogen atmosphere (DA)", lambda r: (r["spectral_type"] or "").startswith("DA")),
        ("WD metal lines (Z)", lambda r: "Z" in wd_letters(r)),
        ("WD carbon features (Q)", lambda r: "Q" in wd_letters(r)),
        ("WD featureless (DC)", lambda r: (r["spectral_type"] or "").startswith("DC")),
        ("WD magnetic (P/H)", lambda r: (r["spectral_type"] or "").startswith("D")
            and bool(re.search(r"[PH]", re.sub(r"[^A-Z]", "", (r["spectral_type"] or "")[2:])))),
        ("member of multiple system", lambda r: int(r["n_system_bodies"]) >= 2),
        ("member of system with >=3 bodies", lambda r: int(r["n_system_bodies"]) >= 3),
        ("primary (brightest) of multiple system",
            lambda r: int(r["n_system_bodies"]) >= 2 and brightest(r["system"]) is r),
        ("has hydrogen-burning companion",
            lambda r: any(o["catalogue_class"] in ("*", "LM", "LM?") for o in siblings(r))),
        ("has brown-dwarf companion",
            lambda r: any(o["catalogue_class"] in ("BD", "BD?") for o in siblings(r))),
        ("has white-dwarf companion",
            lambda r: any(o["catalogue_class"] in ("WD", "WD?") for o in siblings(r))),
        ("hosts confirmed planet", lambda r: len(hosted(r)) >= 1),
        ("hosts >=2 confirmed planets", lambda r: len(hosted(r)) >= 2),
        ("hosts transiting planet", lambda r: any(p["transiting"] == "True" for p in hosted(r))),
        ("hosts planet in conservative HZ", lambda r: any(in_hz(p) for p in hosted(r))),
        ("member of planet-hosting system",
            lambda r: any(o["object"] in planets_of for o in by_system[r["system"]])),
        ("within 5 pc", lambda r: float(r["distance_pc"]) <= 5.0),
        ("G magnitude measured by Gaia", lambda r: r["G"] != ""),
    ]

    star_of = {r["object"]: r for r in stars}
    star_attribute = {name: rule for name, rule in star_rules}

    def host(p):
        return star_of[p["host"]]

    def host_has(p, attribute):
        return star_attribute[attribute](host(p))

    planet_rules = [
        ("mass > 2.04 Earth (above Terran regime)", lambda p: float(p["mass_earth"]) > 2.04),
        ("mass > 0.414 Jupiter (Jovian regime)",
            lambda p: float(p["mass_earth"]) > 0.414 * JUPITER_IN_EARTH_MASSES),
        ("only minimum mass (m sin i) known", lambda p: p["mass_type"].startswith("Msini")),
        ("ultra-short period (P < 1 d)", lambda p: float(p["period_d"]) < 1.0),
        ("instellation above HZ outer edge",
            lambda p: float(p["instellation_Searth"]) > hz_edges(float(p["host_Teff"]))[1]),
        ("instellation above HZ inner edge",
            lambda p: float(p["instellation_Searth"]) > hz_edges(float(p["host_Teff"]))[0]),
        ("discovered by radial velocity",
            lambda p: p["discovery_method"].lower().startswith(("radial", "rv"))),
        ("transits its host", lambda p: p["transiting"] == "True"),
        ("in multi-planet system", lambda p: len(planets_of[p["host"]]) >= 2),
        ("host in multiple-star system", lambda p: host_has(p, "member of multiple system")),
        ("host SpT M", lambda p: host_has(p, "SpT M or later")),
        ("host fully convective (M3.5 or later)",
            lambda p: host_has(p, "SpT M3.5 or later (fully convective)")),
        ("host SpT has emission-line flag (e)",
            lambda p: host_has(p, "emission-line flag (e) in SpT")),
        ("host within 5 pc", lambda p: host_has(p, "within 5 pc")),
        ("in NASA Exoplanet Archive composite (2026)", lambda p: p["in_NASA_2026"] == "True"),
        ("flagged controversial in NASA archive", lambda p: p["NASA_controversial"] == "1"),
    ]

    star_context = ("tenpc_stars", [r["object"] for r in stars],
                    [n for n, _ in star_rules], incidence_from(stars, star_rules))
    planet_context = ("tenpc_exoplanets", [p["planet"] for p in planets],
                      [n for n, _ in planet_rules], incidence_from(planets, planet_rules))
    return star_context, planet_context


# --------------------------------------------------------------------------
# Verification against the contexts produced by the original pipelines
# --------------------------------------------------------------------------

PUBLISHED = {
    "wd40pc": DATASETS / "white_dwarfs" / "wd40pc.cxt",
    "tenpc_stars": DATASETS / "stars_exoplanets" / "tenpc_stars.cxt",
    "tenpc_exoplanets": DATASETS / "stars_exoplanets" / "tenpc_exoplanets.cxt",
}

# The many-valued table each context was derived from, copied next to it so that the
# numbers behind a threshold attribute can be read without leaving the folder.
MANY_VALUED = {
    "wd40pc": (DATASETS / "white_dwarfs" / "wd40pc_source.csv", "wd40pc_manyvalued.csv"),
    "tenpc_stars": (DATASETS / "stars_exoplanets" / "tenpc_stars_source.csv",
                    "tenpc_stars_manyvalued.csv"),
    "tenpc_exoplanets": (DATASETS / "stars_exoplanets" / "tenpc_exoplanets_source.csv",
                         "tenpc_exoplanets_manyvalued.csv"),
}

# The two hand-built contexts are natively binary, so their counterpart is the
# codebook that defines each attribute.
CODEBOOKS = {
    "instruments": (DATASETS / "musical_instruments_codebook.csv", "instruments_codebook.csv"),
    "olympics": (DATASETS / "olympic_disciplines_2024_2026_2028_complete_codebook.csv",
                 "olympics_codebook.csv"),
}


def write_companion_tables(name: str) -> list[str]:
    """Put the many-valued table, or the codebook, beside the context. Returns filenames."""
    written = []
    for mapping in (MANY_VALUED, CODEBOOKS):
        if name in mapping:
            source, filename = mapping[name]
            copy_table(source, CONTEXTS / name / filename)
            written.append(filename)
    if name == "olympics":
        # The two descriptive columns that are deliberately not attributes of the
        # context: they are the only many-valued data this data set carries.
        matrix = read_table(DATASETS / "olympic_disciplines_2024_2026_2028_complete_matrix.csv")
        matrix[["Discipline", "Governing_sport", "Games"]].to_csv(
            CONTEXTS / name / "olympics_manyvalued.csv", index=False)
        written.append("olympics_manyvalued.csv")
    return written


def verify(name, objects, attributes, incidence) -> list[str]:
    """Compare a rebuilt context with the published one; return a list of problems."""
    reference = PUBLISHED.get(name)
    if reference is None or not reference.exists():
        return []
    ref_objects, ref_attributes, ref_incidence = read_cxt(reference)
    problems = []
    if objects != ref_objects:
        problems.append(f"object list differs ({len(objects)} vs {len(ref_objects)})")
    if attributes != ref_attributes:
        problems.append("attribute list differs")
    if not problems:
        for i, (row, ref_row) in enumerate(zip(incidence, ref_incidence)):
            for j, (v, ref_v) in enumerate(zip(row, ref_row)):
                if v != ref_v:
                    problems.append(
                        f"{objects[i]!r} / {attributes[j]!r}: rebuilt "
                        f"{'X' if v else '.'}, published {'X' if ref_v else '.'}")
    return problems


# --------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quiet", action="store_true", help="report only problems")
    args = parser.parse_args()

    stars, exoplanets = build_tenpc()
    built = [build_instruments(), build_olympics(), build_white_dwarfs(), stars, exoplanets]

    failures = 0
    for name, objects, attributes, incidence in built:
        path = CONTEXTS / name / f"{name}.cxt"
        write_cxt(path, objects, attributes, incidence)
        companions = write_companion_tables(name)
        problems = verify(name, objects, attributes, incidence)
        crosses = sum(sum(row) for row in incidence)
        density = crosses / (len(objects) * len(attributes))
        if not args.quiet:
            print(f"{name:18s} {len(objects):5d} objects x {len(attributes):3d} attributes"
                  f"   density {density:.3f}   -> {path.relative_to(ROOT)}")
            print(f"{'':18s} alongside it: {', '.join(companions)}")
        if problems:
            failures += 1
            print(f"  MISMATCH with {PUBLISHED[name].relative_to(ROOT)}:", file=sys.stderr)
            for p in problems[:10]:
                print(f"    {p}", file=sys.stderr)
            if len(problems) > 10:
                print(f"    ... and {len(problems) - 10} more", file=sys.stderr)
        elif name in PUBLISHED and not args.quiet:
            print(f"{'':18s} verified identical to {PUBLISHED[name].relative_to(ROOT)}")

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
