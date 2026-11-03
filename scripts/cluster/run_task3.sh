#!/usr/bin/env bash
# Run Task 3 on BBH, detached, on a KGP GPU box. Tasks 1 and 2 must already have been run.
#
# Usage, from the repo root on the GPU box:
#   scripts/cluster/run_task3.sh <gpu-ids> <log-name> [extra args]
# Examples:
#   scripts/cluster/run_task3.sh 0,1 task3 --tp 2
#   scripts/cluster/run_task3.sh 0,1 task3_smoke --tp 2 --n-limit 10
exec "$(dirname "$0")/run.sh" "$1" "$2" code/task3/run_task3.py --dataset bbh "${@:3}"
