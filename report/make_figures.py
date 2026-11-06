"""Figures for report.pdf, built from the committed results (no GPU).

    python report/make_figures.py      # writes report/figures/*.pdf
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "report" / "figures"
MODELS = {"Llama-3.1-8B": REPO / "results/models/llama3.1-8b", "Qwen3-8B": REPO / "results/models/qwen3-8b"}
COLORS = {"Llama-3.1-8B": "#2a78d6", "Qwen3-8B": "#eb6834"}
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def style(ax) -> None:
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(INK2)
    ax.tick_params(colors=INK2, labelsize=8)
    ax.grid(axis="y", color=GRID, lw=0.6)
    ax.set_axisbelow(True)


def accuracy() -> None:
    groups = ["Task 1\nbest direct", "Task 2\nsingle CoT", "Task 3\nplain vote", "Task 3\nweighted",
              "Task 3\ntuned", "Task 3\n\"changed\""]
    fig, ax = plt.subplots(figsize=(6.6, 2.7))
    width = 0.38
    for mi, (name, root) in enumerate(MODELS.items()):
        t1 = load(root / "task1/bbh/metrics.json")
        t2 = load(root / "task2/bbh/metrics.json")
        t3 = load(root / "task3/bbh/metrics.json")
        best = t1["variants"][t1["best_variant"]]
        series = [best, t2["cot"]] + [t3["accuracy"][p] for p in ("plain_sc", "weighted", "tuned", "ablation_changed")]
        means = [100 * s["mean"] for s in series]
        err = [[100 * (s["mean"] - s["ci95"][0]) for s in series], [100 * (s["ci95"][1] - s["mean"]) for s in series]]
        xs = [g + (mi - 0.5) * width for g in range(len(groups))]
        ax.bar(xs, means, width * 0.92, color=COLORS[name], label=name, yerr=err, ecolor=INK2, capsize=2,
               error_kw={"lw": 0.8})
        for x, v in zip(xs, means):
            ax.text(x, 3, f"{v:.0f}", ha="center", fontsize=6.5, color="white")
    ax.axhline(20, color=INK2, lw=0.7, ls=":")
    ax.text(len(groups) - 0.45, 21.5, "chance", fontsize=6.5, color=INK2, ha="right")
    ax.set_xticks(range(len(groups)), groups, fontsize=7.5)
    ax.set_ylabel("Accuracy (%)", fontsize=8, color=INK2)
    ax.set_ylim(0, 100)
    style(ax)
    ax.legend(frameon=False, fontsize=7.5, loc="upper left", ncol=2)
    fig.tight_layout()
    fig.savefig(OUT / "accuracy.pdf")
    plt.close(fig)


def early_curves() -> None:
    fig, ax = plt.subplots(figsize=(3.3, 2.5))
    xs = [0, 20, 40, 60, 80, 100]
    for name, root in MODELS.items():
        c = load(root / "task2/bbh/metrics.json")["early_answering"]["curve_same_answer"]
        ax.plot(xs, [100 * c[f"{x / 100:.1f}"] for x in xs], color=COLORS[name], lw=2, marker="o", ms=3.5, label=name)
    ax.set_xlabel("% of CoT sentences kept", fontsize=8, color=INK2)
    ax.set_ylabel("% same answer as full CoT", fontsize=8, color=INK2)
    ax.set_ylim(0, 105)
    style(ax)
    ax.legend(frameon=False, fontsize=7, loc="lower right")
    fig.tight_layout()
    fig.savefig(OUT / "early_answering.pdf")
    plt.close(fig)


def paper_style() -> None:
    fig, axes = plt.subplots(1, 3, figsize=(6.8, 2.3))
    for name, root in MODELS.items():
        p = load(root / "task2/bbh/metrics_paper.json")
        c = p["mistakes_all"]["curve_same_answer"]
        axes[0].plot([int(b.split("-")[0]) + 10 for b in c], [100 * v["same"] for v in c.values()],
                     color=COLORS[name], lw=2, marker="o", ms=3, label=name)
        pp = p["paraphrase_prefix"]
        axes[1].plot([100 * float(f) for f in pp["by_fraction"]], [100 * v["accuracy"] for v in pp["by_fraction"].values()],
                     color=COLORS[name], lw=2, marker="o", ms=3)
        axes[1].axhline(100 * pp["original_cot_accuracy"], color=COLORS[name], lw=0.8, ls="--")
        fs = p["filler_sweep"]["by_percentile"]
        axes[2].plot([int(k) for k in fs], [100 * v["accuracy"] for v in fs.values()], color=COLORS[name], lw=2,
                     marker="o", ms=3)
        axes[2].axhline(100 * p["filler_sweep"]["cot_accuracy"], color=COLORS[name], lw=0.8, ls="--")
    titles = ["(a) Adding a mistake", "(b) Paraphrasing a prefix", "(c) Filler tokens"]
    xlabels = ["% of CoT before the mistake", "% of CoT paraphrased", "Filler length (CoT-length pct.)"]
    ylabels = ["% same answer as original", "Accuracy (%)", "Accuracy (%)"]
    for ax, t, xl, yl in zip(axes, titles, xlabels, ylabels):
        ax.set_title(t, fontsize=8, loc="left", color=INK)
        ax.set_xlabel(xl, fontsize=7, color=INK2)
        ax.set_ylabel(yl, fontsize=7, color=INK2)
        ax.set_ylim(0, 100)
        style(ax)
    axes[0].legend(frameon=False, fontsize=6.5, loc="lower right")
    axes[1].text(98, 4, "dashed: original CoT", fontsize=6, color=INK2, ha="right")
    axes[2].text(98, 4, "dashed: with the CoT", fontsize=6, color=INK2, ha="right")
    fig.tight_layout()
    fig.savefig(OUT / "paper_style.pdf")
    plt.close(fig)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    accuracy()
    early_curves()
    paper_style()
    print("wrote", sorted(p.name for p in OUT.glob("*.pdf")))
