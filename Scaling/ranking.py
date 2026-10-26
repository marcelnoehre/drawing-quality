"""Rank the algorithms on drawing quality and on consistency, and on both together.

**Two things are ranked, then combined.** Consistency alone can crown an algorithm
that hardly moves anything because it barely lays anything out: the most stable
layouts are not the best ones. So each algorithm is ranked on

* **drawing quality**, by the fourteen metrics of the surrounding repository and
  exactly the aggregation its own analysis uses (`analysis/results.ipynb`):
  ranks within each lattice, averaged within each of four families -- Crossings,
  Layering, Slopes, Clearance -- and the families averaged with equal weight; and
* **consistency**, ours: |Kendall tau| on x-ranks across nested scales. The
  absolute value, because a mirror image of the whole drawing keeps every
  left-to-right relation, the other way round; the signed tau is ranked beside it
  (`consistency_signed`, `combined_signed`) so the effect of that choice is visible.

**Combined, consistency is a fifth family.** The surrounding analysis weights its
families equally so that no aspect counts more for having more metrics; this
applies the same rule once more, to one more aspect of a drawing algorithm: how
stably it draws the same concepts across views. So the combined rank is the mean of
five family ranks, one of them consistency. Reported beside it: quality and
consistency weighted half and half, and the weight on consistency at which the
first place changes hands, so that how much the conclusion depends on the weight is
visible rather than assumed.

**Why ranks, everywhere.** A tau over 13 shared concepts and one over 319 are not
the same kind of number, and neither are a crossing score and a slope score. Within
one comparison -- one lattice for quality, one nested pair for consistency -- every
algorithm is judged on the same thing, so ranks there are comparable. This is the
method Demšar (2006, "Statistical comparisons of classifiers over multiple data
sets", JMLR 7) recommends, and the one the surrounding analysis already uses.

**Failures are ranked last.** An algorithm without a drawing of a scale shares the
last places on every metric of that scale, and on every nested pair that scale is
part of. Nothing is dropped; failing is never better than drawing badly.

**Views are weighted by log2 of their size; contexts weigh equally.** Within every
measure, each scale's comparison counts in proportion to log2 of its number of
concepts, so failing to draw a large view costs more than failing a small one,
without letting any one lattice decide everything (576 concepts count 2.5 times
13). log2|L| is the size measure the surrounding analysis already uses. For
consistency, the pairs ending in the same finer scale share that scale's weight, so
a scale that many others nest into does not count many times. Ranks are averaged
per context and the contexts averaged with equal weight. The same ranking with
every view counting equally is reported beside it.

This is a second weight, separate from the first: the 4/5 to 1/5 split decides how
much each *measure* counts, the view weights how much each *lattice* counts within
a measure. A failure belongs to a view -- it is already last on every measure of
that view -- so only the view weight can make failing a large lattice cost more.

**Only complete contexts are ranked, and partial results say so.** A context is
ranked only when every one of the eight algorithms has a final outcome on every
drawable scale of its manifest and every usable pair of its nesting matrix
(`coverage`). An algorithm that was not run is never dropped from a ranking, and
never mistaken for one that failed. The overall rows (`context = all`) and
`sensitivity.csv` carry `corpus` and `corpus_complete`; anything over fewer than all
contexts is labelled PARTIAL. All three files are rewritten in full on every run.

**Malformed input stops the ranking.** A score or tau that is not a finite number,
a drawn drawing without scores, or an unknown status raises `RankingInputError`.

**Limit.** The ranks are a description, not a test: nested scales of one context
are not independent cases.

    python ranking.py
    python ranking.py --contexts instruments olympics      # labelled PARTIAL
"""

from __future__ import annotations

import csv
import math
import sys
from pathlib import Path

from scipy.stats import chi2 as chi2_dist, f as f_dist, norm, rankdata, studentized_range

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from node_extents import ALGORITHMS  # noqa: E402  the eight; every one must be ranked
CONTEXTS = HERE / "contexts"
FAILED = ("declined", "timeout", "error", "nonterminating", "invalid")
DRAWN = ("drawn", "cached")

