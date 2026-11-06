# Task 2 - the paper's versions of three interventions (Lanham et al., 2023)

## Adding mistakes at every position

1406 valid mistakes of 1500 rewrites, over 150 CoTs. AOC (mean share of positions where the answer changed): **0.23** [0.18, 0.28]; paper, LogiQA: 0.31. Accuracy after a mistake: 80.9%.

| Share of CoT before the mistake (%) | 0-20 | 20-40 | 40-60 | 60-80 | 80-100 |
| --- | --- | --- | --- | --- | --- |
| % same answer as original | 78.8 (n=335) | 77.1 (n=323) | 76.7 (n=270) | 75.9 (n=237) | 77.6 (n=241) |

## Paraphrasing the first part of the CoT, then re-sampling the rest

Accuracy of the original CoTs: 75.3%.

| % of sentences paraphrased | Accuracy % | % same answer as original | Valid paraphrases |
| --- | --- | --- | --- |
| 20 | 79.7 | 81.2 | 138/150 |
| 40 | 86.5 | 77.0 | 126/150 |
| 60 | 87.8 | 74.0 | 123/150 |
| 80 | 88.2 | 78.7 | 127/150 |
| 100 | 91.1 | 76.3 | 135/150 |

## Filler tokens of increasing length

Accuracy with the original CoT: 75.3%.

| Percentile of CoT length | Filler tokens | Accuracy % | % same answer as with the CoT |
| --- | --- | --- | --- |
| 0 | 0 | 58.0 | 74.7 |
| 10 | 420 | 58.0 | 75.3 |
| 20 | 503 | 58.7 | 75.3 |
| 30 | 512 | 58.7 | 76.0 |
| 40 | 512 | 58.7 | 76.0 |
| 50 | 512 | 58.7 | 76.0 |
| 60 | 512 | 58.7 | 76.0 |
| 70 | 512 | 58.7 | 76.0 |
| 80 | 512 | 58.7 | 76.0 |
| 90 | 512 | 58.7 | 76.0 |
| 100 | 512 | 58.7 | 76.0 |
