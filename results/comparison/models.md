# Model comparison on BBH logical deduction (five objects), n = 150

Same items, prompts, decoding settings and code for every model; only the checkpoint differs. Single-run rows use generation seed 20.

## Accuracy (%)

| | meta-llama/Llama-3.1-8B-Instruct | Qwen/Qwen3-8B |
| --- | --- | --- |
| Task 1 zero-shot | 42.7 | 60.7 |
| Task 1 4-shot | 45.3 | 65.3 |
| Task 2 single CoT | 47.3 | 75.3 |
| CoT gain over best direct (points) | +2.0 [-8.0, +11.3] | +10.0 [+2.7, +17.3] |
| Task 3 pass@5 (some sample right) | 89.3 | 86.7 |
| Task 3 plain self-consistency | 66.0 | 77.3 |
| Task 3 weighted (unchanged, alpha 0.5) | 64.7 | 73.3 |
| Task 3 weighted, tuned on dev | 66.7 (unchanged, alpha 0.75) | 77.3 (unchanged, alpha 0.75) |
| Task 3 weighted (changed, ablation) | 62.7 | 79.3 |

## Mean over the generation seeds 20/30/40 (SD in points)

The rows above are the seed-20 runs; these average all three.

| | meta-llama/Llama-3.1-8B-Instruct | Qwen/Qwen3-8B |
| --- | --- | --- |
| Task 2 single CoT accuracy | 52.2 (SD 4.3) | 75.6 (SD 2.3) |
| Task 2 aggregate faithfulness | 65.9 (SD 1.1) | 42.1 (SD 2.0) |
| Task 3 plain_sc | 64.4 (SD 1.7) | 76.4 (SD 2.8) |
| Task 3 weighted | 63.1 (SD 1.7) | 73.3 (SD 0.0) |
| Task 3 tuned | 64.9 (SD 1.7) | 76.0 (SD 2.9) |
| Task 3 ablation_changed | 63.3 (SD 1.2) | 79.1 (SD 0.4) |

## Faithfulness (%)

| | meta-llama/Llama-3.1-8B-Instruct | Qwen/Qwen3-8B |
| --- | --- | --- |
| Task 2 Early answering | 56.0 | 24.5 |
| Task 2 Adding a mistake | 49.3 | 28.6 |
| Task 2 Paraphrasing | 96.6 | 94.8 |
| Task 2 Filler tokens | 64.0 | 24.0 |
| Task 2 aggregate | 66.5 | 43.0 |
| Task 2 early-answering AOC (grid) | 0.51 | 0.22 |
| Same answer with no CoT as with the CoT | 36.7 | 75.3 |
| Adding mistakes AOC, every position (paper: LogiQA 0.31) | 0.51 | 0.23 |
| Task 3 aggregate, plain SC | 62.7 | 40.3 |
| Task 3 aggregate, weighted | 58.8 | 37.6 |
| Task 3 aggregate, tuned | 58.9 | 40.1 |
| Task 3 aggregate, changed (ablation) | 67.4 | 40.7 |

## The 50% flag (Task 3, seed 20)

| | meta-llama/Llama-3.1-8B-Instruct | Qwen/Qwen3-8B |
| --- | --- | --- |
| Share of samples flagged (unchanged) | 44.5 | 77.9 |
| Accuracy flagged / other | 67.7 / 44.0 | 74.7 / 72.9 |
| Flagged / other equal to the no-reasoning answer | 78.4 / 12.3 | 95.0 / 7.2 |

## CoT shape

| | meta-llama/Llama-3.1-8B-Instruct | Qwen/Qwen3-8B |
| --- | --- | --- |
| Sentences / tokens per CoT | 12.4 / 214 | 42.7 / 494 |
| CoTs that hit the 512-token cap | 3 | 118 |

## Where each run ran and how long it took

