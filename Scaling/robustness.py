"""Robustness of the test across contexts.

The Friedman test and the post-hoc comparisons in `friedman.csv` treat the 11
contexts as independent cases and compare algorithms through mean ranks. This
repeats the test three ways, on the combined, quality and consistency scores of
`ranking.csv` (views weighted by log2 of their size):

* **without Living Beings and Water**, the 19-concept published example with one
  usable pair, whose ranking carries the least information;
* **with the three astronomy contexts as one case**: tenpc_stars, tenpc_exoplanets
  and wd40pc share a design (properties of the object against the state of
  knowledge), so they may be less independent than the rest; their scores are
  averaged into one case before ranking;
* **with pairwise Wilcoxon signed-rank tests** of the best-ranked algorithm against
  each other on the per-context scores, Holm-adjusted, in place of the post-hoc
  tests on mean ranks (Benavoli, Corani and Mangili 2016), since whether one
  algorithm beats another then cannot depend on the remaining algorithms.

    python robustness.py          # writes robustness.csv and prints a summary
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

from scipy.stats import rankdata, wilcoxon

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from ranking import ALGORITHMS, ALPHA, friedman_from_ranks, holm_against_control  # noqa: E402

MEASURES = ["combined", "quality", "consistency"]
ASTRONOMY = ("tenpc_stars", "tenpc_exoplanets", "wd40pc")
BASELINE = "living_beings_and_water"


def scores(measure: str) -> dict[str, dict[str, float]]:
    """{context: {algorithm: per-context mean rank}} from ranking.csv, complete contexts only."""
    out: dict[str, dict[str, float]] = {}
    with (HERE / "ranking.csv").open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["context"] != "all" and r["measure"] == measure and r["view_weighting"] == "log2":
                out.setdefault(r["context"], {})[r["algorithm"]] = float(r["mean_rank"])
    return {c: s for c, s in out.items() if set(s) == set(ALGORITHMS)}


def friedman(cases: dict[str, dict[str, float]]) -> tuple[dict, dict[str, float], str, dict]:
    ranks = {c: dict(zip(ALGORITHMS, rankdata([s[a] for a in ALGORITHMS]))) for c, s in cases.items()}
    mean = {a: sum(ranks[c][a] for c in cases) / len(cases) for a in ALGORITHMS}
    test = friedman_from_ranks(mean, len(cases))
    control, versus = holm_against_control(mean, test["se"])
    return test, mean, control, versus


def holm(pvalues: dict[str, float]) -> dict[str, float]:
    adjusted, running, m = {}, 0.0, len(pvalues)
    for i, a in enumerate(sorted(pvalues, key=pvalues.get)):
        running = max(running, min(1.0, (m - i) * pvalues[a]))
        adjusted[a] = running
    return adjusted


def main() -> int:
    rows = []
    for measure in MEASURES:
        base = scores(measure)
        if len(base) < 3:
            print("fewer than three complete contexts; nothing to test", file=sys.stderr)
            return 1
        astronomy = [c for c in ASTRONOMY if c in base]
        merged = {c: s for c, s in base.items() if c not in astronomy}
        if astronomy:
            merged["astronomy"] = {a: sum(base[c][a] for c in astronomy) / len(astronomy)
                                   for a in ALGORITHMS}
        variants = {
            "all contexts": base,
            "without living_beings_and_water": {c: s for c, s in base.items() if c != BASELINE},
            "astronomy as one case": merged,
        }
        for name, cases in variants.items():
            test, mean, control, versus = friedman(cases)
            for a in sorted(ALGORITHMS, key=mean.get):
                v = versus.get(a, {})
                rows.append({"measure": measure, "variant": name, "test": "mean-rank post hoc (Holm)",
                             "n_cases": len(cases), "algorithm": a,
                             "mean_rank": round(mean[a], 3), "chi2_F": round(test["chi2_F"], 3),
                             "p_F_F": test["p_F_F"], "cd_nemenyi": round(test["cd_nemenyi"], 3),
                             "control": control, "p_holm": v.get("p_holm", ""),
                             "significant": v.get("significant_holm", "")})

        # Wilcoxon signed-rank, best against each other, on the per-context scores.
        _, mean, control, _ = friedman(base)
        raw = {}
        for a in ALGORITHMS:
            if a == control:
                continue
            diffs = [base[c][a] - base[c][control] for c in base]
            raw[a] = float(wilcoxon(diffs, alternative="two-sided").pvalue)
        adjusted = holm(raw)
        for a in sorted(raw, key=raw.get):
            rows.append({"measure": measure, "variant": "all contexts", "test": "Wilcoxon (Holm)",
                         "n_cases": len(base), "algorithm": a, "mean_rank": round(mean[a], 3),
                         "chi2_F": "", "p_F_F": "", "cd_nemenyi": "", "control": control,
                         "p_holm": adjusted[a], "significant": adjusted[a] < ALPHA})

    with (HERE / "robustness.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    for measure in MEASURES:
        print(f"\n{measure}")
        for variant, test in [("all contexts", "mean-rank post hoc (Holm)"),
                              ("without living_beings_and_water", "mean-rank post hoc (Holm)"),
                              ("astronomy as one case", "mean-rank post hoc (Holm)"),
                              ("all contexts", "Wilcoxon (Holm)")]:
            sel = [r for r in rows if r["measure"] == measure and r["variant"] == variant
                   and r["test"] == test]
            worse = [r["algorithm"] for r in sel if r["significant"] is True]
            head = sel[0]
            extra = (f"chi2_F {head['chi2_F']:.1f}, p(F_F) {head['p_F_F']:.1e}, "
                     if head["chi2_F"] != "" else "")
            print(f"  {variant + ', ' + test:62s} N={head['n_cases']:2d}  {extra}best "
                  f"{head['control']}; worse beyond chance: {', '.join(worse) or 'none'}")
    print("-> robustness.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
