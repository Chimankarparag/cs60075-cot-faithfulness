"""Task 3, steps 4-5 - compare the weighted-vote pipeline with Tasks 1 and 2.

Step 4 (accuracy). The pipeline's answer is the weighted vote over the 5 samples. It is compared,
on the same items, with Task 1's best direct variant, Task 2's single CoT, the mean of the 5
individual samples, and plain self-consistency (alpha = 1, the control). Differences get a paired
bootstrap interval and an exact McNemar test (common/metrics.py).

Step 5 (faithfulness). Task 2's four interventions are applied to the CoT the vote selects
(weighted_vote.py documents the rule) and scored exactly as in Task 2 (task2/score.py), so the
aggregate faithfulness is comparable with Task 2's single-CoT number.

Pipelines evaluated (nothing is chosen by looking at the evaluation items):
    weighted          faithful if unchanged,   alpha = 0.5   fixed in advance (assignment wording)
    ablation_changed  faithful if changed,     alpha = 0.5   Task 2 / Lanham direction
    plain_sc          alpha = 1                               control: unweighted majority vote
    tuned             rule and alpha chosen on the 96 development items (tune.py), when
                      results/task3/<dataset>/dev/tuning.json exists
The alpha sweep (0, 0.25, 0.5, 0.75, 1) is reported for every rule as sensitivity only.

Run through run_task3.py. `score_task3` needs no GPU.
"""
from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.config import EARLY_ANSWER_FRACTIONS, GEN_SEED, MODEL_ID, MODEL_KEY, MODEL_REVISION, SEED
from common.io_utils import read_json, read_jsonl, results_dir, write_json, write_jsonl
from common.metrics import fmt_ci, mcnemar_exact, mean, paired_bootstrap_diff, pct, summarize_binary
from task2.interventions import INTERVENTIONS
from task2.score import (early_answering_scores, filler_scores, k_at, mistake_scores,
                         paraphrase_scores, same_by_item)
from task3.sample_k import K
from task3.weighted_vote import FAITHFUL_IF, vote_all, is_flagged

PIPELINES = {                       # name -> (faithful_if, alpha), fixed in advance
    "weighted": ("unchanged", 0.5),
    "ablation_changed": ("changed", 0.5),
    "plain_sc": ("unchanged", 1.0),
}
ALPHA_SWEEP = (0.0, 0.25, 0.5, 0.75, 1.0)
LABELS = {"plain_sc": "Plain self-consistency (alpha = 1, control)",
          "weighted": "Weighted vote, faithful = answer unchanged, alpha = 0.5 (fixed in advance)",
          "ablation_changed": "Weighted vote, faithful = answer changed, alpha = 0.5 (ablation)",
          "tuned": "Weighted vote, rule and alpha chosen on dev"}


def task3_dir(dataset: str, smoke: bool = False, split: str = "test") -> Path:
    """results/task3/<dataset>/ (seed 20) or .../seed_<N>/ (30, 40); the dev run lives in dev/ below
    the seed-20 folder."""
    if split == "dev":
        path = results_dir("task3", dataset, smoke, seed=SEED) / "dev"
        path.mkdir(parents=True, exist_ok=True)
        return path
    return results_dir("task3", dataset, smoke)


def tuning_file(dataset: str, smoke: bool = False) -> Path:
    return task3_dir(dataset, smoke, "dev") / "tuning.json"


def pipelines_for(dataset: str, smoke: bool = False) -> dict[str, tuple[str, float]]:
    """The fixed pipelines plus "tuned" if the dev tuning has been run."""
    pipes = dict(PIPELINES)
    path = tuning_file(dataset, smoke)
    if path.exists():
        chosen = read_json(path)["chosen"]
        pipes["tuned"] = (chosen["faithful_if"], float(chosen["alpha"]))
    return pipes
SCORE_NAMES = ("Early answering", "Adding a mistake", "Paraphrasing", "Filler tokens")


