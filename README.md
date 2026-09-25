# Chain-of-Thought Faithfulness — CS60075 Assignment 2, Project 8

Does a language model's written chain-of-thought (CoT) actually explain how it reached its answer, or is it a
plausible story written afterwards? This repo measures that for an open 8B instruction-tuned model, reproduces the
intervention methodology of Lanham et al. (2023), and tests whether faithfulness can be used to improve
self-consistency voting.

**Author:** Parag Chimankar (23CS10049), IIT Kharagpur — CS60075 Natural Language Processing
**Group members:** _to be added_
**Assigned dataset:** _to be confirmed with the TA_ (the code supports all three via one flag)

> **Status (2026-09-25):** repository, environment plan and datasets are set up. Task code is not written yet;
> commands under "How to run" show the planned interface.

---

## The three tasks

| Task | Marks | What it does | Metrics reported |
| --- | --- | --- | --- |
| 1. Direct answering baseline | 30 | Answer with no reasoning, zero-shot and 4-shot, greedy decoding | Accuracy (zero-shot, 4-shot) |
| 2. Paper reproduction | 30 | Standard CoT, then four interventions on it: early answering, adding a mistake, paraphrasing, filler tokens | CoT accuracy gain over Task 1; faithfulness score per intervention |
| 3. Combine & improve | 40 | Sample 5 CoTs, check each with 50% early answering, weight the majority vote toward "faithful" samples | Accuracy vs Tasks 1 and 2; aggregate faithfulness vs Task 2 |

The assignment gives each group **one** of the three datasets below; all three tasks are run on that one dataset.

## Model

