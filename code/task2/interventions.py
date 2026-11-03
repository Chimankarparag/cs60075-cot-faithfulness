"""Task 2, steps 2-5 - the four interventions of Lanham et al. (2023).

Each function takes the eval items, the CoT rows from generate_cot.py and a
generator, changes the reasoning in one specific way, asks for the answer again,
and records whether it differs from A0 (the answer after the untouched CoT).

    early_answering   keep only the first k sentences          (k = 0 .. n)
    add_mistake       corrupt one sentence, let the model continue from there
    paraphrase        reword the whole CoT without showing the question
    filler_tokens     replace the CoT with " ..." of the same token length

Which direction counts as "faithful" is decided in score.py, not here: these
functions only record what happened.
"""
from __future__ import annotations

import random
import re
import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.answering import force_answers
from common.config import (COT_DECODING, MAX_REWRITE_ATTEMPTS, MISTAKE_DECODING,
                           PARAPHRASE_DECODING, RETRY_TEMPERATURE, SEED, Decoding)
from common.model import Generator, Request
from common.parsing import _ANSWER_CUE, stated_answer, truncate
from common.prompts import FILLER_UNIT, cot_prompt, mistake_prompt, paraphrase_prompt
from task2.generate_cot import cot_seed


def _spans(row: dict) -> list[tuple[int, int]]:
    return [tuple(s) for s in row["spans"]]


# List markers at the start of a line ("1.", "2)", "Step 3:", "**Step 3:**") are
# formatting, not content, so they are ignored when comparing two texts.
_LIST_PREFIX = re.compile(r"(?im)^\s*\**\s*(?:step\s*)?\d+\s*[.):]\**\s+")
_WORD = re.compile(r"[a-z0-9]+(?:\.[0-9]+)?")


def _words(text: str) -> list[str]:
    """Lower-cased words and numbers, ignoring punctuation and list markers."""
    return _WORD.findall(_LIST_PREFIX.sub("", text).lower())


# =========================================================================== #
# (1) Early answering
# =========================================================================== #
def early_answering(items: list[dict], cot_rows: list[dict],
                    gen: Generator) -> list[dict]:
    """Answer after every prefix of the CoT: 0, 1, ..., n-1 sentences.

    The spec asks for 20/40/60/80%; we answer after *every* sentence (cheap: each
    answer is ~5 tokens) so score.py can report both the spec's four points and
    Lanham et al.'s per-sentence AOC. k = n is the full CoT, i.e. A0 itself.
    """
    jobs = []  # (item, cot_row, k, truncated reasoning)
    for item, row in zip(items, cot_rows):
        spans = _spans(row)
        for k in range(len(spans)):  # k = n reuses A0 below
            jobs.append((item, row, k, truncate(row["cot"], spans, k)))

    answers = force_answers(gen, [j[0] for j in jobs], [j[3] for j in jobs],
                            desc="task2 early answering")
    rows = [{"id": row["id"], "k": k, "n": row["n_sentences"], "answer_raw": ans["raw"],
             "answer": ans["answer"], "a0": row["a0"], "same_as_a0": ans["answer"] == row["a0"]}
            for (item, row, k, _), ans in zip(jobs, answers)]
    for row in cot_rows:  # the k = n point
        rows.append({"id": row["id"], "k": row["n_sentences"], "n": row["n_sentences"],
                     "answer_raw": row["a0_raw"], "answer": row["a0"], "a0": row["a0"],
                     "same_as_a0": True})
    return rows


# =========================================================================== #
# Shared helper for the two interventions that ask the model to rewrite text
# =========================================================================== #
def _rewrite_with_retries(gen: Generator, prompts: list, base: Decoding, clean, is_valid,
                          desc: str) -> list[tuple[str, int, bool]]:
    """Generate one rewrite per prompt; re-sample the invalid ones.

    Attempt 1 is greedy. Attempts 2..MAX_REWRITE_ATTEMPTS sample at
    RETRY_TEMPERATURE with a new seed. Returns (text, attempts_used, valid) per
    prompt; if every attempt fails, the last attempt is kept and flagged invalid.
    """
    results: list[tuple[str, int, bool] | None] = [None] * len(prompts)
    pending = list(range(len(prompts)))
    for attempt in range(1, MAX_REWRITE_ATTEMPTS + 1):
        if not pending:
            break
        decoding = base if attempt == 1 else replace(base, temperature=RETRY_TEMPERATURE, top_p=0.95)
        requests = [Request(prompts[i], decoding, SEED + 1000 * attempt + i) for i in pending]
        outputs = gen.generate(requests, desc=f"{desc} (attempt {attempt})")
        still_pending = []
        for i, out in zip(pending, outputs):
            text = clean(out.text)
            ok = is_valid(i, text)
            results[i] = (text, attempt, ok)
            if not ok:
                still_pending.append(i)
        pending = still_pending
    return results  # type: ignore[return-value]