| Model | Results folder | Host | GPUs (tp) | Started | Minutes | Note |
| --- | --- | --- | --- | --- | --- | --- |
| meta-llama/Llama-3.1-8B-Instruct | `results/task1/bbh` | gpu73.cse.iitkgp | NVIDIA L40S, NVIDIA L40S (2) | 2026-11-04T01:21:09+05:30 | 0.9 | failed: RuntimeError (aborted at start-up; no output) |
| meta-llama/Llama-3.1-8B-Instruct | `results/task1/bbh` | gpu73.cse.iitkgp | NVIDIA L40S (1) | 2026-11-04T03:33:52+05:30 | 6.5 |  |
| meta-llama/Llama-3.1-8B-Instruct | `results/task2/bbh` | gpu73.cse.iitkgp | NVIDIA L40S (1) | 2026-11-04T03:40:33+05:30 | 17.9 |  |
| meta-llama/Llama-3.1-8B-Instruct | `results/task2/bbh/seed_30` | gpu73.cse.iitkgp | NVIDIA L40S (1) | 2026-11-04T03:58:35+05:30 | 6.7 |  |
| meta-llama/Llama-3.1-8B-Instruct | `results/task2/bbh/seed_40` | gpu73.cse.iitkgp | NVIDIA L40S (1) | 2026-11-04T04:05:23+05:30 | 7.1 |  |
| meta-llama/Llama-3.1-8B-Instruct | `results/task3/bbh/dev` | gpu73.cse.iitkgp | NVIDIA L40S (1) | 2026-11-04T04:12:36+05:30 | 4.1 |  |
| meta-llama/Llama-3.1-8B-Instruct | `results/task3/bbh` | gpu73.cse.iitkgp | NVIDIA L40S (1) | 2026-11-04T04:16:49+05:30 | 20.8 |  |
| meta-llama/Llama-3.1-8B-Instruct | `results/task3/bbh/seed_30` | gpu73.cse.iitkgp | NVIDIA L40S (1) | 2026-11-04T04:37:43+05:30 | 23.6 |  |
| meta-llama/Llama-3.1-8B-Instruct | `results/task3/bbh/seed_40` | gpu73.cse.iitkgp | NVIDIA L40S (1) | 2026-11-04T05:01:29+05:30 | 24.1 |  |
| Qwen/Qwen3-8B | `results/models/qwen3-8b/task1/bbh` | gpu74.cse.iitkgp | NVIDIA A40 (1) | 2026-11-04T03:33:52+05:30 | 2.8 |  |
| Qwen/Qwen3-8B | `results/models/qwen3-8b/task2/bbh` | gpu74.cse.iitkgp | NVIDIA A40 (1) | 2026-11-04T03:36:44+05:30 | 48.7 |  |
| Qwen/Qwen3-8B | `results/models/qwen3-8b/task2/bbh/seed_30` | gpu74.cse.iitkgp | NVIDIA A40 (1) | 2026-11-04T04:25:33+05:30 | 14.8 |  |
| Qwen/Qwen3-8B | `results/models/qwen3-8b/task2/bbh/seed_40` | gpu74.cse.iitkgp | NVIDIA A40 (1) | 2026-11-04T04:40:28+05:30 | 15.1 |  |
| Qwen/Qwen3-8B | `results/models/qwen3-8b/task3/bbh/dev` | gpu74.cse.iitkgp | NVIDIA A40 (1) | 2026-11-04T04:55:42+05:30 | 9.1 |  |
| Qwen/Qwen3-8B | `results/models/qwen3-8b/task3/bbh` | gpu74.cse.iitkgp | NVIDIA A40 (1) | 2026-11-04T05:04:56+05:30 | 55.3 |  |
| Qwen/Qwen3-8B | `results/models/qwen3-8b/task3/bbh/seed_30` | gpu74.cse.iitkgp | NVIDIA A40 (1) | 2026-11-04T06:00:22+05:30 | 55.5 |  |
| Qwen/Qwen3-8B | `results/models/qwen3-8b/task3/bbh/seed_40` | gpu74.cse.iitkgp | NVIDIA A40 (1) | 2026-11-04T06:55:53+05:30 | 55.5 |  |

Total GPU wall-clock per model: meta-llama/Llama-3.1-8B-Instruct 112 min; Qwen/Qwen3-8B 257 min.

