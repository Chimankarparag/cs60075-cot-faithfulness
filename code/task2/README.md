# Task 2 — CoT faithfulness interventions, after Lanham et al. 2023 (30 marks)

Planned files:

- `generate_cot.py` — "Let's think step by step", temperature 0.7, top-p 0.95, max 512 new tokens.
- `interventions.py` — one function per intervention:
  1. early answering (truncate at 20/40/60/80% of sentences, force an answer),
  2. adding a mistake (corrupt one step, regenerate the rest),
  3. paraphrasing (reword the CoT without the question, re-answer),
  4. filler tokens (replace the CoT with " ..." of the same token length).
- `score.py` — CoT accuracy gain over Task 1, faithfulness score per intervention, early-answering AOC.

Writes to `results/task2/<dataset>/`.
