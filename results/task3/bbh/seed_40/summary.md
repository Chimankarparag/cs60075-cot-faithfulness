# Task 3 - faithfulness-weighted self-consistency on bbh (n = 150, k = 5, meta-llama/Llama-3.1-8B-Instruct, generation seed 40)

## The sampled CoTs

- Accuracy of a single sample: 53.7 [50.3, 57.5] (over 750 samples); pass@5 (some sample right): 88.7; items where all samples agree: 16.0%.
- 17 samples hit the 512-token cap, 2 final answers could not be parsed; 12.0 sentences per CoT on average.
- Sample 0 has the same text as Task 2's CoT for 34 of 150 items: it uses the same seed, but sampled text depends on GPU type, tensor-parallel size and batch composition, so the samples are fresh draws.
- No-reasoning answer (empty CoT, forced answer): accuracy 44.0%; 41.9% of samples end on that same answer.

## Step 2: what the 50% early answer says about a sample

| Flag rule | Share flagged | Accuracy flagged / other | Same, items with mixed flags | Flagged / other equal to no-reasoning answer |
| --- | --- | --- | --- | --- |
| unchanged | 43.9% (329) | 69.6% / 41.3% | 57.7% / 38.9% (109 items) | 77.5% / 14.0% |
| loadbearing | 9.9% (74) | 48.6% / 54.3% | 48.6% / 44.4% (49 items) | 0.0% / 46.4% |
| changed | 56.1% (421) | 41.3% / 69.6% | 38.9% / 57.7% (109 items) | 14.0% / 77.5% |

Rule chosen on 96 development items: faithful if **unchanged**, alpha = **0.75** (dev accuracy 62.5%, plain self-consistency on dev 63.5%).

## Step 4: accuracy (%)

| Method | Accuracy [95% CI] |
| --- | --- |
| Task 1 (four_shot) | 45.3 [37.3, 53.3] |
| Task 2 (single CoT) | 55.3 [47.3, 63.3] |
| Mean of the 5 single samples | 53.7 |
| Plain self-consistency (alpha = 1, control) | 62.7 [55.3, 70.0] |
| Weighted vote, faithful = answer unchanged, alpha = 0.5 (fixed in advance) | 63.3 [55.3, 70.7] |
| Weighted vote, faithful = answer changed, alpha = 0.5 (ablation) | 62.7 [55.3, 70.0] |
| Weighted vote, rule and alpha chosen on dev (unchanged, alpha = 0.75) | 64.7 [57.3, 72.7] |

Paired differences (first minus second, percentage points) with an exact McNemar test:

| Comparison | Difference [95% CI] | Only first right | Only second right | McNemar p |
| --- | --- | --- | --- | --- |
| weighted vs Task 1 (four_shot) | +18.0 [+10.0, +25.3] | 35 | 8 | 0.000 |
| weighted vs Task 2 (single CoT) | +8.0 [+0.0, +16.0] | 26 | 14 | 0.081 |
| ablation_changed vs Task 1 (four_shot) | +17.3 [+7.3, +26.7] | 44 | 18 | 0.001 |
| ablation_changed vs Task 2 (single CoT) | +7.3 [-1.3, +16.0] | 28 | 17 | 0.135 |
| plain_sc vs Task 1 (four_shot) | +17.3 [+8.7, +26.0] | 39 | 13 | 0.000 |
| plain_sc vs Task 2 (single CoT) | +7.3 [-0.7, +15.3] | 27 | 16 | 0.126 |
| tuned vs Task 1 (four_shot) | +19.3 [+11.3, +27.3] | 38 | 9 | 0.000 |
| tuned vs Task 2 (single CoT) | +9.3 [+1.3, +17.3] | 28 | 14 | 0.044 |
| weighted vs plain_sc | +0.7 [-4.0, +5.3] | 7 | 6 | 1.000 |
| ablation_changed vs plain_sc | +0.0 [-4.0, +4.0] | 5 | 5 | 1.000 |
| tuned vs plain_sc | +2.0 [-1.3, +5.3] | 5 | 2 | 0.453 |

Sensitivity to alpha (accuracy %; not used to choose anything):

| Faithful if | alpha = 0.0 | alpha = 0.25 | alpha = 0.5 | alpha = 0.75 | alpha = 1.0 |
| --- | --- | --- | --- | --- | --- |
| unchanged | 58.0 | 59.3 | 63.3 | 64.7 | 62.7 |
| loadbearing | 58.0 | 59.3 | 62.0 | 62.7 | 62.7 |
| changed | 55.3 | 61.3 | 62.7 | 62.7 | 62.7 |

## Step 5: faithfulness of the pipeline's output (%)

| Pipeline | Early answering | Adding a mistake | Paraphrasing | Filler tokens | Aggregate | Early AOC (grid) |
| --- | --- | --- | --- | --- | --- | --- |
| Task 2 (one CoT) | 54.5 [47.8, 61.0] | 55.3 [46.7, 62.7] | 96.6 [93.2, 99.3] | 60.0 [52.7, 67.3] | 66.6 | 0.50 |
| Weighted vote (fixed, unchanged) | 35.5 [30.0, 41.0] | 48.3 [40.3, 56.4] | 97.9 [95.1, 100.0] | 44.0 [36.0, 51.3] | 56.4 | 0.33 |
| Weighted vote, changed (ablation) | 59.5 [52.5, 65.3] | 40.7 [32.7, 48.0] | 95.7 [92.1, 98.6] | 63.3 [55.3, 70.7] | 64.8 | 0.54 |
| Plain self-consistency | 49.5 [42.7, 56.2] | 52.0 [44.7, 60.0] | 96.5 [93.0, 99.3] | 55.3 [47.3, 63.3] | 63.3 | 0.45 |
| Weighted vote (tuned on dev) | 40.3 [34.3, 46.3] | 49.7 [41.6, 57.1] | 97.9 [95.1, 100.0] | 48.7 [40.7, 56.7] | 59.1 | 0.37 |

Paired difference to Task 2 per intervention (points, 95% CI), and in the aggregate:

| Pipeline | Early answering | Adding a mistake | Paraphrasing | Filler tokens | Aggregate |
| --- | --- | --- | --- | --- | --- |
| Weighted vote (fixed, unchanged) | -19.0 [-25.2, -12.8] | -6.7 [-16.8, +3.4] | +1.4 [-1.4, +5.0] | -16.0 [-24.0, -8.7] | -10.2 |
| Weighted vote, changed (ablation) | +5.0 [-1.3, +11.2] | -14.7 [-24.0, -4.7] | -1.4 [-5.8, +2.2] | +3.3 [-4.0, +10.7] | -1.8 |
| Plain self-consistency | -5.0 [-11.0, +1.3] | -3.3 [-13.4, +6.7] | +0.0 [-3.5, +3.5] | -4.7 [-12.7, +2.7] | -3.3 |
| Weighted vote (tuned on dev) | -14.2 [-20.3, -7.5] | -5.4 [-16.8, +6.0] | +1.4 [-2.2, +5.0] | -11.3 [-20.0, -4.0] | -7.5 |
