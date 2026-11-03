# Chain-of-Thought Faithfulness — CS60075 Assignment 2, Project 8

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Chimankarparag/cs60075-cot-faithfulness/blob/main/code/CoT_Faithfulness_Colab.ipynb)

Does a language model's written chain-of-thought (CoT) actually explain how it reached its answer, or is it a
plausible story written afterwards? This repo measures that for an open 8B instruction-tuned model, reproduces the
intervention methodology of Lanham et al. (2023), and tests whether faithfulness can be used to improve
self-consistency voting. The project covers one dataset: **BIG-Bench-Hard (BBH), logical deduction with five
objects**, a multiple-choice task (options A–E).

**Author:** Parag Chimankar (23CS10049), IIT Kharagpur — CS60075 Natural Language Processing
**Group members:** _to be added_
**Assigned dataset:** BIG-Bench-Hard — logical deduction (five objects), used for all three tasks

> **Status:** Tasks 1 and 2 are implemented and have been run on BBH (results below and in `results/`).
> Task 3 is next; its plan is in `code/task3/README.md`. The earlier GSM8K and StrategyQA code and results were
> removed when the group's dataset was confirmed; they remain in the git history.

---

## The three tasks

| Task | Marks | What it does | Metrics reported |
| --- | --- | --- | --- |
| 1. Direct answering baseline (done) | 30 | Answer with no reasoning, zero-shot and 4-shot, greedy decoding | Accuracy (zero-shot, 4-shot) |
| 2. Paper reproduction (done) | 30 | Standard CoT, then four interventions on it: early answering, adding a mistake, paraphrasing, filler tokens | CoT accuracy gain over Task 1; faithfulness score per intervention |
| 3. Combine & improve (to do) | 40 | Sample 5 CoTs, check each with 50% early answering, weight the majority vote toward "faithful" samples | Accuracy vs Tasks 1 and 2; aggregate faithfulness vs Task 2 |

All three tasks are run on the same dataset (BBH logical deduction, five objects).

## Model

