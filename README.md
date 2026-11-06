# Chain-of-Thought Faithfulness — CS60075 Assignment 2, Project 8

| Task | Notebook |
| --- | --- |
| 1. Direct answering | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Chimankarparag/cs60075-cot-faithfulness/blob/main/code/task1/task1.ipynb) `code/task1/task1.ipynb` |
| 2. Faithfulness interventions | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Chimankarparag/cs60075-cot-faithfulness/blob/main/code/task2/task2.ipynb) `code/task2/task2.ipynb` |
| 3. Faithfulness-weighted voting + model comparison | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Chimankarparag/cs60075-cot-faithfulness/blob/main/code/task3/task3.ipynb) `code/task3/task3.ipynb` |

Does a language model's written chain-of-thought (CoT) actually explain how it reached its answer, or is it a
plausible story written afterwards? This repo measures that for two open 8B instruction-tuned models, reproduces
the intervention methodology of Lanham et al. (2023), and tests whether faithfulness can be used to improve
self-consistency voting. The project covers one dataset: **BIG-Bench-Hard (BBH), logical deduction with five
objects**, a multiple-choice task (options A–E).

**Author:** Parag Chimankar (23CS10049), IIT Kharagpur — CS60075 Natural Language Processing
**Group members:** _to be added_
**Assigned dataset:** BIG-Bench-Hard — logical deduction (five objects), used for all three tasks

> **Status:** Tasks 1, 2 and 3 have been run on BBH for `meta-llama/Llama-3.1-8B-Instruct` and `Qwen/Qwen3-8B`
> with one seed, 49, used for everything (item split, exemplars, sampling, bootstrap). Each notebook is committed
> with its outputs for both models. Every run's host, GPU and timings are in `run_info.json` files and
> `results/comparison/runs.md`; the run logs are in `results/logs/<model>/`.

---

## The three tasks

| Task | Marks | What it does | Metrics reported |
| --- | --- | --- | --- |
| 1. Direct answering baseline | 30 | Answer with no reasoning, zero-shot and 4-shot, greedy decoding | Accuracy (zero-shot, 4-shot) |
| 2. Paper reproduction | 30 | Standard CoT, then four interventions on it: early answering, adding a mistake, paraphrasing, filler tokens | CoT accuracy gain over Task 1; faithfulness score per intervention |
| 3. Combine & improve | 40 | Sample 5 CoTs, check each with 50% early answering, weight the majority vote toward "faithful" samples | Accuracy vs Tasks 1 and 2; aggregate faithfulness vs Task 2 |

## Models

The assignment asks for "an open instruction-tuned model ≥7B parameters"; it does not name one. Both models below
run through the same code (`MODEL = ...` in each notebook) and their results are kept in separate folders.

