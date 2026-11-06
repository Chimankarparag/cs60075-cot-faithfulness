# Task 3 - faithfulness-weighted self-consistency on bbh (n = 150, k = 5, Qwen/Qwen3-8B, generation seed 40)

## The sampled CoTs

- Accuracy of a single sample: 73.2 [70.0, 76.3] (over 750 samples); pass@5 (some sample right): 88.7; items where all samples agree: 59.3%.
- 593 samples hit the 512-token cap, 9 final answers could not be parsed; 42.8 sentences per CoT on average.
- Sample 0 has the same text as Task 2's CoT for 17 of 150 items: it uses the same seed, but sampled text depends on GPU type, tensor-parallel size and batch composition, so the samples are fresh draws.
- No-reasoning answer (empty CoT, forced answer): accuracy 58.7%; 74.8% of samples end on that same answer.

## Step 2: what the 50% early answer says about a sample

| Flag rule | Share flagged | Accuracy flagged / other | Same, items with mixed flags | Flagged / other equal to no-reasoning answer |
| --- | --- | --- | --- | --- |
| unchanged | 76.3% (572) | 74.3% / 69.7% | 55.4% / 65.4% (62 items) | 95.5% / 8.4% |
| loadbearing | 3.5% (26) | 69.2% / 73.3% | 69.2% / 50.0% (16 items) | 0.0% / 77.5% |
| changed | 23.7% (178) | 69.7% / 74.3% | 65.4% / 55.4% (62 items) | 8.4% / 95.5% |

Rule chosen on 96 development items: faithful if **unchanged**, alpha = **0.75** (dev accuracy 81.2%, plain self-consistency on dev 81.2%).

## Step 4: accuracy (%)

| Method | Accuracy [95% CI] |
| --- | --- |
| Task 1 (four_shot) | 65.3 [58.0, 73.3] |
| Task 2 (single CoT) | 73.3 [66.0, 80.7] |
| Mean of the 5 single samples | 73.2 |
| Plain self-consistency (alpha = 1, control) | 78.7 [72.0, 85.3] |
| Weighted vote, faithful = answer unchanged, alpha = 0.5 (fixed in advance) | 73.3 [66.0, 80.0] |
| Weighted vote, faithful = answer changed, alpha = 0.5 (ablation) | 79.3 [73.3, 85.3] |
| Weighted vote, rule and alpha chosen on dev (unchanged, alpha = 0.75) | 78.0 [70.7, 84.7] |

Paired differences (first minus second, percentage points) with an exact McNemar test:

| Comparison | Difference [95% CI] | Only first right | Only second right | McNemar p |
| --- | --- | --- | --- | --- |
| weighted vs Task 1 (four_shot) | +8.0 [+1.3, +14.0] | 20 | 8 | 0.036 |
| weighted vs Task 2 (single CoT) | +0.0 [-6.0, +6.0] | 9 | 9 | 1.000 |
| ablation_changed vs Task 1 (four_shot) | +14.0 [+6.7, +20.7] | 28 | 7 | 0.001 |
| ablation_changed vs Task 2 (single CoT) | +6.0 [+0.7, +12.0] | 13 | 4 | 0.049 |
| plain_sc vs Task 1 (four_shot) | +13.3 [+6.0, +20.0] | 26 | 6 | 0.001 |
| plain_sc vs Task 2 (single CoT) | +5.3 [+0.0, +10.7] | 12 | 4 | 0.077 |
| tuned vs Task 1 (four_shot) | +12.7 [+5.3, +19.3] | 26 | 7 | 0.001 |
| tuned vs Task 2 (single CoT) | +4.7 [-0.7, +10.7] | 12 | 5 | 0.143 |
| weighted vs plain_sc | -5.3 [-9.3, -2.0] | 0 | 8 | 0.008 |
| ablation_changed vs plain_sc | +0.7 [-2.7, +4.0] | 4 | 3 | 1.000 |
| tuned vs plain_sc | -0.7 [-2.0, +0.0] | 0 | 1 | 1.000 |

Sensitivity to alpha (accuracy %; not used to choose anything):

| Faithful if | alpha = 0.0 | alpha = 0.25 | alpha = 0.5 | alpha = 0.75 | alpha = 1.0 |
| --- | --- | --- | --- | --- | --- |
| unchanged | 67.3 | 72.0 | 73.3 | 78.0 | 78.7 |
| loadbearing | 78.7 | 78.0 | 77.3 | 78.7 | 78.7 |
| changed | 76.0 | 78.0 | 79.3 | 78.7 | 78.7 |

## Step 5: faithfulness of the pipeline's output (%)

| Pipeline | Early answering | Adding a mistake | Paraphrasing | Filler tokens | Aggregate | Early AOC (grid) |
| --- | --- | --- | --- | --- | --- | --- |
| Task 2 (one CoT) | 21.3 [16.0, 26.7] | 23.4 [16.8, 30.7] | 90.5 [85.4, 94.9] | 24.0 [17.3, 30.7] | 39.8 | 0.19 |
| Weighted vote (fixed, unchanged) | 15.5 [10.8, 19.8] | 22.8 [15.2, 29.7] | 94.8 [90.4, 98.5] | 18.0 [12.7, 24.0] | 37.8 | 0.14 |
| Weighted vote, changed (ablation) | 24.8 [18.8, 30.3] | 18.3 [12.0, 25.4] | 97.0 [94.0, 99.3] | 27.3 [20.0, 34.0] | 41.9 | 0.23 |
| Plain self-consistency | 20.8 [15.2, 26.0] | 20.8 [14.6, 27.8] | 96.4 [93.4, 99.3] | 22.7 [16.7, 28.7] | 40.2 | 0.19 |
| Weighted vote (tuned on dev) | 19.0 [13.8, 24.2] | 18.6 [12.4, 25.5] | 96.3 [92.6, 99.3] | 21.3 [15.3, 27.3] | 38.8 | 0.17 |

Paired difference to Task 2 per intervention (points, 95% CI), and in the aggregate:

| Pipeline | Early answering | Adding a mistake | Paraphrasing | Filler tokens | Aggregate |
| --- | --- | --- | --- | --- | --- |
| Weighted vote (fixed, unchanged) | -5.8 [-11.0, -1.2] | +0.0 [-7.5, +7.5] | +5.4 [+0.0, +11.6] | -6.0 [-12.0, -0.7] | -2.0 |
| Weighted vote, changed (ablation) | +3.5 [-1.2, +8.5] | -3.0 [-11.4, +5.3] | +6.2 [+1.6, +11.7] | +3.3 [-2.7, +9.3] | +2.1 |
| Plain self-consistency | -0.5 [-5.3, +4.3] | -2.2 [-9.0, +4.5] | +6.1 [+0.8, +12.2] | -1.3 [-6.7, +4.0] | +0.4 |
| Weighted vote (tuned on dev) | -2.3 [-6.8, +2.3] | -3.7 [-10.4, +3.0] | +5.4 [+0.8, +11.6] | -2.7 [-8.0, +3.3] | -1.0 |
