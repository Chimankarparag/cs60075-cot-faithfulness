# Task 2 - the paper's versions of three interventions (Lanham et al., 2023)

## Adding mistakes at every position

1429 valid mistakes of 1500 rewrites, over 150 CoTs. AOC (mean share of positions where the answer changed): **0.21** [0.17, 0.26]; paper, LogiQA: 0.31. Accuracy after a mistake: 81.7%.

| Share of CoT before the mistake (%) | 0-20 | 20-40 | 40-60 | 60-80 | 80-100 |
| --- | --- | --- | --- | --- | --- |
| % same answer as original | 80.2 (n=348) | 80.8 (n=344) | 73.8 (n=240) | 74.0 (n=242) | 83.1 (n=255) |

## Paraphrasing the first part of the CoT, then re-sampling the rest

Accuracy of the original CoTs: 76.7%.

| % of sentences paraphrased | Accuracy % | % same answer as original | Valid paraphrases |
| --- | --- | --- | --- |
| 20 | 81.3 | 84.9 | 139/150 |
| 40 | 89.1 | 75.0 | 128/150 |
| 60 | 88.0 | 75.2 | 125/150 |
| 80 | 89.9 | 76.7 | 129/150 |
| 100 | 87.1 | 77.9 | 140/150 |

## Filler tokens of increasing length

Accuracy with the original CoT: 76.7%.

| Percentile of CoT length | Filler tokens | Accuracy % | % same answer as with the CoT |
| --- | --- | --- | --- |
| 0 | 0 | 64.0 | 77.3 |
| 10 | 429 | 62.0 | 75.3 |
| 20 | 496 | 62.7 | 76.0 |
| 30 | 512 | 62.7 | 76.0 |
| 40 | 512 | 62.7 | 76.0 |
| 50 | 512 | 62.7 | 76.0 |
| 60 | 512 | 62.7 | 76.0 |
| 70 | 512 | 62.7 | 76.0 |
| 80 | 512 | 62.7 | 76.0 |
| 90 | 512 | 62.7 | 76.0 |
| 100 | 512 | 62.7 | 76.0 |
