# Task 2 - CoT faithfulness (n = 150, Qwen/Qwen3-8B)

## CoT accuracy

| Method | Accuracy % [95% CI] |
| --- | --- |
| Task 1 best direct (four_shot) | 69.3 |
| Chain of thought | 76.7 [70.0, 83.3] |

Gain: **7.3 points** [95% CI 0.7, 15.3], McNemar p = 0.0801 (CoT-only correct 22, direct-only correct 11).

CoT length: 42.7 sentences, 493 tokens on average; 113 CoTs hit the 512-token cap. Where the CoT states its own answer, it matches A0 for 70.5% of items (55 CoTs state no answer).

## Faithfulness per intervention

| Intervention | Faithful if the answer ... | Score % [95% CI] | Items scored |
| --- | --- | --- | --- |
| Early answering (20/40/60/80%) | changes | 21.3 [15.8, 26.8] | 150 |
| Adding a mistake | changes | 24.6 [18.1, 32.6] | 138 |
| Paraphrasing | stays the same | 92.3 [88.0, 96.5] | 142 |
| Filler tokens | changes | 23.3 [16.7, 30.0] | 150 |

Aggregate faithfulness (mean of the four): **40.4%**

## Early answering curve

| % of CoT kept | 0 | 20 | 40 | 60 | 80 | 100 |
| --- | --- | --- | --- | --- | --- | --- |
| % same answer as A0 | 77.3 | 77.3 | 76.7 | 78.7 | 82.0 | 100.0 |

## Comparison with Lanham et al. (2023), Table 2

| Source | Early answering AOC | Adding mistakes AOC |
| --- | --- | --- |
| Ours: grid AOC (0/20/.../100%) | 0.19 | 0.25 (single position, not an AOC) |
| Ours: Lanham-style per-sentence AOC | 0.21 | - |
| Paper: LogiQA (logical reasoning) | 0.26 | 0.31 |

## Diagnostics

- Mistakes: 138/150 rewrites valid; score over all rows 24.7%.
- Paraphrases: 142/150 kept the conclusion and every option letter; score over all rows 92.0%.
- Filler: accuracy 62.7 [54.7, 70.7] vs 64.0% with no reasoning in the same format; 493 filler tokens vs 493 CoT tokens on average.
- A0 parse failures: 3.
