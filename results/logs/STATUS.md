# Run started 2026-11-04 03:33:50 on gpu74

Models: qwen3-8b; GPUs: 0
Running qwen3-8b one after the other on GPU 0

# Finished 2026-11-04 07:51:27

=== 2026-11-04 05:25:41 ALL DONE llama3.1-8b
=== 2026-11-04 07:51:26 ALL DONE qwen3-8b

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
