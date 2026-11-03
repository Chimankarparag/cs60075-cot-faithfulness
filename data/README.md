
# Data

- `raw/` — the BBH logical-deduction parquet file as downloaded (gitignored). See the README's "Dataset" section for the download command and `MANIFEST.md` for the revision and checksum.
- `processed/` — normalised eval and few-shot JSONL files, rebuilt by `code/common/data.py` (gitignored).
- `splits/bbh.json` — the exact row indices of the 150 eval items and the 4 few-shot exemplars (committed, seed 20); the remaining 96 rows are the dev items.
