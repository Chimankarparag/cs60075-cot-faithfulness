# Task 1 — Direct (no-CoT) answering baseline (30 marks)

```bash
python code/task1/run_direct.py --dataset gsm8k --tp 2        # both variants
python code/task1/run_direct.py --dataset gsm8k --n-limit 10  # smoke test -> results/smoke/
python code/task1/run_direct.py --dataset gsm8k --rescore     # re-parse saved outputs, no GPU
```

- Greedy decoding (temperature 0), at most 16 new tokens, answer-only instruction, reply prefilled with
  "The answer is".
- `zero_shot`: the question only. `four_shot`: the same 4 fixed exemplars (seed 42) before every question, with
  answers only (GSM8K worked solutions are dropped), so the exemplars also demonstrate "no reasoning".
- Writes `results/task1/<dataset>/{zero_shot,four_shot}.jsonl`, `metrics.json` and `summary.md`: accuracy with
  a 95% bootstrap CI, parse failures, and outputs that hit the 16-token cap (a leakage check).
