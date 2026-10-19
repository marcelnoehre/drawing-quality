# Groupings

Every grouping used to build a scale, with the reason it was chosen, written
**before any drawing**. Nothing here may be revised after drawing results are
seen. We choose the scales and then evaluate drawings on them, so this file is
what separates a considered choice from one tuned to the answer.

Scale attributes are original attributes or conjunctions of them, never
disjunctions or negations.

---

## diagnosis

Recorded 2026-10-15T16:02:31+02:00, from `contexts/diagnosis/diagnosis.cxt`, 120 objects
and 17 attributes, imported unchanged from the surrounding repository. Reviewed and
approved before this record was written; no scale of this context had been drawn.

Each variable is encoded as a yes and a no attribute (temperature as three
intervals); every scale takes a variable whole.

### Groups

| Group | Variables | What it is |
|---|---|---|
| lower | urine pushing, micturition pains, burning of the urethra | lower urinary tract symptoms, typical of bladder inflammation |
| upper | temperature, nausea, lumbar pain | upper-tract and systemic signs, typical of renal pelvis nephritis |
| diagnosis | bladder inflammation, pelvis nephritis | what the patient was diagnosed with |

The two symptom groups are the clinical pictures of the two diagnoses in the data.
Temperature is upper: fever is the hallmark of an upper-tract infection.

### Scales

| Scale | Groups | Concepts | The view, in one sentence | Drawn |
|---|---|---|---|---|
| `diagnosis_lower` | lower | 19 | The lower urinary tract symptoms: urgency, pain on urination, burning. | yes |
| `diagnosis_upper` | upper | 18 | The signs of upper-tract, systemic illness: fever, nausea, back pain. | yes |
| `diagnosis_diagnosis` | diagnosis | 10 | What the patient was diagnosed with. | no, below 12 |
| `diagnosis_lower_diagnosis` | lower + diagnosis | 38 | Which lower-tract symptoms go with which diagnosis. | yes |
| `diagnosis_upper_diagnosis` | upper + diagnosis | 36 | Which upper-tract and systemic signs go with which diagnosis. | yes |
| `diagnosis_symptoms` | lower + upper | 78 | The patient's whole presentation, before any diagnosis. | yes |
| `diagnosis` | all | 88 | The data themselves. | yes |

The name `diagnosis_diagnosis` follows the naming rule, context and group both being
called diagnosis; kept deliberately.

### No refinement chain

A diagnosis is a conclusion drawn from the symptoms, not a subdivision of them.

### Rejected

| Candidate | Why not |
|---|---|
| one scale per symptom | a single yes/no variable gives at most 4 concepts |
| temperature apart from nausea and lumbar pain | fever belongs to the upper-tract picture |

### Result

Seven scales, six of them drawable, 12 nested pairs of which 9 are usable. The step
from `symptoms` (78) to the full context (88) is shallow, ratio 1.13, flagged in the
manifest. No drawable scale has two equivalent attributes, and no object shares a
name with an attribute.
