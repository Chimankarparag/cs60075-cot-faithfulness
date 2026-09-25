"""Central configuration for the CoT-faithfulness project.

Everything that must be identical across Tasks 1-3 lives here: paths, the model
checkpoint, seeds, dataset definitions and decoding settings. Scripts import
these constants instead of hard-coding values, so one edit changes the whole
pipeline and the report can point to a single file for "what settings were used".
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

# --------------------------------------------------------------------------- #
# Paths. REPO_ROOT is two levels above this file: code/common/config.py -> repo.
# --------------------------------------------------------------------------- #
REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"              # downloaded parquet files (gitignored)
PROCESSED_DIR = DATA_DIR / "processed"  # normalised JSONL (gitignored)
SPLITS_DIR = DATA_DIR / "splits"        # chosen indices (committed)
RESULTS_DIR = REPO_ROOT / "results"     # generations + metrics (committed)

# --------------------------------------------------------------------------- #
# Model. Pinning the revision means a later update on the Hub cannot silently
# change our numbers.
# --------------------------------------------------------------------------- #
MODEL_ID = "meta-llama/Llama-3.1-8B-Instruct"
MODEL_REVISION = "0e9e39f249a16976918f6564b8830bc894c89659"
MAX_MODEL_LEN = 4096  # prompt + generation budget; our longest prompts are ~2k tokens

# --------------------------------------------------------------------------- #
# Randomness. Every random choice in the project derives from this one seed.
# --------------------------------------------------------------------------- #
SEED = 42
N_FEWSHOT = 4  # the spec asks for 4-shot direct answering in Task 1


@dataclass(frozen=True)
class RawFile:
    """One parquet file on the Hugging Face Hub, pinned to an exact commit."""

    repo_id: str
    revision: str   # commit SHA (for script datasets: of the refs/convert/parquet branch)
    filename: str   # path of the file inside the Hub repo
    local: str      # where we keep it, relative to data/raw/
    sha256: str     # checksum we verify after every download
    n_rows: int


@dataclass(frozen=True)
class DatasetSpec:
    """How to load, sample and grade one dataset."""

    name: str
    answer_type: str                 # "number" (GSM8K), "letter" (BBH) or "yesno" (StrategyQA)
    n_eval: int                      # evaluation sample size fixed by the assignment
    eval_file: RawFile               # pool the evaluation sample is drawn from
    fewshot_file: RawFile | None     # separate exemplar pool, or None = same pool, disjoint indices


_GSM8K_REV = "740312add88f781978c0658806c59bc2815b9866"

DATASETS: dict[str, DatasetSpec] = {
    "gsm8k": DatasetSpec(
        name="gsm8k",
        answer_type="number",
        n_eval=200,
        eval_file=RawFile(
            "openai/gsm8k", _GSM8K_REV, "main/test-00000-of-00001.parquet", "gsm8k/test.parquet",
            "ee7b8da9e381df27b9e3f7758a159ab2bdaa4dbaa910546cbbc47e0cb44e4f59", 1319,
        ),
        fewshot_file=RawFile(
            "openai/gsm8k", _GSM8K_REV, "main/train-00000-of-00001.parquet", "gsm8k/train.parquet",
            "ea82612ea9582142387730c793eb67d3b12849002bc0b7fa6f8efafa7351419d", 7473,
        ),
    ),
    "bbh": DatasetSpec(
        name="bbh",
        answer_type="letter",
        n_eval=150,
        eval_file=RawFile(
            "maveriq/bigbenchhard", "a493490a030bfe06c7baa2db022263afbfa04cfb",
            "logical_deduction_five_objects/train/0000.parquet",
            "bbh_logical_deduction_five_objects/train.parquet",
            "1ddb7e4512bca5fa1009be8fcb8d40f345b8774f0a970978d78f296c53f501b2", 250,
        ),
        fewshot_file=None,
    ),
    "strategyqa": DatasetSpec(
        name="strategyqa",
        answer_type="yesno",
        n_eval=150,
        eval_file=RawFile(
            "wics/strategy-qa", "c9a25e4b10d32364d25f1f1387bf445921b6e75e",
            "strategyQA/test/0000.parquet", "strategyqa/test.parquet",
            "c86cb39299a458683427ade4296546c92c94bee7640e2fa9d3642a0f7675f490", 2290,
        ),
        fewshot_file=None,
    ),
}


@dataclass(frozen=True)
class Decoding:
    """Sampling settings for one kind of generation."""

    temperature: float
    top_p: float
    max_new_tokens: int


# Task 1: greedy, and a small token cap so a "direct" answer cannot turn into reasoning.
DIRECT_DECODING = Decoding(temperature=0.0, top_p=1.0, max_new_tokens=16)
# Task 2 step 1: the spec's CoT settings.
COT_DECODING = Decoding(temperature=0.7, top_p=0.95, max_new_tokens=512)
# Reading off an answer after a (possibly modified) CoT: greedy, a few tokens.
ANSWER_DECODING = Decoding(temperature=0.0, top_p=1.0, max_new_tokens=16)
# Rewriting one reasoning step with a mistake: greedy first, sampled on retries.
MISTAKE_DECODING = Decoding(temperature=0.0, top_p=1.0, max_new_tokens=128)
# Paraphrasing a whole CoT: greedy first, sampled on retries.
PARAPHRASE_DECODING = Decoding(temperature=0.0, top_p=1.0, max_new_tokens=768)
RETRY_TEMPERATURE = 0.7
MAX_REWRITE_ATTEMPTS = 3

# Early-answering truncation points required by the spec (fractions of sentences kept).
EARLY_ANSWER_FRACTIONS = (0.2, 0.4, 0.6, 0.8)

# Bootstrap settings for confidence intervals.
N_BOOTSTRAP = 1000


def get_spec(name: str) -> DatasetSpec:
    """Look up a dataset by name with a helpful error message."""
    if name not in DATASETS:
        raise ValueError(f"Unknown dataset {name!r}; choose from {sorted(DATASETS)}")
    return DATASETS[name]
