"""Turning model text into comparable answers, and splitting a CoT into sentences.

Two jobs live here because both are pure text processing with no model involved,
which makes them easy to unit-test on a laptop:

1. Answer extraction: map free text such as " $1,000." or " (C) The raven ..." to a
   canonical string ("1000", "C", "Yes") so answers can be compared with `==`.
2. Sentence splitting: early answering, adding mistakes and paraphrasing all work
   on "the first k sentences" of a chain of thought, so they must all use the same
   splitter. We keep character offsets (spans) rather than a list of strings, so a
   truncated CoT is an exact prefix of the original text, formatting included.
"""
from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

# --------------------------------------------------------------------------- #
# Numbers (GSM8K)
# --------------------------------------------------------------------------- #
# Either a comma-grouped number ("1,234,567") or a plain one ("1234"), with an
# optional decimal part and minus sign. Grouping must be exactly 3 digits, so a
# list like "3,4" is read as two numbers rather than as 34.
NUMBER_RE = re.compile(r"-?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?")


def canonical_number(text: str) -> str | None:
    """'$1,000.00' -> '1000', '3.50' -> '3.5', 'abc' -> None.

    Integers are written without a decimal point and trailing zeros are removed,
    so equal values always give equal strings.
    """
    match = NUMBER_RE.search(text.replace("$", "").replace("−", "-"))
    if match is None:
        return None
    try:
        value = Decimal(match.group().replace(",", ""))
    except InvalidOperation:
        return None
    if value == value.to_integral_value():
        return str(int(value))
    return format(value.normalize(), "f")


def extract_number(text: str, last: bool = False) -> str | None:
    """First (or last) number mentioned in `text`, canonicalised."""
    cleaned = text.replace("$", "").replace("−", "-")
    matches = NUMBER_RE.findall(cleaned)
    if not matches:
        return None
    return canonical_number(matches[-1] if last else matches[0])


# --------------------------------------------------------------------------- #
# Option letters (BBH)
# --------------------------------------------------------------------------- #
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


# --------------------------------------------------------------------------- #
# Yes / No (StrategyQA)
# --------------------------------------------------------------------------- #
_YESNO = re.compile(r"\b(yes|no|true|false)\b", re.IGNORECASE)
# "not a simple yes or no" mentions both words without choosing either.
_YESNO_PHRASE = re.compile(r"\b(yes\s*(or|/)\s*no|no\s*(or|/)\s*yes|true\s*(or|/)\s*false)\b", re.IGNORECASE)


def extract_yesno(text: str, last: bool = False) -> str | None:
    matches = _YESNO.findall(_YESNO_PHRASE.sub(" ", text))
    if not matches:
        return None
    word = (matches[-1] if last else matches[0]).lower()
    return "Yes" if word in ("yes", "true") else "No"


# --------------------------------------------------------------------------- #
# One entry point for all three answer types
# --------------------------------------------------------------------------- #
def parse_answer(text: str, answer_type: str, options: dict[str, str] | None = None,
                 last: bool = False) -> str | None:
    """Canonical answer from a short model output, or None if nothing parseable."""
    if answer_type == "number":
        return extract_number(text, last)
    if answer_type == "letter":
        return extract_letter(text, options, last)
    if answer_type == "yesno":
        return extract_yesno(text, last)
    raise ValueError(f"unknown answer_type {answer_type!r}")


_ANSWER_CUE = re.compile(r"answer\s*(?:is|:)|\\boxed\{", re.IGNORECASE)


def stated_answer(cot: str, answer_type: str, options: dict[str, str] | None = None) -> str | None:
    """The answer a CoT states itself (e.g. '... so the answer is 18.').

    Takes the text after the last "answer is" / "answer:" / "\\boxed{" cue; if the
    CoT has no cue, falls back to the last answer-like token in the whole CoT.
    Used only for analysis (does the CoT's own conclusion match the forced answer?).
    """
    cues = list(_ANSWER_CUE.finditer(cot))
    if cues:
        found = parse_answer(cot[cues[-1].end():], answer_type, options)
        if found is not None:
            return found
    return parse_answer(cot, answer_type, options, last=True)


def is_correct(pred: str | None, gold: str) -> bool:
    return pred is not None and pred == gold


# --------------------------------------------------------------------------- #
# Sentence splitting
# --------------------------------------------------------------------------- #
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
