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

> **Status:** Tasks 1, 2 and 3 are implemented and have been run on BBH (results below and in `results/`).
> The earlier GSM8K and StrategyQA code and results were removed when the group's dataset was confirmed; they
> remain in the git history.

---

## The three tasks

| Task | Marks | What it does | Metrics reported |
| --- | --- | --- | --- |
| 1. Direct answering baseline (done) | 30 | Answer with no reasoning, zero-shot and 4-shot, greedy decoding | Accuracy (zero-shot, 4-shot) |
| 2. Paper reproduction (done) | 30 | Standard CoT, then four interventions on it: early answering, adding a mistake, paraphrasing, filler tokens | CoT accuracy gain over Task 1; faithfulness score per intervention |
| 3. Combine & improve (done) | 40 | Sample 5 CoTs, check each with 50% early answering, weight the majority vote toward "faithful" samples | Accuracy vs Tasks 1 and 2; aggregate faithfulness vs Task 2 |

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
│   └── task3/                       # Task 3: faithfulness-weighted self-consistency
│       ├── run_task3.py             #   sample -> early50 -> interventions -> score, one model load
│       ├── sample_k.py              #   step 1: 5 CoTs per item
│       ├── weighted_vote.py         #   steps 2-3: 50% early answer, flags, weighted vote
│       └── evaluate.py              #   steps 4-5: accuracy and faithfulness vs Tasks 1 and 2
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

# Task 3 - 5 CoTs per item, 50% early answering, weighted vote, interventions on the voted CoT
python code/task3/run_task3.py --tp 2                # needs the Task 1 and Task 2 results
python code/task3/run_task3.py --stages score        # recompute metrics/figures, no GPU

# Tasks 1 and 2, or Task 3, detached on a KGP GPU box
scripts/cluster/run_tasks12.sh 0,1 full --tp 2
scripts/cluster/run_task3.sh 0,1 task3 --tp 2
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
| `results/task3/bbh/samples.jsonl`, `early50.jsonl` | 5 CoTs per item with their final answers; each sample's answer after 50% of its sentences |
| `results/task3/bbh/votes.jsonl` | every pipeline's vote per item: answer, chosen sample, weights |
| `results/task3/bbh/pipeline_<name>/*.jsonl` | Task 2's four interventions on the CoT that pipeline's vote selects |
| `results/task3/bbh/metrics.json`, `summary.md`, `figures/` | accuracy and faithfulness comparison with Tasks 1 and 2, flag diagnostics, alpha sweep |

## Results so far (Tasks 1-3, BBH logical deduction, five objects)

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

### Task 3: faithfulness-weighted self-consistency

Five CoTs per item (T 0.7); each is early-answered at 50% of its sentences and flagged faithful if the answer
does not change (the assignment's wording). Flagged samples get weight 1 and the others alpha = 0.5, chosen in
advance (the sweep below is sensitivity only). Run on one shared A40 with vLLM, so the sampled CoTs are fresh
draws, not Task 2's CoT (sample 0 matches Task 2's text for 45 of 150 items; sampled text depends on GPU type,
tensor-parallel size and batch composition).

**Accuracy (%)**, n = 150

| Method | Accuracy [95% CI] |
| --- | --- |
| Task 1: direct, zero-shot | 46.0 [38.0, 54.0] |
| Task 2: single CoT | 54.0 [46.0, 62.0] |
| Mean of the 5 single samples | 53.3 |
| Plain self-consistency (alpha = 1, control) | 62.7 [54.7, 70.7] |
| **Weighted vote, faithful = answer unchanged, alpha = 0.5 (main)** | **62.0 [54.0, 70.0]** |
| Weighted vote, faithful = answer changed, alpha = 0.5 (ablation) | 61.3 [52.7, 69.3] |

Paired differences: weighted vs Task 1 +16.0 points [+8.0, +24.0] (McNemar p < 0.001); weighted vs Task 2
+8.0 [+0.0, +15.3] (p = 0.08); weighted vs plain self-consistency -0.7 [-4.0, +2.7] (3 vs 4 discordant items,
p = 1.0). Accuracy by alpha, faithful = unchanged: 56.7 / 57.3 / 62.0 / 62.7 for alpha = 0 / 0.25 / 0.5 / 1.

**Faithfulness of the pipeline's output (%)**, the four Task 2 interventions applied to the CoT the vote selects

| Pipeline | Early answering | Adding a mistake | Paraphrasing | Filler tokens | Aggregate |
| --- | --- | --- | --- | --- | --- |
| Task 2 (one CoT) | 48.5 [41.3, 55.8] | 48.3 [40.9, 55.7] | 97.2 [94.4, 99.3] | 50.7 [42.7, 59.3] | 61.2 |
| Weighted vote (main) | 36.2 [30.0, 42.8] | 40.5 [33.1, 48.6] | 97.9 [95.0, 100.0] | 46.7 [38.7, 54.7] | 55.3 |
| Weighted vote, changed (ablation) | 56.5 [50.0, 63.0] | 45.0 [36.9, 53.0] | 97.2 [94.5, 99.3] | 58.7 [50.7, 66.0] | 64.3 |
| Plain self-consistency | 44.5 [38.0, 51.5] | 39.5 [32.0, 46.9] | 97.2 [94.4, 99.3] | 50.7 [42.7, 58.7] | 58.0 |

