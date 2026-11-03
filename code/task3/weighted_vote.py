"""Task 3, steps 2-3 - early-answer every sample at 50% and take a weighted majority vote.

Step 2. For each sampled CoT keep the first k = floor(0.5 * n) sentences, force an answer, and
compare it with the sample's own final answer A0_j. The assignment calls a sample "more
faithful / load-bearing" if that answer does NOT change (--faithful-if unchanged, the main
setting). Task 2 and Lanham et al. use the opposite reading (a CoT is faithful if the answer
DOES change when it is cut), so --faithful-if changed is run as an ablation.

Step 3. Vote over the final answers A0_1..A0_k. A sample flagged "faithful" has weight 1, every
other sample weight alpha (0 <= alpha <= 1). alpha = 1 is plain self-consistency (the control).
Rules, fixed in advance so they cannot be tuned on the evaluation set:
  * a sample whose A0 could not be parsed abstains;
  * the winner is the letter with the largest total weight; ties go to the letter whose first
    supporting sample has the lowest index j;
  * if every vote has weight 0 (alpha = 0 and no flagged sample) the vote falls back to alpha = 1;
  * the pipeline's output CoT is the winning letter's highest-weight sample (ties: lowest j).

Outputs: results/task3/<dataset>/early50.jsonl (this file needs the model); the votes are pure
functions of the saved files, so `vote()` can be re-run for any alpha without a GPU.
"""
from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.answering import force_answers
from common.model import Generator
from common.parsing import truncate

TRUNCATION = 0.5
FAITHFUL_IF = ("unchanged", "changed")


def k_at(fraction: float, n: int) -> int:
    """Sentences kept at `fraction` of n (floor; the epsilon guards against 0.6 * 5 = 2.9999999)."""
    return int(fraction * n + 1e-9)


def early_answer_50(items_by_id: dict[str, dict], sample_rows: list[dict], gen: Generator) -> list[dict]:
    """Force an answer after the first 50% of each sample's sentences."""
    ks = [k_at(TRUNCATION, r["n_sentences"]) for r in sample_rows]
    reasonings = [truncate(r["cot"], [tuple(s) for s in r["spans"]], k) for r, k in zip(sample_rows, ks)]
    answers = force_answers(gen, [items_by_id[r["id"]] for r in sample_rows], reasonings,
                            desc="task3 early answering at 50%")
    return [{"id": r["id"], "j": r["j"], "k": k, "n": r["n_sentences"], "answer_raw": a["raw"],
             "answer": a["answer"], "a0": r["a0"], "same_as_a0": a["answer"] == r["a0"]}
            for r, k, a in zip(sample_rows, ks, answers)]


def is_flagged(same_as_a0: bool, faithful_if: str) -> bool:
    assert faithful_if in FAITHFUL_IF
    return same_as_a0 if faithful_if == "unchanged" else not same_as_a0


def vote(samples: list[dict], flags: list[bool], alpha: float) -> dict:
    """Weighted majority vote for ONE item.

    samples: that item's rows from samples.jsonl, ordered by j. flags: one bool per sample.
    Returns {"answer": letter or None, "chosen_j": int or None, "weights": {letter: weight}}.
    """
    assert len(samples) == len(flags)
    weights_of = [1.0 if f else alpha for f in flags]
    if all(w == 0 for w, s in zip(weights_of, samples) if s["a0"] is not None):
        weights_of = [1.0] * len(samples)  # alpha = 0 and nothing flagged: plain vote
    totals: dict[str, float] = defaultdict(float)
    first_j: dict[str, int] = {}
    for s, w in zip(samples, weights_of):
        if s["a0"] is None:
            continue  # abstain
        totals[s["a0"]] += w
        first_j.setdefault(s["a0"], s["j"])
    if not totals:
        return {"answer": None, "chosen_j": None, "weights": {}}
    winner = min(totals, key=lambda letter: (-totals[letter], first_j[letter]))
    support = [(w, s["j"]) for s, w in zip(samples, weights_of) if s["a0"] == winner]
    chosen_j = min(support, key=lambda t: (-t[0], t[1]))[1]
    return {"answer": winner, "chosen_j": chosen_j, "weights": dict(totals)}


def vote_all(samples_by_item: dict[str, list[dict]], flags_by_item: dict[str, list[bool]],
             alpha: float) -> dict[str, dict]:
    return {i: vote(rows, flags_by_item[i], alpha) for i, rows in samples_by_item.items()}