# The surrounding repository's metrics and families, as its analysis defines them
# (analysis/results.ipynb, METRICS). The four `_min` variants are not used there.
QUALITY_FAMILIES = {
    "crossings": ["edge_crossing", "crossing_angle"],
    "layering": ["layer_consistency", "vertical_axis_balance"],
    "slopes": ["slope_verticality", "slope_economy", "slope_parallelism",
               "edge_length_uniformity", "slope_standard", "visual_chain_linearity"],
    "clearance": ["node_edge_conflict", "node_node_conflict", "edge_edge_conflict",
                  "nested_suitability"],
}
QUALITY_METRICS = [m for ms in QUALITY_FAMILIES.values() for m in ms]

# How much each view (scale) counts, inside every measure. The ranking uses log2 of
# the number of concepts: failing to draw a large view should cost more than failing
# a small one, and the logarithm keeps any one lattice from deciding everything --
# a 576-concept view counts 2.5 times a 13-concept one, where linear weights would
# make it count 44 times. log2|L| is also the size measure the surrounding
# analysis uses (`log2_n` in analysis/results.ipynb). `equal` is reported beside it.
WEIGHTINGS = {
    "log2": lambda concepts: math.log2(concepts),   # the ranking
    "equal": lambda concepts: 1.0,                  # reported beside it
    "size": lambda concepts: float(concepts),       # linear, for the record only
}
HEADLINE_WEIGHTING = "log2"


