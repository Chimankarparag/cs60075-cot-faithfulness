"""Download, normalise and sample the BIG-Bench-Hard logical-deduction data.

Every question ends up as an *item* with the same keys, so the rest of the pipeline
never needs dataset-specific loading code:

    {"id": "bbh-42",          # stable identifier: dataset and row index
     "index": 42,             # row index inside the source parquet file
     "question": "...",       # text shown to the model (includes the (A)..(E) options)
     "options": {"A": ...},   # option letter -> option text
     "gold": "C"}             # gold option letter

Run as a script to download and prepare everything:
    python code/common/data.py
"""
from __future__ import annotations

import hashlib
import random
import re
import shutil
import sys
from pathlib import Path

if __package__ in (None, ""):  # allow `python code/common/data.py`
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.config import (DATASETS, DEFAULT_DATASET, N_FEWSHOT, PROCESSED_DIR, RAW_DIR, SEED,
                           SPLITS_DIR, DatasetSpec, RawFile, get_spec)
from common.io_utils import read_json, read_jsonl, write_json, write_jsonl


# --------------------------------------------------------------------------- #
# 1. Download
# --------------------------------------------------------------------------- #
def sha256_of(path: Path) -> str:
    """SHA-256 of a file, read in 1 MB chunks so large files don't fill memory."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def ensure_raw_file(raw: RawFile) -> Path:
    """Return the local path of a raw parquet file, downloading it if needed.

    The file is pinned to an exact Hub commit and its checksum is verified, so
    everyone who runs this gets byte-identical data.
    """
    local = RAW_DIR / raw.local
    if local.exists() and sha256_of(local) == raw.sha256:
        return local
    from huggingface_hub import hf_hub_download  # imported lazily: only needed once

    print(f"[data] downloading {raw.repo_id}/{raw.filename} @ {raw.revision[:10]}")
    cached = hf_hub_download(repo_id=raw.repo_id, filename=raw.filename,
                             repo_type="dataset", revision=raw.revision)
    local.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(cached, local)
    got = sha256_of(local)
    if got != raw.sha256:
        raise RuntimeError(f"Checksum mismatch for {local}: expected {raw.sha256}, got {got}")
    return local


def load_rows(raw: RawFile) -> list[dict]:
    """Read a parquet file into a list of plain dicts."""
    import pandas as pd  # lazy import keeps `import common.data` light

    rows = pd.read_parquet(ensure_raw_file(raw)).to_dict(orient="records")
    if len(rows) != raw.n_rows:
        raise RuntimeError(f"{raw.local}: expected {raw.n_rows} rows, found {len(rows)}")
    return rows


# --------------------------------------------------------------------------- #
# 2. Normalise each dataset's rows into the common item format
# --------------------------------------------------------------------------- #
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


# --------------------------------------------------------------------------- #
# 3. Choose the evaluation sample and the few-shot exemplars (seed 42)
# --------------------------------------------------------------------------- #
def choose_indices(spec: DatasetSpec) -> dict:
    """Pick eval and few-shot row indices reproducibly.

    One pool of 250 rows: shuffle all indices once with the seed; the first 4 become
    the few-shot exemplars and the next n_eval the evaluation set, so the two sets are
    disjoint by construction.
    """
    perm = list(range(spec.eval_file.n_rows))
    random.Random(SEED).shuffle(perm)
    shot_idx = perm[:N_FEWSHOT]
    eval_idx = perm[N_FEWSHOT:N_FEWSHOT + spec.n_eval]
    return {"dataset": spec.name, "seed": SEED,
            "eval_indices": sorted(eval_idx), "fewshot_indices": shot_idx}


def prepare(spec: DatasetSpec) -> None:
    """Download (if needed), normalise, sample, and write processed JSONL files."""
    split_path = SPLITS_DIR / f"{spec.name}.json"
    if split_path.exists():
        splits = read_json(split_path)          # reuse committed indices
    else:
        splits = choose_indices(spec)
        write_json(split_path, splits)

    pool = [normalise_bbh(r, i) for i, r in enumerate(load_rows(spec.eval_file))]
    eval_items = [pool[i] for i in splits["eval_indices"]]
    shot_items = [pool[i] for i in splits["fewshot_indices"]]
    assert not set(splits["eval_indices"]) & set(splits["fewshot_indices"])  # prove disjointness

    # Development items: every row that is neither evaluated nor an exemplar (96 of 250). Task 3
    # tunes its vote rule on these, so no choice is ever made by looking at the evaluation items.
    used = set(splits["eval_indices"]) | set(splits["fewshot_indices"])
    dev_items = [pool[i] for i in range(len(pool)) if i not in used]

    out = PROCESSED_DIR / spec.name
    write_jsonl(out / "eval.jsonl", eval_items)
    write_jsonl(out / "fewshot.jsonl", shot_items)
    write_jsonl(out / "dev.jsonl", dev_items)
    print(f"[data] {spec.name}: {len(eval_items)} eval items, {len(shot_items)} exemplars, "
          f"{len(dev_items)} dev items -> {out}")


def load_eval(name: str, n_limit: int | None = None) -> list[dict]:
    """Evaluation items (the same list for Tasks 1, 2 and 3). Prepares data on first use."""
    path = PROCESSED_DIR / name / "eval.jsonl"
    if not path.exists():
        prepare(get_spec(name))
    items = read_jsonl(path)
    return items[:n_limit] if n_limit else items


def load_dev(name: str, n_limit: int | None = None) -> list[dict]:
    """Development items, disjoint from the evaluation sample and the exemplars."""
    path = PROCESSED_DIR / name / "dev.jsonl"
    if not path.exists():
        prepare(get_spec(name))
    items = read_jsonl(path)
    return items[:n_limit] if n_limit else items


def load_fewshot(name: str) -> list[dict]:
    path = PROCESSED_DIR / name / "fewshot.jsonl"
    if not path.exists():
        prepare(get_spec(name))
    return read_jsonl(path)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Download and prepare the BBH data.")
    parser.add_argument("--dataset", default=DEFAULT_DATASET, choices=sorted(DATASETS))
    args = parser.parse_args()
    prepare(get_spec(args.dataset))
