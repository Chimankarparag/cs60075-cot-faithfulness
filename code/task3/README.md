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

## Outputs

`results/models/<model>/task3/bbh/`: `samples.jsonl`, `early50.jsonl`, `prior.jsonl`, `votes.jsonl`,
`pipeline_<name>/{early,mistake,paraphrase,filler}.jsonl`, `metrics.json`, `summary.md`, `run_info.json`, and
`dev/` (the same for the 96 dev items, plus `tuning.json` / `tuning.md`). The notebook's last section writes
`results/comparison/models.md`, `models.json` and `runs.md`.

## Result (seed 49, n = 150)

| | Llama-3.1-8B | Qwen3-8B |
| --- | --- | --- |
| Task 2 single CoT accuracy | 58.0 | 76.7 |
| Plain self-consistency | 61.3 | 79.3 |
| Weighted, unchanged, alpha 0.5 | 62.0 | 78.7 |
| Weighted, tuned on dev (unchanged, alpha 0.75 for both) | 62.0 | 80.0 |
| Weighted, changed (ablation) | 58.7 | 80.7 |
| Aggregate faithfulness: Task 2 / plain / weighted / tuned / changed | 63.9 / 59.6 / 54.4 / 56.9 / 66.8 | 40.4 / 37.9 / 36.8 / 37.0 / 40.3 |

Weighting toward samples flagged "unchanged" is within one point of plain voting for both models (+0.7, -0.7;
p = 1.0), even with the rule chosen on dev. The reason shows in the flags: 80% (Llama) and 95% (Qwen) of flagged
samples end on the model's no-reasoning answer, so the weights pull the vote toward the direct answer and toward
post-hoc CoTs, which also lowers the measured faithfulness of the output. The load-bearing rule removes that
confound but flags only 4-9% of samples. The opposite reading (`changed`) keeps faithfulness at Task 2's level.

## Open question for the TA

The assignment calls a sample faithful if its answer does *not* change at 50% truncation; Task 2 and Lanham et
al. call reasoning faithful when the answer *does* change when the CoT is cut. Both readings are reported.
