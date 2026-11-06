# Tasks 2 and 3 across sampling seeds (meta-llama/Llama-3.1-8B-Instruct, seeds 20, 30, 40)

## Task 3 accuracy (%)

| Pipeline | seed 20 | seed 30 | seed 40 | Mean | SD |
| --- | --- | --- | --- | --- | --- |
| Mean single sample | 54.5 | 52.7 | 53.7 | 53.6 | 0.9 |
| plain_sc | 66.0 | 64.7 | 62.7 | 64.4 | 1.7 |
| weighted | 64.7 | 61.3 | 63.3 | 63.1 | 1.7 |
| tuned | 66.7 | 63.3 | 64.7 | 64.9 | 1.7 |
| ablation_changed | 62.7 | 64.7 | 62.7 | 63.3 | 1.2 |

Task 1 (greedy, the same in every run): Task 1 (four_shot) 45.3%

## Task 2, one CoT per item, per seed (%)

| Measure | seed 20 | seed 30 | seed 40 | Mean | SD |
| --- | --- | --- | --- | --- | --- |
| CoT accuracy | 47.3 | 54.0 | 55.3 | 52.2 | 4.3 |
| Gain over Task 1 (points) | 2.0 | 8.7 | 10.0 | 6.9 | 4.3 |
| Faithfulness: Early answering | 56.0 | 53.0 | 54.5 | 54.5 | 1.5 |
| Faithfulness: Adding a mistake | 49.3 | 48.7 | 55.3 | 51.1 | 3.7 |
| Faithfulness: Paraphrasing | 96.6 | 97.2 | 96.6 | 96.8 | 0.3 |
| Faithfulness: Filler tokens | 64.0 | 60.0 | 60.0 | 61.3 | 2.3 |
| Aggregate faithfulness | 66.5 | 64.7 | 66.6 | 65.9 | 1.1 |

## Differences (points; mean over seeds, and in how many seeds the difference was positive)

| Pipeline | Comparison | Mean | Min | Max | Seeds > 0 |
| --- | --- | --- | --- | --- | --- |
| plain_sc | vs Task 1 (four_shot) | +19.1 | +17.3 | +20.7 | 3/3 |
| plain_sc | vs Task 2 (single CoT) | +12.2 | +7.3 | +18.7 | 3/3 |
| weighted | vs Task 1 (four_shot) | +17.8 | +16.0 | +19.3 | 3/3 |
| weighted | vs Task 2 (single CoT) | +10.9 | +7.3 | +17.3 | 3/3 |
| weighted | vs plain_sc | -1.3 | -3.3 | +0.7 | 1/3 |
| tuned | vs Task 1 (four_shot) | +19.6 | +18.0 | +21.3 | 3/3 |
| tuned | vs Task 2 (single CoT) | +12.7 | +9.3 | +19.3 | 3/3 |
| tuned | vs plain_sc | +0.4 | -1.3 | +2.0 | 2/3 |
| ablation_changed | vs Task 1 (four_shot) | +18.0 | +17.3 | +19.3 | 3/3 |
| ablation_changed | vs Task 2 (single CoT) | +11.1 | +7.3 | +15.3 | 3/3 |
| ablation_changed | vs plain_sc | -1.1 | -3.3 | +0.0 | 0/3 |

## Aggregate faithfulness of the pipeline's output (%)

| Pipeline | seed 20 | seed 30 | seed 40 | Mean | SD |
| --- | --- | --- | --- | --- | --- |
| plain_sc | 62.7 | 62.5 | 63.3 | 62.8 | 0.4 |
| weighted | 58.8 | 58.4 | 56.4 | 57.9 | 1.3 |
| tuned | 58.9 | 58.6 | 59.1 | 58.9 | 0.3 |
| ablation_changed | 67.4 | 64.9 | 64.8 | 65.7 | 1.5 |
