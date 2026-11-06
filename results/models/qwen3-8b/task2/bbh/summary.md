# Task 2 - CoT faithfulness on bbh (n = 150, Qwen/Qwen3-8B)

## CoT accuracy

| Method | Accuracy % [95% CI] |
| --- | --- |
| Task 1 best direct (four_shot) | 65.3 |
| Chain of thought | 75.3 [68.0, 82.7] |

Gain: **10.0 points** [95% CI 2.7, 17.3], McNemar p = 0.0107 (CoT-only correct 23, direct-only correct 8).

CoT length: 42.7 sentences, 494 tokens on average; 118 CoTs hit the 512-token cap. Where the CoT states its own answer, it matches A0 for 66.0% of items (47 CoTs state no answer).

## Faithfulness per intervention

| Intervention | Faithful if the answer ... | Score % [95% CI] | Items scored |
| --- | --- | --- | --- |
| Early answering (20/40/60/80%) | changes | 24.5 [18.5, 30.7] | 150 |
| Adding a mistake | changes | 28.6 [20.7, 36.4] | 140 |
| Paraphrasing | stays the same | 94.8 [91.1, 98.5] | 135 |
| Filler tokens | changes | 24.0 [16.7, 30.7] | 150 |

Aggregate faithfulness (mean of the four): **43.0%**

## Early answering curve

| % of CoT kept | 0 | 20 | 40 | 60 | 80 | 100 |
| --- | --- | --- | --- | --- | --- | --- |
| % same answer as A0 | 75.3 | 73.3 | 76.0 | 74.7 | 78.0 | 100.0 |

## Comparison with Lanham et al. (2023), Table 2

| Source | Early answering AOC | Adding mistakes AOC |
| --- | --- | --- |
| Ours, bbh: grid AOC (0/20/.../100%) | 0.22 | 0.29 (single position, not an AOC) |
| Ours, bbh: Lanham-style per-sentence AOC | 0.22 | - |
| Paper: LogiQA (logical reasoning) | 0.26 | 0.31 |

## Diagnostics

- Mistakes: 140/150 rewrites valid; score over all rows 27.3%.
- Paraphrases: 135/150 kept the conclusion and every option letter; score over all rows 93.3%.
- Filler: accuracy 58.7 [51.3, 66.7] vs 58.7% with no reasoning in the same format; 493 filler tokens vs 493 CoT tokens on average.
- A0 parse failures: 1.
