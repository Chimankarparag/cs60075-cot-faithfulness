# Task 3 - vote rule chosen on 96 development items (k = 5)

| Flag rule | alpha = 0.0 | alpha = 0.25 | alpha = 0.5 | alpha = 0.75 |
| --- | --- | --- | --- | --- |
| unchanged | 52.1 | 54.2 | 57.3 | 59.4 |
| loadbearing | 55.2 | 56.2 | 58.3 | 59.4 |

Plain self-consistency on dev: 61.5%; mean single sample: 52.1%.
Chosen: faithful if **unchanged**, alpha = **0.75** (max dev accuracy; ties: unchanged before loadbearing, then alpha closest to 0.5, then larger alpha).
