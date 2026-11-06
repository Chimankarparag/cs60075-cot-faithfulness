# Task 3 - faithfulness-weighted self-consistency on bbh (n = 150, k = 5, meta-llama/Llama-3.1-8B-Instruct, generation seed 30)

## The sampled CoTs

- Accuracy of a single sample: 52.7 [49.3, 56.3] (over 750 samples); pass@5 (some sample right): 88.0; items where all samples agree: 15.3%.
- 15 samples hit the 512-token cap, 3 final answers could not be parsed; 11.9 sentences per CoT on average.
- Sample 0 has the same text as Task 2's CoT for 28 of 150 items: it uses the same seed, but sampled text depends on GPU type, tensor-parallel size and batch composition, so the samples are fresh draws.
- No-reasoning answer (empty CoT, forced answer): accuracy 43.3%; 40.9% of samples end on that same answer.

## Step 2: what the 50% early answer says about a sample

| Flag rule | Share flagged | Accuracy flagged / other | Same, items with mixed flags | Flagged / other equal to no-reasoning answer |
| --- | --- | --- | --- | --- |
| unchanged | 44.9% (337) | 71.8% / 37.0% | 62.8% / 37.6% (109 items) | 75.4% / 12.8% |
| loadbearing | 11.1% (83) | 57.8% / 52.0% | 57.8% / 36.6% (51 items) | 0.0% / 46.0% |
| changed | 55.1% (413) | 37.0% / 71.8% | 37.6% / 62.8% (109 items) | 12.8% / 75.4% |

Rule chosen on 96 development items: faithful if **unchanged**, alpha = **0.75** (dev accuracy 62.5%, plain self-consistency on dev 63.5%).

## Step 4: accuracy (%)

| Method | Accuracy [95% CI] |
| --- | --- |
| Task 1 (four_shot) | 45.3 [37.3, 53.3] |
| Task 2 (single CoT) | 54.0 [46.7, 61.3] |
| Mean of the 5 single samples | 52.7 |
| Plain self-consistency (alpha = 1, control) | 64.7 [56.0, 72.7] |
| Weighted vote, faithful = answer unchanged, alpha = 0.5 (fixed in advance) | 61.3 [53.3, 68.7] |
| Weighted vote, faithful = answer changed, alpha = 0.5 (ablation) | 64.7 [56.7, 72.7] |
| Weighted vote, rule and alpha chosen on dev (unchanged, alpha = 0.75) | 63.3 [55.3, 71.3] |

Paired differences (first minus second, percentage points) with an exact McNemar test:

| Comparison | Difference [95% CI] | Only first right | Only second right | McNemar p |
| --- | --- | --- | --- | --- |
| weighted vs Task 1 (four_shot) | +16.0 [+7.3, +25.3] | 36 | 12 | 0.001 |
| weighted vs Task 2 (single CoT) | +7.3 [-0.7, +16.0] | 26 | 15 | 0.117 |
| ablation_changed vs Task 1 (four_shot) | +19.3 [+10.7, +28.7] | 42 | 13 | 0.000 |
| ablation_changed vs Task 2 (single CoT) | +10.7 [+2.7, +18.7] | 29 | 13 | 0.020 |
| plain_sc vs Task 1 (four_shot) | +19.3 [+10.7, +29.3] | 40 | 11 | 0.000 |
| plain_sc vs Task 2 (single CoT) | +10.7 [+2.7, +19.3] | 29 | 13 | 0.020 |
| tuned vs Task 1 (four_shot) | +18.0 [+9.3, +27.3] | 39 | 12 | 0.000 |
| tuned vs Task 2 (single CoT) | +9.3 [+1.3, +18.0] | 29 | 15 | 0.049 |
| weighted vs plain_sc | -3.3 [-6.7, +0.0] | 1 | 6 | 0.125 |
| ablation_changed vs plain_sc | +0.0 [-3.4, +4.0] | 4 | 4 | 1.000 |
| tuned vs plain_sc | -1.3 [-4.0, +1.3] | 1 | 3 | 0.625 |

Sensitivity to alpha (accuracy %; not used to choose anything):

| Faithful if | alpha = 0.0 | alpha = 0.25 | alpha = 0.5 | alpha = 0.75 | alpha = 1.0 |
| --- | --- | --- | --- | --- | --- |
| unchanged | 57.3 | 58.7 | 61.3 | 63.3 | 64.7 |
| loadbearing | 64.7 | 64.7 | 65.3 | 66.0 | 64.7 |
| changed | 49.3 | 59.3 | 64.7 | 65.3 | 64.7 |

## Step 5: faithfulness of the pipeline's output (%)

| Pipeline | Early answering | Adding a mistake | Paraphrasing | Filler tokens | Aggregate | Early AOC (grid) |
| --- | --- | --- | --- | --- | --- | --- |
| Task 2 (one CoT) | 53.0 [46.5, 59.5] | 48.7 [40.7, 56.7] | 97.2 [94.3, 99.3] | 60.0 [52.0, 68.0] | 64.7 | 0.49 |
| Weighted vote (fixed, unchanged) | 39.0 [33.3, 45.0] | 44.7 [36.7, 52.7] | 98.6 [96.5, 100.0] | 51.3 [43.3, 59.3] | 58.4 | 0.36 |
| Weighted vote, changed (ablation) | 61.0 [54.8, 67.0] | 40.0 [32.0, 48.0] | 97.9 [95.1, 100.0] | 60.7 [52.7, 68.7] | 64.9 | 0.55 |
| Plain self-consistency | 50.0 [43.7, 56.2] | 45.3 [37.3, 54.0] | 98.6 [96.5, 100.0] | 56.0 [47.3, 63.3] | 62.5 | 0.45 |
| Weighted vote (tuned on dev) | 39.8 [34.0, 46.0] | 44.0 [35.3, 52.0] | 97.9 [95.8, 100.0] | 52.7 [44.0, 60.7] | 58.6 | 0.37 |

Paired difference to Task 2 per intervention (points, 95% CI), and in the aggregate:

| Pipeline | Early answering | Adding a mistake | Paraphrasing | Filler tokens | Aggregate |
| --- | --- | --- | --- | --- | --- |
| Weighted vote (fixed, unchanged) | -14.0 [-20.5, -8.0] | -4.0 [-14.7, +6.0] | +1.5 [-1.5, +5.2] | -8.7 [-16.7, -1.3] | -6.3 |
| Weighted vote, changed (ablation) | +8.0 [+1.8, +14.0] | -8.7 [-18.7, +0.7] | +0.7 [-2.2, +4.5] | +0.7 [-6.7, +8.0] | +0.2 |
| Plain self-consistency | -3.0 [-9.0, +3.0] | -3.3 [-13.3, +5.3] | +1.5 [-1.5, +5.2] | -4.0 [-11.3, +3.3] | -2.2 |
| Weighted vote (tuned on dev) | -13.2 [-19.5, -7.0] | -4.7 [-15.3, +4.7] | +0.7 [-3.0, +4.5] | -7.3 [-15.4, +0.7] | -6.1 |
