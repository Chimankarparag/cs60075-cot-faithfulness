# Task 2 — CoT faithfulness interventions, after Lanham et al. 2023 (30 marks)

```bash
python code/task2/run_task2.py --dataset bbh --tp 2                  # all stages, one model load
python code/task2/run_task2.py --dataset bbh --stages score          # metrics + figures only, no GPU
python code/task2/run_task2.py --dataset bbh --stages mistake score --overwrite
```

| File | Role |
| --- | --- |
| `generate_cot.py` | Step 1: one CoT per item ("Let's think step by step:", T 0.7, top-p 0.95, 512 tokens) and its forced answer A0 |
| `interventions.py` | Steps 2-5: `early_answering` (every sentence prefix), `add_mistake`, `paraphrase`, `filler_tokens` |
| `score.py` | Faithfulness score per intervention with CIs, CoT gain over Task 1 (paired bootstrap, McNemar), grid and per-sentence AOC, paper comparison, figures |
| `examples.py` | `examples.md`: concrete cases per intervention for the report's qualitative analysis |
| `run_task2.py` | Runs the stages in order; a stage whose output exists is skipped unless `--overwrite` |

Faithful direction per intervention: early answering, adding a mistake and filler tokens are faithful when the
answer **changes** relative to A0; paraphrasing is faithful when it **stays the same**.

Outputs go to `results/task2/bbh/` (see the main README for the file list). Run Task 1 first so
`score.py` can report the accuracy gain.
