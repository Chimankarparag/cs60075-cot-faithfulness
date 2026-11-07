# Dataset manifest

The file was downloaded on 2026-09-25 from the Hugging Face Hub, pinned to the exact revision below.
`maveriq/bigbenchhard` is a loading-script repo, which `datasets` 4.x no longer runs, so we use the
Hub's auto-converted parquet file (branch `refs/convert/parquet`).

| Local file | Hub repo | Config / split | Revision (commit SHA) | Rows | SHA-256 |
| --- | --- | --- | --- | --- | --- |
| `raw/bbh_logical_deduction_five_objects/train.parquet` | `maveriq/bigbenchhard` | `logical_deduction_five_objects` / `train` | `a493490a030bfe06c7baa2db022263afbfa04cfb` (parquet branch) | 250 | `1ddb7e4512bca5fa1009be8fcb8d40f345b8774f0a970978d78f296c53f501b2` |

Verify after download:

```bash
cd data && sha256sum raw/*/*.parquet
```

Field notes (checked against the file, which differs from the assignment PDF):

- BBH: `input` (question with embedded `(A)`..`(E)` options), `target` = the option **letter**, e.g. `(A)`
  (the PDF describes `target` as the option's text). The loader raises an error if `target` is not among the parsed options.
- 250 rows: 150 are the evaluation sample, 4 are few-shot exemplars (disjoint from the sample).
