"""Task 1 - direct (no chain-of-thought) answering baseline.

For every evaluation item the model must answer immediately, with greedy decoding
and at most 16 new tokens, in two variants:

* zero_shot - just the question;
* four_shot - the same 4 fixed exemplars (answers only, no worked solutions) first.

Outputs (results/task1/<dataset>/):
    zero_shot.jsonl, four_shot.jsonl   one row per item: raw output, parsed answer, correct?
    metrics.json                       accuracy + 95% CI per variant, best variant
    summary.md                         the same numbers as a table

Usage:
    python code/task1/run_direct.py --dataset bbh
    python code/task1/run_direct.py --dataset bbh --n-limit 10     # smoke test
    python code/task1/run_direct.py --dataset bbh --rescore        # re-parse saved outputs, no GPU
"""
from __future__ import annotations

import sys
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # make `code/` importable

from common.cli import base_parser
from common.config import DIRECT_DECODING, MODEL_ID, MODEL_REVISION, N_FEWSHOT, SEED
from common.data import load_eval, load_fewshot
from common.io_utils import read_jsonl, results_dir, write_json, write_jsonl
from common.metrics import fmt_ci, summarize_binary
from common.model import Output, Request, load_generator
from common.parsing import is_correct, parse_answer
from common.prompts import direct_prompt

# variant name -> number of exemplars
VARIANTS = {"zero_shot": 0, "four_shot": N_FEWSHOT}


def build_requests(items: list[dict], exemplars: list[dict]) -> list[Request]:
    """One greedy request per item. `exemplars` is empty for zero-shot."""
    return [Request(direct_prompt(item, exemplars), DIRECT_DECODING, SEED) for item in items]


def score_row(item: dict, output_text: str, n_tokens: int, finish_reason: str) -> dict:
    """Parse one output and compare it with the gold answer."""
    pred = parse_answer(output_text, item["options"])
    return {"id": item["id"], "gold": item["gold"], "output": output_text, "pred": pred,
            "correct": is_correct(pred, item["gold"]), "n_tokens": n_tokens,
            "hit_max_tokens": finish_reason == "length"}


def score_outputs(items: list[dict], outputs: list[Output]) -> list[dict]:
    return [score_row(item, out.text, out.n_tokens, out.finish_reason)
            for item, out in zip(items, outputs)]


def rescore_rows(items: list[dict], rows: list[dict]) -> list[dict]:
    """Re-parse saved outputs (e.g. after improving the parser) without the model."""
    by_id = {item["id"]: item for item in items}
    return [score_row(by_id[r["id"]], r["output"], r["n_tokens"],
                      "length" if r["hit_max_tokens"] else "stop") for r in rows]


def summarize(rows: list[dict]) -> dict:
    """Accuracy with a bootstrap CI, plus two sanity counts:
    parse failures (no answer found) and outputs that hit the 16-token cap
    (a sign the model started explaining instead of answering)."""
    summary = summarize_binary(r["correct"] for r in rows)
    summary["parse_failures"] = sum(r["pred"] is None for r in rows)
    summary["hit_max_tokens"] = sum(r["hit_max_tokens"] for r in rows)
    return summary


def write_summary_md(path: Path, dataset: str, metrics: dict) -> None:
    lines = [f"# Task 1 - direct answering on {dataset} (n = {metrics['n_items']})", "",
             "| Variant | Accuracy % [95% CI] | Parse failures | Hit 16-token cap |",
             "| --- | --- | --- | --- |"]
    for name, s in metrics["variants"].items():
        mark = " (best)" if name == metrics["best_variant"] else ""
        lines.append(f"| {name}{mark} | {fmt_ci(s)} | {s['parse_failures']} | {s['hit_max_tokens']} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = base_parser("Task 1: direct-answer baseline")
    parser.add_argument("--variants", nargs="+", default=list(VARIANTS), choices=list(VARIANTS))
    parser.add_argument("--rescore", action="store_true", help="re-parse saved outputs; no model needed")
    args = parser.parse_args()

    items = load_eval(args.dataset, args.n_limit)
    out_dir = results_dir("task1", args.dataset, smoke=bool(args.n_limit))

    rows_by_variant: dict[str, list[dict]] = {}
    if args.rescore:
        for variant in args.variants:
            rows_by_variant[variant] = rescore_rows(items, read_jsonl(out_dir / f"{variant}.jsonl"))
    else:
        gen = load_generator(args)
        exemplars = load_fewshot(args.dataset)
        for variant in args.variants:
            shots = exemplars[:VARIANTS[variant]]
            outputs = gen.generate(build_requests(items, shots), desc=f"task1 {variant}")
            rows_by_variant[variant] = score_outputs(items, outputs)

    for variant, rows in rows_by_variant.items():
        write_jsonl(out_dir / f"{variant}.jsonl", rows)

    variants = {v: summarize(rows) for v, rows in rows_by_variant.items()}
    best = max(variants, key=lambda v: variants[v]["mean"])  # ties keep the first (zero_shot)
    metrics = {"task": "task1", "dataset": args.dataset, "n_items": len(items), "model": MODEL_ID,
               "model_revision": MODEL_REVISION, "seed": SEED,
               "decoding": asdict(DIRECT_DECODING),
               "variants": variants, "best_variant": best}
    write_json(out_dir / "metrics.json", metrics)
    write_summary_md(out_dir / "summary.md", args.dataset, metrics)
    print((out_dir / "summary.md").read_text())


if __name__ == "__main__":
    main()
