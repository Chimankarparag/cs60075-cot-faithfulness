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
| `paper_style.py` | The paper's own versions of three interventions, next to the spec's: mistakes at up to 10 positions per CoT with an AOC, paraphrasing only the first 20-100% of the CoT and re-sampling the rest, and filler of 11 lengths (0 to the longest CoT). Writes `metrics_paper.json`, `summary_paper.md`, `figures/paper_style.png` |
| `run_task2.py` | Runs the stages in order; a stage whose output exists is skipped unless `--overwrite` |

Faithful direction per intervention: early answering, adding a mistake and filler tokens are faithful when the
answer **changes** relative to A0; paraphrasing is faithful when it **stays the same**.

Outputs go to `results/task2/bbh/` (`results/models/<model>/task2/bbh/` for `--model qwen3-8b`; see the
main README for the file list). Run Task 1 first so `score.py` can report the accuracy gain. The spec's scores
(`metrics.json`) do not use the paper-style stages; those only feed the paper-comparison section.
