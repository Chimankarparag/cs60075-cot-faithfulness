"""Turning model text into comparable answers, and splitting a CoT into sentences.

Two jobs live here because both are pure text processing with no model involved,
which makes them easy to unit-test on a laptop:

1. Answer extraction: map free text such as " (C) The raven ..." or "is C." to a
   canonical option letter ("C") so answers can be compared with `==`.
2. Sentence splitting: early answering, adding mistakes and paraphrasing all work
   on "the first k sentences" of a chain of thought, so they must all use the same
   splitter. We keep character offsets (spans) rather than a list of strings, so a
   truncated CoT is an exact prefix of the original text, formatting included.
"""
from __future__ import annotations

import re


# Option letters (BBH)
_PAREN_LETTER = re.compile(r"\(([A-Z])\)")
_LEADING_LETTER = re.compile(r"^\s*([A-Z])(?:[).:,]|\s|$)")


def extract_letter(text: str, options: dict[str, str] | None, last: bool = False) -> str | None:
    """Find which option the text picks, trying three rules in order:

    1. a parenthesised letter such as "(C)"            -> most reliable
    2. a bare letter right at the start: "C) ..." / "C." -> e.g. "is C."
    3. the option's text itself: "the raven is the rightmost"
    """
    valid = set(options) if options else set("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    letters = [m for m in _PAREN_LETTER.findall(text) if m in valid]
    if letters:
        return letters[-1] if last else letters[0]
    lead = _LEADING_LETTER.match(text)
    if lead and lead.group(1) in valid:
        return lead.group(1)
    if options:
        lowered = text.lower()
        hits = [(lowered.rfind(body.lower()) if last else lowered.find(body.lower()), letter)
                for letter, body in options.items() if body.lower() in lowered]
        if hits:
            return (max(hits) if last else min(hits))[1]
    return None



# One entry point for answer extraction
def parse_answer(text: str, options: dict[str, str] | None = None, last: bool = False) -> str | None:
    """Canonical option letter from a short model output, or None if nothing parseable."""
    return extract_letter(text, options, last)


_ANSWER_CUE = re.compile(r"answer\s*(?:is|:)|\\boxed\{", re.IGNORECASE)


def stated_answer(cot: str, options: dict[str, str] | None = None) -> str | None:
    """The answer a CoT states itself (e.g. '... so the answer is (C).').

    Takes the text after the last "answer is" / "answer:" / "\\boxed{" cue; if the
    CoT has no cue, falls back to the last answer-like token in the whole CoT.
    Used only for analysis (does the CoT's own conclusion match the forced answer?).
    """
    cues = list(_ANSWER_CUE.finditer(cot))
    if cues:
        found = parse_answer(cot[cues[-1].end():], options)
        if found is not None:
            return found
    return parse_answer(cot, options, last=True)


def is_correct(pred: str | None, gold: str) -> bool:
    return pred is not None and pred == gold



# Sentence splitting
# A sentence ends at ., ! or ? followed by whitespace and then something that can
# start a sentence (capital letter, digit, bracket, quote, markdown *, $).
# "3.5" never splits (no whitespace after the dot); "e.g. the" never splits
# (lower-case next word).
_BOUNDARY = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9(\"'*$])")
# Pieces that are only a list marker ("1.", "2)", "-", "**") are not sentences.
_LIST_MARKER = re.compile(r"^(?:\d+[.)]|[-*•]|\*\*)$")
_MIN_SENTENCE_CHARS = 4


def split_sentences(text: str) -> list[tuple[int, int]]:
    """Split `text` into sentences and return their (start, end) character spans.

    Rules, applied in order:
      1. every non-empty line is split separately (CoTs are often one step per line);
      2. inside a line, split at sentence-ending punctuation (see _BOUNDARY);
      3. a piece that is just a list marker or shorter than 4 characters is merged
         into the following piece (so "1." + "Janet has 16 eggs." is one sentence).
    """
    pieces: list[tuple[int, int]] = []
    for line in re.finditer(r"[^\n]+", text):
        start = line.start()
        for boundary in _BOUNDARY.finditer(line.group()):
            pieces.append((start, line.start() + boundary.start()))
            start = line.start() + boundary.end()
        pieces.append((start, line.end()))

    # Trim surrounding spaces and drop empty pieces.
    trimmed = []
    for s, e in pieces:
        chunk = text[s:e]
        if chunk.strip():
            s += len(chunk) - len(chunk.lstrip())
            e -= len(chunk) - len(chunk.rstrip())
            trimmed.append((s, e))

    # Merge list markers / tiny fragments into the next piece.
    spans: list[tuple[int, int]] = []
    carry_start: int | None = None
    for s, e in trimmed:
        piece = text[s:e].strip()
        start = carry_start if carry_start is not None else s
        if _LIST_MARKER.match(piece) or len(piece) < _MIN_SENTENCE_CHARS:
            carry_start = start
            continue
        spans.append((start, e))
        carry_start = None
    if carry_start is not None:  # a dangling fragment at the very end
        if spans:
            spans[-1] = (spans[-1][0], trimmed[-1][1])
        else:
            spans.append((carry_start, trimmed[-1][1]))
    return spans


def truncate(text: str, spans: list[tuple[int, int]], k: int) -> str:
    """The first k sentences of `text`, exactly as written (k = 0 gives '')."""
    if k <= 0:
        return ""
    return text[: spans[min(k, len(spans)) - 1][1]]
