"""Reading the model's answer after a (possibly modified) chain of thought.

This is the measurement primitive of Lanham et al. (2023): keep the question
fixed, change only the reasoning text, and see which answer the model gives.
Task 2 uses it for the full CoT and for all four interventions; Task 3 reuses it.
"""
from __future__ import annotations

from common.config import ANSWER_DECODING, SEED
from common.model import Generator, Request
from common.parsing import parse_answer
from common.prompts import forced_answer_prompt


def force_answers(gen: Generator, items: list[dict], reasonings: list[str], answer_type: str,
                  desc: str = "forced answers") -> list[dict]:
    """For each (item, reasoning) pair, ask for the final answer greedily.

    Returns one dict per pair: {"raw": model text after the prefill,
    "answer": canonical answer or None}.
    """
    assert len(items) == len(reasonings)
    requests = [Request(forced_answer_prompt(item, answer_type, reasoning), ANSWER_DECODING, SEED)
                for item, reasoning in zip(items, reasonings)]
    outputs = gen.generate(requests, desc)
    return [{"raw": out.text, "answer": parse_answer(out.text, answer_type, item["options"])}
            for item, out in zip(items, outputs)]
