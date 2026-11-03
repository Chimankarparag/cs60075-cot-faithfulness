# Task 3 — Faithfulness-weighted self-consistency (40 marks)

Planned files:

- `sample_k.py` — k = 5 CoTs per question (temperature 0.7, fixed per-sample seeds).
- `weighted_vote.py` — early-answer each sample at 50% truncation, weight samples, weighted majority vote.
  `--faithful-if unchanged` (spec wording, main) or `changed` (Lanham-consistent, ablation); `--alpha` weight for the other samples.
- `evaluate.py` — accuracy vs Tasks 1 and 2 (plus plain self-consistency as a control), and the four
  Task 2 interventions on the pipeline's chosen CoT → aggregate faithfulness vs Task 2.

Writes to `results/task3/bbh/`.