# =========================================================================== #
# (2) Adding a mistake
# =========================================================================== #
def mistake_candidates(row: dict) -> list[int]:
    """Sentences worth corrupting.

    * Never the final sentence, nor any sentence announcing the answer: corrupting
      those would change the answer trivially.
    * Only sentences with at least 4 words (skip headers such as "Step 1:").
    Falls back to any non-final sentence if no sentence qualifies.
    """
    n = row["n_sentences"]
    body = list(range(n - 1)) if n >= 2 else [0]
    # Also skip sentences that announce the answer ("... the answer is:"), wherever they are.
    body = [i for i in body if not _ANSWER_CUE.search(row["cot"][slice(*row["spans"][i])])] or body
    text = [row["cot"][slice(*row["spans"][i])] for i in body]
    good = [i for i, t in zip(body, text) if len(_words(t)) >= 4]
    return good or body


def mistake_position(row: dict) -> int:
    """Pick one candidate uniformly at random, seeded by the item id."""
    return random.Random(f"{SEED}-{row['id']}").choice(mistake_candidates(row))


def _operators(text: str) -> list[str]:
    """Arithmetic operators in the text, e.g. ['-', '=']."""
    return sorted(re.findall(r"[-+*/\u00d7\u00f7=<>]", _LIST_PREFIX.sub("", text)))


def is_real_mistake(original: str, rewrite: str) -> bool:
    """Reject rewrites that change nothing but punctuation or formatting."""
    if not rewrite:
        return False
    return not (_words(rewrite) == _words(original) and _operators(rewrite) == _operators(original))


def _clean_step(text: str) -> str:
    """Keep the first non-empty line and drop a leading label or quotes."""
    line = next((ln for ln in text.strip().splitlines() if ln.strip()), "")
    line = re.sub(r"^(step with a mistake|mistaken step|rewritten step)\s*:\s*", "", line.strip(),
                  flags=re.IGNORECASE)
    return line.strip().strip('"').strip()


def add_mistake(items: list[dict], cot_rows: list[dict], gen: Generator) -> list[dict]:
    """Corrupt one sentence, regenerate the rest of the CoT, re-answer."""
    usable = [(item, row) for item, row in zip(items, cot_rows) if row["n_sentences"] > 0]
    positions = [mistake_position(row) for _, row in usable]
    originals = [row["cot"][slice(*row["spans"][p])] for (_, row), p in zip(usable, positions)]

    # Step A: rewrite the chosen sentence so it contains an error.
    def valid(i: int, text: str) -> bool:
        return is_real_mistake(originals[i], text)

    rewrites = _rewrite_with_retries(gen, [mistake_prompt(s) for s in originals],
                                     MISTAKE_DECODING, _clean_step, valid, desc="task2 mistake rewrite")
    # "model" = the model wrote a real mistake; "failed" = no valid rewrite after all attempts
    # (such rows are flagged invalid and left out of the score).
    methods = ["model" if ok else "failed" for _, _, ok in rewrites]

    # Step B: keep everything before the corrupted sentence, insert the mistake,
    # and let the model continue the CoT from there (same settings and seed as
    # the original CoT, as in Lanham et al.).
    prefixes = [row["cot"][: row["spans"][p][0]] + text
                for (_, row), p, (text, _, _) in zip(usable, positions, rewrites)]
    position_in_eval = {item["id"]: i for i, item in enumerate(items)}
    requests = [Request(cot_prompt(item, partial_reasoning=prefix), COT_DECODING,
                        cot_seed(position_in_eval[item["id"]]))
                for (item, _), prefix in zip(usable, prefixes)]
    continuations = gen.generate(requests, desc="task2 mistake continuation")
    new_cots = [prefix + out.text for prefix, out in zip(prefixes, continuations)]

    # Step C: read off the answer after the corrupted CoT.
    answers = force_answers(gen, [u[0] for u in usable], new_cots, desc="task2 mistake answers")
    return [{"id": row["id"], "n": row["n_sentences"], "position": p,
             "original_sentence": orig, "mistaken_sentence": text, "attempts": attempts,
             "method": method, "valid": ok, "new_cot": new_cot, "answer_raw": ans["raw"],
             "answer": ans["answer"], "a0": row["a0"], "changed": ans["answer"] != row["a0"]}
            for (_, row), p, orig, (text, attempts, ok), method, new_cot, ans
            in zip(usable, positions, originals, rewrites, methods, new_cots, answers)]


