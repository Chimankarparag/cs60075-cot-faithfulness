"""Shared look for the notebook figures: one colour per model, light axes."""
from __future__ import annotations

COLORS = {"llama3.1-8b": "#2a78d6", "qwen3-8b": "#eb6834"}
INK, INK_2, GRID_INK = "#0b0b0b", "#52514e", "#e4e3df"


def label(model: str) -> str:
    return {"llama3.1-8b": "Llama-3.1-8B", "qwen3-8b": "Qwen3-8B"}.get(model, model)


def style(ax) -> None:
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(INK_2)
    ax.tick_params(colors=INK_2, labelsize=8)
    ax.grid(axis="y", color=GRID_INK, lw=0.6)
    ax.set_axisbelow(True)
