"""Build the scale-measures of a context and record what was built.

Every scale here is a context on the *same* objects as the original, whose
attributes are either original attributes kept as they are, which is an attribute
projection and a scale-measure by HH Cor. 22, or conjunctions of original
attributes, which are scale-measures by HH Cor. 17. Disjunction and negation are
never used: they are not guaranteed to give a scale-measure.

Scales are not one cumulative chain. They are independent views, each answering a
single question, plus refinement chains where the hierarchy is real and
appositions where the combined view is one somebody would ask for. Every scale is
nested under the full context by definition, so each still gives one usable
coarse-to-fine pair; the chains and appositions add more.

    python contexts/build_scales.py                 # build, measure, verify
    python contexts/build_scales.py --context instruments

Every scale is written into the folder of the context it is derived from, beside
that context, together with a manifest and the nesting matrix. The identity
scale-measure is the original context file itself, so it is not copied. The build
fails if any scale turns out not to be a scale-measure.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

import numpy as np
import conceptflow as cf

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_scale import check_scale_measure, extents_of, nesting_rows, write_matrix  # noqa: E402

HERE = Path(__file__).resolve().parent          # the contexts directory
ROOT = HERE.parent                              # the Scaling directory

CONJUNCTION = " ∧ "   # the symbol used in the attribute names of a scale

# Every scale file is named after its parent context: `<context>_<name>.cxt`, with
# the full context keeping its own name. Lowercase and underscores only, which is
# also exactly what the drawing generators' slug() leaves unchanged, so a scale's
# id survives into every graphml and drawing path as it is. Nothing ever parses an
# id back into its parts -- the manifest's `context` and `short_name` columns are
# the source of truth -- so underscores inside context names are harmless.
SCALE_ID = re.compile(r"^[a-z0-9]+(_[a-z0-9]+)*$")


def scale_id(context: str, spec: dict) -> str:
    """The identifier of a scale, used for its file and everywhere downstream."""
    sid = context if spec["kind"] == "full" else f"{context}_{spec['name']}"
    if not SCALE_ID.match(sid) or not (sid == context or sid.startswith(context + "_")):
        raise ValueError(f"scale id {sid!r} breaks the naming rule: "
                         f"<context>_<name>, lowercase, underscores only")
    return sid

# A transition this shallow is worth noticing in the results rather than assuming
# it is informative.
LOW_RATIO = 1.5

# The drawable band. Below the floor every algorithm produces nearly the same
# picture; above the ceiling a line diagram is no longer readable. A scale outside
# the band is kept for what it shows about the data but is never drawn. Whether an
# algorithm can draw a lattice inside the band is not assumed: every algorithm is
# asked to draw every drawable scale, under a time budget.
DRAWABLE_MIN = 12
DRAWABLE_MAX = 1000
MIN_WIDTH = 3

# Width and height are quadratic in the number of concepts, so above this they are
# left unmeasured rather than allowed to stall the build.
MEASURE_LIMIT = 2000


# ---------------------------------------------------------------------------
# Instruments: the groupings. Also written, in prose, into groupings.md.
# ---------------------------------------------------------------------------

FAMILY = ["Chordophone", "Aerophone", "Membranophone", "Idiophone"]

EXCITATION = ["Bowed", "Plucked", "Hammered strings", "Single reed", "Double reed",
              "Free reed", "Lip excited", "Edge or fipple blown", "Mouth blown",
              "Bellows or bag", "Struck with implement", "Struck with hands",
              "Shaken or clashed"]

MECHANISM = ["Frets", "Valves", "Slide", "Finger holes", "Keyboard", "Pedals"]

CAPABILITY = ["Definite pitch", "Fully chromatic", "Three or more simultaneous pitches",
              "Continuously variable pitch", "Sustaining"]

PRACTICE = ["Symphony orchestra", "Concert or marching band", "Jazz", "Rock and pop",
            "Transposing", "Played seated", "Marching or processional"]

MAKING = ["Wooden body", "Metal body", "Resonator", "Non European origin", "Post 1900",
          "Requires electricity", "Electrical sound"]

# The Hornbostel-Sachs branch structure: each family, split by how it is excited.
FAMILY_EXCITATION = [
    ("Chordophone", "Bowed"), ("Chordophone", "Plucked"), ("Chordophone", "Hammered strings"),
    ("Aerophone", "Single reed"), ("Aerophone", "Double reed"), ("Aerophone", "Free reed"),
    ("Aerophone", "Lip excited"), ("Aerophone", "Edge or fipple blown"),
    ("Aerophone", "Mouth blown"), ("Aerophone", "Bellows or bag"),
    ("Membranophone", "Struck with implement"), ("Membranophone", "Struck with hands"),
    ("Idiophone", "Struck with implement"), ("Idiophone", "Struck with hands"),
    ("Idiophone", "Shaken or clashed"),
]

# One level deeper: those branches split again by the mechanism they use.
FAMILY_EXCITATION_MECHANISM = [
    ("Chordophone", "Plucked", "Frets"), ("Chordophone", "Plucked", "Pedals"),
    ("Chordophone", "Hammered strings", "Keyboard"),
    ("Aerophone", "Lip excited", "Valves"), ("Aerophone", "Lip excited", "Slide"),
    ("Aerophone", "Edge or fipple blown", "Finger holes"),
    ("Aerophone", "Single reed", "Finger holes"), ("Aerophone", "Double reed", "Finger holes"),
    ("Aerophone", "Free reed", "Keyboard"),
    ("Idiophone", "Struck with implement", "Keyboard"),
    ("Idiophone", "Struck with implement", "Pedals"),
]

INSTRUMENT_SCALES = [
    dict(name="excitation", kind="facet", attributes=[(a,) for a in EXCITATION],
         description="How the sound is set going."),
    dict(name="capability", kind="facet", attributes=[(a,) for a in CAPABILITY],
         description="What the instrument can play."),
    dict(name="practice", kind="facet", attributes=[(a,) for a in PRACTICE],
         description="Where and how it is played, including posture and mobility."),
    dict(name="making", kind="facet", attributes=[(a,) for a in MAKING],
         description="What it is made of, where it came from, whether it needs power."),
    dict(name="family_excitation", kind="chain", chain="hornbostel_sachs", step=1,
         attributes=[(f,) for f in FAMILY] + FAMILY_EXCITATION,
         description="Each family split by how it is excited."),
    dict(name="family_excitation_mechanism", kind="chain", chain="hornbostel_sachs", step=2,
         attributes=[(f,) for f in FAMILY] + FAMILY_EXCITATION + FAMILY_EXCITATION_MECHANISM,
         description="Those branches split again by the pitch mechanism they use."),
    dict(name="playing_mechanism", kind="apposition",
         attributes=[(a,) for a in EXCITATION + MECHANISM],
         description="The mechanics of playing: how sound starts and how pitch is chosen."),
    dict(name="family_making", kind="apposition",
         attributes=[(a,) for a in FAMILY + MAKING],
         description="Which families are built from which materials, which is where the "
                     "woodwind and brass distinction actually lives."),
    dict(name="family_practice", kind="apposition",
         attributes=[(a,) for a in FAMILY + PRACTICE],
         description="Which families populate which ensembles."),
    dict(name="capability_practice_making", kind="apposition",
         attributes=[(a,) for a in CAPABILITY + PRACTICE + MAKING],
         description="The instrument as a musician meets it, setting aside how the sound "
                     "is produced: what it can play, where it is played and what it is "
                     "made of."),
    dict(name="instruments", kind="full", attributes=None,
         description="The data themselves, the identity scale-measure (id, K)."),
]


# ---------------------------------------------------------------------------
# Olympic disciplines: the groupings. Also written, in prose, into groupings.md.
# ---------------------------------------------------------------------------

STRUCTURE = ["Team events", "Individual events", "Head to head", "Judged", "Measured",
             "Physical contact"]
EQUIPMENT = ["Ball", "Handheld implement", "Net or goal", "Vehicle board or runner",
             "Helmet or head protection", "Animal"]
VENUE = ["Grass or turf", "Indoor venue", "Ice or snow", "Water", "Outdoor venue",
         "Fixed marked area"]
DEMANDS = ["Endurance", "Explosive power", "Aim", "Running", "Jumping", "Weight classes"]
FORMAT = ["Clock", "Fixed attempts", "Points accumulate", "Draw possible", "Turn taking"]
INSTITUTION = ["Olympic debut before 1950", "Professional circuit", "Major spectator sport",
               "School sport"]
ORIGINS = ["British or Irish origin", "American origin", "Asian origin",
           "Codified before 1900", "Women's event in the frame"]

# The standard sport typology: a result is settled by judging, by measurement or by
# accumulating points, and each of those splits by who contests it.
DECISION = ["Judged", "Measured", "Points accumulate"]
DECISION_STRUCTURE = [
    ("Judged", "Individual events"), ("Judged", "Team events"),
    ("Measured", "Individual events"), ("Measured", "Team events"),
    ("Measured", "Head to head"),
    ("Points accumulate", "Team events"), ("Points accumulate", "Individual events"),
    ("Points accumulate", "Head to head"), ("Head to head", "Physical contact"),
]
DECISION_STRUCTURE_FORMAT = [
    ("Judged", "Individual events", "Fixed attempts"),
    ("Measured", "Individual events", "Clock"),
    ("Measured", "Individual events", "Fixed attempts"),
    ("Points accumulate", "Team events", "Clock"),
    ("Points accumulate", "Team events", "Draw possible"),
    ("Points accumulate", "Individual events", "Turn taking"),
]

# The same equipment behaves differently depending on what it is used on.
EQUIPMENT_MEDIUM = [
    ("Vehicle board or runner", "Ice or snow"), ("Vehicle board or runner", "Water"),
    ("Vehicle board or runner", "Outdoor venue"), ("Ball", "Grass or turf"),
    ("Ball", "Indoor venue"), ("Handheld implement", "Ice or snow"),
    ("Handheld implement", "Water"), ("Handheld implement", "Indoor venue"),
    ("Animal", "Grass or turf"),
]

OLYMPIC_SCALES = [
    dict(name="structure", kind="facet", attributes=[(a,) for a in STRUCTURE],
         description="How the contest is organised and how a winner is settled."),
    dict(name="demands", kind="facet", attributes=[(a,) for a in DEMANDS],
         description="What the discipline asks of the body."),
    dict(name="equipment", kind="facet", chain="equipment_medium", step=1,
         attributes=[(a,) for a in EQUIPMENT],
         description="What is carried, ridden or played with. Also the root of the "
                     "equipment chain."),
    dict(name="venue", kind="facet", attributes=[(a,) for a in VENUE],
         description="Where it is contested and on what surface.",
         note="Ice or snow stands in for the winter programme, which is not an attribute"),
    dict(name="format", kind="facet", attributes=[(a,) for a in FORMAT],
         description="How play is bounded and scored."),
    dict(name="institution", kind="facet", attributes=[(a,) for a in INSTITUTION],
         description="Its standing: age, professionalism, audience, schools."),
    dict(name="origins", kind="facet", attributes=[(a,) for a in ORIGINS],
         description="Where the modern form was codified, and whether women contest it."),
    dict(name="decision_structure", kind="chain", chain="typology", step=1,
         attributes=[(d,) for d in DECISION] + DECISION_STRUCTURE,
         description="How the result is settled, each way split by who contests it."),
    dict(name="decision_structure_format", kind="chain", chain="typology", step=2,
         attributes=[(d,) for d in DECISION] + DECISION_STRUCTURE + DECISION_STRUCTURE_FORMAT,
         description="Those branches split again by how play is bounded."),
    dict(name="equipment_medium", kind="chain", chain="equipment_medium", step=2,
         attributes=[(a,) for a in EQUIPMENT] + EQUIPMENT_MEDIUM,
         description="Equipment split by the medium it is used in: a runner on ice, a "
                     "boat on water and a ball on grass are different sports."),
    dict(name="structure_format", kind="apposition",
         attributes=[(a,) for a in STRUCTURE + FORMAT],
         description="The rules of the contest: how it is run and how it is decided."),
    dict(name="institution_origins", kind="apposition",
         attributes=[(a,) for a in INSTITUTION + ORIGINS],
         description="Where the discipline came from and what standing it now has."),
    dict(name="venue_equipment", kind="apposition",
         attributes=[(a,) for a in VENUE + EQUIPMENT],
         description="What the ground you play on requires you to carry or ride."),
    dict(name="venue_equipment_demands", kind="apposition",
         attributes=[(a,) for a in VENUE + EQUIPMENT + DEMANDS],
         description="The physical side of competing: the surface underfoot, the gear in "
                     "hand and the effort required."),
    dict(name="olympics", kind="full", attributes=None,
         description="The data themselves, the identity scale-measure (id, K).",
         note="motivation only, far outside the drawable band; never feed it to a layout run"),
]

# ---------------------------------------------------------------------------
# Exoplanets within 10 pc: the groupings. Also written, in prose, into groupings.md.
# The four groups are the ones the context's README already uses for its
# attributes. The state of knowledge is kept apart from the planet itself, as that
# README insists, so the minimum-mass flag sits with knowledge, not with mass.
# ---------------------------------------------------------------------------

PLANET = ["mass > 2.04 Earth (above Terran regime)", "mass > 0.414 Jupiter (Jovian regime)",
          "ultra-short period (P < 1 d)", "instellation above HZ outer edge",
          "instellation above HZ inner edge"]
HOST = ["host SpT M", "host fully convective (M3.5 or later)",
        "host SpT has emission-line flag (e)"]
SYSTEM = ["in multi-planet system", "host in multiple-star system"]
# Distance from the Sun is knowledge, not a property of the host: it says where the
# system is relative to us, and in a distance-limited sample it decides how well a
# system is seen. The companion star context files it the same way; groupings.md
# records the choice.
KNOWLEDGE = ["only minimum mass (m sin i) known", "discovered by radial velocity",
             "transits its host", "host within 5 pc",
             "in NASA Exoplanet Archive composite (2026)",
             "flagged controversial in NASA archive"]
BELOW_DRAWABLE = "below the drawable minimum of 12 concepts; recorded, never drawn"

EXOPLANET_SCALES = [
    dict(name="planet", kind="facet", attributes=[(a,) for a in PLANET],
         description="What kind of planet it is: its mass band and how strongly it is irradiated.",
         note=BELOW_DRAWABLE),
    dict(name="host", kind="facet", attributes=[(a,) for a in HOST],
         description="What kind of star it orbits.", note=BELOW_DRAWABLE),
    dict(name="system", kind="facet", attributes=[(a,) for a in SYSTEM],
         description="Whether it has company: other planets, other stars.", note=BELOW_DRAWABLE),
    dict(name="knowledge", kind="facet", attributes=[(a,) for a in KNOWLEDGE],
         description="How it is known: method, mass provenance, distance, archive status."),
    dict(name="host_system", kind="apposition", attributes=[(a,) for a in HOST + SYSTEM],
         description="The planetary system as a whole: what star, how many planets, how "
                     "many stars."),
    dict(name="planet_system", kind="apposition", attributes=[(a,) for a in PLANET + SYSTEM],
         description="Whether planets of a given kind come alone or in company."),
    dict(name="planet_knowledge", kind="apposition",
         attributes=[(a,) for a in PLANET + KNOWLEDGE],
         description="How well each kind of planet is known, and by which method: the "
                     "detection bias made visible."),
    dict(name="planet_host", kind="apposition", attributes=[(a,) for a in PLANET + HOST],
         description="Which kinds of planets orbit which kinds of stars."),
    dict(name="planet_host_system", kind="apposition",
         attributes=[(a,) for a in PLANET + HOST + SYSTEM],
         description="Everything about the planet and where it lives, setting aside how we "
                     "know it."),
    dict(name="tenpc_exoplanets", kind="full", attributes=None,
         description="The data themselves, the identity scale-measure (id, K)."),
]

# ---------------------------------------------------------------------------
# Stars, brown dwarfs and white dwarfs within 10 pc: the groupings. Also written,
# in prose, into groupings.md. The groups follow the context's README, except that
# catalogue facts are kept apart from the object, as its own caveats ask: the
# emission flag ("about the catalogue, not the star"), the candidate flag, the Gaia
# variability flag, distance and Gaia photometry form the knowledge group, and the
# subdwarf flag joins the object's nature.
# ---------------------------------------------------------------------------

STAR_NATURE = ["hydrogen-burning star", "brown dwarf", "white dwarf",
               "subdwarf (sd/esd, metal-poor)"]
STAR_SPECTRAL = ["SpT on OBAFGKMLTY sequence", "SpT G or later", "SpT K or later",
                 "SpT M or later", "SpT M3.5 or later (fully convective)",
                 "SpT M7 or later (ultracool)", "SpT L or later", "SpT T or later", "SpT Y"]
STAR_WD = ["WD spectral type known", "WD hydrogen atmosphere (DA)", "WD metal lines (Z)",
           "WD carbon features (Q)", "WD featureless (DC)", "WD magnetic (P/H)"]
STAR_COMPANY = ["member of multiple system", "member of system with >=3 bodies",
                "primary (brightest) of multiple system", "has hydrogen-burning companion",
                "has brown-dwarf companion", "has white-dwarf companion"]
STAR_PLANETS = ["hosts confirmed planet", "hosts >=2 confirmed planets",
                "hosts transiting planet", "hosts planet in conservative HZ",
                "member of planet-hosting system"]
STAR_KNOWLEDGE = ["class unconfirmed (candidate)", "emission-line flag (e) in SpT",
                  "Gaia DR3 variable (Reyle+2022)", "within 5 pc",
                  "G magnitude measured by Gaia"]

STAR_SCALES = [
    # The classification chain: what kind of object, then its spectral type (which
    # classifies everything but white dwarfs), then the white dwarfs by their own
    # classes. Each step keeps everything before it.
    dict(name="nature", kind="facet", chain="classification", step=1,
         attributes=[(a,) for a in STAR_NATURE],
         description="What kind of object it is. Also the root of the classification chain.",
         note=BELOW_DRAWABLE),
    dict(name="nature_spectral", kind="chain", chain="classification", step=2,
         attributes=[(a,) for a in STAR_NATURE + STAR_SPECTRAL],
         description="Each kind of object placed on the temperature sequence."),
    dict(name="nature_spectral_wd", kind="chain", chain="classification", step=3,
         attributes=[(a,) for a in STAR_NATURE + STAR_SPECTRAL + STAR_WD],
         description="And the white dwarfs split into their own spectral classes."),
    dict(name="spectral", kind="facet", attributes=[(a,) for a in STAR_SPECTRAL],
         description="Where it sits on the temperature sequence.",
         note="a pure chain (width 1): every type contains the next; never a drawing test"),
    dict(name="wd", kind="facet", attributes=[(a,) for a in STAR_WD],
         description="The white-dwarf spectral classes.", note=BELOW_DRAWABLE),
    dict(name="planets", kind="facet", attributes=[(a,) for a in STAR_PLANETS],
         description="Its planets.", note=BELOW_DRAWABLE),
    dict(name="company", kind="facet", attributes=[(a,) for a in STAR_COMPANY],
         description="The system it belongs to: how many bodies, its role, its companions."),
    dict(name="knowledge", kind="facet", attributes=[(a,) for a in STAR_KNOWLEDGE],
         description="What the catalogue records about how it is seen."),
    dict(name="spectral_planets", kind="apposition",
         attributes=[(a,) for a in STAR_SPECTRAL + STAR_PLANETS],
         description="Which kinds of stars host planets."),
    dict(name="spectral_knowledge", kind="apposition",
         attributes=[(a,) for a in STAR_SPECTRAL + STAR_KNOWLEDGE],
         description="How completely each kind of object is catalogued."),
    dict(name="company_planets", kind="apposition",
         attributes=[(a,) for a in STAR_COMPANY + STAR_PLANETS],
         description="The system an object lives in: its companions and its planets."),
    dict(name="spectral_company", kind="apposition",
         attributes=[(a,) for a in STAR_SPECTRAL + STAR_COMPANY],
         description="Which kinds of objects come in company, and with what: multiplicity "
                     "along the temperature sequence."),
    dict(name="physical", kind="apposition",
         attributes=[(a,) for a in STAR_NATURE + STAR_SPECTRAL + STAR_WD + STAR_COMPANY
                     + STAR_PLANETS],
         description="Everything about the object and its system, setting aside how it is "
                     "catalogued."),
    dict(name="tenpc_stars", kind="full", attributes=None,
         description="The data themselves, the identity scale-measure (id, K)."),
]

# ---------------------------------------------------------------------------
# White dwarfs within 40 pc: the groupings. Also written, in prose, into
# groupings.md. The groups follow the context's README; knowledge -- whether a Gaia
# fit exists, and the two nearer reference volumes -- is kept apart from the object,
# as in the two 10 pc contexts. "Peculiar, warm or uncertain type" bundles a
# physical fact with a knowledge fact and cannot be split, so it stays spectral.
# ---------------------------------------------------------------------------

WD_SPECTRAL = ["hydrogen lines (A)", "helium lines (B)", "featureless spectrum (DC)",
               "carbon features (Q)", "metal lines (Z, polluted)", "magnetic (H or P)",
               "emission lines (e)", "peculiar, warm or uncertain type"]
WD_ATMOSPHERE = ["hydrogen-dominated atmosphere (fit)", "IR-faint (collision-induced absorption)"]
WD_MASS = ["mass < 0.45 Msun (low mass)", "mass > 0.9 Msun (massive)",
           "mass > 1.1 Msun (ultramassive)"]
WD_TEMPERATURE = ["Teff > 5000 K", "Teff > 10500 K", "Teff > 12500 K"]
WD_AGE = ["cooling age > 0.1 Gyr", "cooling age > 1 Gyr", "cooling age > 10 Gyr"]
WD_BINARITY = ["in wide binary or multiple (A6)", "wide main-sequence companion",
               "wide white-dwarf companion", "wide brown-dwarf companion",
               "wide system with >=3 members", "unresolved binary evidence (DD or Gaia orbit)"]
WD_KNOWLEDGE = ["Gaia parameters available", "within 20 pc", "within 10 pc"]
WD_PARAMETERS = WD_MASS + WD_TEMPERATURE + WD_AGE
WD_APPEARANCE = WD_SPECTRAL + WD_ATMOSPHERE
ONE_WIDE = "a pure chain (width 1): every band contains the next; never a drawing test"

WD_SCALES = [
    dict(name="atmosphere", kind="facet", attributes=[(a,) for a in WD_ATMOSPHERE],
         description="What its atmosphere is made of.", note=BELOW_DRAWABLE),
    dict(name="mass", kind="facet", attributes=[(a,) for a in WD_MASS],
         description="How heavy it is.", note=BELOW_DRAWABLE),
    dict(name="temperature", kind="facet", attributes=[(a,) for a in WD_TEMPERATURE],
         description="How hot it is.", note=ONE_WIDE),
    dict(name="age", kind="facet", attributes=[(a,) for a in WD_AGE],
         description="How long it has been cooling.", note=ONE_WIDE),
    dict(name="knowledge", kind="facet", attributes=[(a,) for a in WD_KNOWLEDGE],
         description="How it is seen: whether a fit exists, which reference volume it is in.",
         note=BELOW_DRAWABLE),
    dict(name="binarity", kind="facet", attributes=[(a,) for a in WD_BINARITY],
         description="The company it keeps."),
    dict(name="spectral", kind="facet", attributes=[(a,) for a in WD_SPECTRAL],
         description="What its spectrum shows."),
    dict(name="cooling", kind="apposition", attributes=[(a,) for a in WD_TEMPERATURE + WD_AGE],
         description="Where it is on its cooling track: how hot it still is and how long "
                     "it has been cooling."),
    dict(name="mass_binarity", kind="apposition", attributes=[(a,) for a in WD_MASS + WD_BINARITY],
         description="Whether its mass points to a binary past: low-mass and massive white "
                     "dwarfs against their company."),
    dict(name="parameters", kind="apposition", attributes=[(a,) for a in WD_PARAMETERS],
         description="Its fitted physical parameters: how heavy, how hot, how old."),
    dict(name="appearance", kind="apposition", attributes=[(a,) for a in WD_APPEARANCE],
         description="What its spectrum shows and what its atmosphere is made of."),
    dict(name="spectral_knowledge", kind="apposition",
         attributes=[(a,) for a in WD_SPECTRAL + WD_KNOWLEDGE],
         description="How completely each spectral class is characterised, and how much of "
                     "it lies in the nearest volumes."),
    dict(name="appearance_temperature", kind="apposition",
         attributes=[(a,) for a in WD_APPEARANCE + WD_TEMPERATURE],
         description="Why it looks the way it does: its spectrum against how hot it is."),
    dict(name="parameters_binarity", kind="apposition",
         attributes=[(a,) for a in WD_PARAMETERS + WD_BINARITY],
         description="How mass, temperature and age relate to the company it keeps."),
    dict(name="appearance_parameters", kind="apposition",
         attributes=[(a,) for a in WD_APPEARANCE + WD_PARAMETERS],
         description="Everything about the white dwarf itself, setting aside its company "
                     "and how it is catalogued."),
    dict(name="physical", kind="apposition",
         attributes=[(a,) for a in WD_APPEARANCE + WD_PARAMETERS + WD_BINARITY],
         description="Everything about the white dwarf and its company, setting aside how it "
                     "is catalogued."),
    dict(name="wd40pc", kind="full", attributes=None,
         description="The data themselves, the identity scale-measure (id, K)."),
]

# ---------------------------------------------------------------------------
# Olympic disciplines (imported from the surrounding repository): the groupings.
# Also written, in prose, into groupings.md. The attributes describe a
# discipline's place in the Olympic programme, so the groups are who may enter,
# alone or in teams, where, what kind of sport, and how established it is.
# ---------------------------------------------------------------------------

OD_ENTRY = ["female only events", "male only events", "mixed events", "open events"]
OD_FORMAT = ["individual competition", "team competition"]
OD_VENUE = ["indoor events", "outdoor events"]
OD_SPORT = ["water sport", "ball game", "combat sport", "athletic sport"]
OD_STANDING = ["part of >= 8 olympics", "part of >= 16 olympics", "part of >= 24 olympics",
               ">= 5 events", ">= 10 events", ">= 20 events", "has paralympic equivalent"]
OD_COMPETITORS = OD_ENTRY + OD_FORMAT
OD_DISCIPLINE = OD_SPORT + OD_VENUE

OLYMPIC_DISCIPLINE_SCALES = [
    dict(name="competitors", kind="apposition", attributes=[(a,) for a in OD_COMPETITORS],
         description="Who competes: which genders may enter, and whether alone or in a team."),
    dict(name="standing", kind="apposition", attributes=[(a,) for a in OD_STANDING],
         description="Its place in the Games: how long it has been on the programme, how many "
                     "medal events it has, whether it has a Paralympic counterpart."),
    dict(name="discipline", kind="apposition", attributes=[(a,) for a in OD_DISCIPLINE],
         description="What kind of sport it is and where it is contested."),
    dict(name="sport_competitors", kind="apposition",
         attributes=[(a,) for a in OD_SPORT + OD_COMPETITORS],
         description="Which kinds of sport are contested by whom, alone or in teams."),
    dict(name="sport_standing", kind="apposition",
         attributes=[(a,) for a in OD_SPORT + OD_STANDING],
         description="Which kinds of sport hold what place in the programme."),
    dict(name="competitors_standing", kind="apposition",
         attributes=[(a,) for a in OD_COMPETITORS + OD_STANDING],
         description="How far the programme opens each discipline to women, men and mixed "
                     "teams, against how established and large it is."),
    dict(name="discipline_competitors", kind="apposition",
         attributes=[(a,) for a in OD_DISCIPLINE + OD_COMPETITORS],
         description="The discipline as it is contested -- what sport, where, by whom -- "
                     "setting aside its place in the Games."),
    dict(name="olympic_disciplines", kind="full", attributes=None,
         description="The data themselves, the identity scale-measure (id, K)."),
]

# ---------------------------------------------------------------------------
# Music (imported from the surrounding repository): the groupings. Also written, in
# prose, into groupings.md. Eleven adjectives about how a piece sounds, grouped by
# what they describe. "Playful" is a mood, so character; "sprightly" is energy of
# movement, so motion. Well-rounded and well-balanced hold of exactly the same
# pieces; they are kept apart, as the data has them.
# ---------------------------------------------------------------------------

MUSIC_MOTION = ["fast", "lively", "sprightly", "rhythmizing"]
MUSIC_FORM = ["well-rounded", "well-balanced", "structured thoroughly", "transparent"]
MUSIC_CHARACTER = ["dramatic", "strong", "playful"]

MUSIC_SCALES = [
    dict(name="motion", kind="facet", attributes=[(a,) for a in MUSIC_MOTION],
         description="How the piece moves: its tempo and rhythm."),
    dict(name="form", kind="facet", attributes=[(a,) for a in MUSIC_FORM],
         description="How it is built: proportion, craft, clarity of texture.",
         note=BELOW_DRAWABLE),
    dict(name="character", kind="facet", attributes=[(a,) for a in MUSIC_CHARACTER],
         description="What it expresses.", note=BELOW_DRAWABLE),
    dict(name="form_character", kind="apposition",
         attributes=[(a,) for a in MUSIC_FORM + MUSIC_CHARACTER],
         description="How it is built against what it expresses."),
    dict(name="motion_character", kind="apposition",
         attributes=[(a,) for a in MUSIC_MOTION + MUSIC_CHARACTER],
         description="Its temperament: how it moves and what it expresses."),
    dict(name="motion_form", kind="apposition",
         attributes=[(a,) for a in MUSIC_MOTION + MUSIC_FORM],
         description="How it moves against how it is built."),
    dict(name="music", kind="full", attributes=None,
         description="The data themselves, the identity scale-measure (id, K)."),
]

# ---------------------------------------------------------------------------
# Diagnosis (imported from the surrounding repository): the groupings. Also
# written, in prose, into groupings.md. Six symptoms and two diagnoses, each
# nominally scaled into yes and no; a scale always takes a variable whole. The
# symptoms split as clinical practice splits them: lower urinary tract symptoms,
# typical of bladder inflammation, against upper-tract and systemic signs, typical
# of renal pelvis nephritis.
# ---------------------------------------------------------------------------

DX_LOWER = ["[Urine pushing yes]", "[Urine pushing no]", "[Micturition pains yes]",
            "[Micturition pains no]", "[Burning yes]", "[Burning no]"]
DX_UPPER = ["[Temperatur [\u2208 [35.0 37.5]]]", "[Temperatur [\u2208 [37.5 40.0]]]",
            "[Temperatur [\u2208 [40.0 42.0]]]", "[Nausea yes]", "[Nausea no]",
            "[Lumbar pain yes]", "[Lumbar pain no]"]
DX_DIAGNOSIS = ["[Bladder inflammation? yes]", "[Bladder inflammation? no]",
                "[Pelvis nephritis? yes]", "[Pelvis nephritis? no]"]

DIAGNOSIS_SCALES = [
    dict(name="lower", kind="facet", attributes=[(a,) for a in DX_LOWER],
         description="The lower urinary tract symptoms: urgency, pain on urination, burning."),
    dict(name="upper", kind="facet", attributes=[(a,) for a in DX_UPPER],
         description="The signs of upper-tract, systemic illness: fever, nausea, back pain."),
    dict(name="diagnosis", kind="facet", attributes=[(a,) for a in DX_DIAGNOSIS],
         description="What the patient was diagnosed with.", note=BELOW_DRAWABLE),
    dict(name="lower_diagnosis", kind="apposition",
         attributes=[(a,) for a in DX_LOWER + DX_DIAGNOSIS],
         description="Which lower-tract symptoms go with which diagnosis."),
    dict(name="upper_diagnosis", kind="apposition",
         attributes=[(a,) for a in DX_UPPER + DX_DIAGNOSIS],
         description="Which upper-tract and systemic signs go with which diagnosis."),
    dict(name="symptoms", kind="apposition", attributes=[(a,) for a in DX_LOWER + DX_UPPER],
         description="The patient's whole presentation, before any diagnosis."),
    dict(name="diagnosis", kind="full", attributes=None,
         description="The data themselves, the identity scale-measure (id, K).",
         note="shallow step from symptoms (78 to 88 concepts, ratio 1.13): the diagnoses "
              "are nearly determined by the symptoms"),
]

# ---------------------------------------------------------------------------
# Zoo (imported from the surrounding repository, labels corrected on import; see
# import_standard_contexts.py, LABEL_CORRECTIONS): the groupings. Also written, in
# prose, into groupings.md. Each variable is taken whole, all its values together.
# Milk and mammal, and feathers and bird, hold of exactly the same animals: facts of
# zoology, kept as the data has them.
# ---------------------------------------------------------------------------

ZOO_ANATOMY = [
    '[hair 0]',
    '[hair 1]',
    '[feathers 0]',
    '[feathers 1]',
    '[toothed 0]',
    '[toothed 1]',
    '[backbone 0]',
    '[backbone 1]',
    '[fins 0]',
    '[fins 1]',
    '[leg 0]',
    '[leg 2]',
    '[leg 4]',
    '[leg 5]',
    '[leg 6]',
    '[leg 8]',
    '[tail 0]',
    '[tail 1]',
]
ZOO_PHYSIOLOGY = [
    '[eggs 0]',
    '[eggs 1]',
    '[milk 0]',
    '[milk 1]',
    '[breathes 0]',
    '[breathes 1]',
    '[venomous 0]',
    '[venomous 1]',
]
ZOO_ECOLOGY = [
    '[airborne 0]',
    '[airborne 1]',
    '[aquatic 0]',
    '[aquatic 1]',
    '[predator 0]',
    '[predator 1]',
    '[domestic 0]',
    '[domestic 1]',
    '[catsize 0]',
    '[catsize 1]',
]
ZOO_CLASS = [
    '[type 1]',
    '[type 2]',
    '[type 3]',
    '[type 4]',
    '[type 5]',
    '[type 6]',
    '[type 7]',
]

ZOO_SCALES = [
    dict(name="class", kind="facet", attributes=[(a,) for a in ZOO_CLASS],
         description="Which zoological class it belongs to.", note=BELOW_DRAWABLE),
    dict(name="physiology", kind="facet", attributes=[(a,) for a in ZOO_PHYSIOLOGY],
         description="How its body works: reproduction, breathing, venom."),
    dict(name="class_physiology", kind="apposition",
         attributes=[(a,) for a in ZOO_CLASS + ZOO_PHYSIOLOGY],
         description="How each class reproduces, breathes and defends itself."),
    dict(name="anatomy", kind="facet", attributes=[(a,) for a in ZOO_ANATOMY],
         description="How the animal is built."),
    dict(name="ecology", kind="facet", attributes=[(a,) for a in ZOO_ECOLOGY],
         description="How it lives: whether it flies or swims, hunts, is kept by people, "
                     "how big it is."),
    dict(name="class_anatomy", kind="apposition",
         attributes=[(a,) for a in ZOO_CLASS + ZOO_ANATOMY],
         description="How each class of animal is built."),
    dict(name="class_ecology", kind="apposition",
         attributes=[(a,) for a in ZOO_CLASS + ZOO_ECOLOGY],
         description="Where and how each class of animal lives."),
    dict(name="anatomy_physiology", kind="apposition",
         attributes=[(a,) for a in ZOO_ANATOMY + ZOO_PHYSIOLOGY],
         description="The animal itself, inside and out, setting aside how it lives."),
    dict(name="physiology_ecology", kind="apposition",
         attributes=[(a,) for a in ZOO_PHYSIOLOGY + ZOO_ECOLOGY],
         description="How its body's workings fit its way of life: breathing in water, "
                     "venom for hunting."),
    dict(name="zoo", kind="full", attributes=None,
         description="The data themselves, the identity scale-measure (id, K).",
         note="far outside the drawable band; recorded, never drawn"),
]

# ---------------------------------------------------------------------------
# Living Beings and Water (imported from the surrounding repository), the
# baseline: Hanika and Hirth's published scale-measure, reproduced exactly (their
# Fig. 2: twelve of the nineteen concepts). Their names for its attributes are
# plants, animals, land and water plants, land and water animals, mammals.
# ---------------------------------------------------------------------------

LBW_WATER, LBW_IN_WATER, LBW_LAND = ("needs water to live", "lives in water", "lives on land")
LBW_PLANT, LBW_ANIMAL, LBW_SUCKLES = ("needs chlorophyll to produce food", "can move around",
                                      "suckles its offspring")

LBW_SCALES = [
    dict(name="taxa", kind="apposition",
         attributes=[(LBW_WATER,), (LBW_IN_WATER,), (LBW_PLANT,), (LBW_ANIMAL,),
                     (LBW_LAND, LBW_PLANT), (LBW_IN_WATER, LBW_PLANT),
                     (LBW_LAND, LBW_ANIMAL), (LBW_IN_WATER, LBW_ANIMAL),
                     (LBW_ANIMAL, LBW_SUCKLES)],
         description="Plants and animals by where they live, and the mammals: Hanika and "
                     "Hirth's published scale."),
    dict(name="living_beings_and_water", kind="full", attributes=None,
         description="The data themselves, the identity scale-measure (id, K)."),
]

# ---------------------------------------------------------------------------
# Seasoning planner (imported from the surrounding repository): the groupings.
# Also written, in prose, into groupings.md. The culinary split: herbs are the
# leaves of a plant, spices every other part; spices split by the part, with bark,
# flower, root and bulb merged because each alone is too small. Curry is curry
# powder, a blend, so it sits with the other spices. The dish categories partition
# the dishes.
# ---------------------------------------------------------------------------

SP_HERBS = ["Basilikum gerebelt", "Beifuß gemahlen", "Bohnenkraut gerebelt",
            "Estragon gerebelt", "Lorbeerblätter ganz", "Majoran gerebelt",
            "Oregano gerebelt", "Rosmarin gemahlen", "Thymian gerebelt"]
SP_SEEDS = ["Anis gemahlen", "Koriander gemahlen", "Kümmel gemahlen",
            "Pfeffer \u201cweiß\u201d gemahlen", "Pfeffer \u201cschwarz\u201d gemahlen",
            "Piment gemahlen", "Wacholderbeeren", "Mußkatnuss gemahlen", "Vanillestange",
            "Cayenpfeffer gemahlen", "Paprika \u201cEdelsüß\u201d gemahlen",
            "Paprika \u201cRosen\u201d gemahlen"]
SP_OTHER = ["Zimt gemahlen", "Nelken gemahlen", "Safran gemahlen", "Inger gemahlen",
            "Kurkuma", "Knoblauch granuliert", "Curry gemahlen"]
SP_DISH = ["Gemüse(Gruppierung)", "Fleisch(Gruppierung)", "Geflügel(Gruppierung)",
           "Fisch(Gruppierung)", "Kartoffeln(Gruppierung)", "Reis(Gruppierung)",
           "Saucen(Gruppierung)", "Gebäck/Süßspeisen(Gruppierung)",
           "Verschiedenes(Gruppierung)"]
SP_SPICES = SP_SEEDS + SP_OTHER

SEASONING_SCALES = [
    dict(name="dish", kind="facet", attributes=[(a,) for a in SP_DISH],
         description="The dish categories alone.", note=BELOW_DRAWABLE),
    dict(name="herbs", kind="facet", attributes=[(a,) for a in SP_HERBS],
         description="Which herbs go on the same dishes."),
    dict(name="seeds", kind="facet", attributes=[(a,) for a in SP_SEEDS],
         description="Which seed and fruit spices go on the same dishes."),
    dict(name="other", kind="facet", attributes=[(a,) for a in SP_OTHER],
         description="Which bark, flower, root and bulb spices go on the same dishes."),
    dict(name="spices", kind="apposition", attributes=[(a,) for a in SP_SPICES],
         description="The spices, with the herbs set aside."),
    dict(name="herbs_dish", kind="apposition", attributes=[(a,) for a in SP_HERBS + SP_DISH],
         description="Which herbs go with which kind of dish."),
    dict(name="spices_dish", kind="apposition", attributes=[(a,) for a in SP_SPICES + SP_DISH],
         description="Which spices go with which kind of dish."),
    dict(name="seasonings", kind="apposition", attributes=[(a,) for a in SP_HERBS + SP_SPICES],
         description="The whole seasoning chart, without the dish categories."),
    dict(name="seasoning_planner", kind="full", attributes=None,
         description="The data themselves, the identity scale-measure (id, K)."),
]

CATALOGUE = {"instruments": INSTRUMENT_SCALES, "olympics": OLYMPIC_SCALES,
             "tenpc_exoplanets": EXOPLANET_SCALES, "tenpc_stars": STAR_SCALES,
             "wd40pc": WD_SCALES, "olympic_disciplines": OLYMPIC_DISCIPLINE_SCALES,
             "music": MUSIC_SCALES, "diagnosis": DIAGNOSIS_SCALES, "zoo": ZOO_SCALES,
             "living_beings_and_water": LBW_SCALES, "seasoning_planner": SEASONING_SCALES}


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

def build_scale(original: cf.FormalContext, attributes) -> cf.FormalContext:
    """A context on the same objects whose attributes are the given conjunctions."""
    if attributes is None:
        return original

    index = {name: i for i, name in enumerate(original.attributes)}
    for conjuncts in attributes:
        missing = [c for c in conjuncts if c not in index]
        if missing:
            raise KeyError(f"no such attribute in the original context: {missing}")

    # Canonical column order. The drawing algorithms are deterministic in the file,
    # not in the lattice: shuffling only the attribute columns of one scale changes
    # the drawing in 85% of cases (pipeline.md, *What the algorithms do, measured*).
    # So every scale of a
    # context lists its attributes in one fixed order: by the positions its parts
    # have in the full context, compared as a sorted tuple. Any two attributes that
    # occur in two scales then stand in the same relative order in both, and the
    # only input difference between two levels is the refinement itself. This
    # changes how the file is written, never which attributes it has or what they
    # hold, so the lattice is untouched.
    attributes = sorted(attributes, key=lambda conjuncts: tuple(sorted(index[c] for c in conjuncts)))

    columns, names = [], []
    for conjuncts in attributes:
        column = np.ones(original.n_objects, dtype=bool)
        for conjunct in conjuncts:
            column &= original.incidence[:, index[conjunct]]
        columns.append(column)
        names.append(CONJUNCTION.join(conjuncts))

    if len(set(names)) != len(names):
        raise ValueError("two scale attributes ended up with the same name")
    return cf.FormalContext(objects=tuple(original.objects),
                            attributes=tuple(names),
                            incidence=np.column_stack(columns))


def width(exts: list[frozenset[int]]) -> int:
    """Largest antichain. By Dilworth that is the size minus a maximum matching of
    the strict inclusion order, taken over all comparable pairs, not just covers."""
    items = sorted(exts, key=len)
    n = len(items)
    adjacency: list[list[int]] = [[] for _ in range(n)]
    for a in range(n):
        for b in range(a + 1, n):
            if items[a] < items[b]:
                adjacency[a].append(b)

    matched = [-1] * n

    def augment(u: int, seen: list[bool]) -> bool:
        for v in adjacency[u]:
            if not seen[v]:
                seen[v] = True
                if matched[v] == -1 or augment(matched[v], seen):
                    matched[v] = u
                    return True
        return False

    matching = sum(1 for u in range(n) if augment(u, [False] * n))
    return n - matching


def height(exts: list[frozenset[int]]) -> int:
    """Number of elements of a longest chain."""
    items = sorted(exts, key=len)
    longest: dict[frozenset[int], int] = {}
    for position, a in enumerate(items):
        longest[a] = max((longest[b] + 1 for b in items[:position] if b < a), default=1)
    return max(longest.values()) if longest else 0


def incomparable_pairs(exts: list[frozenset[int]]) -> int:
    """Pairs of concepts neither of which contains the other.

    Recorded for every scale because it is what drives the cost of a two-dimension
    extension: DimDraw's work is orienting incomparable pairs, and its completion
    tracks this far better than it tracks the number of concepts. It is also a
    quadratic stand-in for order dimension, which is NP-hard, if dimension turns
    out to be infeasible at our sizes.
    """
    total = 0
    for i, a in enumerate(exts):
        for b in exts[i + 1:]:
            if not (a <= b or b <= a):
                total += 1
    return total


def measure(scale: cf.FormalContext) -> dict:
    exts = list(extents_of(scale))
    if len(exts) > MEASURE_LIMIT:
        # Quadratic quantities are left unmeasured rather than allowed to stall
        # the build; a scale this large is outside the drawable band anyway.
        return {"concepts": len(exts), "width": None, "height": None,
                "incomparable_pairs": None}
    return {"concepts": len(exts), "width": width(exts), "height": height(exts),
            "incomparable_pairs": incomparable_pairs(exts)}


def is_drawable(stats: dict) -> bool:
    """Whether the drawing pipeline should be given this scale at all."""
    if not DRAWABLE_MIN <= stats["concepts"] <= DRAWABLE_MAX:
        return False
    return stats["width"] is None or stats["width"] >= MIN_WIDTH


# ---------------------------------------------------------------------------

def build_context(name: str, quiet: bool = False) -> int:
    target = HERE / name
    original_path = target / f"{name}.cxt"
    original = cf.io.read_cxt(original_path)

    built: dict[str, cf.FormalContext] = {}
    rows = []
    failures = 0

    for spec in CATALOGUE[name]:
        scale = build_scale(original, spec["attributes"])
        problems = check_scale_measure(original, scale)
        if problems:
            failures += 1
            print(f"FAIL {spec['name']}: not a scale-measure", file=sys.stderr)
            for problem in problems:
                print(f"     {problem}", file=sys.stderr)
            continue

        sid = scale_id(name, spec)
        path = original_path if spec["kind"] == "full" else target / f"{sid}.cxt"
        if spec["kind"] != "full":
            cf.io.write_cxt(scale, path)
        built[sid] = scale
        stats = measure(scale)
        drawable = is_drawable(stats)
        rows.append({
            "context": name,
            "scale": sid,
            "short_name": spec["name"],
            "filename": path.relative_to(ROOT).as_posix(),
            "kind": spec["kind"],
            "chain": spec.get("chain", ""),
            "chain_step": spec.get("step", ""),
            "attributes": len(scale.attributes),
            "concepts": stats["concepts"],
            "width": "" if stats["width"] is None else stats["width"],
            "height": "" if stats["height"] is None else stats["height"],
            "incomparable_pairs": ("" if stats["incomparable_pairs"] is None
                                   else stats["incomparable_pairs"]),
            "drawable": drawable,
            "description": spec["description"],
            "note": spec.get("note", ""),
        })

    if failures:
        return 1

    # Flag shallow transitions inside a chain so they are visible in the results.
    by_id = {r["scale"]: r for r in rows}
    for spec in CATALOGUE[name]:
        if spec["kind"] != "chain" or spec.get("step", 0) < 2:
            continue
        previous = next(s for s in CATALOGUE[name]
                        if s.get("chain") == spec["chain"] and s.get("step") == spec["step"] - 1)
        this, before = by_id[scale_id(name, spec)], by_id[scale_id(name, previous)]
        ratio = this["concepts"] / before["concepts"]
        if ratio < LOW_RATIO:
            this["note"] = (f"low-ratio transition from {before['scale']}: "
                            f"{before['concepts']} to {this['concepts']} concepts, "
                            f"ratio {ratio:.2f}")

    manifest = target / "manifest.csv"
    with manifest.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    matrix = target / "nesting.csv"
    drawable = {r["scale"]: r["drawable"] for r in rows}
    write_matrix(nesting_rows(built, drawable), matrix)

    if not quiet:
        print(f"{name}: {len(rows)} scales -> {target.relative_to(ROOT)}\n")
        print(f"{'scale':44s}{'kind':12s}{'attrs':>6s}{'concepts':>10s}{'width':>7s}"
              f"{'height':>7s}{'incomp':>9s}  drawable")
        for row in rows:
            print(f"{row['scale']:44s}{row['kind']:12s}{row['attributes']:6d}"
                  f"{row['concepts']:10d}{str(row['width']):>7s}{str(row['height']):>7s}"
                  f"{str(row['incomparable_pairs']):>9s}  {'yes' if row['drawable'] else 'NO '}"
                  + ("   " + row["note"] if row["note"] else ""))
        pairs = [r for r in csv.DictReader(matrix.open(encoding="utf-8")) if r["nested"] == "True"]
        print(f"\nevery scale verified as a scale-measure; {len(pairs)} nested pairs "
              f"recorded in {matrix.relative_to(ROOT)}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--context", default="instruments", choices=sorted(CATALOGUE))
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()
    return build_context(args.context, args.quiet)


if __name__ == "__main__":
    raise SystemExit(main())
