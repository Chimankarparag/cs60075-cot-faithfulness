# Task 1 — Direct (no-CoT) answering baseline (30 marks)

Everything is in [`task1.ipynb`](task1.ipynb): prompting, scoring, results for both models, and a figure.

- Greedy decoding (temperature 0), at most 16 new tokens, answer-only instruction, reply prefilled with
  "The answer is".
- `zero_shot`: the question only. `four_shot`: the same 4 fixed exemplars (seed 49) before every question, with
  answers only (the option letter), so the exemplars also demonstrate "no reasoning".
- Writes `results/models/<model>/task1/bbh/{zero_shot,four_shot}.jsonl`, `metrics.json`, `summary.md` and
  `run_info.json`: accuracy with a 95% bootstrap CI, parse failures, and outputs that hit the 16-token cap
  (a leakage check).

Run with `RUN_MODEL = True` and `MODEL = "llama3.1-8b"` or `"qwen3-8b"` to regenerate (GPU); the default
re-scores the committed outputs.
