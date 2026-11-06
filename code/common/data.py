"""Download, normalise and sample the BIG-Bench-Hard logical-deduction data.

Every question becomes an *item* with the same keys:

    {"id": "bbh-7",          # stable identifier: row index in the source file
     "index": 7,
     "question": "...",       # text shown to the model (includes the (A)..(E) options)
     "options": {"A": ...},   # option letter -> option text
     "gold": "C"}             # gold option letter

The 250 rows are split once, with seed 49, into 4 few-shot exemplars, 150 evaluation
items and 96 dev items. The chosen row indices are committed in data/splits/bbh.json, so
anyone can check which questions were used; the items themselves are rebuilt from the
downloaded file in memory (it takes well under a second).
"""
from __future__ import annotations

import hashlib
import random
import re
import shutil
from functools import lru_cache
from pathlib import Path

from common.config import BBH_FILE, N_EVAL, N_FEWSHOT, RAW_DIR, SEED, SPLITS_DIR, RawFile
from common.io_utils import read_json, write_json

SPLIT_FILE = SPLITS_DIR / "bbh.json"


def sha256_of(path: Path) -> str:
    """SHA-256 of a file, read in 1 MB chunks."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def ensure_raw_file(raw: RawFile = BBH_FILE) -> Path:
    """Local path of the parquet file, downloaded on first use. The file is pinned to an
    exact Hub commit and its checksum is verified, so everyone gets byte-identical data."""
    local = RAW_DIR / raw.local
    if local.exists() and sha256_of(local) == raw.sha256:
        return local
    from huggingface_hub import hf_hub_download

    print(f"[data] downloading {raw.repo_id}/{raw.filename} @ {raw.revision[:10]}")
    cached = hf_hub_download(repo_id=raw.repo_id, filename=raw.filename,
                             repo_type="dataset", revision=raw.revision)
    local.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(cached, local)
    got = sha256_of(local)
    if got != raw.sha256:
        raise RuntimeError(f"Checksum mismatch for {local}: expected {raw.sha256}, got {got}")
    return local


# One option per line, e.g. "(C) The raven is the rightmost".
_BBH_OPTION = re.compile(r"^\(([A-Z])\)\s*(.+?)\s*$", re.MULTILINE)


def parse_bbh_options(text: str) -> dict[str, str]:
    """Pull the embedded '(A) ...' options out of a BBH question with one regex."""
    return {letter: body for letter, body in _BBH_OPTION.findall(text)}


def normalise_bbh(row: dict, index: int) -> dict:
    options = parse_bbh_options(row["input"])
    gold = row["target"].strip().strip("()")  # "(A)" -> "A"
    if gold not in options:
        raise ValueError(f"BBH row {index}: target {row['target']!r} not among options {list(options)}")
    return {"id": f"bbh-{index}", "index": index, "question": row["input"].strip(),
            "options": options, "gold": gold}


def choose_indices() -> dict:
    """Shuffle the 250 row indices once with the seed: the first 4 are the exemplars, the next
    150 the evaluation items, the rest the dev items, so the three sets are disjoint."""
    perm = list(range(BBH_FILE.n_rows))
    random.Random(SEED).shuffle(perm)
    shots, evals, dev = perm[:N_FEWSHOT], perm[N_FEWSHOT:N_FEWSHOT + N_EVAL], perm[N_FEWSHOT + N_EVAL:]
    return {"dataset": "bbh", "seed": SEED, "eval_indices": sorted(evals),
            "fewshot_indices": shots, "dev_indices": sorted(dev)}


@lru_cache(maxsize=1)
def _splits() -> dict:
    if SPLIT_FILE.exists():
        splits = read_json(SPLIT_FILE)
        if splits.get("seed") == SEED:
            return splits
    splits = choose_indices()
    write_json(SPLIT_FILE, splits)
    return splits


@lru_cache(maxsize=1)
def _pool() -> tuple[dict, ...]:
    import pandas as pd

    rows = pd.read_parquet(ensure_raw_file()).to_dict(orient="records")
    if len(rows) != BBH_FILE.n_rows:
        raise RuntimeError(f"expected {BBH_FILE.n_rows} rows, found {len(rows)}")
    return tuple(normalise_bbh(r, i) for i, r in enumerate(rows))


def _take(key: str, n_limit: int | None = None) -> list[dict]:
    pool = _pool()
    items = [pool[i] for i in _splits()[key]]
    return items[:n_limit] if n_limit else items


def load_eval(n_limit: int | None = None) -> list[dict]:
    """The 150 evaluation items (the same list for Tasks 1, 2 and 3)."""
    return _take("eval_indices", n_limit)


def load_dev(n_limit: int | None = None) -> list[dict]:
    """The 96 dev items, disjoint from the evaluation items and the exemplars (Task 3 tuning)."""
    return _take("dev_indices", n_limit)


def load_fewshot() -> list[dict]:
    """The 4 few-shot exemplars of Task 1."""
    return _take("fewshot_indices")
