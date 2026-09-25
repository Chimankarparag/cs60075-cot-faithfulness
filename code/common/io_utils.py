"""Small file helpers: JSON / JSONL reading and writing, and result folders."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Iterable

from common.config import RESULTS_DIR


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


def results_dir(task: str, dataset: str, smoke: bool = False) -> Path:
    """results/<task>/<dataset>/ for real runs, results/smoke/<task>/<dataset>/ for
    quick tests with --n-limit, so a smoke test never overwrites real results."""
    base = RESULTS_DIR / "smoke" if smoke else RESULTS_DIR
    path = base / task / dataset
    path.mkdir(parents=True, exist_ok=True)
    return path