# --------------------------------------------------------------------------- #
# Loading and voting
# --------------------------------------------------------------------------- #
def load_samples(out: Path) -> tuple[list[str], dict[str, list[dict]]]:
    rows = read_jsonl(out / "samples.jsonl")
    by_item: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_item[r["id"]].append(r)
    for rs in by_item.values():
        rs.sort(key=lambda r: r["j"])
    return list(by_item), dict(by_item)


def load_prior(out: Path) -> dict[str, str | None]:
    """Each item's no-reasoning answer (prior.jsonl), or {} if that stage has not run."""
    path = out / "prior.jsonl"
    return {r["id"]: r["answer"] for r in read_jsonl(path)} if path.exists() else {}


def load_flags(out: Path, samples_by_item: dict[str, list[dict]], faithful_if: str) -> dict[str, list[bool]]:
    same = {(r["id"], r["j"]): r["same_as_a0"] for r in read_jsonl(out / "early50.jsonl")}
    prior = load_prior(out)
    if faithful_if == "loadbearing" and not prior:
        raise FileNotFoundError(f"{out / 'prior.jsonl'} is needed for the loadbearing rule (stage 'prior')")
    return {i: [is_flagged(same[(i, s["j"])], faithful_if, s["a0"], prior.get(i)) for s in rows]
            for i, rows in samples_by_item.items()}


def pipeline_votes(out: Path, samples_by_item: dict, name: str,
                   pipelines: dict[str, tuple[str, float]] = PIPELINES) -> dict[str, dict]:
    faithful_if, alpha = pipelines[name]
    return vote_all(samples_by_item, load_flags(out, samples_by_item, faithful_if), alpha)


def chosen_cot_rows(ids: list[str], samples_by_item: dict, votes: dict) -> list[dict]:
    """Task-2-format rows for the CoT each item's vote selects. The row's a0 is the sample's own
    final answer, which equals the vote's winner; an item with no parsable vote keeps sample 0."""
    rows = []
    for i in ids:
        j = votes[i]["chosen_j"]
        row = dict(samples_by_item[i][0 if j is None else j])
        row["chosen_j"] = row.pop("j")
        rows.append(row)
    return rows


# --------------------------------------------------------------------------- #
# Per-item score vectors (for paired comparisons with Task 2)
# --------------------------------------------------------------------------- #
def early_item_scores(early_rows: list[dict]) -> dict[str, float]:
    table = same_by_item(early_rows)
    n_of = {r["id"]: r["n"] for r in early_rows}
    return {i: mean(not table[i][k_at(p, n_of[i])] for p in EARLY_ANSWER_FRACTIONS)
            for i in table if n_of[i] > 0}


def item_scores(rows_by_kind: dict[str, list[dict]]) -> dict[str, dict[str, float]]:
    return {
        "Early answering": early_item_scores(rows_by_kind["early"]),
        "Adding a mistake": {r["id"]: float(r["changed"]) for r in rows_by_kind["mistake"] if r["valid"]},
        "Paraphrasing": {r["id"]: float(r["same"]) for r in rows_by_kind["paraphrase"] if r["valid"]},
        "Filler tokens": {r["id"]: float(r["changed"]) for r in rows_by_kind["filler"]},
    }


def faithfulness_of(directory: Path, gold: dict[str, str]) -> dict | None:
    """The four Task 2 scores for the intervention files in `directory` (None if incomplete)."""
    kinds = {k: directory / f"{k}.jsonl" for k in INTERVENTIONS}
    if not all(p.exists() for p in kinds.values()):
        return None
    rows = {k: read_jsonl(p) for k, p in kinds.items()}
    early = early_answering_scores(rows["early"])
    mistake = mistake_scores(rows["mistake"])
    para = paraphrase_scores(rows["paraphrase"])
    filler = filler_scores(rows["filler"], rows["early"], gold)
    scores = {"Early answering": early["score"], "Adding a mistake": mistake["score"],
              "Paraphrasing": para["score"], "Filler tokens": filler["score"]}
    return {"scores": scores, "aggregate": mean(s["mean"] for s in scores.values()),
            "early_aoc_grid": early["aoc_grid"], "early_aoc_lanham": early["aoc_lanham"],
            "n_mistake_valid": mistake["n_valid"], "n_paraphrase_valid": para["n_valid"],
            "item_scores": item_scores(rows)}


