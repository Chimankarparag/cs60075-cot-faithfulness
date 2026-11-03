"""Task 3 end to end (one model load, resumable):  sample -> early50 -> interventions -> score.

    python code/task3/run_task3.py --tp 2                      # everything
    python code/task3/run_task3.py --stages score              # recompute metrics/figures, no GPU
    python code/task3/run_task3.py --stages interventions --pipelines weighted --overwrite

Stages (each saves a file under results/task3/<dataset>/; a stage whose file exists is skipped):
    sample         samples.jsonl            5 CoTs per item and each one's final answer A0_j
    early50        early50.jsonl            each sample's answer after 50% of its sentences
    interventions  pipeline_<name>/*.jsonl  Task 2's four interventions on the CoT each pipeline's vote selects
    score          metrics.json, summary.md, votes.jsonl, figures/

Run Tasks 1 and 2 first: their saved results are the baselines.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.cli import base_parser
from common.data import load_eval
from common.io_utils import read_jsonl, results_dir, write_jsonl
from common.model import load_generator
from task2.interventions import INTERVENTIONS
from task3.evaluate import PIPELINES, chosen_cot_rows, load_samples, pipeline_votes, score_task3
from task3.sample_k import K, sample_cots
from task3.weighted_vote import early_answer_50

STAGES = ["sample", "early50", "interventions", "score"]


def main() -> None:
    parser = base_parser("Task 3: faithfulness-weighted self-consistency")
    parser.add_argument("--stages", nargs="+", default=STAGES, choices=STAGES)
    parser.add_argument("--pipelines", nargs="+", default=list(PIPELINES), choices=list(PIPELINES))
    parser.add_argument("--k", type=int, default=K, help="CoTs per question (the assignment uses 5)")
    parser.add_argument("--overwrite", action="store_true", help="recompute stages whose output exists")
    args = parser.parse_args()

    items = load_eval(args.dataset, args.n_limit)
    out = results_dir("task3", args.dataset, smoke=bool(args.n_limit))
    pipeline_files = {(p, k): out / f"pipeline_{p}" / f"{k}.jsonl" for p in args.pipelines for k in INTERVENTIONS}

    def needs(stage: str) -> bool:
        if stage not in args.stages:
            return False
        if stage == "sample":
            return args.overwrite or not (out / "samples.jsonl").exists()
        if stage == "early50":
            return args.overwrite or not (out / "early50.jsonl").exists()
        return args.overwrite or not all(f.exists() for f in pipeline_files.values())

    gen = load_generator(args) if any(needs(s) for s in ("sample", "early50", "interventions")) else None

    if needs("sample"):
        write_jsonl(out / "samples.jsonl", sample_cots(items, gen, args.k))
        print("[task3] sample: done", flush=True)
    items_by_id = {i["id"]: i for i in items}

    if needs("early50"):
        write_jsonl(out / "early50.jsonl", early_answer_50(items_by_id, read_jsonl(out / "samples.jsonl"), gen))
        print("[task3] early50: done", flush=True)

    if "interventions" in args.stages:
        ids, samples_by_item = load_samples(out)
        for pname in args.pipelines:
            votes = pipeline_votes(out, samples_by_item, pname)
            cot_rows = chosen_cot_rows(ids, samples_by_item, votes)
            pitems = [items_by_id[i] for i in ids]
            (out / f"pipeline_{pname}").mkdir(exist_ok=True)
            for kind, fn in INTERVENTIONS.items():
                path = pipeline_files[(pname, kind)]
                if args.overwrite or not path.exists():
                    write_jsonl(path, fn(pitems, cot_rows, gen))
                    print(f"[task3] {pname}/{kind}: done", flush=True)

    if "score" in args.stages:
        score_task3(args.dataset, smoke=bool(args.n_limit))
        print((out / "summary.md").read_text())


if __name__ == "__main__":
    main()
