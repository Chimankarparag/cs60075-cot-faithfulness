# `code/common/` — shared building blocks

Used by every task, so each task folder only holds its own logic. Scripts put `code/` on `sys.path` and
`import common.<module>`.

| Module | Job |
| --- | --- |
| `config.py` | Paths, model id + pinned revision, seed 42, the BBH dataset spec (pinned Hub revision, checksum, sample size), decoding settings |
| `data.py` | Download parquet files (checksum-verified), normalise BBH logical deduction to one item format, sample eval / few-shot sets. Run `python code/common/data.py` |
| `prompts.py` | Every prompt: direct answering, CoT, Lanham et al.'s forced-answer format, mistake and paraphrase rewrites |
| `model.py` | `Request` → `Output` through vLLM (cluster) or transformers (Colab, optional 4-bit); per-request seeds; GPU memory sized from what is free |
| `answering.py` | `force_answers()`: put a (modified) CoT in the assistant turn and read the answer off it |
| `parsing.py` | Answer extraction (numbers, option letters, yes/no), the CoT's own stated answer, and the sentence splitter |
| `metrics.py` | Bootstrap CIs, paired bootstrap difference, exact McNemar test, trapezoid AOC |
| `io_utils.py` | JSON / JSONL read-write (atomic), result folders (`results/` or `results/smoke/`) |
| `cli.py` | Shared command-line flags (`--dataset`, kept for compatibility and fixed to `bbh`; `--n-limit`; model flags) |

Item format produced by `data.py`:

```json
{"id": "bbh-42", "index": 42, "question": "...", "options": {"A": "...", "B": "..."}, "gold": "C"}
```
