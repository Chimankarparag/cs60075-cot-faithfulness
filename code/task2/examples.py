"""Task 2 - pick concrete examples for the report's qualitative analysis.

The report must discuss individual examples, not just averages. This script
reads the saved generations and writes results/task2/<dataset>/examples.md with,
for every intervention, examples where the answer changed and where it did not,
plus CoTs whose own stated answer disagrees with the forced answer A0.

Selection is deterministic (items in eval order), so reruns give the same file.
Usage:  python code/task2/examples.py [--per-group 2]
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.cli import base_parser
from common.data import load_eval
from common.io_utils import read_jsonl, results_dir
from common.parsing import truncate
from common.prompts import COT_PREFIX


def quote(text: str, limit: int = 1200) -> str:
    """Markdown blockquote of `text`, shortened to `limit` characters."""
    text = text.strip()
    if len(text) > limit:
        text = text[:limit].rstrip() + " [...]"
    return "\n".join("> " + line if line else ">" for line in text.splitlines())


def header(item: dict, cot: dict) -> list[str]:
    return [f"**{item['id']}** - gold `{item['gold']}`, A0 `{cot['a0']}` "
            f"({'correct' if cot['correct'] else 'wrong'})", "", quote(item["question"], 700), ""]


def early_examples(items, cots, rows, k: int) -> list[str]:
    by_id: dict[str, dict[int, dict]] = {}
    for r in rows:
        by_id.setdefault(r["id"], {})[r["k"]] = r
    out = ["## Early answering", ""]
    for label, want_change in (("Answer changes when the CoT is cut to 50%", True),
                               ("Answer already fixed at 50% of the CoT", False)):
        out += [f"### {label}", ""]
        shown = 0
        for item in items:
            c, answers = cots[item["id"]], by_id.get(item["id"], {})
            half = c["n_sentences"] // 2
            if c["n_sentences"] < 4 or half not in answers:
                continue
            if (answers[half]["answer"] != c["a0"]) != want_change:
                continue
            curve = ", ".join(f"{kk}:{answers[kk]['answer']}" for kk in sorted(answers))
            out += header(item, c) + [f"Kept {half}/{c['n_sentences']} sentences -> answer "
                                      f"`{answers[half]['answer']}`. Answer after each prefix: {curve}", "",
                                      quote(COT_PREFIX + truncate(c["cot"], [tuple(s) for s in c["spans"]], half)), ""]
            shown += 1
            if shown == k:
                break
    return out


def simple_examples(title, items, cots, rows, flag, labels, render, k) -> list[str]:
    by_id = {r["id"]: r for r in rows}
    out = [f"## {title}", ""]
    for label, want in labels:
        out += [f"### {label}", ""]
        shown = 0
        for item in items:
            r = by_id.get(item["id"])
            if r is None or r.get("valid") is False or bool(r[flag]) != want:
                continue
            out += header(item, cots[item["id"]]) + render(r) + [""]
            shown += 1
            if shown == k:
                break
    return out


def write_examples(dataset: str, n_limit: int | None = None, k: int = 2) -> Path:
    """Write results/task2/<dataset>/examples.md and return its path."""
    out = results_dir("task2", dataset, smoke=bool(n_limit))
    items = load_eval(dataset, n_limit)
    cots = {r["id"]: r for r in read_jsonl(out / "cot.jsonl")}

    lines = [f"# Task 2 - qualitative examples ({dataset})", "",
             "Selected deterministically in eval order. A0 = answer after the full, untouched CoT.", ""]
    lines += early_examples(items, cots, read_jsonl(out / "early.jsonl"), k)
    lines += simple_examples(
        "Adding a mistake", items, cots, read_jsonl(out / "mistake.jsonl"), "changed",
        [("The mistake changed the answer (faithful)", True), ("The answer survived the mistake", False)],
        lambda r: [f"Sentence {r['position'] + 1}/{r['n']} rewritten ({r['method']}):", "",
                   quote("Original: " + r["original_sentence"]), "", quote("Mistake: " + r["mistaken_sentence"]),
                   "", f"New answer `{r['answer']}` (A0 `{r['a0']}`)."], k)
    lines += simple_examples(
        "Paraphrasing", items, cots, read_jsonl(out / "paraphrase.jsonl"), "same",
        [("Answer unchanged after paraphrasing (faithful)", True), ("Answer changed after paraphrasing", False)],
        lambda r: [quote("Paraphrase: " + r["paraphrase"], 800), "", f"New answer `{r['answer']}` (A0 `{r['a0']}`)."], k)
    lines += simple_examples(
        "Filler tokens", items, cots, read_jsonl(out / "filler.jsonl"), "changed",
        [("Filler changed the answer (faithful)", True), ("Same answer with only filler", False)],
        lambda r: [f"{r['n_filler_tokens']} filler tokens -> answer `{r['answer']}` (A0 `{r['a0']}`)."], k)

    lines += ["## CoT states one answer, forced answer A0 is another", ""]
    shown = 0
    for item in items:
        c = cots[item["id"]]
        if c["stated_answer"] is not None and c["stated_answer"] != c["a0"]:
            lines += header(item, c) + [f"CoT states `{c['stated_answer']}`, forced answer `{c['a0']}`.", "",
                                        quote(COT_PREFIX + c["cot"], 900), ""]
            shown += 1
            if shown == k:
                break
    path = out / "examples.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main() -> None:
    parser = base_parser("Task 2: write qualitative examples", needs_model=False)
    parser.add_argument("--per-group", type=int, default=2)
    args = parser.parse_args()
    print(f"wrote {write_examples(args.dataset, args.n_limit, args.per_group)}")


if __name__ == "__main__":
    main()
