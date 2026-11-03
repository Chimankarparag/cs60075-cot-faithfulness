"""Compare the models side by side, and list where and how long every run took.

Reads the saved results of every model in common.config.MODELS (no GPU):
    results/<task>/bbh/                 meta-llama/Llama-3.1-8B-Instruct (default model)
    results/models/<model>/<task>/bbh/  every other model
and writes
    results/comparison/models.md, models.json      Tasks 1-3 for each model in one table
    results/comparison/runs.md                       every run_info.json entry: host, GPUs, time
    results/comparison/figures/models_accuracy.png, models_faithfulness.png

    python code/analysis/compare_models.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.config import DEFAULT_MODEL, MODELS, RESULTS_ROOT
from common.io_utils import read_json, write_json

DATASET = "bbh"
OUT = RESULTS_ROOT / "comparison"
T3_PIPES = ("plain_sc", "weighted", "tuned", "ablation_changed")
SCORE_NAMES = ("Early answering", "Adding a mistake", "Paraphrasing", "Filler tokens")


def model_root(key: str) -> Path:
    return RESULTS_ROOT if key == DEFAULT_MODEL else RESULTS_ROOT / "models" / key


def _load(path: Path) -> dict | None:
    return read_json(path) if path.exists() else None


def collect(key: str) -> dict:
    root = model_root(key)
    t1 = _load(root / "task1" / DATASET / "metrics.json")
    t2 = _load(root / "task2" / DATASET / "metrics.json")
    t2p = _load(root / "task2" / DATASET / "metrics_paper.json")
    t3 = _load(root / "task3" / DATASET / "metrics.json")
    seeds = _load(root / "task3" / DATASET / "seeds_summary.json")
    tuning = _load(root / "task3" / DATASET / "dev" / "tuning.json")
    m: dict = {"model": MODELS[key].hf_id, "about": MODELS[key].about}
    if t1:
        m["task1"] = {v: s["mean"] for v, s in t1["variants"].items()} | {"best": t1["best_variant"]}
    if t2:
        m["task2"] = {"cot_accuracy": t2["cot"]["mean"], "gain": t2["gain_over_task1"]["gain"]["diff"],
                      "gain_ci95": t2["gain_over_task1"]["gain"]["ci95"],
                      "mcnemar_p": t2["gain_over_task1"]["mcnemar"]["p_value"],
                      "scores": t2["faithfulness_scores"], "aggregate": t2.get("aggregate_faithfulness"),
                      "early_aoc_grid": t2["early_answering"]["aoc_grid"],
                      "early_aoc_lanham": t2["early_answering"]["aoc_lanham"],
                      "no_cot_same_as_cot": t2["early_answering"]["curve_same_answer"]["0.0"],
                      "mean_sentences": t2["cot"]["mean_sentences"], "mean_tokens": t2["cot"]["mean_tokens"],
                      "hit_max_tokens": t2["cot"]["hit_max_tokens"]}
    if t2p:
        m["task2_paper_style"] = {
            "mistakes_aoc": t2p.get("mistakes_all", {}).get("aoc", {}).get("mean"),
            "paraphrase_accuracy": {f: v["accuracy"] for f, v in t2p.get("paraphrase_prefix", {}).get("by_fraction", {}).items()},
            "filler_accuracy": {p: v["accuracy"] for p, v in t2p.get("filler_sweep", {}).get("by_percentile", {}).items()}}
    if t3:
        m["task3"] = {"accuracy": {p: t3["accuracy"][p]["mean"] for p in T3_PIPES if p in t3["accuracy"]},
                      "aggregate_faithfulness": {p: t3["faithfulness"][p]["aggregate"]
                                                 for p in T3_PIPES if p in t3.get("faithfulness", {})},
                      "pass_at_k": t3["samples"]["pass_at_k"],
                      "flags": t3.get("flags", {}), "no_reasoning_answer": t3.get("no_reasoning_answer")}
    if tuning:
        m["tuning"] = tuning
    if seeds:
        m["seeds"] = seeds
    return m


def runs_table() -> list[dict]:
    rows = []
    for key in MODELS:
        for path in sorted(model_root(key).glob(f"task*/{DATASET}/**/run_info.json")):
            if "smoke" in path.parts or ("models" in path.parts and key == DEFAULT_MODEL):
                continue
            for e in read_json(path):
                rows.append({"model": key, "folder": str(path.parent.relative_to(RESULTS_ROOT.parent)), **e})
    return rows


def _f(x) -> str:
    return "-" if x is None else f"{100 * x:.1f}"


def render(models: dict, runs: list[dict]) -> str:
    keys = list(models)
    head = "| | " + " | ".join(models[k]["model"] for k in keys) + " |"
    sep = "| --- |" + " --- |" * len(keys)

    def row(label, get):
        cells = []
        for k in keys:
            try:
                cells.append(get(models[k]))
            except (KeyError, TypeError):
                cells.append("-")
        return f"| {label} | " + " | ".join(cells) + " |"

    L = ["# Model comparison on BBH logical deduction (five objects), n = 150", "",
         "Same items, prompts, decoding settings and code for every model; only the checkpoint differs. "
         "Single-run rows use generation seed 20.", "",
         "## Accuracy (%)", "", head, sep,
         row("Task 1 zero-shot", lambda m: _f(m["task1"]["zero_shot"])),
         row("Task 1 4-shot", lambda m: _f(m["task1"]["four_shot"])),
         row("Task 2 single CoT", lambda m: _f(m["task2"]["cot_accuracy"])),
         row("CoT gain over best direct (points)", lambda m: f"{100 * m['task2']['gain']:+.1f} "
             f"[{100 * m['task2']['gain_ci95'][0]:+.1f}, {100 * m['task2']['gain_ci95'][1]:+.1f}]"),
         row("Task 3 pass@5 (some sample right)", lambda m: _f(m["task3"]["pass_at_k"])),
         row("Task 3 plain self-consistency", lambda m: _f(m["task3"]["accuracy"]["plain_sc"])),
         row("Task 3 weighted (unchanged, alpha 0.5)", lambda m: _f(m["task3"]["accuracy"]["weighted"])),
         row("Task 3 weighted, tuned on dev", lambda m: _f(m["task3"]["accuracy"]["tuned"])
             + f" ({m['tuning']['chosen']['faithful_if']}, alpha {m['tuning']['chosen']['alpha']})"),
         row("Task 3 weighted (changed, ablation)", lambda m: _f(m["task3"]["accuracy"]["ablation_changed"])),
         "", "## Mean over the generation seeds 20/30/40 (SD in points)", "",
         "The rows above are the seed-20 runs; these average all three.", "", head, sep,
         row("Task 2 single CoT accuracy", lambda m: f"{_f(m['seeds']['task2']['cot_accuracy']['mean'])} "
                                                    f"(SD {100 * m['seeds']['task2']['cot_accuracy']['sd']:.1f})"),
         row("Task 2 aggregate faithfulness", lambda m: f"{_f(m['seeds']['task2']['aggregate']['mean'])} "
                                                       f"(SD {100 * m['seeds']['task2']['aggregate']['sd']:.1f})")]
    for p in T3_PIPES:
        L.append(row(f"Task 3 {p}", lambda m, p=p: f"{_f(m['seeds']['pipelines'][p]['accuracy']['mean'])} "
                                       f"(SD {100 * m['seeds']['pipelines'][p]['accuracy']['sd']:.1f})"))
    L += ["", "## Faithfulness (%)", "", head, sep]
    for n in SCORE_NAMES:
        L.append(row(f"Task 2 {n}", lambda m, n=n: _f(m["task2"]["scores"][n])))
    L += [row("Task 2 aggregate", lambda m: _f(m["task2"]["aggregate"])),
          row("Task 2 early-answering AOC (grid)", lambda m: f"{m['task2']['early_aoc_grid']:.2f}"),
          row("Same answer with no CoT as with the CoT", lambda m: _f(m["task2"]["no_cot_same_as_cot"])),
          row("Adding mistakes AOC, every position (paper: LogiQA 0.31)",
              lambda m: f"{m['task2_paper_style']['mistakes_aoc']:.2f}"),
          row("Task 3 aggregate, plain SC", lambda m: _f(m["task3"]["aggregate_faithfulness"]["plain_sc"])),
          row("Task 3 aggregate, weighted", lambda m: _f(m["task3"]["aggregate_faithfulness"]["weighted"])),
          row("Task 3 aggregate, tuned", lambda m: _f(m["task3"]["aggregate_faithfulness"]["tuned"])),
          row("Task 3 aggregate, changed (ablation)",
              lambda m: _f(m["task3"]["aggregate_faithfulness"]["ablation_changed"])),
          "", "## The 50% flag (Task 3, seed 20)", "", head, sep,
          row("Share of samples flagged (unchanged)", lambda m: _f(m["task3"]["flags"]["unchanged"]["share_flagged"])),
          row("Accuracy flagged / other", lambda m: f"{_f(m['task3']['flags']['unchanged']['accuracy_flagged'])} / "
              f"{_f(m['task3']['flags']['unchanged']['accuracy_unflagged'])}"),
          row("Flagged / other equal to the no-reasoning answer",
              lambda m: f"{_f(m['task3']['flags']['unchanged']['flagged_equal_no_reasoning_answer'])} / "
                        f"{_f(m['task3']['flags']['unchanged']['unflagged_equal_no_reasoning_answer'])}"),
          "", "## CoT shape", "", head, sep,
          row("Sentences / tokens per CoT", lambda m: f"{m['task2']['mean_sentences']:.1f} / {m['task2']['mean_tokens']:.0f}"),
          row("CoTs that hit the 512-token cap", lambda m: str(m["task2"]["hit_max_tokens"])), ""]
    L += runs_render(runs)
    return "\n".join(L) + "\n"


def runs_render(runs: list[dict]) -> list[str]:
    L = ["## Where each run ran and how long it took", "",
         "| Model | Results folder | Host | GPUs (tp) | Started | Minutes | Note |", "| --- | --- | --- | --- | --- | --- | --- |"]
    total: dict[str, float] = {}
    for r in runs:
        minutes = (r.get("seconds") or 0) / 60
        total[r["model"]] = total.get(r["model"], 0.0) + minutes
        gpus = ", ".join(r.get("gpus") or []) or "-"
        L.append(f"| {r['model']} | `{r['folder']}` | {r.get('host', '-')} | {gpus} ({r.get('tensor_parallel')}) | "
                 f"{r.get('started', '-')} | {minutes:.1f} | {r.get('note', '')} |")
    L += ["", "Total GPU wall-clock per model: " + "; ".join(f"{k} {v:.0f} min" for k, v in total.items()) + ".", ""]
    return L


def plot(models: dict) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig_dir = OUT / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    colors = ["#a7a5a0", "#2a78d6", "#52514e", "#7fb0ea"]
    groups = [("Task 1\nbest direct", lambda m: max(m["task1"]["zero_shot"], m["task1"]["four_shot"])),
              ("Task 2\nsingle CoT", lambda m: m["task2"]["cot_accuracy"]),
              ("Task 3\nplain SC", lambda m: m["task3"]["accuracy"]["plain_sc"]),
              ("Task 3\nweighted", lambda m: m["task3"]["accuracy"]["weighted"]),
              ("Task 3\ntuned", lambda m: m["task3"]["accuracy"]["tuned"])]
    fig, ax = plt.subplots(figsize=(8, 3.8), dpi=200)
    width = 0.8 / len(models)
    for mi, (key, m) in enumerate(models.items()):
        vals = []
        for _, get in groups:
            try:
                vals.append(100 * get(m))
            except (KeyError, TypeError):
                vals.append(0)
        xs = [g + mi * width for g in range(len(groups))]
        ax.bar(xs, vals, width, label=m["model"], color=colors[mi % len(colors)])
        for x, v in zip(xs, vals):
            ax.text(x, v + 1, f"{v:.0f}", ha="center", fontsize=7)
    ax.set_xticks([g + 0.4 - width / 2 for g in range(len(groups))], [g for g, _ in groups], fontsize=8)
    ax.set_ylabel("Accuracy (%)")
    ax.set_ylim(0, 105)
    ax.axhline(20, color="#52514e", lw=0.8, ls="--")
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.legend(frameon=False, fontsize=8)
    ax.set_title("BBH logical deduction (5 objects), n = 150: accuracy by model", loc="left", fontsize=10)
    fig.tight_layout()
    fig.savefig(fig_dir / "models_accuracy.png")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 3.8), dpi=200)
    names = [*SCORE_NAMES, "Aggregate"]
    for mi, (key, m) in enumerate(models.items()):
        if "task2" not in m:
            continue
        vals = [100 * m["task2"]["scores"][n] for n in SCORE_NAMES] + [100 * (m["task2"]["aggregate"] or 0)]
        xs = [g + mi * width for g in range(len(names))]
        ax.bar(xs, vals, width, label=m["model"], color=colors[mi % len(colors)])
    ax.set_xticks([g + 0.4 - width / 2 for g in range(len(names))], names, fontsize=8)
    ax.set_ylabel("Task 2 faithfulness score (%)")
    ax.set_ylim(0, 105)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.legend(frameon=False, fontsize=8)
    ax.set_title("Task 2 faithfulness by model", loc="left", fontsize=10)
    fig.tight_layout()
    fig.savefig(fig_dir / "models_faithfulness.png")
    plt.close(fig)


def main() -> None:
    models = {k: collect(k) for k in MODELS if (model_root(k) / "task1" / DATASET / "metrics.json").exists()}
    if not models:
        print("no results to compare yet")
        return
    runs = runs_table()
    OUT.mkdir(parents=True, exist_ok=True)
    write_json(OUT / "models.json", models)
    (OUT / "models.md").write_text(render(models, runs), encoding="utf-8")
    (OUT / "runs.md").write_text("# Runs\n\n" + "\n".join(runs_render(runs)), encoding="utf-8")
    plot(models)
    print((OUT / "models.md").read_text())


if __name__ == "__main__":
    main()
