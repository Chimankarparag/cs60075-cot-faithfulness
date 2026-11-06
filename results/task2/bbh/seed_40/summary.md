# Task 2 - CoT faithfulness on bbh (n = 150, meta-llama/Llama-3.1-8B-Instruct)

## CoT accuracy

| Method | Accuracy % [95% CI] |
| --- | --- |
| Task 1 best direct (four_shot) | 45.3 |
| Chain of thought | 55.3 [47.3, 63.3] |

Gain: **10.0 points** [95% CI -0.7, 20.0], McNemar p = 0.0864 (CoT-only correct 41, direct-only correct 26).

CoT length: 11.9 sentences, 206 tokens on average; 4 CoTs hit the 512-token cap. Where the CoT states its own answer, it matches A0 for 92.3% of items (8 CoTs state no answer).

## Faithfulness per intervention

| Intervention | Faithful if the answer ... | Score % [95% CI] | Items scored |
| --- | --- | --- | --- |
| Early answering (20/40/60/80%) | changes | 54.5 [47.8, 61.0] | 150 |
| Adding a mistake | changes | 55.3 [46.7, 62.7] | 150 |
| Paraphrasing | stays the same | 96.6 [93.2, 99.3] | 146 |
| Filler tokens | changes | 60.0 [52.7, 67.3] | 150 |

Aggregate faithfulness (mean of the four): **66.6%**

## Early answering curve

| % of CoT kept | 0 | 20 | 40 | 60 | 80 | 100 |
| --- | --- | --- | --- | --- | --- | --- |
| % same answer as A0 | 40.0 | 38.7 | 41.3 | 46.7 | 55.3 | 100.0 |

## Comparison with Lanham et al. (2023), Table 2

| Source | Early answering AOC | Adding mistakes AOC |
| --- | --- | --- |
| Ours, bbh: grid AOC (0/20/.../100%) | 0.50 | 0.55 (single position, not an AOC) |
| Ours, bbh: Lanham-style per-sentence AOC | 0.49 | - |
| Paper: LogiQA (logical reasoning) | 0.26 | 0.31 |

## Diagnostics

- Mistakes: 150/150 rewrites valid; score over all rows 55.3%.
- Paraphrases: 146/150 kept the conclusion and every option letter; score over all rows 96.0%.
- Filler: accuracy 42.7 [34.7, 51.3] vs 44.7% with no reasoning in the same format; 205 filler tokens vs 205 CoT tokens on average.
- A0 parse failures: 0.
