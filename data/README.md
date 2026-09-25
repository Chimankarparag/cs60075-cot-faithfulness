# Data

- `raw/` — the three datasets as downloaded (gitignored). See the README's "Datasets" section for the download commands and `MANIFEST.md` for revisions and checksums.
- `processed/` — normalised eval and few-shot JSONL files, rebuilt by `code/common/data.py` (gitignored).
- `splits/` — the exact item indices of each eval sample and few-shot set (committed, seed 42).
