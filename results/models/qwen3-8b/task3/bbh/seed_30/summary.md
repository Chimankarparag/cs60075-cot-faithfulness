# Task 3 - faithfulness-weighted self-consistency on bbh (n = 150, k = 5, Qwen/Qwen3-8B, generation seed 30)

## The sampled CoTs

- Accuracy of a single sample: 73.3 [70.0, 76.7] (over 750 samples); pass@5 (some sample right): 89.3; items where all samples agree: 64.7%.
- 579 samples hit the 512-token cap, 8 final answers could not be parsed; 42.6 sentences per CoT on average.
- Sample 0 has the same text as Task 2's CoT for 13 of 150 items: it uses the same seed, but sampled text depends on GPU type, tensor-parallel size and batch composition, so the samples are fresh draws.
- No-reasoning answer (empty CoT, forced answer): accuracy 58.7%; 73.6% of samples end on that same answer.

## Step 2: what the 50% early answer says about a sample

| Flag rule | Share flagged | Accuracy flagged / other | Same, items with mixed flags | Flagged / other equal to no-reasoning answer |
| --- | --- | --- | --- | --- |
| unchanged | 74.4% (558) | 74.6% / 69.8% | 50.6% / 63.5% (61 items) | 95.0% / 11.5% |
| loadbearing | 3.7% (28) | 67.9% / 73.5% | 67.9% / 55.3% (15 items) | 0.0% / 76.5% |
| changed | 25.6% (192) | 69.8% / 74.6% | 63.5% / 50.6% (61 items) | 11.5% / 95.0% |

Rule chosen on 96 development items: faithful if **unchanged**, alpha = **0.75** (dev accuracy 81.2%, plain self-consistency on dev 81.2%).

## Step 4: accuracy (%)

| Method | Accuracy [95% CI] |
| --- | --- |
| Task 1 (four_shot) | 65.3 [58.0, 73.3] |
| Task 2 (single CoT) | 78.0 [70.7, 84.7] |
| Mean of the 5 single samples | 73.3 |
| Plain self-consistency (alpha = 1, control) | 73.3 [65.3, 80.0] |
| Weighted vote, faithful = answer unchanged, alpha = 0.5 (fixed in advance) | 73.3 [66.0, 80.0] |
| Weighted vote, faithful = answer changed, alpha = 0.5 (ablation) | 78.7 [71.3, 85.3] |
| Weighted vote, rule and alpha chosen on dev (unchanged, alpha = 0.75) | 72.7 [65.3, 79.3] |

Paired differences (first minus second, percentage points) with an exact McNemar test:

| Comparison | Difference [95% CI] | Only first right | Only second right | McNemar p |
| --- | --- | --- | --- | --- |
| weighted vs Task 1 (four_shot) | +8.0 [+1.3, +14.0] | 19 | 7 | 0.029 |
| weighted vs Task 2 (single CoT) | -4.7 [-10.0, +0.7] | 4 | 11 | 0.118 |
| ablation_changed vs Task 1 (four_shot) | +13.3 [+5.3, +20.0] | 27 | 7 | 0.001 |
| ablation_changed vs Task 2 (single CoT) | +0.7 [-5.3, +6.7] | 11 | 10 | 1.000 |
| plain_sc vs Task 1 (four_shot) | +8.0 [+1.3, +14.0] | 19 | 7 | 0.029 |
| plain_sc vs Task 2 (single CoT) | -4.7 [-10.7, +0.7] | 5 | 12 | 0.143 |
| tuned vs Task 1 (four_shot) | +7.3 [+0.7, +13.3] | 19 | 8 | 0.052 |
| tuned vs Task 2 (single CoT) | -5.3 [-11.3, +0.7] | 5 | 13 | 0.096 |
| weighted vs plain_sc | +0.0 [-2.7, +2.7] | 2 | 2 | 1.000 |
| ablation_changed vs plain_sc | +5.3 [+0.7, +10.0] | 11 | 3 | 0.057 |
| tuned vs plain_sc | -0.7 [-2.0, +0.0] | 0 | 1 | 1.000 |

Sensitivity to alpha (accuracy %; not used to choose anything):

| Faithful if | alpha = 0.0 | alpha = 0.25 | alpha = 0.5 | alpha = 0.75 | alpha = 1.0 |
| --- | --- | --- | --- | --- | --- |
| unchanged | 69.3 | 72.7 | 73.3 | 72.7 | 73.3 |
| loadbearing | 73.3 | 72.7 | 72.7 | 73.3 | 73.3 |
| changed | 76.7 | 79.3 | 78.7 | 74.7 | 73.3 |

## Step 5: faithfulness of the pipeline's output (%)

| Pipeline | Early answering | Adding a mistake | Paraphrasing | Filler tokens | Aggregate | Early AOC (grid) |
| --- | --- | --- | --- | --- | --- | --- |
| Task 2 (one CoT) | 24.8 [18.5, 30.7] | 26.6 [18.7, 33.8] | 96.3 [93.4, 99.3] | 26.0 [18.7, 32.7] | 43.4 | 0.23 |
| Weighted vote (fixed, unchanged) | 16.0 [11.2, 20.8] | 24.5 [17.3, 31.7] | 94.1 [89.7, 97.8] | 18.7 [12.0, 24.7] | 38.3 | 0.15 |
| Weighted vote, changed (ablation) | 28.8 [22.3, 34.7] | 21.7 [15.9, 28.3] | 95.7 [92.0, 98.6] | 30.7 [23.3, 37.3] | 44.2 | 0.26 |
| Plain self-consistency | 19.0 [13.5, 24.3] | 23.0 [16.5, 29.5] | 93.5 [89.1, 97.1] | 22.0 [16.0, 28.7] | 39.4 | 0.17 |
| Weighted vote (tuned on dev) | 17.5 [12.3, 22.7] | 19.4 [12.9, 26.6] | 95.7 [92.0, 98.6] | 21.3 [15.3, 28.0] | 38.5 | 0.16 |

Paired difference to Task 2 per intervention (points, 95% CI), and in the aggregate:

| Pipeline | Early answering | Adding a mistake | Paraphrasing | Filler tokens | Aggregate |
| --- | --- | --- | --- | --- | --- |
| Weighted vote (fixed, unchanged) | -8.8 [-14.0, -4.2] | +0.0 [-8.5, +8.5] | -2.3 [-7.7, +3.1] | -7.3 [-13.3, -2.7] | -5.1 |
| Weighted vote, changed (ablation) | +4.0 [-1.8, +9.7] | -4.6 [-11.5, +2.3] | +0.0 [-4.6, +4.6] | +4.7 [-2.0, +10.7] | +0.8 |
| Plain self-consistency | -5.8 [-11.2, -0.8] | -2.3 [-10.7, +6.1] | -2.3 [-8.4, +3.1] | -4.0 [-10.0, +1.3] | -4.1 |
| Weighted vote (tuned on dev) | -7.3 [-12.8, -2.2] | -5.3 [-13.0, +3.1] | -0.8 [-6.1, +3.8] | -4.7 [-10.7, +0.7] | -5.0 |
