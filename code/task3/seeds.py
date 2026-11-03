"""Task 3 - how stable are the results across sampling seeds?

Task 3 samples its 5 CoTs per item at temperature 0.7, so one run is one draw. The pipeline is
run with generation seeds 42 (the main run), 20, 30 and 40 (run_task3.py --seed N); the items,
exemplars and baselines are the same in every run. This script reads each run's metrics.json and
reports, per pipeline, the accuracy and aggregate faithfulness in every run with their mean and
spread, and how often each comparison came out the same way.

    python code/task3/seeds.py                 # writes results/task3/<dataset>/seeds_summary.{json,md}
    python code/task3/seeds.py --model qwen3-8b
"""
from __future__ import annotations

import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.cli import base_parser
from common.config import MODEL_ID, SEED
from common.io_utils import read_json, results_dir, write_json

SEEDS = (42, 20, 30, 40)
ORDER = ("plain_sc", "weighted", "tuned", "ablation_changed")


def _spread(values: list[float]) -> dict:
    return {"values": values, "mean": statistics.mean(values),
            "sd": statistics.stdev(values) if len(values) > 1 else 0.0,
            "min": min(values), "max": max(values)}


def aggregate_seeds(dataset: str, seeds=SEEDS, smoke: bool = False) -> dict:
    runs = {}
    for s in seeds:
        path = results_dir("task3", dataset, smoke, seed=s) / "metrics.json"
        if path.exists():
            runs[s] = read_json(path)
    if not runs:
        raise SystemExit("no Task 3 runs found")
    pipes = [p for p in ORDER if all(p in m.get("accuracy", {}) for m in runs.values())]
    first = next(iter(runs.values()))
    out = {"model": MODEL_ID, "dataset": dataset, "seeds": list(runs), "pipelines": {},
           "baselines": {n: b["mean"] for n, b in first["baselines"].items()}}
    t2_agg = first.get("faithfulness", {}).get("task2_single_cot", {}).get("aggregate")
    if t2_agg is not None:
        out["baselines"]["Task 2 aggregate faithfulness"] = t2_agg
    for p in pipes:
        entry = {"accuracy": _spread([m["accuracy"][p]["mean"] for m in runs.values()])}
        if all("faithfulness" in m and p in m["faithfulness"] for m in runs.values()):
            entry["aggregate_faithfulness"] = _spread([m["faithfulness"][p]["aggregate"] for m in runs.values()])
        for b in first["baselines"]:
            diffs = [m["comparisons"][f"{p} vs {b}"]["diff"]["diff"] for m in runs.values()]
            entry[f"diff vs {b}"] = {**_spread(diffs), "n_positive": sum(d > 0 for d in diffs)}
        if p != "plain_sc":
            diffs = [m["comparisons"][f"{p} vs plain_sc"]["diff"]["diff"] for m in runs.values()]
            entry["diff vs plain_sc"] = {**_spread(diffs), "n_positive": sum(d > 0 for d in diffs),
                                         "n_negative": sum(d < 0 for d in diffs)}
        out["pipelines"][p] = entry
    out["mean_single_sample_accuracy"] = _spread([m["samples"]["mean_accuracy_per_item"] for m in runs.values()])
    path = results_dir("task3", dataset, smoke, seed=SEED)
    write_json(path / "seeds_summary.json", out)
    (path / "seeds_summary.md").write_text(render(out), encoding="utf-8")
    return out


def render(o: dict) -> str:
    seeds = o["seeds"]
    f = lambda x: f"{100 * x:.1f}"
    L = [f"# Task 3 across sampling seeds ({o['model']}, seeds {', '.join(map(str, seeds))})", "",
         "## Accuracy (%)", "",
         "| Pipeline | " + " | ".join(f"seed {s}" for s in seeds) + " | Mean | SD |",
         "| --- |" + " --- |" * (len(seeds) + 2)]
    L.append("| Mean single sample | " + " | ".join(f(v) for v in o["mean_single_sample_accuracy"]["values"]) +
             f" | {f(o['mean_single_sample_accuracy']['mean'])} | {f(o['mean_single_sample_accuracy']['sd'])} |")
    for p, e in o["pipelines"].items():
        a = e["accuracy"]
        L.append(f"| {p} | " + " | ".join(f(v) for v in a["values"]) + f" | {f(a['mean'])} | {f(a['sd'])} |")
    L += ["", "Baselines (same in every run): " + "; ".join(f"{n} {f(v)}%" for n, v in o["baselines"].items()), "",
          "## Differences (points; mean over seeds, and in how many seeds the difference was positive)", "",
          "| Pipeline | Comparison | Mean | Min | Max | Seeds > 0 |", "| --- | --- | --- | --- | --- | --- |"]
    for p, e in o["pipelines"].items():
        for key, d in e.items():
            if key.startswith("diff vs"):
                L.append(f"| {p} | {key[5:]} | {100 * d['mean']:+.1f} | {100 * d['min']:+.1f} | "
                         f"{100 * d['max']:+.1f} | {d['n_positive']}/{len(seeds)} |")
    if any("aggregate_faithfulness" in e for e in o["pipelines"].values()):
        L += ["", "## Aggregate faithfulness of the pipeline's output (%)", "",
              "| Pipeline | " + " | ".join(f"seed {s}" for s in seeds) + " | Mean | SD |",
              "| --- |" + " --- |" * (len(seeds) + 2)]
        for p, e in o["pipelines"].items():
            if "aggregate_faithfulness" in e:
                a = e["aggregate_faithfulness"]
                L.append(f"| {p} | " + " | ".join(f(v) for v in a["values"]) + f" | {f(a['mean'])} | {f(a['sd'])} |")
    return "\n".join(L) + "\n"


def main() -> None:
    parser = base_parser("Task 3: summarise the runs with different sampling seeds", needs_model=False)
    args = parser.parse_args()
    print(render(aggregate_seeds(args.dataset, smoke=bool(args.n_limit))))


if __name__ == "__main__":
    main()