def paired_vs_task2(mine: dict, task2: dict) -> dict:
    """Per-intervention paired difference (this pipeline - Task 2) over the items scored in both."""
    out = {}
    for name in SCORE_NAMES:
        a, b = mine["item_scores"][name], task2["item_scores"][name]
        shared = sorted(set(a) & set(b))
        out[name] = {"n": len(shared), **paired_bootstrap_diff([a[i] for i in shared], [b[i] for i in shared])}
    return out


# --------------------------------------------------------------------------- #
# Accuracy comparison
# --------------------------------------------------------------------------- #
def correctness(votes: dict[str, dict], gold: dict[str, str], ids: list[str]) -> list[bool]:
    return [votes[i]["answer"] is not None and votes[i]["answer"] == gold[i] for i in ids]


def compare(a: list[bool], b: list[bool]) -> dict:
    return {"diff": paired_bootstrap_diff(a, b), "mcnemar": mcnemar_exact(a, b)}


def flag_diagnostics(out: Path, samples_by_item: dict, faithful_if: str) -> dict:
    """Do the flags track correctness? Accuracy of flagged vs unflagged samples, overall and within
    the items whose samples are split between flagged and unflagged (where the weights can matter),
    and how often each group's answer equals the model's no-reasoning answer."""
    flags = load_flags(out, samples_by_item, faithful_if)
    prior = load_prior(out)
    pairs = [(s, f, i) for i, rs in samples_by_item.items() for s, f in zip(rs, flags[i])]
    flagged = [s for s, f, _ in pairs if f]
    other = [s for s, f, _ in pairs if not f]
    mixed = {i for i in samples_by_item if 0 < sum(flags[i]) < len(flags[i])}
    out_d = {"share_flagged": len(flagged) / max(len(pairs), 1),
             "accuracy_flagged": mean(s["correct"] for s in flagged),
             "accuracy_unflagged": mean(s["correct"] for s in other),
             "n_flagged": len(flagged), "n_unflagged": len(other),
             "n_mixed_items": len(mixed),
             "mixed_accuracy_flagged": mean(s["correct"] for s, f, i in pairs if f and i in mixed),
             "mixed_accuracy_unflagged": mean(s["correct"] for s, f, i in pairs if not f and i in mixed)}
    if prior:
        out_d["flagged_equal_no_reasoning_answer"] = mean(s["a0"] == prior.get(s["id"]) for s in flagged)
        out_d["unflagged_equal_no_reasoning_answer"] = mean(s["a0"] == prior.get(s["id"]) for s in other)
    return out_d


