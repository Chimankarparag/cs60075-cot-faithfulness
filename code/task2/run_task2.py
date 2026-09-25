"""Task 2 end to end in one process (the model is loaded once).

Stages, in order, each saved to results/task2/<dataset>/:
    cot         CoT generation + A0                 -> cot.jsonl
    early       early answering                     -> early.jsonl
    mistake     adding a mistake                    -> mistake.jsonl
    paraphrase  paraphrasing                        -> paraphrase.jsonl
    filler      filler tokens                       -> filler.jsonl
    score       metrics, summary, figures (no GPU)  -> metrics.json, summary.md, figures/

A stage whose output already exists is skipped unless --overwrite is given, so an
interrupted run resumes where it stopped. Task 1 should run first for the gain.

Usage:
    python code/task2/run_task2.py --dataset gsm8k
    python code/task2/run_task2.py --dataset gsm8k --n-limit 10              # smoke test
    python code/task2/run_task2.py --dataset gsm8k --stages paraphrase score --overwrite
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.cli import base_parser
from common.config import get_spec
from common.data import load_eval
from common.io_utils import read_jsonl, results_dir, write_jsonl
from common.model import load_generator
from task2.generate_cot import generate_cots
from task2.interventions import INTERVENTIONS
from task2.score import score_task2

STAGES = ["cot", *INTERVENTIONS, "score"]


def main() -> None:
    parser = base_parser("Task 2: CoT faithfulness interventions")
    parser.add_argument("--stages", nargs="+", default=STAGES, choices=STAGES)
    parser.add_argument("--overwrite", action="store_true", help="recompute stages whose output exists")
    args = parser.parse_args()

    spec = get_spec(args.dataset)
    items = load_eval(args.dataset, args.n_limit)
    out = results_dir("task2", args.dataset, smoke=bool(args.n_limit))

    def needs_run(stage: str) -> bool:
        return stage in args.stages and (args.overwrite or not (out / f"{stage}.jsonl").exists())

    gen = None
    if any(needs_run(s) for s in STAGES if s != "score"):
        gen = load_generator(args)

    if needs_run("cot"):
        write_jsonl(out / "cot.jsonl", generate_cots(items, spec.answer_type, gen))
    cot_rows = read_jsonl(out / "cot.jsonl")
    assert [r["id"] for r in cot_rows] == [i["id"] for i in items], "cot.jsonl does not match the eval items"

    for name, intervention in INTERVENTIONS.items():
        if needs_run(name):
            write_jsonl(out / f"{name}.jsonl", intervention(items, cot_rows, spec.answer_type, gen))
            print(f"[task2] {name}: done", flush=True)

    if "score" in args.stages:
        score_task2(args.dataset, smoke=bool(args.n_limit))
        print((out / "summary.md").read_text())


if __name__ == "__main__":
    main()
