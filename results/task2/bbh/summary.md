# Task 2 - CoT faithfulness on bbh (n = 150, meta-llama/Llama-3.1-8B-Instruct)

## CoT accuracy

| Method | Accuracy % [95% CI] |
| --- | --- |
| Task 1 best direct (four_shot) | 45.3 |
| Chain of thought | 47.3 [39.3, 55.3] |

Gain: **2.0 points** [95% CI -8.0, 11.3], McNemar p = 0.788 (CoT-only correct 29, direct-only correct 26).

CoT length: 12.4 sentences, 214 tokens on average; 3 CoTs hit the 512-token cap. Where the CoT states its own answer, it matches A0 for 92.4% of items (6 CoTs state no answer).

## Faithfulness per intervention

| Intervention | Faithful if the answer ... | Score % [95% CI] | Items scored |
| --- | --- | --- | --- |
| Early answering (20/40/60/80%) | changes | 56.0 [49.2, 62.3] | 150 |
| Adding a mistake | changes | 49.3 [41.3, 56.7] | 150 |
| Paraphrasing | stays the same | 96.6 [93.2, 99.3] | 146 |
| Filler tokens | changes | 64.0 [56.7, 72.0] | 150 |

Aggregate faithfulness (mean of the four): **66.5%**

## Early answering curve

| % of CoT kept | 0 | 20 | 40 | 60 | 80 | 100 |
| --- | --- | --- | --- | --- | --- | --- |
| % same answer as A0 | 36.7 | 40.7 | 38.7 | 40.7 | 56.0 | 100.0 |

## Comparison with Lanham et al. (2023), Table 2

| Source | Early answering AOC | Adding mistakes AOC |
| --- | --- | --- |
| Ours, bbh: grid AOC (0/20/.../100%) | 0.51 | 0.49 (single position, not an AOC) |
| Ours, bbh: Lanham-style per-sentence AOC | 0.49 | - |
| Paper: LogiQA (logical reasoning) | 0.26 | 0.31 |

## Diagnostics

- Mistakes: 150/150 rewrites valid; score over all rows 49.3%.
- Paraphrases: 146/150 kept the conclusion and every option letter; score over all rows 96.7%.
- Filler: accuracy 44.7 [36.7, 52.7] vs 44.7% with no reasoning in the same format; 213 filler tokens vs 213 CoT tokens on average.
- A0 parse failures: 0.
