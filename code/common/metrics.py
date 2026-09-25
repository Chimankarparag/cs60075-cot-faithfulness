"""Accuracy, confidence intervals and paired tests.

With n = 150-200 items, sampling noise is large (a 95% interval on an accuracy is
roughly +/-7 points), so every headline number comes with a bootstrap interval,
and comparisons between two methods on the SAME items use paired statistics.
"""
from __future__ import annotations

import numpy as np

from common.config import N_BOOTSTRAP, SEED


def mean(values) -> float:
    values = list(values)
    return float(np.mean(values)) if values else float("nan")


def bootstrap_ci(values, n_boot: int = N_BOOTSTRAP, seed: int = SEED, level: float = 0.95) -> list[float]:
    """Percentile bootstrap interval for the mean of `values` (e.g. 0/1 correctness).

    Resample the items with replacement n_boot times, recompute the mean each time,
    and take the middle `level` of those means.
    """
    arr = np.asarray(list(values), dtype=float)
    if arr.size == 0:
        return [float("nan"), float("nan")]
    rng = np.random.default_rng(seed)
    means = arr[rng.integers(0, arr.size, size=(n_boot, arr.size))].mean(axis=1)
    tail = (1 - level) / 2 * 100
    return [float(np.percentile(means, tail)), float(np.percentile(means, 100 - tail))]


def summarize_binary(values) -> dict:
    """{"mean", "ci95", "n"} for a list of booleans / 0-1 values."""
    values = [float(v) for v in values]
    return {"mean": mean(values), "ci95": bootstrap_ci(values), "n": len(values)}


def paired_bootstrap_diff(a, b, n_boot: int = N_BOOTSTRAP, seed: int = SEED) -> dict:
    """Difference mean(a) - mean(b) for two methods scored on the same items.

    Items are resampled jointly (the same resampled item for both methods), which
    removes the item-difficulty noise that an unpaired comparison would include.
    """
    a = np.asarray(list(a), dtype=float)
    b = np.asarray(list(b), dtype=float)
    assert a.shape == b.shape, "paired comparison needs the same items"
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, a.size, size=(n_boot, a.size))
    diffs = a[idx].mean(axis=1) - b[idx].mean(axis=1)
    return {"diff": float(a.mean() - b.mean()),
            "ci95": [float(np.percentile(diffs, 2.5)), float(np.percentile(diffs, 97.5))]}


def mcnemar_exact(a_correct, b_correct) -> dict:
    """Exact McNemar test: do methods A and B differ in accuracy on the same items?

    Only the discordant items matter: `a_only` = A right & B wrong, `b_only` = the
    reverse. Under "no difference" each discordant item is a fair coin flip, so the
    p-value is a two-sided binomial test on a_only out of (a_only + b_only).
    """
    from scipy.stats import binomtest

    a_only = sum(1 for x, y in zip(a_correct, b_correct) if x and not y)
    b_only = sum(1 for x, y in zip(a_correct, b_correct) if y and not x)
    n = a_only + b_only
    p = 1.0 if n == 0 else float(binomtest(a_only, n, 0.5).pvalue)
    return {"a_only": a_only, "b_only": b_only, "p_value": p}


def trapezoid_area(xs, ys) -> float:
    """Area under the piecewise-linear curve through (xs, ys)."""
    xs, ys = list(xs), list(ys)
    return float(sum((xs[i + 1] - xs[i]) * (ys[i] + ys[i + 1]) / 2 for i in range(len(xs) - 1)))


def pct(x: float) -> str:
    """0.4567 -> '45.7'."""
    return f"{100 * x:.1f}"


def fmt_ci(summary: dict) -> str:
    """{"mean": .5, "ci95": [.43, .57]} -> '50.0 [43.0, 57.0]'."""
    lo, hi = summary["ci95"]
    return f"{pct(summary['mean'])} [{pct(lo)}, {pct(hi)}]"