def read(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


class RankingInputError(ValueError):
    """A results file holds something the ranking cannot rank honestly.

    Raised rather than worked around: a NaN ranked as a number makes every rank of
    its comparison NaN, and a missing value ranked as a failure punishes an algorithm
    for a gap in our own pipeline.
    """


def _number(text, where: str) -> float:
    """A finite float, or RankingInputError naming where it came from."""
    try:
        value = float(text)
    except (TypeError, ValueError):
        raise RankingInputError(f"{where}: {text!r} is not a number") from None
    if not math.isfinite(value):
        raise RankingInputError(f"{where}: {text!r} is not a finite number")
    return value


def _ranks_with_failures(values: dict[str, float | None], algorithms: list[str]) -> dict[str, float]:
    """Rank 1 = highest value; algorithms with None share the last places."""
    for a, v in values.items():
        if v is not None and not math.isfinite(v):
            raise RankingInputError(f"{a}: value {v!r} cannot be ranked")
    drawn = [a for a in algorithms if values.get(a) is not None]
    failed = [a for a in algorithms if values.get(a) is None]
    ranks = {}
    if drawn:
        for a, r in zip(drawn, rankdata([-values[a] for a in drawn], method="average")):
            ranks[a] = float(r)
    last = (len(drawn) + 1 + len(algorithms)) / 2
    ranks.update({a: last for a in failed})
    return ranks


def consistency_value(row: dict, signed: bool = False) -> float:
    """The ranked consistency of one comparison: |tau|, or tau itself if `signed`.

    |tau| is invariant under mirroring the whole drawing, which negates every x and
    so negates tau and nothing else: a drawing that keeps the shared concepts' order
    the other way round has kept it. The signed tau is ranked beside it, as
    `consistency_signed`, so the effect of this choice is always visible.
    """
    where = (f"consistency {row.get('context')} {row.get('scale_a')} -> "
             f"{row.get('scale_b')} {row.get('algorithm')}")
    tau = _number(row.get("tau_x"), where)
    if not -1 - 1e-9 <= tau <= 1 + 1e-9:
        raise RankingInputError(f"{where}: tau {tau} outside [-1, 1]")
    return tau if signed else abs(tau)


def rank_context(context: str, consistency: list[dict], sizes: dict[str, int],
                 weighting: str, pairs: list[tuple[str, str]] | None = None,
                 algorithms: list[str] | None = None,
                 signed: bool = False) -> tuple[dict[str, float], list[str]]:
    """Mean weighted consistency rank per algorithm in one context, and those left out.

    `pairs` and `algorithms`, when given, are the comparisons and algorithms that must
    be there (from the manifests); otherwise whatever the rows contain is used.
    """
    rows = [r for r in consistency if r["context"] == context and r["usable"] == "True"]
    if pairs is None:
        pairs = sorted({(r["scale_a"], r["scale_b"]) for r in rows})
    if algorithms is None:
        algorithms = sorted({r["algorithm"] for r in rows})
    by_key = {(r["scale_a"], r["scale_b"], r["algorithm"]): r for r in rows}

    # Only algorithms with an outcome on every pair are ranked; one that was simply
    # not run must not look like one that failed.
    complete = [a for a in algorithms if all((p[0], p[1], a) in by_key for p in pairs)]
    left_out = [a for a in algorithms if a not in complete]

    per_finer: dict[str, int] = {}
    for _, fine in pairs:
        per_finer[fine] = per_finer.get(fine, 0) + 1
    weight_of = WEIGHTINGS[weighting]

    total = {a: 0.0 for a in complete}
    weights = 0.0
    for coarse, fine in pairs:
        taus = {}
        for a in complete:
            r = by_key[(coarse, fine, a)]
            if r["status"] == "ok":
                taus[a] = consistency_value(r, signed)
            elif r["status"] == "failed":
                taus[a] = None
            else:
                raise RankingInputError(f"consistency {context} {coarse} -> {fine} {a}: "
                                        f"unknown status {r['status']!r}")
        ranks = _ranks_with_failures(taus, complete)
        w = weight_of(sizes[fine]) / per_finer[fine]
        weights += w
        for a in complete:
            total[a] += w * ranks[a]
    return ({a: total[a] / weights for a in complete} if weights else {}), left_out


def quality_context(context: str, drawings: list[dict], quality: list[dict],
                    sizes: dict[str, int] | None = None, weighting: str = "equal",
                    scales: list[str] | None = None, algorithms: list[str] | None = None
                    ) -> tuple[dict[str, dict[str, float]], list[str]]:
    """Mean rank per algorithm and quality family in one context, and those left out.

    Exactly the surrounding analysis's aggregation, with failures added: on every
    scale, rank the algorithms on each metric (failed drawings last), average the
    metric ranks within each family, then average over the scales, each scale
    weighted by `weighting` of its number of concepts.

    A drawn drawing without a complete row of finite scores is an error, never a
    failure: the gap would be ours, not the algorithm's.
    """
    mine = [r for r in drawings if r["context"] == context]
    if scales is None:
        scales = sorted({r["scale"] for r in mine})
    if algorithms is None:
        algorithms = sorted({r["algorithm"] for r in mine})
    status = {(r["scale"], r["algorithm"]): r["status"] for r in mine}
    complete = [a for a in algorithms if all((s, a) in status for s in scales)]
    left_out = [a for a in algorithms if a not in complete]
    scores = {(r["scale"], r["algorithm"]): r for r in quality if r["context"] == context}

    weight_of = WEIGHTINGS[weighting]
    weight = {s: weight_of(sizes[s]) if sizes else 1.0 for s in scales}
    total_weight = sum(weight.values())
    acc = {a: {f: 0.0 for f in QUALITY_FAMILIES} for a in complete}
    for scale in scales:
        values_by_metric = {m: {} for m in QUALITY_METRICS}
        for a in complete:
            state = status[(scale, a)]
            if state in FAILED:
                for m in QUALITY_METRICS:
                    values_by_metric[m][a] = None
                continue
            if state not in DRAWN:
                raise RankingInputError(f"drawing {context} {scale} {a}: unknown status {state!r}")
            row = scores.get((scale, a))
            if row is None:
                raise RankingInputError(f"quality {context} {scale} {a}: drawn but never scored")
            for m in QUALITY_METRICS:
                values_by_metric[m][a] = _number(row.get(m), f"quality {context} {scale} {a} {m}")
        for family, metrics in QUALITY_FAMILIES.items():
            family_rank = {a: 0.0 for a in complete}
            for m in metrics:
                for a, r in _ranks_with_failures(values_by_metric[m], complete).items():
                    family_rank[a] += r / len(metrics)
            for a in complete:
                acc[a][family] += family_rank[a] * weight[scale] / total_weight
    return acc, left_out


def coverage(context: str, manifest: list[dict], nesting: list[dict], drawings: list[dict],
             quality: list[dict], consistency: list[dict]) -> list[str]:
    """What is missing before this context can be ranked; empty when nothing is.

    Complete means: every algorithm has a final outcome on every drawable scale of
    the manifest, every drawn drawing has its scores, and every usable pair of
    the nesting matrix has a comparison for every algorithm whose status agrees
    with the drawings. The manifests and the nesting matrix are the source of truth,
    so rows left over from scales that no longer exist are never ranked.
    """
    problems = []
    drawable = [r["scale"] for r in manifest if r["drawable"] == "True"]
    status = {(r["scale"], r["algorithm"]): r["status"]
              for r in drawings if r["context"] == context}
    scored = {(r["scale"], r["algorithm"]) for r in quality if r["context"] == context}
    for scale in drawable:
        for a in ALGORITHMS:
            state = status.get((scale, a))
            if state is None:
                problems.append(f"{a} not attempted on {scale}")
            elif state not in DRAWN + FAILED:
                problems.append(f"{a} on {scale}: unknown status {state!r}")
            elif state in DRAWN and (scale, a) not in scored:
                problems.append(f"{a} on {scale}: drawn but not scored")
    compared = {(r["scale_a"], r["scale_b"], r["algorithm"]): r["status"]
                for r in consistency if r["context"] == context}
    for p in nesting:
        if p["usable"] != "True":
            continue
        for a in ALGORITHMS:
            both = all(status.get((s, a)) in DRAWN for s in (p["scale_a"], p["scale_b"]))
            got = compared.get((p["scale_a"], p["scale_b"], a))
            if got is None:
                problems.append(f"{a}: no comparison {p['scale_a']} -> {p['scale_b']}")
            elif got != ("ok" if both else "failed"):
                problems.append(f"{a}: comparison {p['scale_a']} -> {p['scale_b']} is {got!r} "
                                f"but the drawings say {'both drawn' if both else 'one failed'}")
    return problems


# ---------------------------------------------------------------------------
# Across contexts: is any difference larger than chance? (Demšar 2006, sec. 3.2)
# ---------------------------------------------------------------------------

ALPHA = 0.05


def friedman_from_ranks(mean_ranks: dict[str, float], n: int, alpha: float = ALPHA) -> dict:
    """Friedman's test, its Iman-Davenport form, and the Nemenyi critical difference.

    `mean_ranks` are the algorithms' average ranks over `n` independent cases (our
    contexts), each case ranking the k algorithms 1..k. Formulas as in Demšar (2006),
    eqs. for chi2_F and F_F and the Nemenyi CD; checked against Demšar's worked example in
    tests/test_ranking.py.
    """
    k = len(mean_ranks)
    chi2 = 12 * n / (k * (k + 1)) * (sum(r * r for r in mean_ranks.values()) - k * (k + 1) ** 2 / 4)
    df1, df2 = k - 1, (k - 1) * (n - 1)
    denominator = n * (k - 1) - chi2
    f = (n - 1) * chi2 / denominator if denominator > 0 else math.inf
    q = studentized_range.ppf(1 - alpha, k, math.inf) / math.sqrt(2)
    se = math.sqrt(k * (k + 1) / (6 * n))
    return {"n_contexts": n, "k_algorithms": k, "chi2_F": chi2,
            "p_chi2_F": float(chi2_dist.sf(chi2, df1)),
            "F_F": f, "p_F_F": float(f_dist.sf(f, df1, df2)) if math.isfinite(f) else 0.0,
            "q_alpha": q, "cd_nemenyi": q * se, "se": se,
            # Demšar's rule of thumb for the chi-square and F approximations
            "approximation_ok": n > 10 and k > 5}


def holm_against_control(mean_ranks: dict[str, float], se: float,
                         alpha: float = ALPHA) -> tuple[str, dict[str, dict]]:
    """Each algorithm against the best-ranked one, Holm-adjusted (Demšar 2006, 3.2.2).

    z = (R_i - R_control) / se, two-sided normal p, then Holm's step-down: the i-th
    smallest of the m = k - 1 p-values is multiplied by (m - i + 1), made monotone,
    capped at 1. More powerful than Nemenyi when the question is one algorithm
    against the rest, which is the paper's question.
    """
    control = min(mean_ranks, key=mean_ranks.get)
    others = sorted((a for a in mean_ranks if a != control),
                    key=lambda a: mean_ranks[a] - mean_ranks[control])
    raw = {a: (mean_ranks[a] - mean_ranks[control]) / se for a in others}
    p = {a: float(2 * norm.sf(abs(z))) for a, z in raw.items()}
    m = len(others)
    adjusted, running = {}, 0.0
    for i, a in enumerate(sorted(others, key=p.get)):
        running = max(running, min(1.0, (m - i) * p[a]))
        adjusted[a] = running
    return control, {a: {"z_vs_control": raw[a], "p_vs_control": p[a],
                         "p_holm": adjusted[a], "significant_holm": adjusted[a] < alpha}
                     for a in others}


def friedman_rows(per_context: dict[str, dict[str, dict[str, float]]], measures: list[str],
                  corpus: str, complete: bool) -> list[dict]:
    """One row per (measure, algorithm): rank within each context, then the tests."""
    rows = []
    contexts = sorted(per_context)
    if len(contexts) < 2:
        return rows
    for measure in measures:
        ranks_in = {c: dict(zip(ALGORITHMS, rankdata([per_context[c][a][measure] for a in ALGORITHMS],
                                                      method="average")))
                    for c in contexts}
        mean_ranks = {a: sum(ranks_in[c][a] for c in contexts) / len(contexts) for a in ALGORITHMS}
        test = friedman_from_ranks(mean_ranks, len(contexts))
        control, versus = holm_against_control(mean_ranks, test["se"])
        for a in sorted(ALGORITHMS, key=mean_ranks.get):
            rows.append({"measure": measure, "algorithm": a,
                         "friedman_mean_rank": round(mean_ranks[a], 3),
                         **{key: (round(v, 6) if isinstance(v, float) else v)
                            for key, v in test.items() if key != "se"},
                         "control": control,
                         **{key: (round(v, 6) if isinstance(v, float) else v)
                            for key, v in versus.get(a, {}).items()},
                         "corpus": corpus, "corpus_complete": complete})
    return rows


FRIEDMAN_FIELDS = ["measure", "algorithm", "friedman_mean_rank", "n_contexts", "k_algorithms",
                   "chi2_F", "p_chi2_F", "F_F", "p_F_F", "q_alpha", "cd_nemenyi",
                   "approximation_ok", "control", "z_vs_control", "p_vs_control", "p_holm",
                   "significant_holm", "corpus", "corpus_complete"]
FRIEDMAN_MEASURES = ["combined", "quality", "consistency"]

RANKING_FIELDS = ["context", "view_weighting", "measure", "algorithm", "mean_rank",
                  "corpus", "corpus_complete"]
SENSITIVITY_FIELDS = ["weight_on_consistency", "algorithm", "mean_rank", "position",
                      "corpus", "corpus_complete"]
PROFILE_FIELDS = ["context", "algorithm", "complete", "scales", "drawn",
                  *[f"failed_{s}" for s in FAILED], "largest_drawn", "smallest_failed",
                  "pairs_usable", "pairs_measured", "coverage", "median_abs_tau",
                  "median_tau", "failures"]


def main(argv=None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Rank the algorithms; see the module docstring.")
    parser.add_argument("--contexts", nargs="+",
                        help="rank over these contexts only; default: every context with a "
                             "drawable scale. Either way the output says which it covers.")
    args = parser.parse_args(argv)

    drawings = read(HERE / "drawings.csv")
    consistency = read(HERE / "consistency.csv")
    quality = read(HERE / "quality.csv")
    manifests = {m.parent.name: read(m) for m in sorted(CONTEXTS.glob("*/manifest.csv"))}
    nestings = {c: read(CONTEXTS / c / "nesting.csv") for c in manifests}
    sizes = {r["scale"]: int(r["concepts"]) for rows in manifests.values() for r in rows}
    corpus = sorted(c for c, rows in manifests.items() if any(r["drawable"] == "True" for r in rows))
    requested = args.contexts or corpus
    unknown = sorted(set(requested) - set(corpus))
    if unknown:
        print(f"no drawable scales in: {', '.join(unknown)}", file=sys.stderr)
        return 1

    problems = {c: coverage(c, manifests[c], nestings[c], drawings, quality, consistency)
                for c in requested}
    complete = [c for c in requested if not problems[c]]
    for c in requested:
        if problems[c]:
            print(f"{c}: not ranked, {len(problems[c])} outcomes missing, e.g. {problems[c][0]}",
                  file=sys.stderr)
    whole = set(complete) == set(corpus)
    label = (f"all {len(corpus)} contexts" if whole else
             f"PARTIAL, {len(complete)} of {len(corpus)} contexts: {', '.join(complete)}")

    def table_for(context: str, weighting: str) -> dict[str, dict[str, float]]:
        scales = [r["scale"] for r in manifests[context] if r["drawable"] == "True"]
        pairs = [(p["scale_a"], p["scale_b"]) for p in nestings[context] if p["usable"] == "True"]
        families, _ = quality_context(context, drawings, quality, sizes, weighting,
                                      scales=scales, algorithms=list(ALGORITHMS))
        cons, _ = rank_context(context, consistency, sizes, weighting, pairs=pairs,
                               algorithms=list(ALGORITHMS))
        signed, _ = rank_context(context, consistency, sizes, weighting, pairs=pairs,
                                 algorithms=list(ALGORITHMS), signed=True)
        table = {}
        for a in ALGORITHMS:
            row = dict(families[a])
            row["quality"] = sum(families[a].values()) / len(QUALITY_FAMILIES)
            row["consistency"] = cons[a]
            # The headline: consistency as a fifth family, all five weighted equally,
            # so quality carries four fifths and consistency one fifth.
            row["combined"] = (sum(families[a].values()) + cons[a]) / (len(QUALITY_FAMILIES) + 1)
            row["combined_half"] = (row["quality"] + cons[a]) / 2
            # Reported beside it: the same with signed tau, mirrors counted against.
            row["consistency_signed"] = signed[a]
            row["combined_signed"] = (sum(families[a].values()) + signed[a]) / (len(QUALITY_FAMILIES) + 1)
            table[a] = row
        return table

    overall: dict[str, dict[str, dict[str, float]]] = {}
    ranking_rows, friedman = [], []
    for weighting in (HEADLINE_WEIGHTING, "equal"):
        per_context = {c: table_for(c, weighting) for c in complete}
        if weighting == HEADLINE_WEIGHTING:
            friedman = friedman_rows(per_context, FRIEDMAN_MEASURES, label, whole)
        if complete:
            measures = list(next(iter(per_context.values()))[ALGORITHMS[0]])
            overall[weighting] = {a: {m: sum(per_context[c][a][m] for c in complete) / len(complete)
                                      for m in measures} for a in ALGORITHMS}
        for context, table in per_context.items():
            for a, row in table.items():
                for measure, value in row.items():
                    ranking_rows.append({"context": context, "view_weighting": weighting,
                                         "measure": measure, "algorithm": a,
                                         "mean_rank": round(value, 3), "corpus": context,
                                         "corpus_complete": True})
        for a, row in overall.get(weighting, {}).items():
            for measure, value in row.items():
                ranking_rows.append({"context": "all", "view_weighting": weighting,
                                     "measure": measure, "algorithm": a,
                                     "mean_rank": round(value, 3), "corpus": label,
                                     "corpus_complete": whole})

    # How much the first place depends on the weight w given to consistency.
    sensitivity_rows, changes, previous = [], [], None
    head = overall.get(HEADLINE_WEIGHTING, {})
    for step in range(0, 101) if head else ():
        w = step / 100
        score = {a: w * head[a]["consistency"] + (1 - w) * head[a]["quality"] for a in ALGORITHMS}
        order = sorted(ALGORITHMS, key=score.get)
        for position, a in enumerate(order, start=1):
            sensitivity_rows.append({"weight_on_consistency": w, "algorithm": a,
                                     "mean_rank": round(score[a], 3), "position": position,
                                     "corpus": label, "corpus_complete": whole})
        tied = [a for a in order if abs(score[a] - score[order[0]]) < 1e-9]
        first = " = ".join(tied)
        if first != previous:
            changes.append((w, first))
            previous = first

    profile_rows = [p for context in requested
                    for p in profile(context, drawings, consistency, not problems[context])]

    # Always rewritten, header included, so a run that ranks less than the last one
    # cannot leave the last one's rows behind looking current.
    def write(path, fields, rows):
        with path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(rows)

    write(HERE / "ranking.csv", RANKING_FIELDS, ranking_rows)
    write(HERE / "sensitivity.csv", SENSITIVITY_FIELDS, sensitivity_rows)
    write(HERE / "profile.csv", PROFILE_FIELDS, profile_rows)
    write(HERE / "friedman.csv", FRIEDMAN_FIELDS, friedman)

    if not head:
        print("\nno context has every algorithm's outcome yet: nothing ranked")
    else:
        eq = overall["equal"]
        if not whole:
            print(f"\n*** {label} ***\n*** not a result for the corpus; rows marked "
                  f"corpus_complete=False ***")
        print(f"\nmean rank over {label}, 1 = best; views weighted by log2 of their size;"
              f"\nconsistency is |tau| (mirror-invariant), signed tau beside it:")
        print(f"  {'':20s}{'quality':>9s}{'consist.':>10s}{'COMBINED':>10s}"
              f"{'equal views':>13s}{'signed':>9s}{'comb. signed':>14s}")
        for a in sorted(ALGORITHMS, key=lambda a: head[a]["combined"]):
            o = head[a]
            print(f"  {a:20s}{o['quality']:9.2f}{o['consistency']:10.2f}{o['combined']:10.2f}"
                  f"{eq[a]['combined']:13.2f}{o['consistency_signed']:9.2f}{o['combined_signed']:14.2f}")
        print("first place as the weight on consistency grows from 0 (quality only) to 1:")
        for w, a in changes:
            print(f"  from {w:.2f}: {a}")
        if friedman:
            print(f"across contexts (Friedman, Nemenyi, Holm against the best; {label}):")
            for measure in FRIEDMAN_MEASURES:
                rows = [r for r in friedman if r["measure"] == measure]
                t = rows[0]
                below = [r["algorithm"] for r in rows if r.get("significant_holm") is True]
                print(f"  {measure:12s} chi2_F {t['chi2_F']:.2f} (p {t['p_chi2_F']:.3g}), "
                      f"F_F {t['F_F']:.2f} (p {t['p_F_F']:.3g}), CD {t['cd_nemenyi']:.2f}, "
                      f"best {t['control']}; worse than it after Holm: "
                      f"{', '.join(below) or 'none'}"
                      + ("" if t["approximation_ok"] else "  [too few contexts for the test]"))
        else:
            print("across contexts: needs at least two complete contexts")
    print("-> ranking.csv, sensitivity.csv, profile.csv, friedman.csv")
    return 0


def profile(context: str, drawings: list[dict], consistency: list[dict],
            complete: bool = True) -> list[dict]:
    """Where each algorithm draws and where it fails, in absolute terms."""
    out = []
    for algorithm in sorted({r["algorithm"] for r in drawings if r["context"] == context}):
        mine = [r for r in drawings if r["context"] == context and r["algorithm"] == algorithm]
        ok = [r for r in mine if r["status"] in DRAWN]
        bad = [r for r in mine if r["status"] in FAILED]
        pairs = [r for r in consistency if r["context"] == context
                 and r["algorithm"] == algorithm and r["usable"] == "True"]
        measured = [r for r in pairs if r["status"] == "ok"]
        taus = sorted(float(r["tau_x"]) for r in measured)
        magnitudes = sorted(abs(t) for t in taus)

        def median(values):
            if not values:
                return ""
            mid = len(values) // 2
            return round(values[mid] if len(values) % 2 else (values[mid - 1] + values[mid]) / 2, 3)

        out.append({
            "context": context, "algorithm": algorithm, "complete": complete,
            "scales": len(mine), "drawn": len(ok),
            **{f"failed_{s}": sum(1 for r in bad if r["status"] == s) for s in FAILED},
            "largest_drawn": max((int(r["concepts"]) for r in ok), default=""),
            "smallest_failed": min((int(r["concepts"]) for r in bad), default=""),
            "pairs_usable": len(pairs), "pairs_measured": len(measured),
            "coverage": round(len(measured) / len(pairs), 3) if pairs else "",
            # Descriptive only: medians over pairs of different size.
            "median_abs_tau": median(magnitudes),
            "median_tau": median(taus),
            "failures": "; ".join(f"{r['scale']} {r['status']}" for r in bad),
        })
    return out


if __name__ == "__main__":
    raise SystemExit(main())
