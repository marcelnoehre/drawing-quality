# Diagnosis

`diagnosis.cxt` — 120 patients described by 17 attributes: six symptoms and
two diagnoses, each variable nominally scaled into its yes and no values, and body
temperature into three intervals. Imported unchanged from the surrounding
repository, `contexts/real-world/original/diagnosis.cxt` (see `.imported-from`).

## Source

The file came without documentation, and none was found in the surrounding
repository. Its shape matches the *Acute Inflammations* data set of the UCI Machine
Learning Repository (Czerniak, J. and Zarzycki, H., 2003): 120 patients, the
symptoms temperature, nausea, lumbar pain, urine pushing, micturition pains and
burning of the urethra, and two diagnoses, inflammation of the urinary bladder and
nephritis of renal pelvis origin. As described there, the data were created by a
medical expert to test a diagnostic expert system, so the diagnoses follow rules
from the symptoms. conexp-clj's context descriptions confirm both, for the file this
one was converted from: "scaled from the data found at
https://archive.ics.uci.edu/ml/datasets/Acute+Inflammations", "created by a medical
expert as a data set to test the expert system" (https://github.com/tomhanika/conexp-clj/blob/master/testing-data/context-descriptions.org).

## Attributes, by what they are about

The count is the number of patients having the attribute. Every variable appears
twice, as its yes and its no value, so each pair of rows below partitions the
patients.

### Lower urinary tract symptoms

| # | Attribute | Count |
|---|---|---|
| 7 | `[Urine pushing yes]` | 80 |
| 5 | `[Urine pushing no]` | 40 |
| 10 | `[Micturition pains yes]` | 59 |
| 1 | `[Micturition pains no]` | 61 |
| 3 | `[Burning yes]` | 50 |
| 2 | `[Burning no]` | 70 |

### Upper-tract and systemic signs

| # | Attribute | Count |
|---|---|---|
| 16 | `[Temperatur [∈ [35.0 37.5]]]` | 39 |
| 12 | `[Temperatur [∈ [37.5 40.0]]]` | 31 |
| 15 | `[Temperatur [∈ [40.0 42.0]]]` | 50 |
| 13 | `[Nausea yes]` | 29 |
| 14 | `[Nausea no]` | 91 |
| 6 | `[Lumbar pain yes]` | 70 |
| 17 | `[Lumbar pain no]` | 50 |

### Diagnoses

| # | Attribute | Count |
|---|---|---|
| 8 | `[Bladder inflammation? yes]` | 59 |
| 11 | `[Bladder inflammation? no]` | 61 |
| 4 | `[Pelvis nephritis? yes]` | 50 |
| 9 | `[Pelvis nephritis? no]` | 70 |

# Scales of this context

Seven scale-measures, built by `../build_scales.py` and verified by
`../verify_scale.py`. The groupings, with the reason for each and the candidates
rejected, are in `groupings.md` beside this file, fixed before any drawing. The
machine-readable summaries are `manifest.csv` and `nesting.csv`.

| Scale | Kind | One sentence | Attributes | Concepts | Width | Height | Drawn |
|---|---|---|---|---|---|---|---|
| `diagnosis_lower` | facet | the lower urinary tract symptoms: urgency, pain on urination, burning | 6 | 19 | 7 | 5 | yes |
| `diagnosis_upper` | facet | the signs of upper-tract, systemic illness: fever, nausea, back pain | 7 | 18 | 7 | 5 | yes |
| `diagnosis_diagnosis` | facet | what the patient was diagnosed with | 4 | 10 | 4 | 4 | no |
| `diagnosis_lower_diagnosis` | apposition | which lower-tract symptoms go with which diagnosis | 10 | 38 | 12 | 7 | yes |
| `diagnosis_upper_diagnosis` | apposition | which upper-tract and systemic signs go with which diagnosis | 11 | 36 | 10 | 7 | yes |
| `diagnosis_symptoms` | apposition | the patient's whole presentation, before any diagnosis | 13 | 78 | 21 | 8 | yes |
| `diagnosis` | full | the data themselves, the identity scale-measure | 17 | 88 | 22 | 9 | yes |

## Why these scales

**The symptoms split as clinical practice splits them.** Urgency, pain on urination
and burning are lower urinary tract symptoms, typical of bladder inflammation.
Fever, nausea and back (lumbar) pain are signs of upper-tract, systemic illness,
typical of renal pelvis nephritis. Those are exactly the two diagnoses in this data,
so the two symptom groups are the two clinical pictures, and each is a view a
clinician would recognise. Temperature belongs with the upper group: fever is the
hallmark of an upper-tract infection.

**A scale takes each variable whole.** Every variable is encoded as a yes and a no
attribute; a scale includes both or neither, so it never shows half of a variable.

**The diagnoses alone are not drawn**: two yes/no variables give 10 concepts, below
the drawable minimum. They are drawn joined to each symptom group, where the view is
which symptoms go with which diagnosis, and in the full context.

**There is no refinement chain.** A diagnosis is a conclusion drawn from the
symptoms, not a subdivision of them.

**Rejected:** one scale per symptom (a single yes/no variable gives at most 4
concepts), and temperature apart from nausea and lumbar pain (fever is part of the
upper-tract picture).

## Nesting

12 nested pairs, of which 9 have both scales drawn. `lower` (19) and `upper` (18) each
nest into their diagnosis view, into `symptoms` (78) and into the full context (88).
For a ladder figure, `lower` nests into `lower_diagnosis` (38), `symptoms` and the full
context.

## Two things to know when reading results

- **The step from `symptoms` (78) to the full context (88) is very shallow**, ratio
  1.13: adding the diagnoses adds almost nothing, because they are nearly determined
  by the symptoms. A comparison across that step shares 78 concepts out of 88, so
  an algorithm has little reason to move anything, and a low tau there would be
  telling.
- **No drawable scale has two equivalent attributes**, and no object shares a name
  with an attribute, so neither known algorithm defect is triggered.

## What is computed from these scales

Of the 7 scales above, **6 are drawable** -- between 12 and 1000 concepts, with width
at least 3 -- from 18 to 88 concepts; the other is recorded and never drawn. Of 12
nested pairs, **9 are usable**: both scales drawable, and sharing at least 8
concepts. From these, `../../run_harness.py` computes:

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
