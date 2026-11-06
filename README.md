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

> **Status:** Tasks 1, 2 and 3 are implemented and have been run on BBH for two models
> (`meta-llama/Llama-3.1-8B-Instruct` and `Qwen/Qwen3-8B`), with sampling seeds 20, 30 and 40 (results below
> and in `results/`). Every run's host, GPUs and timings are in `run_info.json` files and summarised in
> `results/comparison/models.md`; the run logs are in `results/logs/`.
> Earlier results (GSM8K, StrategyQA, and BBH runs that used seed 42 and a different 150-item sample) were
> removed and remain in the git history.

---

## The three tasks

| Task | Marks | What it does | Metrics reported |
| --- | --- | --- | --- |
| 1. Direct answering baseline (done) | 30 | Answer with no reasoning, zero-shot and 4-shot, greedy decoding | Accuracy (zero-shot, 4-shot) |
| 2. Paper reproduction (done) | 30 | Standard CoT, then four interventions on it: early answering, adding a mistake, paraphrasing, filler tokens | CoT accuracy gain over Task 1; faithfulness score per intervention |
| 3. Combine & improve (done) | 40 | Sample 5 CoTs, check each with 50% early answering, weight the majority vote toward "faithful" samples | Accuracy vs Tasks 1 and 2; aggregate faithfulness vs Task 2 |

All three tasks are run on the same dataset (BBH logical deduction, five objects).

## Model

The assignment asks for "an open instruction-tuned model ≥7B parameters"; it does not name one. Both models
below are run through the same code (`--model`), and their results are kept in separate folders.