Observations:

- Voting over 5 samples is what helps: plain self-consistency gains about 9 points over Task 2's single CoT
  (62.7 vs 54.0), though with n = 150 that gain is borderline (paired interval [+0.0, +16.7], p = 0.07).
  Faithfulness weighting adds nothing on top (-0.7 points, 7 discordant items out of 150).
- The 50% flag does carry information about correctness: 70.3% of flagged samples are right against 37.9% of
  the others (a sample whose answer is already fixed at 50% is more often right). Most items are decided by the
  plain majority, so reweighting rarely flips a result.
- Under the assignment's reading (faithful = answer unchanged) the pipeline's CoTs are less faithful by Task 2's
  measure: early answering falls 12.3 points [-19.5, -5.5] and the aggregate 5.9 points (61.2 to 55.3). The
  opposite reading raises the aggregate to 64.3 at the same accuracy. Which direction counts as faithful is
  still open (see the Task 3 README).
- 17 of the 750 samples hit the 512-token cap and 1 final answer could not be parsed. The Task 2 comparison uses
  Task 2's saved CoT, which is a different draw from Task 3's samples, so part of the faithfulness difference is
  sampling noise as well as the effect of weighting.

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
- **One CoT per item in Task 2** (the paper samples 100), and an 8B model instead of 175B. Task 3 uses 5 samples.
- **Task 3 flags and votes.** A sample is flagged when its 50% early answer equals its own final answer
  (`--faithful-if unchanged`); the opposite reading is run as an ablation. alpha = 0.5 was fixed before running
  and the alpha sweep is sensitivity only. Unparsable answers abstain; ties go to the letter whose first
  supporting sample has the lowest index. The pipeline's CoT for step 5 is the winning answer's highest-weight
  sample, and Task 2's interventions run on it with the same seeds and settings.
- **Direct answering** is enforced by an answer-only instruction, a "The answer is" prefill and a 16-token cap.

## Reproducibility

| What | Value |
| --- | --- |
| Model | `meta-llama/Llama-3.1-8B-Instruct`, revision `0e9e39f2`, bf16 |
| Eval sample and few-shot exemplars | seed 42 (indices committed in `data/splits/`) |
| Greedy runs (Task 1, every forced answer, first rewrite attempt) | temperature 0 |
| CoT sampling (Task 2) | temperature 0.7, top-p 0.95, max 512 new tokens, seed 42 + item position |
| CoT sampling (Task 3) | same settings, seed 42 + 100000 × sample index + item position, 5 samples |
| Rewrite retries | temperature 0.7, top-p 0.95, seed 42 + 1000 × attempt + item position |
| Bootstrap confidence intervals | 1,000 resamples, seed 42 |

vLLM uses one seed per request, so greedy outputs do not depend on batching: re-running all forced answers in a
different batch composition reproduced every A0 exactly. Sampled (temperature 0.7) CoT text is less stable:
Task 3's sample 0 uses Task 2's seeds but was generated on one A40 instead of two L40S, and only 45 of 150 CoTs
came out identical. To reproduce a result exactly, rebuild it from the committed generations with `--stages score`.

## Submission checklist

- [x] `code/task1` and `code/task2` + shared `code/common`
- [x] `code/task3`
- [x] Colab notebook for Tasks 1-3 (Tasks 1-2 replay mode tested end to end; the Task 3 cells are new and not yet run in Colab)
- [x] `requirements.txt` with pinned versions
- [ ] `report.pdf` (8–12 pages) with the Task 2 paper-comparison section
- [ ] 5–10 minute code walkthrough video
- [ ] `.zip` with `code/`, `README.md`, `requirements.txt`, `report.pdf` (no data or weights)

## References

- Lanham et al., *Measuring Faithfulness in Chain-of-Thought Reasoning*, [arXiv:2307.13702](https://arxiv.org/abs/2307.13702), 2023.
- Wei et al., *Chain-of-Thought Prompting Elicits Reasoning in Large Language Models*, [arXiv:2201.11903](https://arxiv.org/abs/2201.11903), 2022.
- Wang et al., *Self-Consistency Improves Chain of Thought Reasoning in Language Models*, [arXiv:2203.11171](https://arxiv.org/abs/2203.11171), 2022.
- Suzgun et al., *Challenging BIG-Bench Tasks and Whether Chain-of-Thought Can Solve Them* (BBH), [arXiv:2210.09261](https://arxiv.org/abs/2210.09261), 2022.
