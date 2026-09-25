# Dataset manifest

All files were downloaded on 2026-09-25 from the Hugging Face Hub, pinned to the exact revisions below.
BBH and StrategyQA are loading-script repos, which `datasets` 4.x no longer runs, so we use the
Hub's auto-converted parquet files (branch `refs/convert/parquet`).

| Local file | Hub repo | Config / split | Revision (commit SHA) | Rows | SHA-256 |
| --- | --- | --- | --- | --- | --- |
| `raw/gsm8k/train.parquet` | `openai/gsm8k` | `main` / `train` | `740312add88f781978c0658806c59bc2815b9866` | 7,473 | `ea82612ea9582142387730c793eb67d3b12849002bc0b7fa6f8efafa7351419d` |
| `raw/gsm8k/test.parquet` | `openai/gsm8k` | `main` / `test` | `740312add88f781978c0658806c59bc2815b9866` | 1,319 | `ee7b8da9e381df27b9e3f7758a159ab2bdaa4dbaa910546cbbc47e0cb44e4f59` |
| `raw/bbh_logical_deduction_five_objects/train.parquet` | `maveriq/bigbenchhard` | `logical_deduction_five_objects` / `train` | `a493490a030bfe06c7baa2db022263afbfa04cfb` (parquet branch) | 250 | `1ddb7e4512bca5fa1009be8fcb8d40f345b8774f0a970978d78f296c53f501b2` |
| `raw/strategyqa/test.parquet` | `wics/strategy-qa` | `strategyQA` / `test` | `c9a25e4b10d32364d25f1f1387bf445921b6e75e` (parquet branch) | 2,290 | `c86cb39299a458683427ade4296546c92c94bee7640e2fa9d3642a0f7675f490` |

Verify after download:

```bash
cd data && sha256sum raw/*/*.parquet
```

Field notes (checked against the files, which differ in places from the assignment PDF):

- GSM8K: `question`, `answer`; the gold number follows `####` in `answer`.
- BBH: `input` (question with embedded `(A)`..`(E)` options), `target` = the option **letter**, e.g. `(A)`.
- StrategyQA: `qid`, `term`, `description`, `question`, `answer` (bool), `facts`, `decomposition`.
  The mirror labels its 2,290 questions as split `test`; the PDF calls it `train`. Never show `facts`/`decomposition` to the model.
