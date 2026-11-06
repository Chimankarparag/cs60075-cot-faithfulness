"""Small file helpers shared by every task: JSON / JSONL read-write and result folders."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Iterable

from common.config import DATASET, RESULTS_ROOT


def write_jsonl(path: Path, rows: Iterable[dict]) -> None:
    """Write one JSON object per line, atomically (temp file + rename), so an
    interrupted run never leaves a half-written file that looks finished."""
    path = Path(path)
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
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
    os.replace(tmp, path)


def read_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def results_dir(model: str, task: str, smoke: bool = False) -> Path:
    """results/models/<model>/<task>/bbh/ (results/smoke/<model>/<task>/bbh/ for quick tests
    with a limited number of items, so a smoke test never overwrites real results)."""
    base = RESULTS_ROOT / "smoke" if smoke else RESULTS_ROOT / "models"
    path = base / model / task / DATASET
    path.mkdir(parents=True, exist_ok=True)
    return path
