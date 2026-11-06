# Task 2 - CoT faithfulness on bbh (n = 150, meta-llama/Llama-3.1-8B-Instruct)

## CoT accuracy

| Method | Accuracy % [95% CI] |
| --- | --- |
| Task 1 best direct (four_shot) | 45.3 |
| Chain of thought | 54.0 [46.7, 61.3] |

Gain: **8.7 points** [95% CI -0.7, 17.3], McNemar p = 0.0854 (CoT-only correct 31, direct-only correct 18).

CoT length: 12.7 sentences, 217 tokens on average; 4 CoTs hit the 512-token cap. Where the CoT states its own answer, it matches A0 for 91.0% of items (6 CoTs state no answer).

## Faithfulness per intervention

| Intervention | Faithful if the answer ... | Score % [95% CI] | Items scored |
| --- | --- | --- | --- |
| Early answering (20/40/60/80%) | changes | 53.0 [46.5, 59.5] | 150 |
| Adding a mistake | changes | 48.7 [40.7, 56.7] | 150 |
| Paraphrasing | stays the same | 97.2 [94.3, 99.3] | 141 |
| Filler tokens | changes | 60.0 [52.0, 68.0] | 150 |

Aggregate faithfulness (mean of the four): **64.7%**

## Early answering curve

| % of CoT kept | 0 | 20 | 40 | 60 | 80 | 100 |
| --- | --- | --- | --- | --- | --- | --- |
| % same answer as A0 | 38.7 | 41.3 | 44.7 | 46.0 | 56.0 | 100.0 |

## Comparison with Lanham et al. (2023), Table 2

| Source | Early answering AOC | Adding mistakes AOC |
| --- | --- | --- |
| Ours, bbh: grid AOC (0/20/.../100%) | 0.49 | 0.49 (single position, not an AOC) |
| Ours, bbh: Lanham-style per-sentence AOC | 0.47 | - |
| Paper: LogiQA (logical reasoning) | 0.26 | 0.31 |

## Diagnostics

- Mistakes: 150/150 rewrites valid; score over all rows 48.7%.
- Paraphrases: 141/150 kept the conclusion and every option letter; score over all rows 97.3%.
- Filler: accuracy 44.0 [36.0, 52.0] vs 44.7% with no reasoning in the same format; 216 filler tokens vs 216 CoT tokens on average.
- A0 parse failures: 0.
