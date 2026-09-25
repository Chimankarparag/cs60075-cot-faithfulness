# Task 2 - CoT faithfulness on gsm8k (n = 200)

## CoT accuracy

| Method | Accuracy % [95% CI] |
| --- | --- |
| Task 1 best direct (zero_shot) | 16.5 |
| Chain of thought | 90.0 [86.0, 94.0] |

Gain: **73.5 points** [95% CI 66.5, 80.0], McNemar p = 1.05e-40 (CoT-only correct 150, direct-only correct 3).

CoT length: 8.7 sentences, 156 tokens on average; 0 CoTs hit the 512-token cap. Where the CoT states its own answer, it matches A0 for 95.0% of items (0 CoTs state no answer).

## Faithfulness per intervention

| Intervention | Faithful if the answer ... | Score % [95% CI] | Items scored |
| --- | --- | --- | --- |
| Early answering (20/40/60/80%) | changes | 63.7 [59.9, 67.4] | 200 |
| Adding a mistake | changes | 65.5 [59.0, 72.0] | 200 |
| Paraphrasing | stays the same | 99.4 [98.3, 100.0] | 179 |
| Filler tokens | changes | 85.0 [80.0, 89.5] | 200 |

Aggregate faithfulness (mean of the four): **78.4%**

## Early answering curve

| % of CoT kept | 0 | 20 | 40 | 60 | 80 | 100 |
| --- | --- | --- | --- | --- | --- | --- |
| % same answer as A0 | 10.0 | 11.0 | 15.0 | 42.5 | 76.5 | 100.0 |

## Comparison with Lanham et al. (2023), Table 2

| Source | Early answering AOC | Adding mistakes AOC |
| --- | --- | --- |
| Ours, gsm8k: grid AOC (0/20/.../100%) | 0.60 | 0.66 (single position, not an AOC) |
| Ours, gsm8k: Lanham-style per-sentence AOC | 0.56 | - |
| Paper: AQuA (algebra word problems) | 0.44 | 0.52 |

## Diagnostics

- Mistakes: 200/200 rewrites valid (6 by the number-bump fallback); score over all rows 65.5%, over model-written mistakes only 64.4%.
- Paraphrases: 179/200 kept every number and the conclusion; score over all rows 99.5%.
- Filler: accuracy 15.5 [11.0, 20.5] vs 10.0% with no reasoning in the same format; 155 filler tokens vs 155 CoT tokens on average.
- A0 parse failures: 0.
