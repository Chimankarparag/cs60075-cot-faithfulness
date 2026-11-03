"""Task 3 - choose the vote rule on the development items, never on the evaluation items.

The 96 BBH rows that are neither evaluated nor few-shot exemplars (common/data.py, load_dev)
get the same treatment as the evaluation items: 5 sampled CoTs, the 50% early answer, and the
no-reasoning answer. Every candidate rule below is scored on them by vote accuracy, and the best
one becomes the "tuned" pipeline that is then run, unchanged, on the 150 evaluation items.

Candidates (fixed before any dev result was seen):
    flag rule  in {unchanged, loadbearing}        (weighted_vote.py explains both)
    alpha      in {0, 0.25, 0.5, 0.75}             weight of an unflagged sample; < 1, so the vote
                                                   is always weighted toward the flagged samples,
                                                   as the assignment asks (alpha = 1 would be plain
                                                   self-consistency, reported separately)
Selection: highest dev accuracy. Ties go to the assignment's literal rule (unchanged) first,
then to the alpha closest to 0.5 (the value fixed in advance for the main pipeline), then to the
larger alpha.

Output: results/task3/<dataset>/dev/tuning.json
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.io_utils import write_json
from common.metrics import mean

TUNE_RULES = ("unchanged", "loadbearing")
TUNE_ALPHAS = (0.0, 0.25, 0.5, 0.75)


def candidate_key(rule: str, alpha: float) -> str:
    return f"{rule}@{alpha}"


def tune(dev_dir: Path) -> dict:
    # Imported here: evaluate.py imports this module for the tuned pipeline.
    from task3.evaluate import correctness, load_flags, load_samples
    from task3.weighted_vote import vote_all

    ids, samples_by_item = load_samples(dev_dir)
    gold = {i: samples_by_item[i][0]["gold"] for i in ids}

    def accuracy(rule: str, alpha: float) -> float:
        votes = vote_all(samples_by_item, load_flags(dev_dir, samples_by_item, rule), alpha)
        return mean(correctness(votes, gold, ids))

    scores = {candidate_key(r, a): accuracy(r, a) for r in TUNE_RULES for a in TUNE_ALPHAS}
    ranked = sorted(((r, a) for r in TUNE_RULES for a in TUNE_ALPHAS),
                    key=lambda c: (-scores[candidate_key(*c)], TUNE_RULES.index(c[0]),
                                   abs(c[1] - 0.5), -c[1]))
    rule, alpha = ranked[0]
    result = {
        "n_dev_items": len(ids),
        "k": len(samples_by_item[ids[0]]),
        "dev_accuracy": scores,
        "dev_accuracy_plain_sc": accuracy("unchanged", 1.0),
        "dev_accuracy_mean_single_sample": mean(s["correct"] for i in ids for s in samples_by_item[i]),
        "chosen": {"faithful_if": rule, "alpha": alpha},
        "selection_rule": "max dev accuracy; ties: unchanged before loadbearing, then alpha closest "
                          "to 0.5, then larger alpha",
    }
    write_json(dev_dir / "tuning.json", result)
    return result


def render_tuning(t: dict) -> str:
    lines = [f"# Task 3 - vote rule chosen on {t['n_dev_items']} development items (k = {t['k']})", "",
             "| Flag rule | " + " | ".join(f"alpha = {a}" for a in TUNE_ALPHAS) + " |",
             "| --- |" + " --- |" * len(TUNE_ALPHAS)]
    for r in TUNE_RULES:
        lines.append(f"| {r} | " + " | ".join(f"{100 * t['dev_accuracy'][candidate_key(r, a)]:.1f}"
                                            for a in TUNE_ALPHAS) + " |")
    c = t["chosen"]
    lines += ["", f"Plain self-consistency on dev: {100 * t['dev_accuracy_plain_sc']:.1f}%; "
                  f"mean single sample: {100 * t['dev_accuracy_mean_single_sample']:.1f}%.",
              f"Chosen: faithful if **{c['faithful_if']}**, alpha = **{c['alpha']}** ({t['selection_rule']})."]
    return "\n".join(lines) + "\n"
