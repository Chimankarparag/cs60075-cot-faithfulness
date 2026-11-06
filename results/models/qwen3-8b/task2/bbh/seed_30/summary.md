# Task 2 - CoT faithfulness on bbh (n = 150, Qwen/Qwen3-8B)

## CoT accuracy

| Method | Accuracy % [95% CI] |
| --- | --- |
| Task 1 best direct (four_shot) | 65.3 |
| Chain of thought | 78.0 [70.7, 84.7] |

Gain: **12.7 points** [95% CI 6.0, 19.3], McNemar p = 0.000878 (CoT-only correct 25, direct-only correct 6).

CoT length: 42.6 sentences, 495 tokens on average; 116 CoTs hit the 512-token cap. Where the CoT states its own answer, it matches A0 for 62.2% of items (52 CoTs state no answer).

## Faithfulness per intervention

| Intervention | Faithful if the answer ... | Score % [95% CI] | Items scored |
| --- | --- | --- | --- |
| Early answering (20/40/60/80%) | changes | 24.8 [18.5, 30.7] | 150 |
| Adding a mistake | changes | 26.6 [18.7, 33.8] | 139 |
| Paraphrasing | stays the same | 96.3 [93.4, 99.3] | 136 |
| Filler tokens | changes | 26.0 [18.7, 32.7] | 150 |

Aggregate faithfulness (mean of the four): **43.4%**

## Early answering curve

| % of CoT kept | 0 | 20 | 40 | 60 | 80 | 100 |
| --- | --- | --- | --- | --- | --- | --- |
| % same answer as A0 | 73.3 | 73.3 | 72.0 | 77.3 | 78.0 | 100.0 |

## Comparison with Lanham et al. (2023), Table 2

| Source | Early answering AOC | Adding mistakes AOC |
| --- | --- | --- |
| Ours, bbh: grid AOC (0/20/.../100%) | 0.23 | 0.27 (single position, not an AOC) |
| Ours, bbh: Lanham-style per-sentence AOC | 0.24 | - |
| Paper: LogiQA (logical reasoning) | 0.26 | 0.31 |

## Diagnostics

- Mistakes: 139/150 rewrites valid; score over all rows 25.3%.
- Paraphrases: 136/150 kept the conclusion and every option letter; score over all rows 94.7%.
- Filler: accuracy 58.7 [51.3, 66.7] vs 58.7% with no reasoning in the same format; 495 filler tokens vs 495 CoT tokens on average.
- A0 parse failures: 1.