| Role | Checkpoint | Source |
| --- | --- | --- |
| Main model | `meta-llama/Llama-3.1-8B-Instruct`, revision `0e9e39f249a16976918f6564b8830bc894c89659` | https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct (gated: accept Meta's licence on the page first) |
| Fallback if access is delayed | `Qwen/Qwen2.5-7B-Instruct` | https://huggingface.co/Qwen/Qwen2.5-7B-Instruct (not gated) |

Only the `*.safetensors` and `*.json` files are downloaded (15 GB); the `original/` folder is skipped:

```bash
hf download meta-llama/Llama-3.1-8B-Instruct --include "*.json" --include "*.safetensors" --exclude "original/*"
```

## Repository layout

```
cs60075-cot-faithfulness/
├── README.md
├── requirements.txt                 # pinned direct dependencies
├── env/cotfaith-freeze.txt          # full pip freeze of the cluster environment
├── code/
│   ├── CoT_Faithfulness_Colab.ipynb # end-to-end notebook: setup -> Task 1 -> Task 2
│   ├── common/                      # shared by all tasks
│   │   ├── config.py                #   paths, model revision, seed, BBH spec, decoding settings
│   │   ├── data.py                  #   download (pinned + checksummed), normalise, sample
│   │   ├── prompts.py               #   every prompt, incl. Lanham et al.'s forced-answer format
│   │   ├── model.py                 #   vLLM / transformers backends behind one generate()
│   │   ├── answering.py             #   read the answer after a (modified) CoT
│   │   ├── parsing.py               #   answer extraction + CoT sentence splitter
│   │   ├── metrics.py               #   bootstrap CIs, paired tests, AOC
│   │   ├── io_utils.py, cli.py      #   file helpers, shared command-line flags
│   ├── task1/run_direct.py          # Task 1: zero-shot and 4-shot direct answering
│   ├── task2/
│   │   ├── run_task2.py             # Task 2 end to end (one model load, resumable)
│   │   ├── generate_cot.py          #   step 1: CoT + its answer A0
│   │   ├── interventions.py         #   steps 2-5: early answering, mistake, paraphrase, filler
│   │   ├── score.py                 #   faithfulness scores, AOC, paper comparison, figures
│   │   └── examples.py              #   qualitative examples for the report
│   └── task3/                       # Task 3 (to do)
├── data/
│   ├── MANIFEST.md                  # pinned revisions, row counts, SHA-256 checksums
│   ├── splits/                      # exact eval and few-shot indices (seed 42, committed)
│   ├── raw/, processed/             # downloaded / prepared data (gitignored)
├── results/
│   ├── task1/bbh/                   # zero_shot.jsonl, four_shot.jsonl, metrics.json, summary.md
│   └── task2/bbh/                   # cot/early/mistake/paraphrase/filler.jsonl, metrics.json,
│                                    # summary.md, examples.md, figures/*.png
└── scripts/cluster/                 # env.sh, run.sh, run_tasks12.sh for the KGP GPU servers
```

`code/` is deliberately not a Python package (the name would shadow Python's built-in `code` module):
scripts are run by path and put `code/` on the import path themselves.

## Environment setup

### Option A — Google Colab (end-to-end, recommended for graders)

1. Open `code/CoT_Faithfulness_Colab.ipynb` in Colab (badge above), or in VS Code with the **Google Colab**
   extension (`Google.colab`): *Select Kernel → Colab →* sign in → choose a GPU runtime.
2. Leave `REUSE_RESULTS = True` to rebuild every table and figure from the committed generations in seconds
   (no GPU needed), or set it to `False` to regenerate everything with the model.
3. For live runs add the Colab secret `HF_TOKEN` (an account that has accepted the Llama 3.1 licence), and
   `GITHUB_TOKEN` while the repo is private.

A free T4 (~15 GB) cannot hold the 8B model in 16-bit, so live runs on a T4 load it in 4-bit NF4 with
transformers; on L4 / A100 it runs in bf16. The notebook keeps Colab's own PyTorch: the pinned
`torch==2.13.0` is a CUDA 13.0 build that needs an NVIDIA driver >= 580.

### Option B — IIT KGP CSE GPU servers (used for the committed results)

```bash
# once, on a login node (10.5.18.114)
conda create -n cotfaith python=3.11 -y -c conda-forge --override-channels
~/miniconda3/envs/cotfaith/bin/pip install --no-cache-dir -r requirements.txt
~/miniconda3/envs/cotfaith/bin/python code/common/data.py

# on gpu73 (2x L40S) or gpu74 (2x A40): check free memory, then launch detached
nvidia-smi --query-gpu=index,memory.used,memory.total --format=csv
scripts/cluster/run_tasks12.sh 0,1 full --tp 2
tail -f logs/full.log
```

`scripts/cluster/env.sh` fixes two problems met on these machines: Rocky Linux 9's system `libstdc++` is too
old for conda-forge's ICU (vLLM fails with `CXXABI_1.3.15 not found`), and FlashInfer's sampler would need
`nvcc` to compile, so vLLM's PyTorch sampler is used instead. The GPUs are shared, so `code/common/model.py`
sizes vLLM's memory from what is free at start-up; with ~15 GB free per card the model runs with
tensor parallelism over both cards (`--tp 2`).

### VS Code

Recommended extensions are listed in `.vscode/extensions.json` (Python, Jupyter, Google Colab, Remote-SSH).

## Dataset — download and prepare

| Name used here | Hub repo | Config / split | Rows | Used for |
| --- | --- | --- | --- | --- |
| `bbh` | [`maveriq/bigbenchhard`](https://huggingface.co/datasets/maveriq/bigbenchhard) | `logical_deduction_five_objects` / `train` | 250 | eval n = 150; 4 exemplars from the remaining 100 |

`maveriq/bigbenchhard` is a loading-script repo, which `datasets` 4.x refuses to run, so we download the Hub's
auto-converted parquet file at a pinned revision. One command downloads, verifies and prepares everything:

```bash
python code/common/data.py
```

It writes `data/raw/` (checksum checked against `data/MANIFEST.md`), `data/processed/bbh/eval.jsonl` and
`fewshot.jsonl`, and reuses the committed indices in `data/splits/bbh.json`. The same file by hand:

```bash
mkdir -p data/raw/bbh_logical_deduction_five_objects
curl -L -o data/raw/bbh_logical_deduction_five_objects/train.parquet \
  https://huggingface.co/datasets/maveriq/bigbenchhard/resolve/a493490a030bfe06c7baa2db022263afbfa04cfb/logical_deduction_five_objects/train/0000.parquet
(cd data && sha256sum raw/*/*.parquet)   # compare with data/MANIFEST.md
```

Preprocessing (done by `code/common/data.py`): the options `(A)`..`(E)` are parsed from `input` with one regex,
and gold = the letter in `target`, e.g. `(A)`. The loader stops if the gold letter is not one of the options.

## How to run

`--n-limit N` runs a quick test on the first N items and writes to `results/smoke/` instead. Model flags:
`--backend vllm|hf`, `--tp 2` (vLLM on two GPUs), `--quant 4bit` (transformers only). The scripts also accept
`--dataset bbh`, the only value.

```bash
# Task 1 - direct answering, zero-shot and 4-shot
python code/task1/run_direct.py --tp 2
python code/task1/run_direct.py --rescore          # re-parse saved outputs, no GPU

# Task 2 - CoT + four interventions + scoring, one model load (run Task 1 first for the gain)
python code/task2/run_task2.py --tp 2
python code/task2/run_task2.py --stages score      # recompute metrics/figures, no GPU
python code/task2/run_task2.py --stages paraphrase score --overwrite   # redo one stage

# Both tasks, detached on a KGP GPU box
scripts/cluster/run_tasks12.sh 0,1 full --tp 2
```

Task 2's stages (`cot`, `early`, `mistake`, `paraphrase`, `filler`, `score`) each save a JSONL file; a stage whose
file exists is skipped, so an interrupted run resumes where it stopped.

## Outputs

| File | Contents |
| --- | --- |
| `results/task1/bbh/zero_shot.jsonl`, `four_shot.jsonl` | per item: raw output, parsed answer, gold, correct, token count |
| `results/task1/bbh/metrics.json`, `summary.md` | accuracy + 95% CI per variant, parse failures, best variant |
| `results/task2/bbh/cot.jsonl` | CoT text, sentence spans, forced answer A0, the CoT's own stated answer, correct |
| `results/task2/bbh/early.jsonl` | answer after every sentence prefix k = 0..n |
| `results/task2/bbh/mistake.jsonl` | corrupted sentence (before/after), regenerated CoT, new answer |
| `results/task2/bbh/paraphrase.jsonl`, `filler.jsonl` | paraphrase / filler length, new answer |
| `results/task2/bbh/metrics.json`, `summary.md` | all Task 2 numbers, incl. the paper comparison |
| `results/task2/bbh/examples.md` | qualitative examples for the report |
| `results/task2/bbh/figures/` | early-answering curve, faithfulness bar chart |

## Results so far (Tasks 1 and 2, BBH logical deduction, five objects)

Llama-3.1-8B-Instruct in bf16 (vLLM), seed 42, n = 150 items. Brackets are 95% bootstrap intervals.

**Task 1 and CoT accuracy (%)**

| Direct, zero-shot | Direct, 4-shot | CoT (Task 2) | CoT gain over best direct |
| --- | --- | --- | --- |
| 46.0 [38.0, 54.0] | 43.3 [35.3, 52.0] | 54.0 [46.0, 62.0] | +8.0 [-2.0, 17.3], McNemar p = 0.13 (32 vs 20 discordant items) |

**Task 2 faithfulness scores (%)** — share of items whose answer changes (early answering, mistake, filler)
or stays the same (paraphrase) relative to the answer after the full CoT

| Early answering | Adding a mistake | Paraphrasing | Filler tokens | Aggregate |
| --- | --- | --- | --- | --- |
| 48.5 [41.3, 55.8] | 48.3 [40.9, 55.7] (n = 149) | 97.2 [94.4, 99.3] (n = 144) | 50.7 [42.7, 59.3] | 61.2 |

**Early-answering AOC vs Lanham et al. (2023), Table 2** (175B model; closest paper task is LogiQA)

| Ours: grid AOC | Ours: per-sentence AOC | Paper AOC (LogiQA) |
| --- | --- | --- |
| 0.44 | 0.44 | 0.26 |

Share of items whose early answer already equals the final answer A0, by fraction of the CoT shown:
46.7% at 0%, 47.3% at 20%, 47.3% at 40%, 50.7% at 60%, 60.7% at 80% (100% by definition at the end).

First observations:

- CoT helps by 8 points, but the interval includes zero (p = 0.13), so with 150 items the gain is suggestive,
  not established.
- About half the answers (46.7%) are already fixed before any reasoning is shown, and the curve stays flat until
  the last 40% of the CoT, so the conclusion is mostly reached late. Our AOC (0.44) is above the paper's LogiQA
  value (0.26). The paper reports that smaller models often give more faithful CoTs, which fits an 8B model
  scoring above a 175B one; one CoT per item and a fixed truncation grid also differ from their setup.
- Paraphrasing almost never changes the answer (97.2%), so there is no sign of information hidden in the exact
  wording, matching the paper's finding.
- Filler tokens do not help: filler accuracy is 48.0%, close to answering with no reasoning in the same format
  (46.7%).
- CoTs average 12.0 sentences (211 tokens); 5 hit the 512-token cap and 7 never state an answer. For the rest,
  the CoT's own stated answer matches the forced answer A0 in 92.3% of items.

## Implementation notes and deviations

- **Answer read-out** follows Lanham et al.: the (possibly modified) CoT is placed in the assistant turn, the user
  asks "Given all of the above, what's the single, most likely answer?", and the reply is prefilled with
  "The single, most likely answer is". Greedy, 16 tokens.
- **Early answering** is run after every sentence, not only at 20/40/60/80%; the spec's score uses those four
  points (k = floor(p × n) sentences), and the extra points give a per-sentence AOC comparable to the paper's.
- **Adding a mistake**: one sentence, chosen at random (seeded by item id) among non-final sentences that do not
  announce the answer, is rewritten by the same model with a 3-shot
  prompt; rewrites that change only punctuation are rejected (up to 3 attempts; if all fail the item is
  dropped, which is why n = 149). The rest of the CoT is regenerated with the original settings.
  The paper corrupts sentences with a separate model and averages over positions; we use one position per item.
- **Paraphrasing** rewrites the whole CoT without the question; a paraphrase counts only if it keeps the stated
  conclusion and every option letter it mentions. Valid: 144/150.
- **Filler** is `" ..."` repeated to the CoT's token length (the paper's filler token).
- **One CoT per item** (the paper samples 100), and an 8B model instead of 175B.
- **Direct answering** is enforced by an answer-only instruction, a "The answer is" prefill and a 16-token cap.

## Reproducibility

| What | Value |
| --- | --- |
| Model | `meta-llama/Llama-3.1-8B-Instruct`, revision `0e9e39f2`, bf16 |
| Eval sample and few-shot exemplars | seed 42 (indices committed in `data/splits/`) |
| Greedy runs (Task 1, every forced answer, first rewrite attempt) | temperature 0 |
| CoT sampling (Task 2) | temperature 0.7, top-p 0.95, max 512 new tokens, seed 42 + item position |
| Rewrite retries | temperature 0.7, top-p 0.95, seed 42 + 1000 × attempt + item position |
| Bootstrap confidence intervals | 1,000 resamples, seed 42 |

vLLM uses one seed per request, so outputs do not depend on batching: re-running all forced answers in a
different batch composition reproduced every A0 exactly.

## Submission checklist

- [x] `code/task1` and `code/task2` + shared `code/common`
- [ ] `code/task3`
- [x] Colab notebook for Tasks 1-2 (replay mode tested end to end)
- [x] `requirements.txt` with pinned versions
- [ ] `report.pdf` (8–12 pages) with the Task 2 paper-comparison section
- [ ] 5–10 minute code walkthrough video
- [ ] `.zip` with `code/`, `README.md`, `requirements.txt`, `report.pdf` (no data or weights)

## References

- Lanham et al., *Measuring Faithfulness in Chain-of-Thought Reasoning*, [arXiv:2307.13702](https://arxiv.org/abs/2307.13702), 2023.
- Wei et al., *Chain-of-Thought Prompting Elicits Reasoning in Large Language Models*, [arXiv:2201.11903](https://arxiv.org/abs/2201.11903), 2022.
- Wang et al., *Self-Consistency Improves Chain of Thought Reasoning in Language Models*, [arXiv:2203.11171](https://arxiv.org/abs/2203.11171), 2022.
- Suzgun et al., *Challenging BIG-Bench Tasks and Whether Chain-of-Thought Can Solve Them* (BBH), [arXiv:2210.09261](https://arxiv.org/abs/2210.09261), 2022.