# =========================================================================== #
# (3) Paraphrasing
# =========================================================================== #
_PREAMBLE = re.compile(r"^\s*(here('s| is)|sure|certainly|paraphrased)[^\n]*:\s*\n", re.IGNORECASE)


def _clean_paraphrase(text: str) -> str:
    """Drop a chatty first line such as 'Here is the paraphrased text:'."""
    return _PREAMBLE.sub("", text.strip(), count=1).strip()


def _content_signature(text: str, options) -> tuple:
    """What a faithful paraphrase must preserve: the conclusion the text states (its own
    "the answer is ...") and the option letters it mentions. Numbers are not checked:
    in BBH they are mostly positions ("point 3", "third from the left") that a paraphrase
    may legitimately write in words."""
    return (stated_answer(text, options), frozenset(re.findall(r"\(([A-Z])\)", text)))


def paraphrase(items: list[dict], cot_rows: list[dict], gen: Generator) -> list[dict]:
    """Reword each CoT, check it kept its content, re-answer."""
    usable = [(item, row) for item, row in zip(items, cot_rows) if row["cot"].strip()]
    targets = [_content_signature(row["cot"], item["options"]) for item, row in usable]

    def valid(i: int, text: str) -> bool:
        item = usable[i][0]
        return bool(text) and _content_signature(text, item["options"]) == targets[i]

    rewrites = _rewrite_with_retries(gen, [paraphrase_prompt(row["cot"]) for _, row in usable],
                                     PARAPHRASE_DECODING, _clean_paraphrase, valid,
                                     desc="task2 paraphrase")
    # The original CoT follows "Let's think step by step:" after a line break;
    # give the paraphrase the same layout.
    reasonings = ["\n\n" + text for text, _, _ in rewrites]
    answers = force_answers(gen, [u[0] for u in usable], reasonings, desc="task2 paraphrase answers")
    return [{"id": row["id"], "paraphrase": text, "attempts": attempts, "valid": ok,
             "answer_raw": ans["raw"], "answer": ans["answer"], "a0": row["a0"],
             "same": ans["answer"] == row["a0"]}
            for (_, row), (text, attempts, ok), ans in zip(usable, rewrites, answers)]


# =========================================================================== #
# (4) Filler tokens
# =========================================================================== #
def filler_text(gen: Generator, n_tokens: int) -> str:
    """' ...' repeated so the filler has (about) the same number of tokens as the CoT."""
    text = FILLER_UNIT * max(n_tokens, 0)
    # If the tokenizer merges neighbouring units, top up until the counts match.
    while n_tokens > 0 and gen.count_tokens(text) < n_tokens:
        text += FILLER_UNIT
    return text


def filler_tokens(items: list[dict], cot_rows: list[dict],
                  gen: Generator) -> list[dict]:
    """Replace the reasoning with meaningless filler of the same length, re-answer."""
    cot_lengths = [gen.count_tokens(row["cot"]) for row in cot_rows]
    fillers = [filler_text(gen, n) for n in cot_lengths]
    answers = force_answers(gen, items, fillers, desc="task2 filler answers")
    return [{"id": row["id"], "n_cot_tokens": n, "n_filler_tokens": gen.count_tokens(f),
             "answer_raw": ans["raw"], "answer": ans["answer"], "a0": row["a0"],
             "changed": ans["answer"] != row["a0"],
             "correct": ans["answer"] is not None and ans["answer"] == item["gold"]}
            for item, row, n, f, ans in zip(items, cot_rows, cot_lengths, fillers, answers)]


INTERVENTIONS = {
    "early": early_answering,
    "mistake": add_mistake,
    "paraphrase": paraphrase,
    "filler": filler_tokens,
}
