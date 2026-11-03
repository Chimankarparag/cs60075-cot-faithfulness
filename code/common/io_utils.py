"""Small file helpers: JSON / JSONL reading and writing, and result folders."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Iterable

from common.config import GEN_SEED, RESULTS_DIR, SEED


def write_jsonl(path: Path, rows: Iterable[dict]) -> None:
    """Write one JSON object per line. Writes to a temp file first, then renames,
    so a crash never leaves a half-written file that a later stage would trust."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    os.replace(tmp, path)


def read_jsonl(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp, path)


def read_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def results_dir(task: str, dataset: str, smoke: bool = False, seed: int | None = None) -> Path:
    """Where a task's results live.

    results/<task>/<dataset>/            real runs with the default seed (42)
    results/<task>/<dataset>/seed_<N>/   repeats with another generation seed (--seed N)
    results/smoke/<task>/<dataset>/      quick tests with --n-limit (never overwrite real results)

    RESULTS_DIR already points at results/models/<model>/ for a non-default model. `seed`
    defaults to this run's GEN_SEED; pass SEED to address the default-seed results (the
    Task 1 and Task 2 baselines that every Task 3 repeat is compared with).
    """
    base = RESULTS_DIR / "smoke" if smoke else RESULTS_DIR
    path = base / task / dataset
    seed = GEN_SEED if seed is None else seed
    if seed != SEED:
        path = path / f"seed_{seed}"
    path.mkdir(parents=True, exist_ok=True)
    return path
