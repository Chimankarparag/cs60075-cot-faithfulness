# Task 2 - CoT faithfulness on bbh (n = 150, Qwen/Qwen3-8B)

## CoT accuracy

| Method | Accuracy % [95% CI] |
| --- | --- |
| Task 1 best direct (four_shot) | 65.3 |
| Chain of thought | 73.3 [66.0, 80.7] |

Gain: **8.0 points** [95% CI 1.3, 14.7], McNemar p = 0.0357 (CoT-only correct 20, direct-only correct 8).

CoT length: 43.2 sentences, 496 tokens on average; 117 CoTs hit the 512-token cap. Where the CoT states its own answer, it matches A0 for 61.2% of items (47 CoTs state no answer).

## Faithfulness per intervention

| Intervention | Faithful if the answer ... | Score % [95% CI] | Items scored |
| --- | --- | --- | --- |
| Early answering (20/40/60/80%) | changes | 21.3 [16.0, 26.7] | 150 |
| Adding a mistake | changes | 23.4 [16.8, 30.7] | 137 |
| Paraphrasing | stays the same | 90.5 [85.4, 94.9] | 137 |
| Filler tokens | changes | 24.0 [17.3, 30.7] | 150 |

Aggregate faithfulness (mean of the four): **39.8%**

## Early answering curve

| % of CoT kept | 0 | 20 | 40 | 60 | 80 | 100 |
| --- | --- | --- | --- | --- | --- | --- |
| % same answer as A0 | 76.7 | 76.7 | 78.0 | 79.3 | 80.7 | 100.0 |

## Comparison with Lanham et al. (2023), Table 2

| Source | Early answering AOC | Adding mistakes AOC |
| --- | --- | --- |
| Ours, bbh: grid AOC (0/20/.../100%) | 0.19 | 0.23 (single position, not an AOC) |
| Ours, bbh: Lanham-style per-sentence AOC | 0.20 | - |
| Paper: LogiQA (logical reasoning) | 0.26 | 0.31 |

## Diagnostics

- Mistakes: 137/150 rewrites valid; score over all rows 22.7%.
- Paraphrases: 137/150 kept the conclusion and every option letter; score over all rows 90.0%.
- Filler: accuracy 57.3 [50.0, 64.7] vs 58.7% with no reasoning in the same format; 496 filler tokens vs 496 CoT tokens on average.
- A0 parse failures: 1.
