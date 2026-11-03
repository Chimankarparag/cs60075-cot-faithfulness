"""Task 3 end to end (one model load, resumable).

    python code/task3/run_task3.py --split dev --tp 2          # 1) choose the vote rule on dev items
    python code/task3/run_task3.py --tp 2                      # 2) everything on the 150 eval items
    python code/task3/run_task3.py --seed 20 --tp 2            #    a repeat with another sampling seed
    python code/task3/run_task3.py --stages score              # recompute metrics/figures, no GPU
    python code/task3/run_task3.py --model qwen3-8b --tp 2     # the same for another model

Stages (each saves a file; a stage whose file exists is skipped unless --overwrite):
    sample         samples.jsonl            5 CoTs per item and each one's final answer A0_j
    early50        early50.jsonl            each sample's answer after 50% of its sentences
    prior          prior.jsonl              each item's answer with no reasoning (for loadbearing)
    tune           tuning.json, tuning.md   dev split only: choose rule and alpha (tune.py)
    interventions  pipeline_<name>/*.jsonl  Task 2's four interventions on the CoT each vote selects
    score          metrics.json, summary.md, votes.jsonl, figures/

Folders: results/task3/<dataset>/ (seed 42), .../seed_<N>/ (other seeds), .../dev/ (dev split);
under results/models/<model>/ for a model other than the default. Run Tasks 1 and 2 first: their
saved default-seed results are the baselines. Where and how long each run took is appended to
run_info.json in the same folder.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.cli import base_parser
from common.data import load_dev, load_eval
from common.io_utils import read_jsonl, write_jsonl
from common.model import load_generator
from common.runinfo import RunRecord
from task2.interventions import INTERVENTIONS
from task3.evaluate import chosen_cot_rows, load_samples, pipeline_votes, pipelines_for, score_task3, task3_dir
from task3.sample_k import K, sample_cots
from task3.tune import render_tuning, tune
from task3.weighted_vote import early_answer_50, prior_answers

STAGES = ["sample", "early50", "prior", "tune", "interventions", "score"]
GPU_STAGES = ("sample", "early50", "prior", "interventions")


def main() -> None:
    parser = base_parser("Task 3: faithfulness-weighted self-consistency")
    parser.add_argument("--split", choices=["test", "dev"], default="test",
                        help="test = the 150 evaluation items; dev = the 96 unused items for tuning")
    parser.add_argument("--stages", nargs="+", default=None, choices=STAGES)
    parser.add_argument("--pipelines", nargs="+", default=None,
                        help="pipelines to run interventions for (default: all, incl. tuned if available)")
    parser.add_argument("--k", type=int, default=K, help="CoTs per question (the assignment uses 5)")
    parser.add_argument("--overwrite", action="store_true", help="recompute stages whose output exists")
    args = parser.parse_args()
    smoke = bool(args.n_limit)
    dev = args.split == "dev"
    if dev and args.seed != 42:
        parser.error("the dev split is run once, with the default seed")
    stages = args.stages or ([s for s in STAGES if s not in ("interventions", "score")] if dev
                             else [s for s in STAGES if s != "tune"])

    items = (load_dev if dev else load_eval)(args.dataset, args.n_limit)
    items_by_id = {i["id"]: i for i in items}
    out = task3_dir(args.dataset, smoke, args.split)
    pipes = pipelines_for(args.dataset, smoke)
    wanted = args.pipelines or list(pipes)
    unknown = [p for p in wanted if p not in pipes]
    if unknown:
        parser.error(f"unknown or unavailable pipelines {unknown} (tuned needs --split dev first)")
    files = {"sample": out / "samples.jsonl", "early50": out / "early50.jsonl", "prior": out / "prior.jsonl"}
    pipeline_files = {(p, kind): out / f"pipeline_{p}" / f"{kind}.jsonl" for p in wanted for kind in INTERVENTIONS}

    def needs(stage: str) -> bool:
        if stage not in stages:
            return False
        if stage in files:
            return args.overwrite or not files[stage].exists()
        if stage == "interventions":
            return not dev and (args.overwrite or not all(f.exists() for f in pipeline_files.values()))
        return True

    use_gpu = any(needs(s) for s in GPU_STAGES)
    with RunRecord(out, args, enabled=use_gpu) as record:
        gen = load_generator(args) if use_gpu else None

        if needs("sample"):
            with record.stage("sample"):
                write_jsonl(files["sample"], sample_cots(items, gen, args.k))
        if needs("early50"):
            with record.stage("early50"):
                write_jsonl(files["early50"], early_answer_50(items_by_id, read_jsonl(files["sample"]), gen))
        if needs("prior"):
            with record.stage("prior"):
                write_jsonl(files["prior"], prior_answers(items, gen))

        if dev and "tune" in stages:
            result = tune(out)
            (out / "tuning.md").write_text(render_tuning(result), encoding="utf-8")
            print(render_tuning(result))

        if needs("interventions"):
            ids, samples_by_item = load_samples(out)
            pitems = [items_by_id[i] for i in ids]
            done: dict[tuple, str] = {}   # (rule, alpha) -> pipeline whose files already hold the result
            for pname in wanted:
                if not args.overwrite and all(pipeline_files[(pname, k)].exists() for k in INTERVENTIONS):
                    done.setdefault(pipes[pname], pname)
            for pname in wanted:
                pdir = out / f"pipeline_{pname}"
                pdir.mkdir(exist_ok=True)
                twin = done.get(pipes[pname])
                if twin == pname:
                    continue  # already complete
                if twin:
                    # Same rule and alpha as a pipeline already done: identical votes and CoTs.
                    for kind in INTERVENTIONS:
                        if not pipeline_files[(pname, kind)].exists():
                            shutil.copyfile(out / f"pipeline_{twin}" / f"{kind}.jsonl", pipeline_files[(pname, kind)])
                    print(f"[task3] {pname}: same rule as {twin}, files copied", flush=True)
                    continue
                votes = pipeline_votes(out, samples_by_item, pname, pipes)
                cot_rows = chosen_cot_rows(ids, samples_by_item, votes)
                for kind, fn in INTERVENTIONS.items():
                    path = pipeline_files[(pname, kind)]
                    if args.overwrite or not path.exists():
                        with record.stage(f"{pname}/{kind}"):
                            write_jsonl(path, fn(pitems, cot_rows, gen))
                done[pipes[pname]] = pname

        if not dev and "score" in stages:
            score_task3(args.dataset, smoke=smoke)
            print((out / "summary.md").read_text())


if __name__ == "__main__":
    main()
