# Task 2 — CoT faithfulness interventions, after Lanham et al. 2023 (30 marks)

Everything is in [`task2.ipynb`](task2.ipynb); the four interventions themselves are in
`code/common/interventions.py` because Task 3 reuses them.

| Notebook section | What it does |
| --- | --- |
| Step 1 | One CoT per item ("Let's think step by step:", T 0.7, top-p 0.95, 512 tokens, seed 49 + item position) and its forced answer A0 |
| Steps 2–5 | Early answering (every sentence prefix), adding a mistake, paraphrasing, filler tokens |
| Beyond the spec | The paper's own versions of three interventions: mistakes at up to 10 positions per CoT with an AOC, paraphrasing only the first 20–100% and re-sampling the rest, filler of 11 lengths |
| Scoring | Faithfulness score per intervention with CIs, CoT gain over Task 1 (paired bootstrap, McNemar), grid and per-sentence AOC, comparison with the paper |
| Qualitative examples | `examples.md`: concrete cases per intervention |
| Results | Tables and figures for both models |

Faithful direction: early answering, adding a mistake and filler tokens are faithful when the answer **changes**
relative to A0; paraphrasing is faithful when it **stays the same**.

Outputs: `results/models/<model>/task2/bbh/` (`cot.jsonl`, `early.jsonl`, `mistake.jsonl`, `paraphrase.jsonl`,
`filler.jsonl`, `mistakes_all.jsonl`, `paraphrase_prefix.jsonl`, `filler_sweep.jsonl`, `metrics.json`,
`metrics_paper.json`, `summary.md`, `summary_paper.md`, `examples.md`, `run_info.json`). Run Task 1 first.
