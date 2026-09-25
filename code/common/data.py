"""Download, normalise and sample the three Project 8 datasets.

Every dataset ends up as a list of *items* with the same keys, so the rest of the
pipeline never needs dataset-specific loading code:

    {"id": "gsm8k-test-42",   # stable identifier: dataset, source split, row index
     "index": 42,             # row index inside the source parquet file
     "question": "...",       # text shown to the model (BBH: includes the options)
     "options": {"A": ...},   # BBH only: option letter -> option text; else None
     "gold": "18"}            # canonical gold answer: number / letter / "Yes"|"No"

Run as a script to download and prepare everything:
    python code/common/data.py --dataset all
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

from common.config import (DATASETS, N_FEWSHOT, PROCESSED_DIR, RAW_DIR, SEED, SPLITS_DIR,
                           DatasetSpec, RawFile, get_spec)
from common.io_utils import read_json, read_jsonl, write_json, write_jsonl
from common.parsing import canonical_number


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
def gsm8k_gold(answer_field: str) -> str:
    """GSM8K solutions end with '#### <number>'; the gold answer is that number,
    with currency symbols and thousands separators stripped."""
    final = answer_field.split("####")[-1].strip()
    number = canonical_number(final)
    if number is None:
        raise ValueError(f"Could not parse GSM8K gold answer from {final!r}")
    return number


def normalise_gsm8k(row: dict, index: int, split: str) -> dict:
    return {"id": f"gsm8k-{split}-{index}", "index": index, "question": row["question"].strip(),
            "options": None, "gold": gsm8k_gold(row["answer"])}


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


def normalise_strategyqa(row: dict, index: int) -> dict:
    # This mirror stores the answer as a Python/NumPy bool; we map it to "Yes"/"No".
    # facts / decomposition are deliberately dropped: the model must never see them.
    answer = row["answer"]
    if not isinstance(answer, (bool,)) and str(answer) not in ("True", "False"):
        raise ValueError(f"StrategyQA row {index}: unexpected answer encoding {answer!r}")
    gold = "Yes" if str(answer) == "True" else "No"
    return {"id": f"strategyqa-{row['qid']}", "index": index, "question": row["question"].strip(),
            "options": None, "gold": gold}


def normalise(spec: DatasetSpec, rows: list[dict], split: str) -> list[dict]:
    if spec.name == "gsm8k":
        return [normalise_gsm8k(r, i, split) for i, r in enumerate(rows)]
    if spec.name == "bbh":
        return [normalise_bbh(r, i) for i, r in enumerate(rows)]
    if spec.name == "strategyqa":
        return [normalise_strategyqa(r, i) for i, r in enumerate(rows)]
    raise ValueError(spec.name)


# --------------------------------------------------------------------------- #
# 3. Choose the evaluation sample and the few-shot exemplars (seed 42)
# --------------------------------------------------------------------------- #
def choose_indices(spec: DatasetSpec) -> dict:
    """Pick eval and few-shot row indices reproducibly.

    * GSM8K: eval = 200 rows of `test`; exemplars = 4 rows of `train`
      (two independent pools, so overlap is impossible).
    * BBH / StrategyQA: one pool. Shuffle all indices once with the seed; the
      first 4 become exemplars and the next n_eval the eval set, so the two
      sets are disjoint by construction.
    """
    if spec.fewshot_file is not None:
        eval_idx = random.Random(SEED).sample(range(spec.eval_file.n_rows), spec.n_eval)
        shot_idx = random.Random(SEED + 1).sample(range(spec.fewshot_file.n_rows), N_FEWSHOT)
    else:
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

    eval_split = "test" if spec.name == "gsm8k" else "all"
    eval_pool = normalise(spec, load_rows(spec.eval_file), eval_split)
    shot_pool = eval_pool if spec.fewshot_file is None else normalise(spec, load_rows(spec.fewshot_file), "train")

    eval_items = [eval_pool[i] for i in splits["eval_indices"]]
    shot_items = [shot_pool[i] for i in splits["fewshot_indices"]]
    if spec.fewshot_file is None:  # same pool: prove disjointness instead of assuming it
        assert not set(splits["eval_indices"]) & set(splits["fewshot_indices"])

    out = PROCESSED_DIR / spec.name
    write_jsonl(out / "eval.jsonl", eval_items)
    write_jsonl(out / "fewshot.jsonl", shot_items)
    print(f"[data] {spec.name}: {len(eval_items)} eval items, {len(shot_items)} exemplars -> {out}")


def load_eval(name: str, n_limit: int | None = None) -> list[dict]:
    """Evaluation items (the same list for Tasks 1, 2 and 3). Prepares data on first use."""
    path = PROCESSED_DIR / name / "eval.jsonl"
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

    parser = argparse.ArgumentParser(description="Download and prepare the datasets.")
    parser.add_argument("--dataset", default="all", choices=["all", *DATASETS])
    args = parser.parse_args()
    for name in (DATASETS if args.dataset == "all" else [args.dataset]):
        prepare(get_spec(name))
