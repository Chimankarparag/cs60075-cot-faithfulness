# Task 2 - CoT faithfulness (n = 150, meta-llama/Llama-3.1-8B-Instruct)

## CoT accuracy

| Method | Accuracy % [95% CI] |
| --- | --- |
| Task 1 best direct (zero_shot) | 44.7 |
| Chain of thought | 58.0 [50.0, 66.0] |

Gain: **13.3 points** [95% CI 4.7, 22.7], McNemar p = 0.00779 (CoT-only correct 36, direct-only correct 16).

CoT length: 12.2 sentences, 211 tokens on average; 6 CoTs hit the 512-token cap. Where the CoT states its own answer, it matches A0 for 90.1% of items (9 CoTs state no answer).

## Faithfulness per intervention

| Intervention | Faithful if the answer ... | Score % [95% CI] | Items scored |
| --- | --- | --- | --- |
| Early answering (20/40/60/80%) | changes | 54.0 [47.8, 60.5] | 150 |
| Adding a mistake | changes | 47.3 [39.3, 54.7] | 150 |
| Paraphrasing | stays the same | 94.3 [90.1, 97.9] | 141 |
| Filler tokens | changes | 60.0 [52.0, 68.0] | 150 |

Aggregate faithfulness (mean of the four): **63.9%**

## Early answering curve

| % of CoT kept | 0 | 20 | 40 | 60 | 80 | 100 |
| --- | --- | --- | --- | --- | --- | --- |
| % same answer as A0 | 40.0 | 36.0 | 43.3 | 46.7 | 58.0 | 100.0 |

## Comparison with Lanham et al. (2023), Table 2

| Source | Early answering AOC | Adding mistakes AOC |
| --- | --- | --- |
| Ours: grid AOC (0/20/.../100%) | 0.49 | 0.47 (single position, not an AOC) |
| Ours: Lanham-style per-sentence AOC | 0.48 | - |
| Paper: LogiQA (logical reasoning) | 0.26 | 0.31 |

## Diagnostics

- Mistakes: 150/150 rewrites valid; score over all rows 47.3%.
- Paraphrases: 141/150 kept the conclusion and every option letter; score over all rows 92.7%.
- Filler: accuracy 44.7 [36.0, 52.7] vs 44.7% with no reasoning in the same format; 210 filler tokens vs 210 CoT tokens on average.
- A0 parse failures: 0.
