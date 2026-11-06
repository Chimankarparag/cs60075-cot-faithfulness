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


def cot_seed(position: int) -> int:
    """Seed of the CoT sampled for the item at `position` in the evaluation list. Regenerating
    the rest of a CoT after an intervention reuses it."""
    return SEED + position


def force_answers(gen: Generator, items: list[dict], reasonings: list[str],
                  desc: str = "forced answers") -> list[dict]:
    """For each (item, reasoning) pair, ask for the final answer greedily.

    Returns one dict per pair: {"raw": model text after the prefill,
    "answer": option letter or None}.
    """
    assert len(items) == len(reasonings)
    requests = [Request(forced_answer_prompt(item, reasoning), ANSWER_DECODING, SEED)
                for item, reasoning in zip(items, reasonings)]
    outputs = gen.generate(requests, desc)
    return [{"raw": out.text, "answer": parse_answer(out.text, item["options"])}
            for item, out in zip(items, outputs)]
