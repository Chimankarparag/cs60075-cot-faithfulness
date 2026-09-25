# Task 1 — Direct (no-CoT) answering baseline (30 marks)

Planned entry point: `run_direct.py --dataset <gsm8k|bbh|strategyqa> --shots <0|4>`

- Greedy decoding (temperature 0), `max_new_tokens` = 16, answer-only instruction.
- 4-shot: the same 4 fixed exemplars (seed 42) for every question, answers only.
- Writes `results/task1/<dataset>/{zero_shot,four_shot}.jsonl` and `metrics.json`.
- Reports: accuracy (zero-shot, 4-shot) with 95% CI and parse-failure rate.
