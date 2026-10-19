"""The ranking rules, on small made-up comparisons where the right answer is known.

    python tests/test_ranking.py        # standalone
    pytest tests/test_ranking.py        # or under pytest
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from ranking import (ALGORITHMS, QUALITY_FAMILIES, RankingInputError, coverage,  # noqa: E402
                     friedman_from_ranks, holm_against_control, quality_context,
                     rank_context)


def row(a, b, algorithm, tau):
    """One consistency row; tau None means one of the two drawings failed."""
    return {"context": "c", "scale_a": a, "scale_b": b, "algorithm": algorithm,
            "usable": "True", "status": "ok" if tau is not None else "failed",
            "tau_x": "" if tau is None else str(tau)}


SIZES = {"small": 13, "mid": 46, "full": 576}


def test_a_failure_ranks_below_any_drawing_even_a_reversed_one():
    rows = [row("small", "mid", "reversed", -1.0), row("small", "mid", "failed", None)]
    ranks, _ = rank_context("c", rows, SIZES, "equal")
    assert ranks["reversed"] < ranks["failed"]


def test_ties_share_the_average_rank():
    rows = [row("small", "mid", x, 0.5) for x in ("p", "q")] + [row("small", "mid", "r", 0.1)]
    ranks, _ = rank_context("c", rows, SIZES, "equal")
    assert ranks["p"] == ranks["q"] == 1.5 and ranks["r"] == 3.0


def test_every_scale_counts_once_however_many_pairs_end_in_it():
    # Three pairs end in `full`, one in `mid`. X wins the three, Y wins the one.
    # Counted per pair X would lead 3 to 1; counted per scale they tie.
    rows = []
    for coarse in ("small", "mid", "other"):
        rows += [row(coarse, "full", "X", 0.9), row(coarse, "full", "Y", 0.1)]
    rows += [row("small", "mid", "X", 0.1), row("small", "mid", "Y", 0.9)]
    ranks, _ = rank_context("c", rows, {**SIZES, "other": 20}, "equal")
    assert ranks["X"] == ranks["Y"] == 1.5


def test_the_a_versus_b_case():
    # A draws everything, mediocre; B is better everywhere but fails the full lattice.
    # Three scales: B wins the two smaller ones and fails the top one.
    sizes = {**SIZES, "upper": 107}
    rows = [row("small", "mid", "A", 0.2), row("small", "mid", "B", 0.8),
            row("mid", "upper", "A", 0.2), row("mid", "upper", "B", 0.8),
            row("upper", "full", "A", 0.2), row("upper", "full", "B", None)]
    equal, _ = rank_context("c", rows, sizes, "equal")
    assert equal["B"] < equal["A"], "every scale once: B's one failure costs one of three scales"
    size, _ = rank_context("c", rows, sizes, "size")
    assert size["A"] < size["B"], "weighted by size, failing on the 576-concept scale dominates"


def test_an_algorithm_not_run_on_every_pair_is_left_out_not_ranked_last():
    rows = [row("small", "mid", "A", 0.5), row("small", "mid", "B", 0.4),
            row("mid", "full", "A", 0.5)]                     # B never attempted mid -> full
    ranks, left_out = rank_context("c", rows, SIZES, "equal")
    assert left_out == ["B"] and set(ranks) == {"A"}


def drawing(scale, algorithm, status="drawn"):
    return {"context": "c", "scale": scale, "algorithm": algorithm, "status": status}


def scores(scale, algorithm, value_by_family):
    row = {"context": "c", "scale": scale, "algorithm": algorithm}
    for family, metrics in QUALITY_FAMILIES.items():
        for m in metrics:
            row[m] = str(value_by_family[family])
    return row


def test_each_quality_family_counts_once_however_many_metrics_it_has():
    # X wins slopes (five metrics) and clearance (four); Y wins crossings and
    # layering (two each). Counted per metric X would lead 9 to 4; per family they tie.
    x = {"crossings": 0.1, "layering": 0.1, "slopes": 0.9, "clearance": 0.9}
    y = {"crossings": 0.9, "layering": 0.9, "slopes": 0.1, "clearance": 0.1}
    families, _ = quality_context("c", [drawing("s", "X"), drawing("s", "Y")],
                                  [scores("s", "X", x), scores("s", "Y", y)])
    assert sum(families["X"].values()) == sum(families["Y"].values())


def test_a_failed_drawing_is_last_on_every_quality_family():
    good = {f: 0.0 for f in QUALITY_FAMILIES}            # the worst possible scores
    families, _ = quality_context("c", [drawing("s", "drew"), drawing("s", "failed", "timeout")],
                                  [scores("s", "drew", good)])
    assert all(families["failed"][f] > families["drew"][f] for f in QUALITY_FAMILIES)



def test_failing_a_large_view_costs_more_than_failing_a_small_one():
    # X fails the 576-concept view, Y the 13-concept one; otherwise identical.
    same = {f: 0.5 for f in QUALITY_FAMILIES}
    drawings = [drawing("small", "X"), drawing("full", "X", "timeout"),
                drawing("small", "Y", "timeout"), drawing("full", "Y")]
    quality = [scores("small", "X", same), scores("full", "Y", same)]
    sizes = {"small": 13, "full": 576}
    log2, _ = quality_context("c", drawings, quality, sizes, "log2")
    assert sum(log2["X"].values()) > sum(log2["Y"].values())
    equal, _ = quality_context("c", drawings, quality, sizes, "equal")
    assert sum(equal["X"].values()) == sum(equal["Y"].values())


def raises(error, call):
    try:
        call()
    except error:
        return True
    return False


def test_a_mirror_ranks_with_the_identical_drawing():
    # Mirroring the whole drawing negates tau. Ranked by |tau| it ties with the
    # unchanged drawing; ranked by the signed tau it is last.
    rows = [row("small", "mid", "same", 1.0), row("small", "mid", "mirror", -1.0),
            row("small", "mid", "scramble", 0.0)]
    ranks, _ = rank_context("c", rows, SIZES, "equal")
    assert ranks["same"] == ranks["mirror"] == 1.5 and ranks["scramble"] == 3.0
    signed, _ = rank_context("c", rows, SIZES, "equal", signed=True)
    assert signed["same"] == 1.0 and signed["scramble"] == 2.0 and signed["mirror"] == 3.0


def test_a_partial_mirror_still_counts_against():
    # tau -0.4 is as consistent as +0.4 up to a mirror, and less than 0.9 either way.
    rows = [row("small", "mid", "a", -0.4), row("small", "mid", "b", 0.4),
            row("small", "mid", "c", -0.9)]
    ranks, _ = rank_context("c", rows, SIZES, "equal")
    assert ranks["c"] == 1.0 and ranks["a"] == ranks["b"] == 2.5


def test_a_nan_tau_stops_the_ranking():
    rows = [row("small", "mid", "A", 0.5), row("small", "mid", "B", float("nan"))]
    assert raises(RankingInputError, lambda: rank_context("c", rows, SIZES, "equal"))


def test_a_tau_outside_minus_one_to_one_stops_the_ranking():
    rows = [row("small", "mid", "A", 0.5), row("small", "mid", "B", 1.5)]
    assert raises(RankingInputError, lambda: rank_context("c", rows, SIZES, "equal"))


def test_an_unknown_comparison_status_stops_the_ranking():
    rows = [row("small", "mid", "A", 0.5), {**row("small", "mid", "B", 0.4), "status": "weird"}]
    assert raises(RankingInputError, lambda: rank_context("c", rows, SIZES, "equal"))


def test_a_nan_score_stops_the_ranking():
    values = {f: 0.5 for f in QUALITY_FAMILIES}
    bad = scores("s", "Y", values)
    bad["edge_crossing"] = "nan"
    assert raises(RankingInputError, lambda: quality_context(
        "c", [drawing("s", "X"), drawing("s", "Y")], [scores("s", "X", values), bad]))


def test_a_drawn_drawing_without_scores_is_an_error_not_a_failure():
    values = {f: 0.5 for f in QUALITY_FAMILIES}
    assert raises(RankingInputError, lambda: quality_context(
        "c", [drawing("s", "X"), drawing("s", "Y")], [scores("s", "X", values)]))


def full_context(skip=()):
    """One context, two drawable scales nested once, every algorithm drawing both."""
    manifest = [{"scale": s, "drawable": "True"} for s in ("small", "mid")]
    nesting = [{"scale_a": "small", "scale_b": "mid", "usable": "True"}]
    drawings = [drawing(s, a) for s in ("small", "mid") for a in ALGORITHMS
                if (s, a) not in skip]
    quality = [scores(s, a, {f: 0.5 for f in QUALITY_FAMILIES})
               for s in ("small", "mid") for a in ALGORITHMS]
    consistency = [row("small", "mid", a, 0.5) for a in ALGORITHMS]
    return manifest, nesting, drawings, quality, consistency


def test_a_complete_context_has_no_coverage_problems():
    assert coverage("c", *full_context()) == []


def test_an_algorithm_not_attempted_makes_the_context_incomplete():
    problems = coverage("c", *full_context(skip={("mid", ALGORITHMS[0])}))
    assert any("not attempted" in p for p in problems)


def test_a_comparison_contradicting_the_drawings_makes_the_context_incomplete():
    manifest, nesting, drawings, quality, consistency = full_context()
    drawings[0] = {**drawings[0], "status": "timeout"}        # its comparison says ok
    assert any("drawings say" in p for p in coverage("c", manifest, nesting, drawings,
                                                      quality, consistency))


def test_friedman_reproduces_demsars_worked_example():
    # Demšar (2006), section 3.2.4: four variants of C4.5 on fourteen data sets,
    # average ranks 3.143, 2.000, 2.893, 1.964 give chi2_F = 9.28, F_F = 3.69, and a
    # Nemenyi critical difference of 1.25 at alpha = 0.05 (q = 2.569).
    ranks = {"C4.5": 3.143, "C4.5+m": 2.000, "C4.5+cf": 2.893, "C4.5+m+cf": 1.964}
    t = friedman_from_ranks(ranks, 14)
    assert round(t["chi2_F"], 2) == 9.28 and round(t["F_F"], 2) == 3.69, t
    assert round(t["q_alpha"], 3) == 2.569 and round(t["cd_nemenyi"], 2) == 1.25, t


def test_nemenyi_q_matches_demsars_table_for_eight_algorithms():
    t = friedman_from_ranks({str(i): 4.5 for i in range(8)}, 11)
    assert round(t["q_alpha"], 3) == 3.031 and round(t["cd_nemenyi"], 2) == 3.17, t
    assert t["chi2_F"] == 0.0, "identical mean ranks: no evidence of any difference"


def test_holm_steps_down_from_the_smallest_p():
    # Against the control, three others with z = 1, 2, 3: raw p 0.317, 0.0455, 0.0027;
    # Holm multiplies by 3, 2, 1 from the smallest, so 0.0081, 0.091, 0.317.
    control, versus = holm_against_control({"c": 1.0, "x": 2.0, "y": 3.0, "z": 4.0}, se=1.0)
    assert control == "c"
    assert round(versus["z"]["p_holm"], 4) == round(3 * versus["z"]["p_vs_control"], 4)
    assert round(versus["y"]["p_holm"], 4) == round(2 * versus["y"]["p_vs_control"], 4)
    assert versus["x"]["p_holm"] == max(versus["y"]["p_holm"], versus["x"]["p_vs_control"])
    assert versus["z"]["significant_holm"] and not versus["x"]["significant_holm"]


if __name__ == "__main__":
    failed = False
    for name, test in sorted(globals().items()):
        if name.startswith("test_"):
            try:
                test()
                print(f"  ok    {name}")
            except AssertionError as failure:
                print(f"  FAIL  {name}: {failure}")
                failed = True
    raise SystemExit(1 if failed else 0)
