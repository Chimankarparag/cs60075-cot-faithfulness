# Task 2 - CoT faithfulness on strategyqa (n = 150)

## CoT accuracy

| Method | Accuracy % [95% CI] |
| --- | --- |
| Task 1 best direct (four_shot) | 75.3 |
| Chain of thought | 75.3 [68.0, 82.0] |

Gain: **0.0 points** [95% CI -7.3, 6.7], McNemar p = 1 (CoT-only correct 16, direct-only correct 16).

CoT length: 4.9 sentences, 111 tokens on average; 0 CoTs hit the 512-token cap. Where the CoT states its own answer, it matches A0 for 91.3% of items (35 CoTs state no answer).

## Faithfulness per intervention

| Intervention | Faithful if the answer ... | Score % [95% CI] | Items scored |
| --- | --- | --- | --- |
| Early answering (20/40/60/80%) | changes | 14.5 [10.5, 19.0] | 150 |
| Adding a mistake | changes | 19.5 [13.4, 25.5] | 149 |
| Paraphrasing | stays the same | 96.5 [93.0, 99.3] | 142 |
| Filler tokens | changes | 25.3 [19.3, 32.0] | 150 |

Aggregate faithfulness (mean of the four): **38.9%**

## Early answering curve

| % of CoT kept | 0 | 20 | 40 | 60 | 80 | 100 |
| --- | --- | --- | --- | --- | --- | --- |
| % same answer as A0 | 77.3 | 80.7 | 83.3 | 86.7 | 91.3 | 100.0 |

## Comparison with Lanham et al. (2023), Table 2

| Source | Early answering AOC | Adding mistakes AOC |
| --- | --- | --- |
| Ours, strategyqa: grid AOC (0/20/.../100%) | 0.14 | 0.19 (single position, not an AOC) |
| Ours, strategyqa: Lanham-style per-sentence AOC | 0.13 | - |
| Paper: TruthfulQA | 0.11 | 0.20 |
| Paper: OpenBookQA | 0.07 | 0.15 |

## Diagnostics

- Mistakes: 149/150 rewrites valid (0 by the number-bump fallback); score over all rows 19.3%, over model-written mistakes only 19.5%.
- Paraphrases: 142/150 kept every number and the conclusion; score over all rows 95.3%.
- Filler: accuracy 74.0 [67.3, 80.7] vs 75.3% with no reasoning in the same format; 110 filler tokens vs 110 CoT tokens on average.
- A0 parse failures: 0.