| Role | Checkpoint | Source |
| --- | --- | --- |
| Main model (`--model llama3.1-8b`, default) | `meta-llama/Llama-3.1-8B-Instruct`, revision `0e9e39f249a16976918f6564b8830bc894c89659` | https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct (gated: accept Meta's licence on the page first) |
| Stronger model for comparison (`--model qwen3-8b`) | `Qwen/Qwen3-8B`, revision `b968826d9c46dd6066d109eabc6255188de91218`, thinking mode off (`enable_thinking=False`) | https://huggingface.co/Qwen/Qwen3-8B (not gated) |

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
│   │   ├── config.py                #   paths, models (--model), seeds (20; --seed 20/30/40), BBH spec, decoding
│   │   ├── data.py                  #   download (pinned + checksummed), normalise, sample
│   │   ├── prompts.py               #   every prompt, incl. Lanham et al.'s forced-answer format
│   │   ├── model.py                 #   vLLM / transformers backends behind one generate()
│   │   ├── answering.py             #   read the answer after a (modified) CoT
│   │   ├── parsing.py               #   answer extraction + CoT sentence splitter
│   │   ├── metrics.py               #   bootstrap CIs, paired tests, AOC
│   │   ├── io_utils.py, cli.py      #   file helpers / result folders, shared command-line flags
│   │   └── runinfo.py               #   run_info.json: host, GPUs, versions, timings of every GPU run
│   ├── task1/run_direct.py          # Task 1: zero-shot and 4-shot direct answering
│   ├── task2/
│   │   ├── run_task2.py             # Task 2 end to end (one model load, resumable)
│   │   ├── generate_cot.py          #   step 1: CoT + its answer A0
│   │   ├── interventions.py         #   steps 2-5: early answering, mistake, paraphrase, filler
│   │   ├── score.py                 #   faithfulness scores, AOC, paper comparison, figures
│   │   ├── paper_style.py           #   the paper's own versions: mistakes at many positions,
│   │   │                            #   prefix paraphrasing, filler-length sweep
│   │   └── examples.py              #   qualitative examples for the report
│   └── task3/                       # Task 3: faithfulness-weighted self-consistency
│       ├── run_task3.py             #   sample -> early50 -> interventions -> score, one model load
│       ├── sample_k.py              #   step 1: 5 CoTs per item
│       ├── weighted_vote.py         #   steps 2-3: 50% early answer, no-reasoning answer, flags, vote
│       ├── tune.py                  #   choose flag rule and alpha on the 96 dev items
│       ├── evaluate.py              #   steps 4-5: accuracy and faithfulness vs Tasks 1 and 2
│       └── seeds.py                 #   Tasks 2-3 across seeds 20/30/40
│   └── analysis/compare_models.py   # both models side by side + where/how long every run took
├── data/
│   ├── MANIFEST.md                  # pinned revisions, row counts, SHA-256 checksums
│   ├── splits/                      # exact eval and few-shot indices (seed 20, committed); the other 96 = dev
│   ├── raw/, processed/             # downloaded / prepared data (gitignored)
├── results/                         # Llama-3.1-8B (default model)
│   ├── task1/bbh/                   # zero_shot.jsonl, four_shot.jsonl, metrics.json, summary.md
│   ├── task2/bbh/                   # seed 20: cot/early/mistake/paraphrase/filler.jsonl, the
│   │                                # paper-style stages, metrics*.json, summary*.md, figures/
│   │   └── seed_30/, seed_40/       # the other two seeds
│   ├── task3/bbh/                   # seed 20; dev/ (tuning), seed_30/, seed_40/, seeds_summary.md
│   ├── models/qwen3-8b/             # the same tree for Qwen3-8B
│   ├── comparison/                  # models.md/json, runs.md, figures/
│   └── logs/<model>/                # the log of every step of the final runs
└── scripts/cluster/                 # env.sh, run_all.sh, campaign.sh, status.sh, ... (KGP GPU servers)
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

**Everything at once, on a KGP GPU box** (picks free GPUs, runs every task for the chosen model(s) detached,
then writes `results/comparison/` and `logs/STATUS.md`):

```bash
scripts/cluster/run_all.sh llama --tp 1      # or: qwen, both
scripts/cluster/status.sh                    # progress on one screen
```

**Step by step.** `--model llama3.1-8b|qwen3-8b` picks the model (default Llama; Qwen writes to
`results/models/qwen3-8b/`), `--seed 20|30|40` the generation seed (default 20; 30 and 40 write to `seed_<N>/`).
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

python code/task2/run_task2.py --seed 30 --stages cot early mistake paraphrase filler score   # another seed

# Task 3 - 5 CoTs per item, 50% early answering, weighted vote, interventions on the voted CoT
python code/task3/run_task3.py --split dev --tp 2    # 1) choose rule and alpha on the 96 dev items
python code/task3/run_task3.py --tp 2                # 2) the 150 eval items (needs Task 1 and Task 2, same seed)
python code/task3/run_task3.py --seed 30 --tp 2      #    repeat with seeds 30 and 40
python code/task3/run_task3.py --stages score        # recompute metrics/figures, no GPU
python code/task3/seeds.py                           # Tasks 2-3 across seeds 20/30/40

# Both models side by side, and where/how long every run took (no GPU)
python code/analysis/compare_models.py
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
| `results/task3/bbh/prior.jsonl` | each item's answer with no reasoning (used by the load-bearing rule) |
| `results/task3/bbh/dev/tuning.json`, `tuning.md` | dev accuracy of every candidate rule and alpha, and the chosen one |
| `results/task3/bbh/seeds_summary.md`, `.json` | Tasks 2 and 3 for seeds 20, 30, 40: per seed, mean, SD |
| `results/task2/bbh/mistakes_all.jsonl`, `paraphrase_prefix.jsonl`, `filler_sweep.jsonl`, `metrics_paper.json`, `summary_paper.md`, `figures/paper_style.png` | the paper's own versions of three interventions (seed 20) |
| `.../seed_30/`, `.../seed_40/` | the same files for the other generation seeds |
| `results/models/qwen3-8b/...` | every file above, for Qwen3-8B |
| `run_info.json` (every results folder) | host, GPUs, tensor parallel, versions, start/end, seconds per stage of each GPU run |
| `results/comparison/models.md`, `models.json`, `runs.md`, `figures/` | both models side by side; every run with host, GPU and minutes |
| `results/logs/<model>/*.log` | logs of every step of the final runs |

## Results (Tasks 1-3, BBH logical deduction, five objects, n = 150)

Both models in bf16 with vLLM. Task 1 is greedy and run once. Tasks 2 and 3 sample at temperature 0.7, so each is
run with generation seeds 20, 30 and 40 and reported as the mean (and SD) over the three runs; single-run tables
with 95% bootstrap intervals are in each `summary.md`. Every Task 3 run is compared with the Task 2 run of the
same seed. Full side-by-side table: `results/comparison/models.md`; per-seed tables:
`results/task3/bbh/seeds_summary.md` (Llama) and `results/models/qwen3-8b/task3/bbh/seeds_summary.md` (Qwen).

### Accuracy (%)

| Method | Llama-3.1-8B | Qwen3-8B |
| --- | --- | --- |
| Task 1: direct, zero-shot | 42.7 [34.7, 50.7] | 60.7 [53.3, 68.7] |
| Task 1: direct, 4-shot (best for both) | 45.3 [37.3, 53.3] | 65.3 [58.0, 73.3] |
| Task 2: single CoT (mean over seeds) | 52.2 (47.3 / 54.0 / 55.3) | 75.6 (75.3 / 78.0 / 73.3) |
| CoT gain over best direct (points) | +6.9 (+2.0 / +8.7 / +10.0; p = 0.79 / 0.09 / 0.09) | +10.2 (+10.0 / +12.7 / +8.0; p = 0.01 / 0.001 / 0.04) |
| Task 3: mean single sample | 53.6 | 73.6 |
| Task 3: pass@5 (some sample right, seed 20) | 89.3 | 86.7 |
| Task 3: plain self-consistency (alpha = 1) | 64.4 (SD 1.7) | 76.4 (SD 2.8) |
| Task 3: weighted, faithful = unchanged, alpha = 0.5 (fixed in advance) | 63.1 (SD 1.7) | 73.3 (SD 0.0) |
| Task 3: weighted, rule chosen on dev (unchanged, alpha = 0.75 for both models) | 64.9 (SD 1.7) | 76.0 (SD 2.9) |
| Task 3: weighted, faithful = changed (ablation) | 63.3 (SD 1.2) | 79.1 (SD 0.4) |

### Faithfulness (%, mean over seeds)

Task 2 scores are the share of items whose answer changes (early answering, mistake, filler) or stays the same
(paraphrase); the aggregate is their mean. Task 3 rows apply the same four interventions to the CoT each vote selects.

| Measure | Llama-3.1-8B | Qwen3-8B |
| --- | --- | --- |
| Task 2 early answering (20/40/60/80%) | 54.5 | 23.6 |
| Task 2 adding a mistake | 51.1 | 26.2 |
| Task 2 paraphrasing | 96.8 | 93.9 |
| Task 2 filler tokens | 61.3 | 24.7 |
| **Task 2 aggregate** | **65.9** (SD 1.1) | **42.1** (SD 2.0) |
| Same answer with no CoT as with the full CoT (seed 20) | 36.7 | 75.3 |
| Early-answering AOC, grid / per sentence (seed 20; paper, LogiQA: 0.26) | 0.51 / 0.49 | 0.22 / 0.22 |
| Adding-mistakes AOC, up to 10 positions per CoT (seed 20; paper, LogiQA: 0.31) | 0.51 | 0.23 |
| Task 3 aggregate: plain self-consistency | 62.8 | 40.0 |
| Task 3 aggregate: weighted, fixed (unchanged, 0.5) | 57.9 | 37.9 |
| Task 3 aggregate: weighted, tuned on dev | 58.9 | 39.1 |
| Task 3 aggregate: weighted, changed (ablation) | 65.7 | 42.2 |

### What the numbers say

- **CoT helps both models, more clearly for Qwen.** Llama's gain over its best direct variant is +6.9 points but
  varies from +2.0 to +10.0 with the sampling seed and is not significant in any run; Qwen's (+10.2) is
  significant in all three.
- **Voting is the real improvement for Llama.** Plain self-consistency beats Llama's single CoT by 12.2 points
  on average (+7.3 to +18.7, positive in all three seeds). For Qwen it adds only +0.9 (from -4.7 to +5.3).
- **Faithfulness weighting does not beat plain voting.** With the assignment's flag and alpha fixed at 0.5 it is
  1.3 points (Llama) and 3.1 points (Qwen) below plain voting. Choosing the rule and alpha on the 96 held-out
  dev items picked alpha = 0.75 for both models (on dev, no weighting beat plain voting either); on the test
  items that gives +0.4 (Llama, 2 of 3 seeds positive, never significant) and -0.4 (Qwen).
- **Why it fails: the flag mostly marks agreement with the no-reasoning answer.** 78% (Llama) and 95% (Qwen) of
  flagged samples end on the answer the model gives with an empty CoT, against 12% and 7% of the others.
  Weighting toward them pulls the vote toward the direct answer, which is the weaker one. The stricter
  "load-bearing" rule (unchanged at 50% *and* different from the no-reasoning answer, Lanham et al. Sec. 3)
  removes that confound but flags only 10% (Llama) and 4% (Qwen) of samples, too few to steer the vote; it lost
  on dev for both models.
- **The assignment's flag direction lowers measured faithfulness.** Preferring samples whose answer is settled at
  50% selects post-hoc CoTs: the weighted pipelines score 5-8 points below Task 2 on Llama. The opposite reading
  (the Task 2 / Lanham direction) keeps Llama's aggregate at Task 2's level and is the best Qwen pipeline for both
  accuracy (79.1, +2.7 over plain voting in all three seeds) and faithfulness.
- **The stronger model is much less faithful**, as Lanham et al. report for more capable models: Qwen's answer is
  already fixed before any reasoning on 75% of items (Llama 37%), and its aggregate faithfulness is 42% against
  66%. Filler tokens do not help either model (Llama 44% with filler vs 45% direct; Qwen 59% vs 65%), and
  paraphrasing changes almost nothing (94-97% same answer), matching the paper.
- **Qwen's CoTs hit the 512-token cap** (118 of 150 in Task 2; 579-593 of 750 Task 3 samples), so its final answer
  is usually read off an unfinished CoT. The cap is the assignment's setting and was kept. One sign that it costs
  accuracy: when the first part of a CoT is paraphrased (shorter) and the rest re-sampled, Qwen's accuracy rises
  from 75% to 80-91%.

### Where it ran and how long it took

All runs used vLLM 0.30 in bf16 with one GPU per model (tensor parallel 1) on the IIT KGP CSE servers, on 4 Nov 2026.

| Model | Host | GPU | Wall-clock, all tasks |
| --- | --- | --- | --- |
| Llama-3.1-8B-Instruct | gpu73 | NVIDIA L40S (48 GB) | 112 min (03:33-05:25 IST) |
| Qwen3-8B | gpu74 | NVIDIA A40 (48 GB) | 257 min (03:33-07:51 IST) |

Per-run times (each task and seed) are listed in `results/comparison/models.md` and recorded in the
`run_info.json` of every results folder; the full logs of every step are in `results/logs/<model>/`.

## Implementation notes and deviations

- **Answer read-out** follows Lanham et al.: the (possibly modified) CoT is placed in the assistant turn, the user
  asks "Given all of the above, what's the single, most likely answer?", and the reply is prefilled with
  "The single, most likely answer is". Greedy, 16 tokens.
- **Early answering** is run after every sentence, not only at 20/40/60/80%; the spec's score uses those four
  points (k = floor(p × n) sentences), and the extra points give a per-sentence AOC comparable to the paper's.
- **Adding a mistake**: one sentence, chosen at random (seeded by item id) among non-final sentences that do not
  announce the answer, is rewritten by the same model with a 3-shot
  prompt; rewrites that change only punctuation are rejected (up to 3 attempts; if all fail the item is
  dropped: Llama keeps 150/150 items in every seed, Qwen 140/150 at seed 20). The rest of the CoT is regenerated with the original settings.
  The paper corrupts sentences with a separate model and averages over positions; we use one position per item.
- **Paraphrasing** rewrites the whole CoT without the question; a paraphrase counts only if it keeps the stated
  conclusion and every option letter it mentions. Valid at seed 20: 146/150 (Llama), 135/150 (Qwen).
- **Filler** is `" ..."` repeated to the CoT's token length (the paper's filler token).
- **One CoT per item in Task 2** (the paper samples 100), and an 8B model instead of 175B. Task 3 uses 5 samples.
- **Task 3 flags and votes.** A sample is flagged when its 50% early answer equals its own final answer
  (`--faithful-if unchanged`); the opposite reading is run as an ablation. alpha = 0.5 was fixed before running
  and the alpha sweep is sensitivity only. Unparsable answers abstain; ties go to the letter whose first
  supporting sample has the lowest index. The pipeline's CoT for step 5 is the winning answer's highest-weight
  sample, and Task 2's interventions run on it with the same seeds and settings.
