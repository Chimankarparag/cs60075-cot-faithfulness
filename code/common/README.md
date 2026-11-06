# `code/common/` — shared building blocks

The three task notebooks (`code/task1/task1.ipynb`, `code/task2/task2.ipynb`, `code/task3/task3.ipynb`) hold each
task's own logic; what more than one task needs lives here. The notebooks put `code/` on `sys.path` and
`import common.<module>`.

| Module | Job |
| --- | --- |
| `config.py` | Paths, the two models (Hub id + pinned revision), the one seed (49), the BBH file (pinned Hub revision, checksum), split sizes, decoding settings |
| `data.py` | Download the parquet file (checksum-verified), turn each row into an item, split the 250 rows into 4 exemplars, 150 evaluation items and 96 dev items (indices in `data/splits/bbh.json`) |
| `prompts.py` | Every prompt: direct answering, CoT, Lanham et al.'s forced-answer format, mistake and paraphrase rewrites |
| `model.py` | `Request` → `Output` through vLLM (KGP servers) or transformers (Colab, 4-bit on small GPUs); per-request seeds |
| `answering.py` | `force_answers()`: put a (possibly modified) CoT in the assistant turn and read the answer off it; `cot_seed()` |
| `interventions.py` | The four interventions (early answering, adding a mistake, paraphrasing, filler tokens), used by Task 2 on its CoT and by Task 3 on the CoT its vote selects |
| `faithfulness.py` | The four faithfulness scores, early-answering curve and AOC, per-item scores for paired comparisons |
| `parsing.py` | Option-letter extraction, the CoT's own stated answer, the sentence splitter |
| `metrics.py` | Bootstrap CIs, paired bootstrap difference, exact McNemar test, trapezoid AOC |
| `io_utils.py` | JSON / JSONL read-write; `results_dir(model, task)` → `results/models/<model>/<task>/bbh/` (`results/smoke/...` for test runs) |
| `runinfo.py` | `RunRecord`: appends host, GPUs, versions, start/end time and seconds per stage of every model run to `run_info.json` |
| `notebook.py` | Notebook helpers: package install and Hugging Face login on Colab, backend choice, which models have results |
| `plots.py` | One colour per model and the axis style of the notebook figures |

Item format produced by `data.py`:

```json
{"id": "bbh-7", "index": 7, "question": "...", "options": {"A": "...", "B": "..."}, "gold": "C"}
```
