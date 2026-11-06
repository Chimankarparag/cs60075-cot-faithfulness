# Task 3 - vote rule chosen on 96 development items (k = 5)

| Flag rule | alpha = 0.0 | alpha = 0.25 | alpha = 0.5 | alpha = 0.75 |
| --- | --- | --- | --- | --- |
| unchanged | 67.7 | 74.0 | 77.1 | 80.2 |
| loadbearing | 77.1 | 78.1 | 80.2 | 80.2 |

Plain self-consistency on dev: 80.2%; mean single sample: 77.9%.
Chosen: faithful if **unchanged**, alpha = **0.75** (max dev accuracy; ties: unchanged before loadbearing, then alpha closest to 0.5, then larger alpha).
