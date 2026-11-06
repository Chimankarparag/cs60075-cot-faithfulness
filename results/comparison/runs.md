# Runs

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
