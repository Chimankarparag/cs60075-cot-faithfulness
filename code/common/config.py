"""Central configuration for the CoT-faithfulness project (BIG-Bench-Hard, logical deduction).

Everything that must be identical across Tasks 1-3 lives here: paths, the model
checkpoint, seeds, dataset definitions and decoding settings. Scripts import
these constants instead of hard-coding values, so one edit changes the whole
pipeline and the report can point to a single file for "what settings were used".
"""
from __future__ import annotations

import os
import sys
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
RESULTS_ROOT = REPO_ROOT / "results"   # generations + metrics (committed)


# --------------------------------------------------------------------------- #
# Run-level choices: which model, which generation seed.
#
# Both are module constants imported all over the code, so they must be known when
# this module is first imported, before argparse runs. They are therefore read here
# from the command line (--model X / --seed N, also declared in cli.py so --help and
# validation work) or from the environment (COTFAITH_MODEL / COTFAITH_SEED).
# --------------------------------------------------------------------------- #
def _run_choice(flag: str, env: str, default: str) -> str:
    argv = sys.argv[1:]
    for i, arg in enumerate(argv):
        if arg == flag and i + 1 < len(argv):
            return argv[i + 1]
        if arg.startswith(flag + "="):
            return arg.split("=", 1)[1]
    return os.environ.get(env, default)


# --------------------------------------------------------------------------- #
# Models. Pinning the revision means a later update on the Hub cannot silently
# change our numbers.
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class ModelSpec:
    key: str                  # short name used on the command line and in result paths
    hf_id: str                # Hugging Face model id
    revision: str             # pinned commit
    chat_template_kwargs: tuple = ()   # extra (name, value) arguments for the chat template
    about: str = ""


MODELS: dict[str, ModelSpec] = {
    # The model used for the main results (Tasks 1-3).
    "llama3.1-8b": ModelSpec("llama3.1-8b", "meta-llama/Llama-3.1-8B-Instruct",
                             "0e9e39f249a16976918f6564b8830bc894c89659",
                             about="Meta Llama 3.1 8B Instruct (July 2024)"),
    # A stronger open instruction-tuned model of the same size class, for comparison.
    # Qwen3 has a built-in "thinking" mode; it is switched off so that the model writes the
    # same kind of CoT as Llama: one visible reasoning text after "Let's think step by step:".
    "qwen3-8b": ModelSpec("qwen3-8b", "Qwen/Qwen3-8B", "b968826d9c46dd6066d109eabc6255188de91218",
                          chat_template_kwargs=(("enable_thinking", False),),
                          about="Alibaba Qwen3 8B (April 2025), thinking mode off"),
}
DEFAULT_MODEL = "llama3.1-8b"
MODEL_KEY = _run_choice("--model", "COTFAITH_MODEL", DEFAULT_MODEL)
if MODEL_KEY not in MODELS:
    raise SystemExit(f"Unknown model {MODEL_KEY!r}; choose from {sorted(MODELS)}")
MODEL = MODELS[MODEL_KEY]
MODEL_ID = MODEL.hf_id
MODEL_REVISION = MODEL.revision
MAX_MODEL_LEN = 4096  # prompt + generation budget; our longest prompts are ~2k tokens

# Results of the default model stay at results/<task>/bbh/ (the paths used since Task 1);
# every other model gets its own tree, results/models/<key>/<task>/bbh/, so the two can be
# compared side by side without overwriting each other.
RESULTS_DIR = RESULTS_ROOT if MODEL_KEY == DEFAULT_MODEL else RESULTS_ROOT / "models" / MODEL_KEY

# --------------------------------------------------------------------------- #
# Randomness. The data split, exemplars and bootstrap use SEED; sampling uses GEN_SEED.
# --------------------------------------------------------------------------- #
SEED = 42
# Seed for sampled generations (CoTs, Task 3 samples, mistake/paraphrase retries). It equals SEED
# unless a run passes --seed N (Task 3 is repeated with seeds 20, 30 and 40). The data split,
# the few-shot exemplars and the bootstrap always use SEED, so every run sees the same items.
GEN_SEED = int(_run_choice("--seed", "COTFAITH_SEED", str(SEED)))
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
    """How to load and sample the dataset."""

    name: str
    n_eval: int          # evaluation sample size fixed by the assignment
    eval_file: RawFile   # pool the evaluation sample AND the few-shot exemplars are drawn from


# BIG-Bench-Hard, subtask logical_deduction_five_objects: 250 multiple-choice questions.
# 150 form the evaluation sample (assignment); 4 more are the few-shot exemplars, disjoint from them.
DATASETS: dict[str, DatasetSpec] = {
    "bbh": DatasetSpec(
        name="bbh",
        n_eval=150,
        eval_file=RawFile(
            "maveriq/bigbenchhard", "a493490a030bfe06c7baa2db022263afbfa04cfb",
            "logical_deduction_five_objects/train/0000.parquet",
            "bbh_logical_deduction_five_objects/train.parquet",
            "1ddb7e4512bca5fa1009be8fcb8d40f345b8774f0a970978d78f296c53f501b2", 250,
        ),
    ),
}
DEFAULT_DATASET = "bbh"


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