def score_task3(dataset: str, smoke: bool = False, make_plots: bool = True) -> dict:
    out = task3_dir(dataset, smoke)
    pipes = pipelines_for(dataset, smoke)
    ids, samples_by_item = load_samples(out)
    gold = {i: samples_by_item[i][0]["gold"] for i in ids}
    k = len(samples_by_item[ids[0]])
    metrics: dict = {"task": "task3", "dataset": dataset, "n_items": len(ids), "k": k,
                     "model_key": MODEL_KEY, "model": MODEL_ID, "model_revision": MODEL_REVISION,
                     "seed": SEED, "gen_seed": GEN_SEED,
                     "pipelines": {n: {"faithful_if": f, "alpha": a} for n, (f, a) in pipes.items()}}
    if "tuned" in pipes:
        metrics["tuning"] = read_json(tuning_file(dataset, smoke))

    # ---- the samples themselves -------------------------------------------------------------
    all_samples = [s for i in ids for s in samples_by_item[i]]
    per_item_acc = [mean(s["correct"] for s in samples_by_item[i]) for i in ids]
    metrics["samples"] = {
        "accuracy_per_sample": summarize_binary(s["correct"] for s in all_samples),
        "mean_accuracy_per_item": mean(per_item_acc),
        "pass_at_k": mean(any(s["correct"] for s in samples_by_item[i]) for i in ids),
        "unanimous_items": mean(len({s["a0"] for s in samples_by_item[i]}) == 1 for i in ids),
        "hit_max_tokens": sum(s["finish_reason"] == "length" for s in all_samples),
        "a0_parse_failures": sum(s["a0"] is None for s in all_samples),
        "mean_sentences": mean(s["n_sentences"] for s in all_samples),
    }
    # Baselines: Task 1 (greedy, run once) and the Task 2 run with the same generation seed.
    t2_dir = results_dir("task2", dataset, smoke)
    t2_path = t2_dir / "cot.jsonl"
    t2_rows = {r["id"]: r for r in read_jsonl(t2_path)} if t2_path.exists() else {}
    if t2_rows:
        same = sum(samples_by_item[i][0]["cot"] == t2_rows[i]["cot"] for i in ids if i in t2_rows)
        metrics["sample0_matches_task2_cot"] = {"matches": same, "of": sum(i in t2_rows for i in ids)}

    # ---- step 2: do the 50% flags track correctness? ----------------------------------------
    prior = load_prior(out)
    rules = [f for f in FAITHFUL_IF if f != "loadbearing" or prior]
    if prior:
        metrics["no_reasoning_answer"] = {
            "accuracy": mean(prior[i] == gold[i] for i in ids),
            "share_samples_equal": mean(s["a0"] == prior[s["id"]] for s in all_samples)}
    if (out / "early50.jsonl").exists():
        metrics["flags"] = {f: flag_diagnostics(out, samples_by_item, f) for f in rules}

        # ---- step 3-4: votes and accuracy -----------------------------------------------------
        pipes = {n: v for n, v in pipes.items() if v[0] in rules}
        votes = {n: pipeline_votes(out, samples_by_item, n, pipes) for n in pipes}
        correct = {n: correctness(v, gold, ids) for n, v in votes.items()}
        acc = {n: summarize_binary(c) for n, c in correct.items()}
        for n in pipes:
            acc[n]["share_same_answer_as_plain"] = mean(votes[n][i]["answer"] == votes["plain_sc"][i]["answer"]
                                                        for i in ids)
        metrics["accuracy"] = acc
        metrics["alpha_sweep"] = {
            f"{f}@{a}": mean(correctness(vote_all(samples_by_item, load_flags(out, samples_by_item, f), a),
                                         gold, ids))
            for f in rules for a in ALPHA_SWEEP}

        baselines: dict[str, list[bool]] = {}
        t1_dir = results_dir("task1", dataset, smoke, seed=SEED)
        if (t1_dir / "metrics.json").exists():
            best = read_json(t1_dir / "metrics.json")["best_variant"]
            t1 = {r["id"]: r["correct"] for r in read_jsonl(t1_dir / f"{best}.jsonl")}
            if all(i in t1 for i in ids):
                baselines[f"Task 1 ({best})"] = [bool(t1[i]) for i in ids]
        if all(i in t2_rows for i in ids):
            baselines["Task 2 (single CoT)"] = [bool(t2_rows[i]["correct"]) for i in ids]
        metrics["baselines"] = {n: summarize_binary(c) for n, c in baselines.items()}
        metrics["comparisons"] = {}
        for pname in pipes:
            for bname, bc in baselines.items():
                metrics["comparisons"][f"{pname} vs {bname}"] = compare(correct[pname], bc)
        for pname in pipes:
            if pname != "plain_sc":
                metrics["comparisons"][f"{pname} vs plain_sc"] = compare(correct[pname], correct["plain_sc"])

        # ---- step 5: faithfulness of the pipeline's output --------------------------------------
        t2_faith = faithfulness_of(t2_dir, gold) if t2_rows else None
        faith: dict = {}
        if t2_faith:
            faith["task2_single_cot"] = {k_: v for k_, v in t2_faith.items() if k_ != "item_scores"}
        for pname in pipes:
            mine = faithfulness_of(out / f"pipeline_{pname}", gold)
            if mine is None:
                continue
            entry = {k_: v for k_, v in mine.items() if k_ != "item_scores"}
            if t2_faith:
                entry["aggregate_diff_vs_task2"] = mine["aggregate"] - t2_faith["aggregate"]
                entry["paired_vs_task2"] = paired_vs_task2(mine, t2_faith)
            entry["share_chosen_equals_sample0"] = mean(votes[pname][i]["chosen_j"] == 0 for i in ids)
            faith[pname] = entry
        if faith:
            metrics["faithfulness"] = faith

    write_json(out / "metrics.json", metrics)
    (out / "summary.md").write_text(render_summary(metrics), encoding="utf-8")
    if make_plots and "accuracy" in metrics:
        fig_dir = out / "figures"
        fig_dir.mkdir(exist_ok=True)
        plot_accuracy(metrics, fig_dir / "accuracy_comparison.png")
        if "faithfulness" in metrics:
            plot_faithfulness(metrics, fig_dir / "faithfulness_comparison.png")
    votes_rows = []
    if (out / "early50.jsonl").exists():
        for n in votes:
            for i in ids:
                v = votes[n][i]
                votes_rows.append({"id": i, "pipeline": n, "answer": v["answer"], "gold": gold[i],
                                   "correct": v["answer"] == gold[i], "chosen_j": v["chosen_j"],
                                   "weights": v["weights"]})
        write_jsonl(out / "votes.jsonl", votes_rows)
    return metrics


