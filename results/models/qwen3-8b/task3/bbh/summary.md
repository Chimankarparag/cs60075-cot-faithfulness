# Task 3 - faithfulness-weighted self-consistency (n = 150, k = 5, Qwen/Qwen3-8B)

## The sampled CoTs

- Accuracy of a single sample: 77.2 [74.1, 80.1] (over 750 samples); pass@5 (some sample right): 92.0%; items where all samples agree: 66.0%.
- 591 samples hit the 512-token cap, 8 final answers could not be parsed; 42.8 sentences per CoT on average.
- Sample 0 has the same text as Task 2's CoT for 4 of 150 items (same seed; sampled text also depends on GPU type and batch layout, so the samples are fresh draws).
- No-reasoning answer (empty CoT, forced answer): accuracy 63.3%; 76.8% of samples end on that same answer.

## Step 2: what the 50% early answer says about a sample

| Flag rule | Share flagged | Accuracy flagged / other | Same, items with mixed flags | Flagged / other equal to no-reasoning answer |
| --- | --- | --- | --- | --- |
| unchanged | 77.9% (584) | 79.5% / 69.3% | 49.7% / 63.2% (57 items) | 94.5% / 14.5% |
| loadbearing | 4.3% (32) | 78.1% / 77.2% | 74.1% / 50.0% (15 items) | 0.0% / 80.2% |
| changed | 22.1% (166) | 69.3% / 79.5% | 63.2% / 49.7% (57 items) | 14.5% / 94.5% |

Rule chosen on 96 development items: faithful if **unchanged**, alpha = **0.75** (dev accuracy 80.2%, plain self-consistency on dev 80.2%).

## Step 4: accuracy (%)

| Method | Accuracy [95% CI] |
| --- | --- |
| Task 1 (four_shot) | 69.3 [61.3, 76.0] |
| Task 2 (single CoT) | 76.7 [70.0, 83.3] |
| Mean of the 5 single samples | 77.2 |
| Plain self-consistency (alpha = 1, control) | 79.3 [72.7, 86.0] |
| Weighted vote, faithful = answer unchanged, alpha = 0.5 (fixed in advance) | 78.7 [72.0, 85.3] |
| Weighted vote, faithful = answer changed, alpha = 0.5 (ablation) | 80.7 [74.0, 87.3] |
| Weighted vote, rule and alpha chosen on dev (unchanged, alpha = 0.75) | 80.0 [74.0, 86.7] |

Paired differences (first minus second, percentage points) with an exact McNemar test:

| Comparison | Difference [95% CI] | Only first right | Only second right | McNemar p |
| --- | --- | --- | --- | --- |
| weighted vs Task 1 (four_shot) | +9.3 [+2.7, +16.7] | 21 | 7 | 0.013 |
| weighted vs Task 2 (single CoT) | +2.0 [-3.3, +8.0] | 11 | 8 | 0.648 |
| ablation_changed vs Task 1 (four_shot) | +11.3 [+4.0, +18.7] | 25 | 8 | 0.005 |
| ablation_changed vs Task 2 (single CoT) | +4.0 [-1.3, +10.0] | 13 | 7 | 0.263 |
| plain_sc vs Task 1 (four_shot) | +10.0 [+3.3, +17.3] | 22 | 7 | 0.008 |
| plain_sc vs Task 2 (single CoT) | +2.7 [-3.3, +8.7] | 12 | 8 | 0.503 |
| tuned vs Task 1 (four_shot) | +10.7 [+4.0, +17.3] | 22 | 6 | 0.004 |
| tuned vs Task 2 (single CoT) | +3.3 [-2.0, +9.3] | 12 | 7 | 0.359 |
| weighted vs plain_sc | -0.7 [-4.0, +2.7] | 3 | 4 | 1.000 |
| ablation_changed vs plain_sc | +1.3 [-2.0, +4.7] | 4 | 2 | 0.688 |
| tuned vs plain_sc | +0.7 [+0.0, +2.0] | 1 | 0 | 1.000 |

Items where a weighted pipeline and plain voting disagree:

| Pipeline | Items | Weighted picks the no-reasoning answer | Weighted right | Plain right |
| --- | --- | --- | --- | --- |
| weighted | 7 | 5 | 3 | 4 |
| ablation_changed | 6 | 0 | 4 | 2 |
| tuned | 1 | 1 | 1 | 0 |

Sensitivity to alpha (accuracy %; not used to choose anything):

| Faithful if | alpha = 0.0 | alpha = 0.25 | alpha = 0.5 | alpha = 0.75 | alpha = 1.0 |
| --- | --- | --- | --- | --- | --- |
| unchanged | 73.3 | 75.3 | 78.7 | 80.0 | 79.3 |
| loadbearing | 80.7 | 81.3 | 80.7 | 79.3 | 79.3 |
| changed | 82.7 | 82.7 | 80.7 | 79.3 | 79.3 |

## Step 5: faithfulness of the pipeline's output (%)

| Pipeline | Early answering | Adding a mistake | Paraphrasing | Filler tokens | Aggregate | Early AOC (grid) |
| --- | --- | --- | --- | --- | --- | --- |
| Task 2 (one CoT) | 21.3 [15.8, 26.8] | 24.6 [18.1, 32.6] | 92.3 [88.0, 96.5] | 23.3 [16.7, 30.0] | 40.4 | 0.19 |
| Plain self-consistency | 19.3 [14.0, 25.2] | 19.0 [13.4, 25.4] | 92.8 [88.4, 97.1] | 20.7 [14.7, 28.0] | 37.9 | 0.17 |
| Weighted vote (fixed, unchanged) | 15.3 [10.8, 20.8] | 21.0 [14.7, 28.0] | 92.1 [87.9, 96.4] | 18.7 [13.3, 25.3] | 36.8 | 0.14 |
| Weighted vote (tuned on dev) | 17.0 [12.2, 22.7] | 17.6 [12.0, 23.9] | 93.6 [89.3, 97.1] | 20.0 [14.0, 26.7] | 37.0 | 0.16 |
| Weighted vote, changed (ablation) | 23.8 [17.8, 30.2] | 19.3 [13.1, 26.2] | 93.4 [89.0, 97.1] | 24.7 [18.0, 32.0] | 40.3 | 0.21 |

Paired difference to Task 2 per intervention (points, 95% CI), and in the aggregate:

| Pipeline | Early answering | Adding a mistake | Paraphrasing | Filler tokens | Aggregate |
| --- | --- | --- | --- | --- | --- |
| Plain self-consistency | -2.0 [-7.3, +3.0] | -4.5 [-12.7, +3.7] | +0.7 [-5.2, +7.5] | -2.7 [-8.7, +3.3] | -2.4 |
| Weighted vote (fixed, unchanged) | -6.0 [-11.5, -1.0] | -2.2 [-11.1, +6.7] | +0.0 [-6.6, +6.6] | -4.7 [-10.7, +1.3] | -3.6 |
| Weighted vote (tuned on dev) | -4.3 [-9.2, +0.3] | -6.0 [-14.9, +2.2] | +1.5 [-4.4, +8.1] | -3.3 [-9.3, +2.7] | -3.3 |
| Weighted vote, changed (ablation) | +2.5 [-2.7, +7.2] | -5.2 [-13.3, +3.0] | +1.5 [-4.5, +7.5] | +1.3 [-4.0, +6.7] | -0.1 |
