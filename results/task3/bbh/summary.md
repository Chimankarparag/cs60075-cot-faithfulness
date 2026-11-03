# Task 3 - faithfulness-weighted self-consistency on bbh (n = 150, k = 5)

## The sampled CoTs

- Accuracy of a single sample: 53.3 [49.9, 56.8] (over 750 samples); pass@5 (some sample right): 83.3; items where all samples agree: 20.7%.
- 17 samples hit the 512-token cap, 1 final answers could not be parsed; 11.7 sentences per CoT on average.
- Sample 0 has the same text as Task 2's CoT for 45 of 150 items: it uses the same seed, but sampled text depends on GPU type, tensor-parallel size and batch composition, so the samples are fresh draws.

## Step 2: what the 50% early answer says about a sample

| Flag rule | Share flagged | Accuracy, flagged samples | Accuracy, other samples |
| --- | --- | --- | --- |
| faithful if answer unchanged | 47.6% (357) | 70.3% | 37.9% (393) |
| faithful if answer changed | 52.4% (393) | 37.9% | 70.3% (357) |

## Step 4: accuracy (%)

| Method | Accuracy [95% CI] |
| --- | --- |
| Task 1 (zero_shot) | 46.0 [38.0, 54.0] |
| Task 2 (single CoT) | 54.0 [46.0, 62.0] |
| Mean of the 5 single samples | 53.3 |
| Plain self-consistency (alpha = 1, control) | 62.7 [54.7, 70.7] |
| Weighted vote, faithful = answer unchanged, alpha = 0.5 (main) | 62.0 [54.0, 70.0] |
| Weighted vote, faithful = answer changed, alpha = 0.5 (ablation) | 61.3 [52.7, 69.3] |

Paired differences (first minus second, percentage points) with an exact McNemar test:

| Comparison | Difference [95% CI] | Only first right | Only second right | McNemar p |
| --- | --- | --- | --- | --- |
| weighted vs Task 1 (zero_shot) | +16.0 [+8.0, +24.0] | 34 | 10 | 0.000 |
| weighted vs Task 2 (single CoT) | +8.0 [+0.0, +15.3] | 26 | 14 | 0.081 |
| ablation_changed vs Task 1 (zero_shot) | +15.3 [+6.0, +24.7] | 38 | 15 | 0.002 |
| ablation_changed vs Task 2 (single CoT) | +7.3 [-2.0, +15.3] | 28 | 17 | 0.135 |
| plain_sc vs Task 1 (zero_shot) | +16.7 [+8.0, +24.7] | 36 | 11 | 0.000 |
| plain_sc vs Task 2 (single CoT) | +8.7 [+0.0, +16.7] | 28 | 15 | 0.066 |
| weighted vs plain_sc | -0.7 [-4.0, +2.7] | 3 | 4 | 1.000 |
| ablation_changed vs plain_sc | -1.3 [-5.3, +2.0] | 3 | 5 | 0.727 |

Sensitivity to alpha (accuracy %; not used to choose alpha):

| Faithful if | alpha = 0.0 | alpha = 0.25 | alpha = 0.5 | alpha = 1.0 |
| --- | --- | --- | --- | --- |
| unchanged | 56.7 | 57.3 | 62.0 | 62.7 |
| changed | 50.0 | 56.7 | 61.3 | 62.7 |

## Step 5: faithfulness of the pipeline's output (%)

| Pipeline | Early answering | Adding a mistake | Paraphrasing | Filler tokens | Aggregate | Early AOC (grid) |
| --- | --- | --- | --- | --- | --- | --- |
| Task 2 (one CoT) | 48.5 [41.3, 55.8] | 48.3 [40.9, 55.7] | 97.2 [94.4, 99.3] | 50.7 [42.7, 59.3] | 61.2 | 0.44 |
| Weighted vote (main) | 36.2 [30.0, 42.8] | 40.5 [33.1, 48.6] | 97.9 [95.0, 100.0] | 46.7 [38.7, 54.7] | 55.3 | 0.34 |
| Weighted vote, changed (ablation) | 56.5 [50.0, 63.0] | 45.0 [36.9, 53.0] | 97.2 [94.5, 99.3] | 58.7 [50.7, 66.0] | 64.3 | 0.51 |
| Plain self-consistency | 44.5 [38.0, 51.5] | 39.5 [32.0, 46.9] | 97.2 [94.4, 99.3] | 50.7 [42.7, 58.7] | 58.0 | 0.41 |

Paired difference to Task 2 per intervention (points, 95% CI), and in the aggregate:

| Pipeline | Early answering | Adding a mistake | Paraphrasing | Filler tokens | Aggregate |
| --- | --- | --- | --- | --- | --- |
| Weighted vote (main) | -12.3 [-19.5, -5.5] | -8.1 [-16.9, +0.7] | +0.7 [-2.9, +4.4] | -4.0 [-12.7, +4.7] | -5.9 |
| Weighted vote, changed (ablation) | +8.0 [+1.8, +14.7] | -3.4 [-13.4, +6.0] | +0.0 [-4.2, +3.5] | +8.0 [-0.0, +16.7] | +3.2 |
| Plain self-consistency | -4.0 [-11.3, +3.2] | -9.5 [-18.4, -1.4] | +0.0 [-4.3, +4.3] | +0.0 [-8.7, +8.7] | -3.2 |
