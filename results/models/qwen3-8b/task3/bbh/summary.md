# Task 3 - faithfulness-weighted self-consistency on bbh (n = 150, k = 5, Qwen/Qwen3-8B, generation seed 20)

## The sampled CoTs

- Accuracy of a single sample: 74.3 [71.1, 77.3] (over 750 samples); pass@5 (some sample right): 86.7; items where all samples agree: 64.7%.
- 579 samples hit the 512-token cap, 6 final answers could not be parsed; 42.5 sentences per CoT on average.
- Sample 0 has the same text as Task 2's CoT for 13 of 150 items: it uses the same seed, but sampled text depends on GPU type, tensor-parallel size and batch composition, so the samples are fresh draws.
- No-reasoning answer (empty CoT, forced answer): accuracy 58.7%; 75.6% of samples end on that same answer.

## Step 2: what the 50% early answer says about a sample

| Flag rule | Share flagged | Accuracy flagged / other | Same, items with mixed flags | Flagged / other equal to no-reasoning answer |
| --- | --- | --- | --- | --- |
| unchanged | 77.9% (584) | 74.7% / 72.9% | 45.3% / 69.4% (56 items) | 95.0% / 7.2% |
| loadbearing | 3.9% (29) | 65.5% / 74.6% | 65.5% / 55.4% (17 items) | 0.0% / 78.6% |
| changed | 22.1% (166) | 72.9% / 74.7% | 69.4% / 45.3% (56 items) | 7.2% / 95.0% |

Rule chosen on 96 development items: faithful if **unchanged**, alpha = **0.75** (dev accuracy 81.2%, plain self-consistency on dev 81.2%).

## Step 4: accuracy (%)

| Method | Accuracy [95% CI] |
| --- | --- |
| Task 1 (four_shot) | 65.3 [58.0, 73.3] |
| Task 2 (single CoT) | 75.3 [68.0, 82.7] |
| Mean of the 5 single samples | 74.3 |
| Plain self-consistency (alpha = 1, control) | 77.3 [70.7, 84.0] |
| Weighted vote, faithful = answer unchanged, alpha = 0.5 (fixed in advance) | 73.3 [66.0, 80.0] |
| Weighted vote, faithful = answer changed, alpha = 0.5 (ablation) | 79.3 [72.7, 86.0] |
| Weighted vote, rule and alpha chosen on dev (unchanged, alpha = 0.75) | 77.3 [70.7, 84.0] |

Paired differences (first minus second, percentage points) with an exact McNemar test:

| Comparison | Difference [95% CI] | Only first right | Only second right | McNemar p |
| --- | --- | --- | --- | --- |
| weighted vs Task 1 (four_shot) | +8.0 [+1.3, +14.7] | 20 | 8 | 0.036 |
| weighted vs Task 2 (single CoT) | -2.0 [-7.3, +3.3] | 6 | 9 | 0.607 |
| ablation_changed vs Task 1 (four_shot) | +14.0 [+7.3, +20.0] | 26 | 5 | 0.000 |
| ablation_changed vs Task 2 (single CoT) | +4.0 [-1.3, +8.7] | 11 | 5 | 0.210 |
| plain_sc vs Task 1 (four_shot) | +12.0 [+4.7, +18.7] | 24 | 6 | 0.001 |
| plain_sc vs Task 2 (single CoT) | +2.0 [-2.7, +6.7] | 8 | 5 | 0.581 |
| tuned vs Task 1 (four_shot) | +12.0 [+4.7, +18.7] | 24 | 6 | 0.001 |
| tuned vs Task 2 (single CoT) | +2.0 [-2.7, +6.7] | 8 | 5 | 0.581 |
| weighted vs plain_sc | -4.0 [-7.3, -1.3] | 0 | 6 | 0.031 |
| ablation_changed vs plain_sc | +2.0 [-1.3, +5.3] | 5 | 2 | 0.453 |
| tuned vs plain_sc | +0.0 [+0.0, +0.0] | 0 | 0 | 1.000 |

Sensitivity to alpha (accuracy %; not used to choose anything):

| Faithful if | alpha = 0.0 | alpha = 0.25 | alpha = 0.5 | alpha = 0.75 | alpha = 1.0 |
| --- | --- | --- | --- | --- | --- |
| unchanged | 70.0 | 72.0 | 73.3 | 77.3 | 77.3 |
| loadbearing | 78.7 | 78.7 | 78.7 | 78.0 | 77.3 |
| changed | 78.7 | 80.0 | 79.3 | 78.0 | 77.3 |

## Step 5: faithfulness of the pipeline's output (%)

| Pipeline | Early answering | Adding a mistake | Paraphrasing | Filler tokens | Aggregate | Early AOC (grid) |
| --- | --- | --- | --- | --- | --- | --- |
| Task 2 (one CoT) | 24.5 [18.5, 30.7] | 28.6 [20.7, 36.4] | 94.8 [91.1, 98.5] | 24.0 [16.7, 30.7] | 43.0 | 0.22 |
| Weighted vote (fixed, unchanged) | 16.5 [11.8, 21.5] | 23.0 [16.5, 30.2] | 92.8 [88.5, 97.1] | 18.0 [12.0, 24.0] | 37.6 | 0.15 |
| Weighted vote, changed (ablation) | 26.2 [20.3, 31.7] | 21.9 [15.3, 28.5] | 89.2 [84.2, 94.2] | 25.3 [18.0, 32.0] | 40.7 | 0.24 |
| Plain self-consistency | 20.3 [15.3, 25.2] | 27.7 [20.6, 35.5] | 92.0 [87.7, 96.4] | 21.3 [14.7, 27.3] | 40.3 | 0.18 |
| Weighted vote (tuned on dev) | 20.0 [14.8, 25.0] | 25.4 [18.3, 32.4] | 93.5 [89.2, 97.1] | 21.3 [14.7, 27.3] | 40.1 | 0.18 |

Paired difference to Task 2 per intervention (points, 95% CI), and in the aggregate:

| Pipeline | Early answering | Adding a mistake | Paraphrasing | Filler tokens | Aggregate |
| --- | --- | --- | --- | --- | --- |
| Weighted vote (fixed, unchanged) | -8.0 [-13.3, -2.8] | -3.8 [-11.5, +3.8] | -2.3 [-8.5, +3.8] | -6.0 [-11.3, -1.3] | -5.4 |
| Weighted vote, changed (ablation) | +1.7 [-3.8, +7.0] | -3.8 [-10.8, +3.1] | -5.4 [-12.3, +0.8] | +1.3 [-3.3, +6.0] | -2.3 |
| Plain self-consistency | -4.2 [-9.2, +0.8] | +0.0 [-7.5, +7.5] | -3.1 [-9.2, +3.1] | -2.7 [-7.3, +2.0] | -2.6 |
| Weighted vote (tuned on dev) | -4.5 [-9.7, +0.7] | -1.5 [-9.0, +6.0] | -1.5 [-6.9, +4.6] | -2.7 [-7.3, +2.0] | -2.9 |