# --------------------------------------------------------------------------- #
# Report text and figures
# --------------------------------------------------------------------------- #
def render_summary(m: dict) -> str:
    seed_note = f", generation seed {m['gen_seed']}"
    L = [f"# Task 3 - faithfulness-weighted self-consistency on {m['dataset']} "
         f"(n = {m['n_items']}, k = {m['k']}, {m.get('model', MODEL_ID)}{seed_note})", ""]
    s = m["samples"]
    L += ["## The sampled CoTs", "",
          f"- Accuracy of a single sample: {fmt_ci(s['accuracy_per_sample'])} (over {s['accuracy_per_sample']['n']} samples); "
          f"pass@{m['k']} (some sample right): {pct(s['pass_at_k'])}; items where all samples agree: {pct(s['unanimous_items'])}%.",
          f"- {s['hit_max_tokens']} samples hit the 512-token cap, {s['a0_parse_failures']} final answers could not be parsed; "
          f"{s['mean_sentences']:.1f} sentences per CoT on average."]
    if "sample0_matches_task2_cot" in m:
        c = m["sample0_matches_task2_cot"]
        L.append(f"- Sample 0 has the same text as Task 2's CoT for {c['matches']} of {c['of']} items: it uses the same seed, but sampled "
            "text depends on GPU type, tensor-parallel size and batch composition, so the samples are fresh draws.")
    if "no_reasoning_answer" in m:
        nr = m["no_reasoning_answer"]
        L.append(f"- No-reasoning answer (empty CoT, forced answer): accuracy {pct(nr['accuracy'])}%; "
                 f"{pct(nr['share_samples_equal'])}% of samples end on that same answer.")
    if "accuracy" not in m:
        return "\n".join(L) + "\n"

    L += ["", "## Step 2: what the 50% early answer says about a sample", "",
          "| Flag rule | Share flagged | Accuracy flagged / other | Same, items with mixed flags | "
          "Flagged / other equal to no-reasoning answer |", "| --- | --- | --- | --- | --- |"]
    for f, d in m["flags"].items():
        prior_cell = (f"{pct(d['flagged_equal_no_reasoning_answer'])}% / {pct(d['unflagged_equal_no_reasoning_answer'])}%"
                      if "flagged_equal_no_reasoning_answer" in d else "-")
        L.append(f"| {f} | {pct(d['share_flagged'])}% ({d['n_flagged']}) | "
                 f"{pct(d['accuracy_flagged'])}% / {pct(d['accuracy_unflagged'])}% | "
                 f"{pct(d['mixed_accuracy_flagged'])}% / {pct(d['mixed_accuracy_unflagged'])}% ({d['n_mixed_items']} items) | "
                 f"{prior_cell} |")

    if "tuning" in m:
        t = m["tuning"]
        rule, alpha = t["chosen"]["faithful_if"], t["chosen"]["alpha"]
        dev_acc = t["dev_accuracy"][f"{rule}@{alpha}"]
        L += ["", f"Rule chosen on {t['n_dev_items']} development items: faithful if **{rule}**, "
                  f"alpha = **{alpha}** (dev accuracy {pct(dev_acc)}%, "
                  f"plain self-consistency on dev {pct(t['dev_accuracy_plain_sc'])}%)."]

    L += ["", "## Step 4: accuracy (%)", "", "| Method | Accuracy [95% CI] |", "| --- | --- |"]
    for n, b in m["baselines"].items():
        L.append(f"| {n} | {fmt_ci(b)} |")
    L.append(f"| Mean of the {m['k']} single samples | {pct(s['mean_accuracy_per_item'])} |")
    for n in ("plain_sc", "weighted", "ablation_changed", "tuned"):
        if n in m["accuracy"]:
            label = LABELS[n]
            if n == "tuned":
                label += f" ({m['pipelines']['tuned']['faithful_if']}, alpha = {m['pipelines']['tuned']['alpha']})"
            L.append(f"| {label} | {fmt_ci(m['accuracy'][n])} |")
    L += ["", "Paired differences (first minus second, percentage points) with an exact McNemar test:", "",
          "| Comparison | Difference [95% CI] | Only first right | Only second right | McNemar p |",
          "| --- | --- | --- | --- | --- |"]
    for name, c in m["comparisons"].items():
        d = c["diff"]
        L.append(f"| {name} | {100 * d['diff']:+.1f} [{100 * d['ci95'][0]:+.1f}, {100 * d['ci95'][1]:+.1f}] | "
                 f"{c['mcnemar']['a_only']} | {c['mcnemar']['b_only']} | {c['mcnemar']['p_value']:.3f} |")
    rules = sorted({key.split("@")[0] for key in m["alpha_sweep"]}, key=FAITHFUL_IF.index)
    L += ["", "Sensitivity to alpha (accuracy %; not used to choose anything):", "",
          "| Faithful if | " + " | ".join(f"alpha = {a}" for a in ALPHA_SWEEP) + " |",
          "| --- |" + " --- |" * len(ALPHA_SWEEP)]
    for f in rules:
        L.append(f"| {f} | " + " | ".join(pct(m["alpha_sweep"][f"{f}@{a}"]) for a in ALPHA_SWEEP) + " |")

    if "faithfulness" in m:
        F = m["faithfulness"]
        L += ["", "## Step 5: faithfulness of the pipeline's output (%)", "",
              "| Pipeline | " + " | ".join(SCORE_NAMES) + " | Aggregate | Early AOC (grid) |",
              "| --- |" + " --- |" * (len(SCORE_NAMES) + 2)]
        names = {"task2_single_cot": "Task 2 (one CoT)", "weighted": "Weighted vote (fixed, unchanged)",
                 "ablation_changed": "Weighted vote, changed (ablation)", "plain_sc": "Plain self-consistency",
                 "tuned": "Weighted vote (tuned on dev)"}
        for key, label in names.items():
            if key in F:
                e = F[key]
                L.append(f"| {label} | " + " | ".join(fmt_ci(e["scores"][n]) for n in SCORE_NAMES) +
                         f" | {pct(e['aggregate'])} | {e['early_aoc_grid']:.2f} |")
        L += ["", "Paired difference to Task 2 per intervention (points, 95% CI), and in the aggregate:", "",
              "| Pipeline | " + " | ".join(SCORE_NAMES) + " | Aggregate |", "| --- |" + " --- |" * (len(SCORE_NAMES) + 1)]
        for key in ("weighted", "ablation_changed", "plain_sc", "tuned"):
            if key in F and "paired_vs_task2" in F[key]:
                p = F[key]["paired_vs_task2"]
                cells = [f"{100 * p[n]['diff']:+.1f} [{100 * p[n]['ci95'][0]:+.1f}, {100 * p[n]['ci95'][1]:+.1f}]"
                         for n in SCORE_NAMES]
                L.append(f"| {names[key]} | " + " | ".join(cells) + f" | {100 * F[key]['aggregate_diff_vs_task2']:+.1f} |")
    return "\n".join(L) + "\n"