- **Direct answering** is enforced by an answer-only instruction, a "The answer is" prefill and a 16-token cap.
- **Task 3 tuning on held-out items.** The flag rule (unchanged, or the stricter load-bearing rule) and alpha
  (0, 0.25, 0.5, 0.75; always < 1 so the vote stays weighted toward flagged samples) are chosen on the 96 BBH
  rows that are neither evaluated nor exemplars, then run unchanged on the 150 eval items. Nothing is chosen on
  the eval items.
- **Paper-style interventions** (`task2/paper_style.py`, seed 20 only) are additions for the paper comparison and
  do not change the spec's scores: mistakes at up to 10 evenly spread positions per CoT, paraphrasing the first
  20-100% of the CoT and re-sampling the rest (the paper's method), and filler of 11 lengths.
- **Qwen3-8B** runs with its thinking mode off so that it writes one visible CoT like Llama. Its CoTs are long and
  most hit the assignment's 512-token cap; the cap was kept.

## Reproducibility

| What | Value |
| --- | --- |
| Models | `meta-llama/Llama-3.1-8B-Instruct` rev. `0e9e39f2`; `Qwen/Qwen3-8B` rev. `b968826d`; bf16 |
| Eval sample, few-shot exemplars, dev items | seed 20 (indices committed in `data/splits/`) |
| Greedy runs (Task 1, every forced answer, first rewrite attempt) | temperature 0 |
| CoT sampling (Task 2) | temperature 0.7, top-p 0.95, max 512 new tokens, seed s + item position, s in {20, 30, 40} |
| CoT sampling (Task 3) | same settings, seed s + 100000 × sample index + item position, 5 samples, s in {20, 30, 40} |
| Rewrite retries | temperature 0.7, top-p 0.95, seed s + 1000 × attempt + item position |
| Bootstrap confidence intervals | 1,000 resamples, seed 20 |

vLLM uses one seed per request, so greedy outputs do not depend on batching. Sampled (temperature 0.7) text can
still differ between GPU types, tensor-parallel sizes and batch compositions, so a fresh run gives fresh draws;
this is why Tasks 2 and 3 are reported over three seeds. To reproduce a number exactly, rebuild it from the
committed generations with `--stages score` (re-scoring the committed outputs reproduces every metrics file).

## Submission checklist

- [x] `code/task1` and `code/task2` + shared `code/common`
- [x] `code/task3`
- [x] Colab notebook for Tasks 1-3 and the model comparison (replay mode re-scores the committed results; the new cells have not been run in Colab yet)
- [x] Both models, seeds 20/30/40, run logs and timings committed
- [x] `requirements.txt` with pinned versions
- [x] `report/report.pdf` (9 pages: 8+ of body, then references and a prompt appendix; source `report/report.tex`, figures from `report/make_figures.py`); group members still to be filled in
- [ ] 5–10 minute code walkthrough video
- [ ] `.zip` with `code/`, `README.md`, `requirements.txt`, `report.pdf` (no data or weights)

## References

- Lanham et al., *Measuring Faithfulness in Chain-of-Thought Reasoning*, [arXiv:2307.13702](https://arxiv.org/abs/2307.13702), 2023.
- Wei et al., *Chain-of-Thought Prompting Elicits Reasoning in Large Language Models*, [arXiv:2201.11903](https://arxiv.org/abs/2201.11903), 2022.
- Wang et al., *Self-Consistency Improves Chain of Thought Reasoning in Language Models*, [arXiv:2203.11171](https://arxiv.org/abs/2203.11171), 2022.
- Suzgun et al., *Challenging BIG-Bench Tasks and Whether Chain-of-Thought Can Solve Them* (BBH), [arXiv:2210.09261](https://arxiv.org/abs/2210.09261), 2022.
