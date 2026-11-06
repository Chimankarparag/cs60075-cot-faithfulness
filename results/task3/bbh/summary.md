# Task 3 - faithfulness-weighted self-consistency on bbh (n = 150, k = 5, meta-llama/Llama-3.1-8B-Instruct, generation seed 20)

## The sampled CoTs

- Accuracy of a single sample: 54.5 [50.9, 58.1] (over 750 samples); pass@5 (some sample right): 89.3; items where all samples agree: 18.7%.
- 17 samples hit the 512-token cap, 2 final answers could not be parsed; 12.1 sentences per CoT on average.
- Sample 0 has the same text as Task 2's CoT for 37 of 150 items: it uses the same seed, but sampled text depends on GPU type, tensor-parallel size and batch composition, so the samples are fresh draws.
- No-reasoning answer (empty CoT, forced answer): accuracy 44.0%; 41.7% of samples end on that same answer.

## Step 2: what the 50% early answer says about a sample

| Flag rule | Share flagged | Accuracy flagged / other | Same, items with mixed flags | Flagged / other equal to no-reasoning answer |
| --- | --- | --- | --- | --- |
| unchanged | 44.5% (334) | 67.7% / 44.0% | 56.3% / 45.3% (105 items) | 78.4% / 12.3% |
| loadbearing | 9.6% (72) | 44.4% / 55.6% | 41.8% / 46.4% (50 items) | 0.0% / 46.2% |
| changed | 55.5% (416) | 44.0% / 67.7% | 45.3% / 56.3% (105 items) | 12.3% / 78.4% |

Rule chosen on 96 development items: faithful if **unchanged**, alpha = **0.75** (dev accuracy 62.5%, plain self-consistency on dev 63.5%).

## Step 4: accuracy (%)

| Method | Accuracy [95% CI] |
| --- | --- |
| Task 1 (four_shot) | 45.3 [37.3, 53.3] |
| Task 2 (single CoT) | 47.3 [39.3, 55.3] |
| Mean of the 5 single samples | 54.5 |
| Plain self-consistency (alpha = 1, control) | 66.0 [58.7, 73.3] |
| Weighted vote, faithful = answer unchanged, alpha = 0.5 (fixed in advance) | 64.7 [56.7, 71.3] |
| Weighted vote, faithful = answer changed, alpha = 0.5 (ablation) | 62.7 [54.7, 70.0] |
| Weighted vote, rule and alpha chosen on dev (unchanged, alpha = 0.75) | 66.7 [58.7, 74.0] |

Paired differences (first minus second, percentage points) with an exact McNemar test:

| Comparison | Difference [95% CI] | Only first right | Only second right | McNemar p |
| --- | --- | --- | --- | --- |
| weighted vs Task 1 (four_shot) | +19.3 [+11.3, +27.3] | 37 | 8 | 0.000 |
| weighted vs Task 2 (single CoT) | +17.3 [+8.7, +27.3] | 39 | 13 | 0.000 |
| ablation_changed vs Task 1 (four_shot) | +17.3 [+6.7, +27.3] | 45 | 19 | 0.002 |
| ablation_changed vs Task 2 (single CoT) | +15.3 [+6.7, +24.0] | 35 | 12 | 0.001 |
| plain_sc vs Task 1 (four_shot) | +20.7 [+12.0, +30.0] | 43 | 12 | 0.000 |
| plain_sc vs Task 2 (single CoT) | +18.7 [+10.7, +27.3] | 37 | 9 | 0.000 |
| tuned vs Task 1 (four_shot) | +21.3 [+12.7, +29.3] | 40 | 8 | 0.000 |
| tuned vs Task 2 (single CoT) | +19.3 [+10.7, +29.3] | 40 | 11 | 0.000 |
| weighted vs plain_sc | -1.3 [-5.3, +2.7] | 4 | 6 | 0.754 |
| ablation_changed vs plain_sc | -3.3 [-8.7, +2.0] | 5 | 10 | 0.302 |
| tuned vs plain_sc | +0.7 [-2.7, +4.0] | 4 | 3 | 1.000 |

Sensitivity to alpha (accuracy %; not used to choose anything):

| Faithful if | alpha = 0.0 | alpha = 0.25 | alpha = 0.5 | alpha = 0.75 | alpha = 1.0 |
| --- | --- | --- | --- | --- | --- |
| unchanged | 59.3 | 60.0 | 64.7 | 66.7 | 66.0 |
| loadbearing | 60.0 | 62.7 | 65.3 | 65.3 | 66.0 |
| changed | 56.0 | 62.0 | 62.7 | 64.0 | 66.0 |

## Step 5: faithfulness of the pipeline's output (%)

| Pipeline | Early answering | Adding a mistake | Paraphrasing | Filler tokens | Aggregate | Early AOC (grid) |
| --- | --- | --- | --- | --- | --- | --- |
| Task 2 (one CoT) | 56.0 [49.2, 62.3] | 49.3 [41.3, 56.7] | 96.6 [93.2, 99.3] | 64.0 [56.7, 72.0] | 66.5 | 0.51 |
| Weighted vote (fixed, unchanged) | 39.8 [33.8, 45.3] | 46.0 [38.0, 54.0] | 99.3 [97.9, 100.0] | 50.0 [42.0, 58.0] | 58.8 | 0.37 |
| Weighted vote, changed (ablation) | 59.7 [53.7, 65.7] | 47.3 [39.3, 55.3] | 100.0 [100.0, 100.0] | 62.7 [55.3, 70.0] | 67.4 | 0.54 |
| Plain self-consistency | 51.3 [44.8, 57.7] | 42.7 [34.7, 50.0] | 100.0 [100.0, 100.0] | 56.7 [48.7, 64.0] | 62.7 | 0.47 |
| Weighted vote (tuned on dev) | 43.0 [37.0, 48.7] | 40.7 [33.3, 48.7] | 99.3 [97.9, 100.0] | 52.7 [44.7, 60.7] | 58.9 | 0.40 |

Paired difference to Task 2 per intervention (points, 95% CI), and in the aggregate:

| Pipeline | Early answering | Adding a mistake | Paraphrasing | Filler tokens | Aggregate |
| --- | --- | --- | --- | --- | --- |
| Weighted vote (fixed, unchanged) | -16.2 [-23.0, -9.2] | -3.3 [-14.0, +6.7] | +2.9 [-0.7, +6.4] | -14.0 [-21.3, -6.0] | -7.7 |
| Weighted vote, changed (ablation) | +3.7 [-3.2, +11.0] | -2.0 [-12.7, +8.0] | +3.6 [+0.7, +7.2] | -1.3 [-8.0, +6.0] | +0.9 |
| Plain self-consistency | -4.7 [-11.8, +3.0] | -6.7 [-16.7, +2.7] | +3.6 [+0.7, +7.2] | -7.3 [-14.0, +0.7] | -3.8 |
| Weighted vote (tuned on dev) | -13.0 [-20.2, -5.5] | -8.7 [-18.7, +0.0] | +2.9 [-0.7, +6.4] | -11.3 [-18.7, -3.3] | -7.6 |
