# Task 3 - vote rule chosen on 96 development items (k = 5)

| Flag rule | alpha = 0.0 | alpha = 0.25 | alpha = 0.5 | alpha = 0.75 |
| --- | --- | --- | --- | --- |
| unchanged | 58.3 | 59.4 | 61.5 | 62.5 |
| loadbearing | 59.4 | 59.4 | 59.4 | 60.4 |

Plain self-consistency on dev: 63.5%; mean single sample: 57.7%.
Chosen: faithful if **unchanged**, alpha = **0.75** (max dev accuracy; ties: unchanged before loadbearing, then alpha closest to 0.5, then larger alpha).
