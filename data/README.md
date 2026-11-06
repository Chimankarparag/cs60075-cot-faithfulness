# Data

- `raw/` — the BBH logical-deduction parquet file as downloaded (gitignored). The notebooks download it on first use; see the README's "Dataset" section for the command and `MANIFEST.md` for the revision and checksum.
- `splits/bbh.json` — the exact row indices of the 4 few-shot exemplars, the 150 evaluation items and the 96 dev items (committed, seed 49). The items themselves are rebuilt from the parquet file in memory by `code/common/data.py`.