| Role | Checkpoint | Source |
| --- | --- | --- |
| Main model | `meta-llama/Llama-3.1-8B-Instruct` | https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct (gated: accept Meta's licence on the page first) |
| Fallback if access is delayed | `Qwen/Qwen2.5-7B-Instruct` | https://huggingface.co/Qwen/Qwen2.5-7B-Instruct (not gated) |

Only the `*.safetensors`, `*.json` and tokenizer files are downloaded; the `original/` folder is skipped.

## Repository layout

```
cs60075-cot-faithfulness/
├── README.md
├── requirements.txt            # pinned versions (added after the environment is built)
├── code/
│   ├── CoT_Faithfulness_Colab.ipynb   # end-to-end notebook: setup → Task 1 → Task 2 → Task 3
│   ├── common/                 # shared: config, data, prompts, model backend, parsing, metrics, cache
│   ├── task1/                  # direct-answer baseline
│   ├── task2/                  # CoT generation + four faithfulness interventions
│   └── task3/                  # faithfulness-weighted self-consistency
├── data/
│   ├── MANIFEST.md             # pinned revisions, row counts, SHA-256 checksums
│   ├── raw/                    # downloaded parquet files (gitignored)
│   ├── processed/              # normalised eval / few-shot JSONL (gitignored)
│   └── splits/                 # exact eval and few-shot indices (committed)
├── results/task1|task2|task3/  # generations (JSONL) and metrics (JSON) per dataset
├── report/                     # report.pdf and figures
└── scripts/cluster/            # how to run on the IIT KGP GPU servers
```

## Environment setup

### Option A — Google Colab (end-to-end, recommended for graders)

1. Open `code/CoT_Faithfulness_Colab.ipynb` in Colab (browser), or in VS Code with the **Google Colab** extension
   (`Google.colab`): *Select Kernel → Colab →* sign in → choose a GPU runtime.
2. Add a Hugging Face read token as the Colab secret `HF_TOKEN` (the account must have Llama access).
3. Run all cells. Setting `REUSE_RESULTS = True` rebuilds every table from the committed generations in minutes.

A free T4 (~15 GB) cannot hold the 8B model in 16-bit, so the notebook loads it in 4-bit NF4 there and in bf16 on
L4 / A100. The headline numbers in the report come from bf16 runs on the KGP GPU servers.

### Option B — IIT KGP CSE GPU servers

See `scripts/cluster/README.md`. In short: log in through `10.5.18.114`, run on `gpu73` (L40S) or `gpu74` (A40) with
`CUDA_VISIBLE_DEVICES` pinned to a card with at least 20 GB free, and launch long jobs with `setsid nohup`.

```bash
conda create -n cotfaith python=3.10 -y -c conda-forge --override-channels
conda activate cotfaith
pip install -r requirements.txt
export HF_TOKEN=<your read token>
```

### VS Code

Recommended extensions are listed in `.vscode/extensions.json` (Python, Jupyter, Google Colab, Remote-SSH).

## Datasets — download and prepare (all three)

| Name used here | Hub repo | Config / split | Rows | Used for |
| --- | --- | --- | --- | --- |
| `gsm8k` | [`openai/gsm8k`](https://huggingface.co/datasets/openai/gsm8k) | `main` / `test` (+ `train` for exemplars) | 1,319 (+7,473) | eval n = 200 from test; 4 exemplars from train |
| `bbh` | [`maveriq/bigbenchhard`](https://huggingface.co/datasets/maveriq/bigbenchhard) | `logical_deduction_five_objects` / `train` | 250 | eval n = 150; 4 exemplars from the remaining 100 |
| `strategyqa` | [`wics/strategy-qa`](https://huggingface.co/datasets/wics/strategy-qa) | `strategyQA` / `test` | 2,290 | eval n = 150; 4 exemplars from disjoint indices |

BBH and StrategyQA are loading-script repos, which `datasets` 4.x refuses to run, so we download the Hub's
auto-converted parquet files at pinned revisions:

```bash
mkdir -p data/raw/{gsm8k,bbh_logical_deduction_five_objects,strategyqa}
HF=https://huggingface.co/datasets
curl -L -o data/raw/gsm8k/train.parquet  $HF/openai/gsm8k/resolve/740312add88f781978c0658806c59bc2815b9866/main/train-00000-of-00001.parquet
curl -L -o data/raw/gsm8k/test.parquet   $HF/openai/gsm8k/resolve/740312add88f781978c0658806c59bc2815b9866/main/test-00000-of-00001.parquet
curl -L -o data/raw/bbh_logical_deduction_five_objects/train.parquet \
  $HF/maveriq/bigbenchhard/resolve/a493490a030bfe06c7baa2db022263afbfa04cfb/logical_deduction_five_objects/train/0000.parquet
curl -L -o data/raw/strategyqa/test.parquet \
  $HF/wics/strategy-qa/resolve/c9a25e4b10d32364d25f1f1387bf445921b6e75e/strategyQA/test/0000.parquet
(cd data && sha256sum raw/*/*.parquet)   # compare with data/MANIFEST.md
```

Preprocessing (done by `code/common/data.py`, planned):

- **GSM8K:** gold = number after `####`; strip `$` and commas before comparing.
- **BBH:** options parsed from `input` with one regex; gold = the letter in `target`, e.g. `(A)`.
- **StrategyQA:** `answer` is a bool → `Yes` / `No`; `facts` and `decomposition` are never shown to the model.

## How to run (planned interface)

```bash
# Task 1 — direct answering
python code/task1/run_direct.py   --dataset gsm8k --shots 0
python code/task1/run_direct.py   --dataset gsm8k --shots 4

# Task 2 — CoT + four interventions
python code/task2/generate_cot.py  --dataset gsm8k
python code/task2/interventions.py --dataset gsm8k --which all
python code/task2/score.py         --dataset gsm8k

# Task 3 — faithfulness-weighted self-consistency
python code/task3/sample_k.py      --dataset gsm8k --k 5
python code/task3/weighted_vote.py --dataset gsm8k --faithful-if unchanged --alpha 0.5
python code/task3/evaluate.py      --dataset gsm8k
```

Scripts are run by path: `code/` is deliberately not a Python package, because that name would shadow Python's built-in `code` module.
Each task can run on its own (it reads earlier results from `results/` when it needs them) or in sequence via the notebook.

## Outputs

`results/task{1,2,3}/<dataset>/` holds every generation as JSONL (prompt, settings, seed, raw output, parsed answer)
and a `metrics.json` per stage. Plots for the report go to `report/figures/`.

## Reproducibility

| What | Value |
| --- | --- |
| Eval sample and few-shot exemplars | seed 42 |
| Greedy runs (Task 1, forced answers) | temperature 0 |
| CoT sampling (Tasks 2, 3) | temperature 0.7, top-p 0.95, max 512 new tokens, seed 42 + item index (+ 1000 × sample index in Task 3) |
| Bootstrap confidence intervals | 1,000 resamples, seed 42 |

## Submission checklist

- [ ] `code/task1`, `code/task2`, `code/task3` + shared `code/common`
- [ ] End-to-end Colab notebook
- [ ] `requirements.txt` with pinned versions
- [ ] `report.pdf` (8–12 pages) with the Task 2 paper-comparison section
- [ ] 5–10 minute code walkthrough video
- [ ] `.zip` with `code/`, `README.md`, `requirements.txt`, `report.pdf` (no data or weights)

## References

- Lanham et al., *Measuring Faithfulness in Chain-of-Thought Reasoning*, [arXiv:2307.13702](https://arxiv.org/abs/2307.13702), 2023.
- Wei et al., *Chain-of-Thought Prompting Elicits Reasoning in Large Language Models*, [arXiv:2201.11903](https://arxiv.org/abs/2201.11903), 2022.
- Wang et al., *Self-Consistency Improves Chain of Thought Reasoning in Language Models*, [arXiv:2203.11171](https://arxiv.org/abs/2203.11171), 2022.
- Cobbe et al., *Training Verifiers to Solve Math Word Problems* (GSM8K), [arXiv:2110.14168](https://arxiv.org/abs/2110.14168), 2021.
- Suzgun et al., *Challenging BIG-Bench Tasks and Whether Chain-of-Thought Can Solve Them* (BBH), [arXiv:2210.09261](https://arxiv.org/abs/2210.09261), 2022.
- Geva et al., *Did Aristotle Use a Laptop? A Question Answering Benchmark with Implicit Reasoning Strategies* (StrategyQA), TACL 2021.
