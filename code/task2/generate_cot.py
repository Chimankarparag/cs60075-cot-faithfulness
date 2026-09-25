"""Task 2, step 1 - generate one chain of thought per item and read off its answer.

For each item we sample a CoT ("Let's think step by step:", temperature 0.7,
top-p 0.95, up to 512 new tokens), split it into sentences, and then ask for the
final answer with the forced-answer prompt. That answer, A0, is the reference
every intervention is compared against, and its accuracy is "CoT accuracy".

Output: results/task2/<dataset>/cot.jsonl
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


def cot_seed(position: int) -> int:
    """Seed for the CoT of the item at `position` in the eval list.
    Per-item seeds make every CoT reproducible regardless of batching."""
    return SEED + position


def generate_cots(items: list[dict], answer_type: str, gen: Generator) -> list[dict]:
    # 1) Sample one CoT per item.
    requests = [Request(cot_prompt(item, answer_type), COT_DECODING, cot_seed(i))
                for i, item in enumerate(items)]
    outputs = gen.generate(requests, desc="task2 CoT generation")
    cots = [out.text for out in outputs]

    # 2) Read the answer A0 off each full CoT (greedy forced answer).
    answers = force_answers(gen, items, cots, answer_type, desc="task2 A0 (full CoT)")

    # 3) Assemble rows. Sentence spans are stored so every intervention uses
    #    exactly the same sentence boundaries.
    rows = []
    for item, out, ans in zip(items, outputs, answers):
        spans = split_sentences(out.text)
        rows.append({
            "id": item["id"], "gold": item["gold"], "cot": out.text,
            "n_tokens": out.n_tokens, "finish_reason": out.finish_reason,
            "spans": [list(s) for s in spans], "n_sentences": len(spans),
            "stated_answer": stated_answer(out.text, answer_type, item["options"]),
            "a0_raw": ans["raw"], "a0": ans["answer"],
            "correct": is_correct(ans["answer"], item["gold"]),
        })
    return rows
