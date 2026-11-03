# Task 3 — Faithfulness-weighted self-consistency (40 marks)

Sample 5 CoTs per question, use Task 2's early-answering intervention at 50% truncation as a per-sample
faithfulness proxy, take a weighted majority vote, and compare accuracy and faithfulness with Tasks 1 and 2.

| Step (assignment) | File | What it does |
| --- | --- | --- |
| 1. Sample k = 5 CoTs (T 0.7) | `sample_k.py` | Same prompt and decoding as Task 2; sample j of item i uses seed `42 + 100000·j + i`, same seed as Task 2 for j = 0, but sampled text depends on the GPU and batch setup, so the samples are fresh draws. Each sample's final answer A0_j is read off with the forced-answer prompt |
| 2. Early answering at 50% | `weighted_vote.py` | Keeps the first floor(0.5·n) sentences of each sample and forces an answer. The sample is *flagged* faithful (load-bearing) if that answer does **not** change (`--faithful-if unchanged`, the assignment's wording) |
| 3. Weighted majority vote | `weighted_vote.py` | Flagged samples weight 1, the others weight `alpha`; the winner is the answer with the largest total weight |
| 4. Compare accuracy with Tasks 1 and 2 | `evaluate.py` | Paired bootstrap interval and exact McNemar test against Task 1's best direct variant, Task 2's single CoT, and plain self-consistency (alpha = 1, the control) |
| 5. Four interventions on the pipeline's output | `evaluate.py`, `task2/interventions.py` | Task 2's early answering, mistake, paraphrase and filler are applied to the CoT the vote selects and scored exactly as in Task 2 |

`run_task3.py` runs everything with one model load; each stage saves a file and is skipped if it exists.

```bash
python code/task3/run_task3.py --tp 2                         # sample, early50, interventions, score
python code/task3/run_task3.py --stages score                 # recompute metrics, summary, figures (no GPU)
scripts/cluster/run_task3.sh 0,1 task3 --tp 2                 # detached, on a KGP GPU box
```

Run Tasks 1 and 2 first (`results/task1/bbh`, `results/task2/bbh` are the baselines).

## Rules fixed in advance (not tuned on the evaluation set)

- Pipelines: `weighted` (faithful if answer *unchanged*, alpha = 0.5, the main result), `ablation_changed`
  (faithful if answer *changed*, the direction Task 2 and Lanham et al. call faithful) and `plain_sc` (alpha = 1).
  The alpha sweep 0 / 0.25 / 0.5 / 1 is reported as sensitivity only.
- A sample whose final answer cannot be parsed abstains. Ties go to the letter whose first supporting sample has the
  lowest index. If alpha = 0 and no sample is flagged, the vote falls back to alpha = 1.
- The pipeline's output CoT is the winning answer's highest-weight sample (ties: lowest index); the four
  interventions run on it, with the same seeds and settings as Task 2.

## Outputs (`results/task3/bbh/`)

| File | Contents |
| --- | --- |
| `samples.jsonl` | 5 CoTs per item: text, sentence spans, stated answer, final answer A0_j, correctness |
| `early50.jsonl` | each sample's answer after 50% of its sentences and whether it equals A0_j |
| `votes.jsonl` | the vote of every pipeline per item: answer, correctness, chosen sample, weights |
| `pipeline_<name>/{early,mistake,paraphrase,filler}.jsonl` | Task 2's interventions on that pipeline's chosen CoTs |
| `metrics.json`, `summary.md`, `figures/` | accuracy comparison, flag diagnostics, alpha sweep, faithfulness vs Task 2 |

## Result in one paragraph

On BBH (n = 150) the weighted vote reaches 62.0% against 54.0% for Task 2's single CoT and 46.0% for direct
answering, but plain self-consistency (alpha = 1) is just as good (62.7%), so the faithfulness weights add
nothing measurable. The pipeline's output scores lower on Task 2's aggregate faithfulness (55.3% vs 61.2%) under
the assignment's flag direction, and higher (64.3%) under the opposite direction. Full tables: `results/task3/bbh/summary.md`
and the root README.

## Open question for the TA

The assignment treats a sample as more faithful when its answer does *not* change at 50% truncation; Task 2 and
Lanham et al. treat a CoT as faithful when the answer *does* change. Both directions are run (`weighted` is the
assignment's wording, `ablation_changed` the other), so the report can state either.
