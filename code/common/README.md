# `code/common/` — shared building blocks (planned, not written yet)

Used by all three tasks, so each task folder only holds its own logic.

| Module | Job |
| --- | --- |
| `config.py` | Dataset, model id, seeds, n, paths, decoding settings; all overridable from the command line |
| `data.py` | Load the parquet files, normalise rows to one schema, build the eval and few-shot files |
| `prompts.py` | Chat templates: direct zero-shot, direct 4-shot, CoT, forced answer, add-a-mistake, paraphrase |
| `model.py` | One `generate()` interface over vLLM (cluster) and transformers (Colab / P100), incl. 4-bit on small GPUs |
| `parsing.py` | Answer extraction per dataset and the CoT sentence splitter |
| `metrics.py` | Accuracy + bootstrap 95% CI, McNemar test, faithfulness scores, AOC |
| `cache.py` | JSONL cache keyed by item id + stage + settings, so reruns and the notebook replay instead of regenerating |