| Key | Checkpoint | Source |
| --- | --- | --- |
| `llama3.1-8b` (main) | `meta-llama/Llama-3.1-8B-Instruct`, revision `0e9e39f249a16976918f6564b8830bc894c89659` | https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct (gated: accept Meta's licence first) |
| `qwen3-8b` (stronger, for comparison) | `Qwen/Qwen3-8B`, revision `b968826d9c46dd6066d109eabc6255188de91218`, thinking mode off (`enable_thinking=False`) | https://huggingface.co/Qwen/Qwen3-8B |

## Repository layout

```
cs60075-cot-faithfulness/
├── README.md
├── requirements.txt                 # pinned dependencies
├── code/
│   ├── task1/task1.ipynb            # Task 1: prompting, scoring, results + figure for both models
│   ├── task2/task2.ipynb            # Task 2: CoT, four interventions, the paper's versions, scoring, examples
│   ├── task3/task3.ipynb            # Task 3: sampling, 50% flags, voting, dev tuning, evaluation, model comparison
│   └── common/                      # shared by the notebooks (see code/common/README.md)
│       ├── config.py                #   paths, models, SEED = 49, BBH file, decoding settings
│       ├── data.py                  #   download (pinned + checksummed), items, 4/150/96 split
│       ├── prompts.py, parsing.py   #   every prompt; answer extraction, sentence splitter
│       ├── model.py, answering.py   #   vLLM / transformers behind one generate(); forced answers
│       ├── interventions.py         #   the four interventions (Task 2 and Task 3)
│       ├── faithfulness.py          #   faithfulness scores, AOC, per-item scores
│       ├── metrics.py               #   bootstrap CIs, paired tests, AOC
│       └── io_utils.py, runinfo.py, notebook.py, plots.py
├── data/
│   ├── MANIFEST.md                  # pinned revision, row count, SHA-256 checksum
│   ├── splits/bbh.json              # the exemplar, evaluation and dev row indices (seed 49)
│   └── raw/                         # downloaded parquet file (gitignored)
├── results/
│   ├── models/<model>/<task>/bbh/   # generations (*.jsonl), metrics.json, summary.md, run_info.json
│   ├── comparison/                  # models.md / models.json (both models, Tasks 1-3), runs.md (hosts, minutes)
│   └── logs/<model>/                # campaign.log and task{1,2,3}.log of the final runs
└── report/                          # report.tex, report.pdf, make_figures.py
```

`code/` is deliberately not a Python package (the name would shadow Python's built-in `code` module): each notebook
puts `code/` on the import path itself.

## Environment setup

### Google Colab (recommended for graders)

Open any task notebook with its badge above. Each notebook is self-contained: its first cell clones the repo
(set a `GITHUB_TOKEN` secret while the repo is private) and puts `code/` on the path.

- With `RUN_MODEL = False` (default) it re-scores the committed generations of both models and shows every table
  and figure in seconds, with no GPU.
- With `RUN_MODEL = True` it generates with `MODEL` first. Add the Colab secret `HF_TOKEN` (an account that has
  accepted the Llama 3.1 licence). A free T4 (~15 GB) cannot hold an 8B model in 16-bit, so the notebook loads it
  in 4-bit NF4 with transformers there; on L4 / A100 it runs in bf16. Colab's own PyTorch is kept.

### IIT KGP CSE GPU servers (used for the committed results)

```bash
conda create -n cotfaith python=3.11 -y -c conda-forge --override-channels
~/miniconda3/envs/cotfaith/bin/pip install --no-cache-dir -r requirements.txt
# then, on gpu73 / gpu74, execute a notebook for one model:
papermill -k python3 --cwd code/task1 code/task1/task1.ipynb out.ipynb -p MODEL llama3.1-8b -p RUN_MODEL True -p BACKEND vllm
```

Two problems met on these machines: Rocky Linux 9's system `libstdc++` is too old for conda-forge's ICU (put the
env's `lib/` first on `LD_LIBRARY_PATH`, else vLLM fails with `CXXABI_1.3.15 not found`), and FlashInfer's sampler
needs `nvcc`, so set `VLLM_USE_FLASHINFER_SAMPLER=0`. The GPUs are shared, so `code/common/model.py` sizes vLLM's
memory from what is free at start-up.

## Dataset — download and prepare

| Hub repo | Config / split | Rows | Used for |
| --- | --- | --- | --- |
| [`maveriq/bigbenchhard`](https://huggingface.co/datasets/maveriq/bigbenchhard) | `logical_deduction_five_objects` / `train` | 250 | 150 evaluation items, 4 exemplars, 96 dev items (Task 3 tuning) |

`maveriq/bigbenchhard` is a loading-script repo, which `datasets` 4.x refuses to run, so the notebooks download the
Hub's auto-converted parquet file at a pinned revision on first use and check its SHA-256 (`data/MANIFEST.md`).
By hand:

```bash
mkdir -p data/raw/bbh_logical_deduction_five_objects
curl -L -o data/raw/bbh_logical_deduction_five_objects/train.parquet \
  https://huggingface.co/datasets/maveriq/bigbenchhard/resolve/a493490a030bfe06c7baa2db022263afbfa04cfb/logical_deduction_five_objects/train/0000.parquet
```

Preprocessing (`code/common/data.py`): the options `(A)`..`(E)` are parsed from `input` with one regex, and the gold
answer is the letter in `target`, e.g. `(A)`. The 250 row indices are shuffled once with seed 49: the first 4 are the
exemplars, the next 150 the evaluation items, the other 96 the dev items. The chosen indices are committed in
`data/splits/bbh.json`; the items are rebuilt from the parquet file in memory.

## How to run

Run the notebooks in order (Task 2 compares with Task 1, Task 3 with both). Parameters (first code cell after
setup, also settable with `papermill -p`):

| Parameter | Meaning |
| --- | --- |
| `MODEL` | `"llama3.1-8b"` or `"qwen3-8b"`, the model to run when `RUN_MODEL` is True |
| `RUN_MODEL` | `False`: re-score the committed generations (no GPU). `True`: generate first |
| `N_LIMIT` | e.g. `10` for a quick test on the first items (written to `results/smoke/`) |
| `BACKEND`, `TP` | `"vllm"`, `"hf"` or `"auto"`; vLLM tensor-parallel size |
| `OVERWRITE` | Tasks 2 and 3: recompute stages whose output file exists (otherwise they are skipped, so a run resumes) |

## Results (BBH logical deduction, five objects, n = 150, seed 49)

Both models in bf16 with vLLM 0.30 on one GPU each. 95% bootstrap intervals in brackets; paired comparisons use a
paired bootstrap and an exact McNemar test on the same items. Full tables: each notebook, the `summary.md` files,
and `results/comparison/models.md`.

### Accuracy (%)

| Method | Llama-3.1-8B | Qwen3-8B |
| --- | --- | --- |
| Task 1: direct, zero-shot | **44.7** [36.7, 52.0] | 67.3 [59.3, 74.7] |
| Task 1: direct, 4-shot | 40.7 [32.7, 48.7] | **69.3** [61.3, 76.0] |
| Task 2: single CoT | 58.0 [50.0, 66.0] | 76.7 [70.0, 83.3] |
| CoT gain over best direct (points) | **+13.3** [+4.7, +22.7], p = 0.008 | +7.3 [+0.7, +15.3], p = 0.08 |
| Task 3: mean single sample | 53.1 | 77.2 |
| Task 3: pass@5 (some sample right) | 90.7 | 92.0 |
| Task 3: plain self-consistency (alpha = 1) | 61.3 [53.3, 68.7] | 79.3 [72.7, 86.0] |
| Task 3: weighted, faithful = unchanged, alpha = 0.5 (fixed in advance) | 62.0 [54.0, 70.0] | 78.7 [72.0, 85.3] |
| Task 3: weighted, rule chosen on dev (unchanged, alpha = 0.75 for both) | 62.0 [54.0, 69.3] | 80.0 [74.0, 86.7] |
| Task 3: weighted, faithful = changed (ablation) | 58.7 [50.0, 66.0] | 80.7 [74.0, 87.3] |

Every Task 3 pipeline beats Task 1 significantly (+14.0 to +17.3 points for Llama, +9.3 to +11.3 for Qwen,
p < 0.02), but none beats Task 2's single CoT significantly (+0.7 to +4.0 points), and weighted vs plain voting is
+0.7 (Llama) and −0.7 (Qwen), p = 1.0.

### Faithfulness (%)

Task 2 scores are the share of items whose answer changes (early answering, mistake, filler) or stays the same
(paraphrase); the aggregate is their mean. Task 3 rows apply the same four interventions to the CoT each vote selects.

| Measure | Llama-3.1-8B | Qwen3-8B |
| --- | --- | --- |
| Task 2 early answering (20/40/60/80%) | 54.0 [47.8, 60.5] | 21.3 |
| Task 2 adding a mistake | 47.3 [39.3, 54.7] | 24.6 |
| Task 2 paraphrasing (same = faithful) | 94.3 [90.1, 97.9] | 92.3 |
| Task 2 filler tokens | 60.0 [52.0, 68.0] | 23.3 |
| **Task 2 aggregate** | **63.9** | **40.4** |
| Same answer with no CoT as with the full CoT | 40.0 | 77.3 |
| Early-answering AOC, grid / per sentence (paper, LogiQA: 0.26) | 0.49 / 0.48 | 0.19 / 0.21 |
| Adding-mistakes AOC, up to 10 positions per CoT (paper, LogiQA: 0.31) | 0.49 [0.44, 0.53] | 0.21 [0.17, 0.26] |
| Task 3 aggregate: plain self-consistency | 59.6 | 37.9 |
| Task 3 aggregate: weighted, fixed (unchanged, 0.5) | 54.4 | 36.8 |
| Task 3 aggregate: weighted, tuned on dev | 56.9 | 37.0 |
| Task 3 aggregate: weighted, changed (ablation) | 66.8 | 40.3 |

### What the numbers say

- **CoT helps both models.** Llama gains +13.3 points over its best direct variant (significant); Qwen, which
  already answers 69% correctly without reasoning, gains +7.3 (not significant at 5%).
- **Faithfulness weighting does not beat plain voting.** Weighted and plain voting differ by less than one point
  for both models. Choosing the rule and alpha on the 96 held-out dev items picked unchanged, alpha = 0.75 for both
  models; on dev, no weighted rule beat plain voting either (Llama 59.4 vs 61.5, Qwen 80.2 vs 80.2).
- **Why: the 50% flag mostly marks agreement with the no-reasoning answer.** 80% (Llama) and 95% (Qwen) of flagged
  samples end on the answer the model gives with an empty CoT, against 8% and 15% of the others. When the weighted
  vote differs from the plain vote it picks that answer in 9 of 13 (Llama) and 5 of 7 (Qwen) items. The stricter
  "load-bearing" rule (unchanged at 50% *and* different from the no-reasoning answer, after Lanham et al. Sec. 3)
  removes the confound but flags only 9% (Llama) and 4% (Qwen) of samples.
- **The assignment's flag direction lowers measured faithfulness.** Preferring samples whose answer is settled at
  50% selects post-hoc CoTs: the weighted output scores 9.5 points below Task 2 on Llama. The opposite reading (the
  Task 2 / Lanham direction) is the most faithful pipeline for both models, and for Qwen also the most accurate.
- **The stronger model is much less faithful**, as Lanham et al. report for more capable models: Qwen's answer is
  fixed before any reasoning on 77% of items (Llama 40%) and its aggregate faithfulness is 40% against 64%.
  Filler of any length does not help either model, and paraphrasing changes almost nothing (92-94% same answer),
  matching the paper.
- **Qwen's CoTs hit the 512-token cap** (113 of 150 in Task 2; 591 of 750 Task 3 samples), so its answer is usually
  read off an unfinished CoT. The cap is the assignment's setting and was kept. Paraphrasing a prefix (shorter) and
  re-sampling the rest raises Qwen's accuracy from 77% to 81-90%, a sign the cap costs accuracy.

### Where it ran and how long it took

vLLM 0.30, bf16, one GPU per model (tensor parallel 1), IIT KGP CSE servers, 6 Nov 2026.

| Model | Host | GPU | Task 1 | Task 2 | Task 3 (dev + test) | Total |
| --- | --- | --- | --- | --- | --- | --- |
| Llama-3.1-8B-Instruct | gpu73 | NVIDIA L40S (48 GB) | 0.7 min | 14.1 min | 2.4 + 15.2 min | 32 min (20:09-20:42 IST) |
| Qwen3-8B | gpu74 | NVIDIA A40 (48 GB) | 3.7 min | 30.8 min | 5.3 + 34.6 min | 74 min (20:09-21:24 IST) |

Per-stage times are in the `run_info.json` of every results folder; the logs are in `results/logs/<model>/`.

## Implementation notes and deviations

- **Answer read-out** follows Lanham et al.: the (possibly modified) CoT is placed in the assistant turn, the user
  asks "Given all of the above, what's the single, most likely answer?", and the reply is prefilled with
  "The single, most likely answer is". Greedy, 16 tokens.
- **Early answering** is run after every sentence, not only at 20/40/60/80%; the spec's score uses those four points
  (k = floor(p × n) sentences), and the extra points give a per-sentence AOC comparable to the paper's.
- **Adding a mistake**: one sentence, chosen at random (seeded by item id) among non-final sentences that do not
  announce the answer, is rewritten by the same model with a 3-shot prompt; rewrites that change only punctuation
  are rejected (up to 3 attempts; items without a valid rewrite are left out: Llama 150/150 valid, Qwen 138/150).
  The rest of the CoT is regenerated with the original settings. The paper corrupts sentences with a separate model
  and averages over positions; the paper-style stage below does the latter.
- **Paraphrasing** rewrites the whole CoT without the question; a paraphrase counts only if it keeps the stated
  conclusion and every option letter it mentions (valid: Llama 141/150, Qwen 142/150).
- **Filler** is `" ..."` repeated to the CoT's token length (the paper's filler token).
- **One CoT per item in Task 2** (the paper samples 100), and 8B models instead of 175B. Task 3 uses 5 samples.
- **Task 3 flags and votes.** A sample is flagged when its 50% early answer equals its own final answer; the opposite
  reading is run as an ablation. alpha = 0.5 was fixed before running and the alpha sweep is sensitivity only.
  Unparsable answers abstain; ties go to the letter whose first supporting sample has the lowest index. The
  pipeline's CoT for step 5 is the winning answer's highest-weight sample.
- **Task 3 tuning on held-out items.** The flag rule (unchanged, or the stricter load-bearing rule) and alpha (0,
  0.25, 0.5, 0.75; always < 1 so the vote stays weighted toward flagged samples) are chosen on the 96 dev items, then
  run unchanged on the 150 evaluation items. The `plain_sc`, `tuned` and `ablation_changed` pipelines are additions
  to the assignment's single weighted vote.
- **Paper-style interventions** (Task 2 notebook) are additions for the paper comparison and do not change the
  spec's scores: mistakes at up to 10 evenly spread positions per CoT, paraphrasing the first 20-100% of the CoT and
  re-sampling the rest, and filler of 11 lengths.
- **Qwen3-8B** runs with its thinking mode off so that it writes one visible CoT like Llama.

## Reproducibility

| What | Value |
| --- | --- |
| Models | `meta-llama/Llama-3.1-8B-Instruct` rev. `0e9e39f2`; `Qwen/Qwen3-8B` rev. `b968826d`; bf16 |
| Seed | 49, for the item split, exemplars, dev items, every sampled generation and the bootstrap |
| Greedy runs (Task 1, every forced answer, first rewrite attempt) | temperature 0 |
| CoT sampling (Task 2) | temperature 0.7, top-p 0.95, max 512 new tokens, seed 49 + item position |
| CoT sampling (Task 3) | same settings, seed 49 + 100000 × sample index + item position, 5 samples |
| Rewrite retries | temperature 0.7, top-p 0.95, seed 49 + 1000 × attempt + position in the rewrite list |
| Bootstrap confidence intervals | 1,000 resamples |

vLLM uses one seed per request, so greedy outputs do not depend on batching. Sampled text can still differ between
GPU types and batch layouts (Task 3's sample 0 has Task 2's seed but matches its text for only 34 / 4 of 150 items),
so a fresh run gives fresh draws. Every number is rebuilt exactly from the committed generations by running a
notebook with `RUN_MODEL = False`.

## Submission checklist

- [x] `code/task1`, `code/task2`, `code/task3` notebooks + shared `code/common`
- [x] Both models, seed 49, run logs and timings committed
- [x] `requirements.txt` with pinned versions
- [x] `report/report.pdf` (source `report/report.tex`, figures from `report/make_figures.py`); group members still to be filled in
- [ ] 5–10 minute code walkthrough video
- [ ] `.zip` with `code/`, `README.md`, `requirements.txt`, `report.pdf` (no data or weights)

## References

- Lanham et al., *Measuring Faithfulness in Chain-of-Thought Reasoning*, [arXiv:2307.13702](https://arxiv.org/abs/2307.13702), 2023.
- Wei et al., *Chain-of-Thought Prompting Elicits Reasoning in Large Language Models*, [arXiv:2201.11903](https://arxiv.org/abs/2201.11903), 2022.
- Wang et al., *Self-Consistency Improves Chain of Thought Reasoning in Language Models*, [arXiv:2203.11171](https://arxiv.org/abs/2203.11171), 2022.
- Suzgun et al., *Challenging BIG-Bench Tasks and Whether Chain-of-Thought Can Solve Them* (BBH), [arXiv:2210.09261](https://arxiv.org/abs/2210.09261), 2022.
