# Task 3 - faithfulness-weighted self-consistency (n = 150, k = 5, meta-llama/Llama-3.1-8B-Instruct)

## The sampled CoTs

- Accuracy of a single sample: 53.1 [49.5, 56.8] (over 750 samples); pass@5 (some sample right): 90.7%; items where all samples agree: 17.3%.
- 18 samples hit the 512-token cap, 4 final answers could not be parsed; 12.1 sentences per CoT on average.
- Sample 0 has the same text as Task 2's CoT for 34 of 150 items (same seed; sampled text also depends on GPU type and batch layout, so the samples are fresh draws).
- No-reasoning answer (empty CoT, forced answer): accuracy 44.7%; 42.7% of samples end on that same answer.

## Step 2: what the 50% early answer says about a sample

| Flag rule | Share flagged | Accuracy flagged / other | Same, items with mixed flags | Flagged / other equal to no-reasoning answer |
| --- | --- | --- | --- | --- |
| unchanged | 48.0% (360) | 71.7% / 35.9% | 60.8% / 36.9% (110 items) | 80.3% / 7.9% |
| loadbearing | 9.5% (71) | 62.0% / 52.1% | 59.1% / 38.0% (49 items) | 0.0% / 47.1% |
| changed | 52.0% (390) | 35.9% / 71.7% | 36.9% / 60.8% (110 items) | 7.9% / 80.3% |

Rule chosen on 96 development items: faithful if **unchanged**, alpha = **0.75** (dev accuracy 59.4%, plain self-consistency on dev 61.5%).

## Step 4: accuracy (%)

| Method | Accuracy [95% CI] |
| --- | --- |
| Task 1 (zero_shot) | 44.7 [36.7, 52.0] |
| Task 2 (single CoT) | 58.0 [50.0, 66.0] |
| Mean of the 5 single samples | 53.1 |
| Plain self-consistency (alpha = 1, control) | 61.3 [53.3, 68.7] |
| Weighted vote, faithful = answer unchanged, alpha = 0.5 (fixed in advance) | 62.0 [54.0, 70.0] |
| Weighted vote, faithful = answer changed, alpha = 0.5 (ablation) | 58.7 [50.0, 66.0] |
| Weighted vote, rule and alpha chosen on dev (unchanged, alpha = 0.75) | 62.0 [54.0, 69.3] |

Paired differences (first minus second, percentage points) with an exact McNemar test:

| Comparison | Difference [95% CI] | Only first right | Only second right | McNemar p |
| --- | --- | --- | --- | --- |
| weighted vs Task 1 (zero_shot) | +17.3 [+10.0, +25.3] | 32 | 6 | 0.000 |
| weighted vs Task 2 (single CoT) | +4.0 [-4.7, +12.7] | 24 | 18 | 0.441 |
| ablation_changed vs Task 1 (zero_shot) | +14.0 [+5.3, +24.0] | 35 | 14 | 0.004 |
| ablation_changed vs Task 2 (single CoT) | +0.7 [-6.7, +8.0] | 19 | 18 | 1.000 |
| plain_sc vs Task 1 (zero_shot) | +16.7 [+8.7, +24.7] | 32 | 7 | 0.000 |
| plain_sc vs Task 2 (single CoT) | +3.3 [-5.3, +11.3] | 22 | 17 | 0.522 |
| tuned vs Task 1 (zero_shot) | +17.3 [+9.3, +26.0] | 33 | 7 | 0.000 |
| tuned vs Task 2 (single CoT) | +4.0 [-4.7, +12.0] | 23 | 17 | 0.430 |
| weighted vs plain_sc | +0.7 [-2.7, +4.0] | 4 | 3 | 1.000 |
| ablation_changed vs plain_sc | -2.7 [-7.4, +2.0] | 5 | 9 | 0.424 |
| tuned vs plain_sc | +0.7 [-1.3, +2.7] | 2 | 1 | 1.000 |

Items where a weighted pipeline and plain voting disagree:

| Pipeline | Items | Weighted picks the no-reasoning answer | Weighted right | Plain right |
| --- | --- | --- | --- | --- |
| weighted | 13 | 9 | 4 | 3 |
| ablation_changed | 15 | 0 | 5 | 9 |
| tuned | 7 | 4 | 2 | 1 |

Sensitivity to alpha (accuracy %; not used to choose anything):

| Faithful if | alpha = 0.0 | alpha = 0.25 | alpha = 0.5 | alpha = 0.75 | alpha = 1.0 |
| --- | --- | --- | --- | --- | --- |
| unchanged | 62.0 | 63.3 | 62.0 | 62.0 | 61.3 |
| loadbearing | 62.0 | 63.3 | 63.3 | 62.7 | 61.3 |
| changed | 46.7 | 55.3 | 58.7 | 62.0 | 61.3 |

## Step 5: faithfulness of the pipeline's output (%)

| Pipeline | Early answering | Adding a mistake | Paraphrasing | Filler tokens | Aggregate | Early AOC (grid) |
| --- | --- | --- | --- | --- | --- | --- |
| Task 2 (one CoT) | 54.0 [47.8, 60.5] | 47.3 [39.3, 54.7] | 94.3 [90.1, 97.9] | 60.0 [52.0, 68.0] | 63.9 | 0.49 |
| Plain self-consistency | 45.3 [39.7, 52.2] | 45.3 [37.3, 53.3] | 97.2 [94.4, 99.3] | 50.7 [42.7, 58.7] | 59.6 | 0.41 |
| Weighted vote (fixed, unchanged) | 33.2 [27.0, 39.8] | 39.3 [32.0, 47.3] | 98.6 [96.6, 100.0] | 46.7 [38.7, 54.0] | 54.4 | 0.31 |
| Weighted vote (tuned on dev) | 37.3 [31.3, 43.8] | 41.6 [34.2, 49.7] | 98.6 [96.6, 100.0] | 50.0 [41.3, 58.0] | 56.9 | 0.35 |
| Weighted vote, changed (ablation) | 57.3 [51.0, 64.2] | 52.7 [44.7, 60.7] | 97.2 [94.4, 99.3] | 60.0 [52.0, 68.0] | 66.8 | 0.52 |

Paired difference to Task 2 per intervention (points, 95% CI), and in the aggregate:

| Pipeline | Early answering | Adding a mistake | Paraphrasing | Filler tokens | Aggregate |
| --- | --- | --- | --- | --- | --- |
| Plain self-consistency | -8.7 [-14.7, -2.7] | -2.0 [-11.3, +7.3] | +2.9 [-0.7, +6.6] | -9.3 [-16.7, -2.7] | -4.3 |
| Weighted vote (fixed, unchanged) | -20.8 [-27.5, -13.7] | -8.0 [-16.0, +0.7] | +4.3 [+0.7, +7.9] | -13.3 [-20.7, -5.3] | -9.5 |
| Weighted vote (tuned on dev) | -16.7 [-23.2, -9.3] | -5.4 [-14.8, +4.0] | +4.3 [+0.7, +8.7] | -10.0 [-17.3, -2.0] | -7.0 |
| Weighted vote, changed (ablation) | +3.3 [-3.3, +9.7] | +5.3 [-4.0, +14.0] | +3.0 [-1.5, +8.1] | +0.0 [-7.3, +7.3] | +2.9 |