def _bar_axes(figsize):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=figsize)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    return plt, fig, ax


def plot_accuracy(m: dict, path: Path) -> None:
    labels, vals, errs, colors = [], [], [], []
    rows = [(n, b) for n, b in m["baselines"].items()]
    rows += [("Plain SC", m["accuracy"]["plain_sc"]), ("Weighted\n(unchanged)", m["accuracy"]["weighted"]),
             ("Weighted\n(changed)", m["accuracy"]["ablation_changed"])]
    if "tuned" in m["accuracy"]:
        rows.append(("Weighted\n(tuned on dev)", m["accuracy"]["tuned"]))
    for n, b in rows:
        labels.append(n.replace(" (", "\n("))
        vals.append(100 * b["mean"])
        errs.append([100 * b["mean"] - 100 * b["ci95"][0], 100 * b["ci95"][1] - 100 * b["mean"]])
        colors.append("#2a78d6" if n.startswith(("Weighted\n(unch", "Weighted\n(tuned")) else "#a7a5a0")
    plt, fig, ax = _bar_axes((8, 4))
    ax.bar(range(len(vals)), vals, color=colors, yerr=list(zip(*errs)), capsize=3)
    ax.set_xticks(range(len(vals)), labels, fontsize=8)
    ax.axhline(20, color="#52514e", lw=0.8, ls="--")
    ax.text(len(vals) - 0.5, 21, "chance 20%", ha="right", fontsize=8, color="#52514e")
    ax.set_ylabel("Accuracy (%)")
    ax.set_title(f"{m['dataset']}: accuracy, n = {m['n_items']}", loc="left", fontsize=11)
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def plot_faithfulness(m: dict, path: Path) -> None:
    F = m["faithfulness"]
    series = [("task2_single_cot", "Task 2 (one CoT)", "#a7a5a0"), ("weighted", "Weighted vote", "#2a78d6"),
              ("tuned", "Weighted, tuned on dev", "#7fb0ea"), ("plain_sc", "Plain SC", "#52514e")]
    series = [s for s in series if s[0] in F]
    groups = [*SCORE_NAMES, "Aggregate"]
    plt, fig, ax = _bar_axes((9, 4))
    width = 0.8 / len(series)
    for si, (key, label, color) in enumerate(series):
        vals = [100 * F[key]["scores"][n]["mean"] for n in SCORE_NAMES] + [100 * F[key]["aggregate"]]
        ax.bar([g + si * width for g in range(len(groups))], vals, width, label=label, color=color)
    ax.set_xticks([g + 0.4 - width / 2 for g in range(len(groups))], groups, fontsize=9)
    ax.set_ylabel("Faithfulness score (%)")
    ax.set_ylim(0, 105)
    ax.legend(frameon=False, fontsize=8)
    ax.set_title(f"{m['dataset']}: faithfulness of the pipeline's output vs Task 2", loc="left", fontsize=11)
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)
