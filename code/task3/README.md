# Task 3 — Faithfulness-weighted self-consistency (40 marks)

Use Task 2's early-answering intervention as a per-sample faithfulness signal inside a self-consistency vote,
and test whether that improves accuracy and aggregate faithfulness over a single, unweighted CoT.

Everything is in [`task3.ipynb`](task3.ipynb), which also writes the model comparison
(`results/comparison/`).

| Spec step | What the notebook does |
| --- | --- |
| 1. Sample k = 5 CoTs (T 0.7) | Same prompt and decoding as Task 2; sample j of item i uses seed `49 + 100000·j + i`. Each sample's final answer A0_j is read off with the forced-answer prompt |
| 2. Early-answer each sample at 50% | Keeps floor(0.5 · n) sentences, forces an answer, compares it with A0_j. Also reads each item's answer with an empty CoT (the no-reasoning answer) |
| 3. Weighted majority vote | Flagged samples weigh 1, the others alpha; unparsable answers abstain; ties go to the letter whose first supporting sample has the lowest index; the pipeline's CoT is the winning answer's highest-weight sample |
| Choosing the rule | Scores every candidate rule and alpha on the 96 dev items and picks one (below) |
| 4. Accuracy vs Tasks 1 and 2 | Paired bootstrap and exact McNemar against Task 1, Task 2 and plain voting |
| 5. Four interventions on the output | Task 2's interventions on the CoT each vote selects; aggregate faithfulness vs Task 2 |

## Flag rules and pipelines

| Rule | A sample is flagged faithful if |
| --- | --- |
| `unchanged` | its answer at 50% equals its final answer (the assignment's wording) |
| `loadbearing` | `unchanged` **and** its final answer differs from the no-reasoning answer. Lanham et al. (Sec. 3) use "same answer with and without CoT" as their marker of post-hoc reasoning; "unchanged at 50%" cannot tell "settled by the first half of the reasoning" from "settled before any reasoning", and this rule keeps only the first |
| `changed` | its answer at 50% differs from its final answer (the Task 2 / Lanham direction; ablation only) |

| Pipeline | Rule, alpha | Why |
| --- | --- | --- |
| `weighted` | unchanged, 0.5 | fixed in advance |
| `tuned` | chosen on the dev items | the rule and alpha with the best dev accuracy among unchanged / loadbearing × alpha ∈ {0, 0.25, 0.5, 0.75}; ties go to unchanged, then the alpha closest to 0.5, then the larger alpha |
| `ablation_changed` | changed, 0.5 | the opposite reading of "faithful" |
| `plain_sc` | alpha = 1 | control: ordinary self-consistency |

The dev items are the 96 BBH rows that are neither among the 150 evaluated items nor the 4 exemplars, so no choice
is made by looking at the evaluation items. alpha is always below 1 in the tuned grid, so the vote stays weighted
toward the flagged samples, as the assignment asks.

## Open question for the TA

The assignment calls a sample faithful if its answer does *not* change at 50% truncation; Task 2 and Lanham et
al. call reasoning faithful when the answer *does* change when the CoT is cut. Both readings are reported.
