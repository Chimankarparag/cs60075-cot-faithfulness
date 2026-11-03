"""Task 3, step 1 - sample k = 5 independent CoTs per question.

Same prompt and decoding as Task 2 (temperature 0.7, top-p 0.95, 512 tokens). Sample j of the
item at position i uses seed SEED + 100000 * j + i, so sample 0 uses the same seed as Task 2's
single CoT. Sampled text is only reproducible on the same hardware and batch setup (GPU type,
tensor-parallel size and batch composition change floating-point rounding, and a sampled token
can flip), so sample 0 is a fresh draw, not a copy of Task 2's CoT; score_task3 reports how many
match. Each CoT is split into
sentences and its final answer A0_j is read off with the forced-answer prompt, as in Task 2.

Output: results/task3/<dataset>/samples.jsonl  (one row per item and sample)
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.answering import force_answers
from common.config import COT_DECODING, SEED
from common.model import Generator, Request
from common.parsing import is_correct, split_sentences, stated_answer
from common.prompts import cot_prompt

K = 5  # number of CoTs per question (assignment)


def sample_seed(position: int, j: int) -> int:
    """Seed of sample j for the item at `position`; j = 0 equals Task 2's cot_seed(position)."""
    return SEED + 100_000 * j + position


def sample_cots(items: list[dict], gen: Generator, k: int = K) -> list[dict]:
    jobs = [(i, j) for i in range(len(items)) for j in range(k)]
    requests = [Request(cot_prompt(items[i]), COT_DECODING, sample_seed(i, j)) for i, j in jobs]
    outputs = gen.generate(requests, desc=f"task3 sampling {k} CoTs per item")
    answers = force_answers(gen, [items[i] for i, _ in jobs], [o.text for o in outputs],
                            desc="task3 A0 (full CoT) per sample")
    rows = []
    for (i, j), out, ans in zip(jobs, outputs, answers):
        item = items[i]
        spans = split_sentences(out.text)
        rows.append({
            "id": item["id"], "j": j, "gold": item["gold"], "cot": out.text,
            "n_tokens": out.n_tokens, "finish_reason": out.finish_reason,
            "spans": [list(s) for s in spans], "n_sentences": len(spans),
            "stated_answer": stated_answer(out.text, item["options"]),
            "a0_raw": ans["raw"], "a0": ans["answer"],
            "correct": is_correct(ans["answer"], item["gold"]),
        })
    return rows
