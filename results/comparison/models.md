# Model comparison on BBH logical deduction (five objects), n = 150, seed 49

Same items, prompts, decoding settings and code for every model; only the checkpoint differs.

## Accuracy (%)

| | meta-llama/Llama-3.1-8B-Instruct | Qwen/Qwen3-8B |
| --- | --- | --- |
| Task 1 zero-shot | 44.7 | 67.3 |
| Task 1 4-shot | 40.7 | 69.3 |
| Task 2 single CoT | 58.0 | 76.7 |
| CoT gain over best direct (points) | +13.3 [+4.7, +22.7] | +7.3 [+0.7, +15.3] |
| Task 3 pass@5 (some sample right) | 90.7 | 92.0 |
| Task 3 plain self-consistency | 61.3 | 79.3 |
| Task 3 weighted (unchanged, alpha 0.5) | 62.0 | 78.7 |
| Task 3 weighted, tuned on dev | 62.0 (unchanged, alpha 0.75) | 80.0 (unchanged, alpha 0.75) |
| Task 3 weighted (changed, ablation) | 58.7 | 80.7 |

## Faithfulness (%)

| | meta-llama/Llama-3.1-8B-Instruct | Qwen/Qwen3-8B |
| --- | --- | --- |
| Task 2 Early answering | 54.0 | 21.3 |
| Task 2 Adding a mistake | 47.3 | 24.6 |
| Task 2 Paraphrasing | 94.3 | 92.3 |
| Task 2 Filler tokens | 60.0 | 23.3 |
| Task 2 aggregate | 63.9 | 40.4 |
| Task 2 early-answering AOC (grid / per-sentence) | 0.49 / 0.48 | 0.19 / 0.21 |
| Same answer with no CoT as with the CoT | 40.0 | 77.3 |
| Adding mistakes AOC, many positions (paper: LogiQA 0.31) | 0.49 | 0.21 |
| Task 3 aggregate, plain_sc | 59.6 | 37.9 |
| Task 3 aggregate, weighted | 54.4 | 36.8 |
| Task 3 aggregate, tuned | 56.9 | 37.0 |
| Task 3 aggregate, ablation_changed | 66.8 | 40.3 |

## The 50% flag (Task 3)

| | meta-llama/Llama-3.1-8B-Instruct | Qwen/Qwen3-8B |
| --- | --- | --- |
| Share of samples flagged (unchanged) | 48.0 | 77.9 |
| Accuracy flagged / other | 71.7 / 35.9 | 79.5 / 69.3 |
| Flagged / other equal to the no-reasoning answer | 80.3 / 7.9 | 94.5 / 14.5 |
| Weighted vs plain disagree: items / weighted picks no-reasoning answer | 13 / 9 | 7 / 5 |
| ... of those, weighted right / plain right | 4 / 3 | 3 / 4 |

## CoT shape

| | meta-llama/Llama-3.1-8B-Instruct | Qwen/Qwen3-8B |
| --- | --- | --- |
| Sentences / tokens per CoT | 12.2 / 211 | 42.7 / 493 |
| CoTs that hit the 512-token cap | 6 | 113 |

## Where each run ran and how long it took

| Model | Results folder | Host | GPUs (tp) | Started | Minutes | Status |
| --- | --- | --- | --- | --- | --- | --- |
| meta-llama/Llama-3.1-8B-Instruct | `results/models/llama3.1-8b/task1/bbh` | gpu73.cse.iitkgp | NVIDIA L40S (1) | 2026-11-06T20:09:12+05:30 | 0.7 | ok |
| meta-llama/Llama-3.1-8B-Instruct | `results/models/llama3.1-8b/task2/bbh` | gpu73.cse.iitkgp | NVIDIA L40S (1) | 2026-11-06T20:09:59+05:30 | 14.1 | ok |
| meta-llama/Llama-3.1-8B-Instruct | `results/models/llama3.1-8b/task3/bbh/dev` | gpu73.cse.iitkgp | NVIDIA L40S (1) | 2026-11-06T20:24:12+05:30 | 2.4 | ok |
| meta-llama/Llama-3.1-8B-Instruct | `results/models/llama3.1-8b/task3/bbh` | gpu73.cse.iitkgp | NVIDIA L40S (1) | 2026-11-06T20:26:33+05:30 | 15.2 | ok |
| Qwen/Qwen3-8B | `results/models/qwen3-8b/task1/bbh` | gpu74.cse.iitkgp | NVIDIA A40 (1) | 2026-11-06T20:09:20+05:30 | 3.7 | ok |
| Qwen/Qwen3-8B | `results/models/qwen3-8b/task2/bbh` | gpu74.cse.iitkgp | NVIDIA A40 (1) | 2026-11-06T20:13:11+05:30 | 30.8 | ok |
| Qwen/Qwen3-8B | `results/models/qwen3-8b/task3/bbh/dev` | gpu74.cse.iitkgp | NVIDIA A40 (1) | 2026-11-06T20:44:15+05:30 | 5.3 | ok |
| Qwen/Qwen3-8B | `results/models/qwen3-8b/task3/bbh` | gpu74.cse.iitkgp | NVIDIA A40 (1) | 2026-11-06T20:49:33+05:30 | 34.6 | ok |

Total GPU wall-clock per model: meta-llama/Llama-3.1-8B-Instruct 32 min; Qwen/Qwen3-8B 74 min.

