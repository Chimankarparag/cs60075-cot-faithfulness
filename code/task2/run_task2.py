"""Task 2 end to end in one process (the model is loaded once).

Stages, in order, each saved to results/task2/<dataset>/:
    cot         CoT generation + A0                 -> cot.jsonl
    early       early answering                     -> early.jsonl
    mistake     adding a mistake                    -> mistake.jsonl
    paraphrase  paraphrasing                        -> paraphrase.jsonl
    filler      filler tokens                       -> filler.jsonl
    mistakes_all, paraphrase_prefix, filler_sweep   the paper's own versions of three
                interventions (paper_style.py)      -> <stage>.jsonl
    score       metrics, summary, figures, examples -> metrics.json, summary.md, figures/,
                (no GPU)                               examples.md, metrics_paper.json,
                                                       summary_paper.md

A stage whose output already exists is skipped unless --overwrite is given, so an
interrupted run resumes where it stopped. Task 1 should run first for the gain.

Usage:
    python code/task2/run_task2.py --dataset bbh
    python code/task2/run_task2.py --dataset bbh --n-limit 10              # smoke test
    python code/task2/run_task2.py --dataset bbh --stages paraphrase score --overwrite
    python code/task2/run_task2.py --model qwen3-8b          # another model, own results folder

Where and how long each run took is appended to run_info.json in the results folder.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.cli import base_parser
from common.data import load_eval
from common.io_utils import read_jsonl, results_dir, write_jsonl
from common.model import load_generator
from common.runinfo import RunRecord
from task2.generate_cot import generate_cots
from task2.interventions import INTERVENTIONS
from task2.examples import write_examples
from task2.paper_style import PAPER_STAGES, score_paper_style
from task2.score import score_task2

STAGES = ["cot", *INTERVENTIONS, *PAPER_STAGES, "score"]


def main() -> None:
    parser = base_parser("Task 2: CoT faithfulness interventions")
    parser.add_argument("--stages", nargs="+", default=STAGES, choices=STAGES)
    parser.add_argument("--overwrite", action="store_true", help="recompute stages whose output exists")
    args = parser.parse_args()

    items = load_eval(args.dataset, args.n_limit)
    out = results_dir("task2", args.dataset, smoke=bool(args.n_limit))

    def needs_run(stage: str) -> bool:
        return stage in args.stages and (args.overwrite or not (out / f"{stage}.jsonl").exists())

    use_gpu = any(needs_run(s) for s in STAGES if s != "score")
    with RunRecord(out, args, enabled=use_gpu) as record:
        gen = load_generator(args) if use_gpu else None

        if needs_run("cot"):
            with record.stage("cot"):
                write_jsonl(out / "cot.jsonl", generate_cots(items, gen))
        cot_rows = read_jsonl(out / "cot.jsonl")
        assert [r["id"] for r in cot_rows] == [i["id"] for i in items], "cot.jsonl does not match the eval items"

        for name, intervention in {**INTERVENTIONS, **PAPER_STAGES}.items():
            if needs_run(name):
                with record.stage(name):
                    write_jsonl(out / f"{name}.jsonl", intervention(items, cot_rows, gen))
                print(f"[task2] {name}: done", flush=True)

    if "score" in args.stages:
        score_task2(args.dataset, smoke=bool(args.n_limit))
        print((out / "summary.md").read_text())
        if score_paper_style(out):
            print((out / "summary_paper.md").read_text())
        # Qualitative examples for the report (reads the same files, no GPU).
        print(f"[task2] wrote {write_examples(args.dataset, args.n_limit)}")


if __name__ == "__main__":
    main()
