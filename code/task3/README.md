# Task 3 — Faithfulness-weighted self-consistency (40 marks)

Use Task 2's early-answering intervention as a per-sample faithfulness signal inside a self-consistency vote,
and test whether that improves accuracy and aggregate faithfulness over a single, unweighted CoT.

| Spec step | File | What it does |
| --- | --- | --- |
| 1. Sample k = 5 CoTs (T 0.7) | `sample_k.py` | Same prompt and decoding as Task 2; sample j of item i uses seed `s + 100000·j + i` for generation seed s ∈ {20, 30, 40}. Each sample's final answer A0_j is read off with the forced-answer prompt |
| 2. Early-answer each sample at 50% | `weighted_vote.py` | Keeps floor(0.5 · n) sentences, forces an answer, compares it with A0_j. Also reads each item's answer with an empty CoT (the no-reasoning answer) |
| 3. Weighted majority vote | `weighted_vote.py` | Flagged samples weigh 1, the others alpha; unparsable answers abstain; ties go to the letter whose first supporting sample has the lowest index; the pipeline's CoT is the winning answer's highest-weight sample |
| Choosing the rule | `tune.py` | Scores every candidate rule and alpha on the 96 dev items and picks one (below) |
| 4. Accuracy vs Tasks 1 and 2 | `evaluate.py` | Paired bootstrap and exact McNemar against Task 1 and the Task 2 run of the same seed, and against plain voting |
| 5. Four interventions on the output | `evaluate.py` + `run_task3.py` | Task 2's interventions on the CoT each vote selects; aggregate faithfulness vs Task 2 |
| Across seeds | `seeds.py` | Tasks 2 and 3 for seeds 20, 30, 40: per seed, mean, SD, how often each comparison has the same sign |

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

## Run

```bash
python code/task3/run_task3.py --split dev --tp 2         # dev items: samples, 50% answers, tuning.json
python code/task3/run_task3.py --tp 2                     # eval items, seed 20 (Tasks 1 and 2 first)
python code/task3/run_task3.py --seed 30 --tp 2           # and 40
python code/task3/run_task3.py --stages score             # rebuild metrics/figures, no GPU
python code/task3/seeds.py                                # summary across seeds
python code/task3/run_task3.py --model qwen3-8b ...       # every command works for the second model
```

Outputs: `results/task3/bbh/` (seed 20), `seed_30/`, `seed_40/`, `dev/`, `seeds_summary.md`;
`results/models/qwen3-8b/task3/bbh/` for Qwen3-8B. Each folder has `samples.jsonl`, `early50.jsonl`, `prior.jsonl`,
`votes.jsonl`, `pipeline_<name>/{early,mistake,paraphrase,filler}.jsonl`, `metrics.json`, `summary.md`,
`figures/` and `run_info.json`.

## Result (mean over seeds 20, 30, 40; n = 150)

| | Llama-3.1-8B | Qwen3-8B |
| --- | --- | --- |
| Task 2 single CoT accuracy | 52.2 | 75.6 |
| Plain self-consistency | 64.4 | 76.4 |
| Weighted, unchanged, alpha 0.5 | 63.1 | 73.3 |
| Weighted, tuned on dev (unchanged, alpha 0.75 for both) | 64.9 | 76.0 |
| Weighted, changed (ablation) | 63.3 | 79.1 |
| Aggregate faithfulness: Task 2 / plain / weighted / tuned / changed | 65.9 / 62.8 / 57.9 / 58.9 / 65.7 | 42.1 / 40.0 / 37.9 / 39.1 / 42.2 |

Voting is what helps (Llama +12 points over its single CoT in every seed). Weighting toward samples flagged
"unchanged" never beats plain voting by more than noise, for either model, even with the rule chosen on dev.
The reason shows in the flags: 78% (Llama) and 95% (Qwen) of flagged samples end on the model's no-reasoning
answer, so the weights pull the vote toward the weaker direct answer and toward post-hoc CoTs, which also lowers
the measured faithfulness of the output. The load-bearing rule removes that confound but flags only 4-10% of
samples. The opposite reading (`changed`) keeps faithfulness at Task 2's level and, for Qwen, is the most accurate
pipeline (+2.7 over plain voting in all three seeds). Full tables: `results/task3/bbh/seeds_summary.md`,
`results/models/qwen3-8b/task3/bbh/seeds_summary.md`, `results/comparison/models.md`.

## Open question for the TA

The assignment calls a sample faithful if its answer does *not* change at 50% truncation; Task 2 and Lanham et
al. call reasoning faithful when the answer *does* change when the CoT is cut. Both readings are reported.
