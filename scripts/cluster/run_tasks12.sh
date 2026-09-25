#!/usr/bin/env bash
# Run Task 1 and then Task 2 for one or more datasets, in the background.
#
# Usage, from the repo root on the GPU box:
#   scripts/cluster/run_tasks12.sh <gpu-ids> <log-name> "<datasets>" [extra args for both scripts]
# Examples:
#   scripts/cluster/run_tasks12.sh 0,1 full "gsm8k bbh strategyqa" --tp 2
#   scripts/cluster/run_tasks12.sh 0,1 smoke "bbh strategyqa" --tp 2 --n-limit 10
set -euo pipefail
GPUS=$1; NAME=$2; DATASETS=$3
cd "$(dirname "$0")/../.."
mkdir -p logs

# First call: re-launch this same script detached (setsid + nohup) so it keeps
# running after the SSH session ends, then return immediately.
if [[ "${_TASKS12_DETACHED:-}" != 1 ]]; then
  _TASKS12_DETACHED=1 setsid nohup "$0" "$@" > "logs/$NAME.log" 2>&1 < /dev/null &
  echo "started pid $! on GPU(s) $GPUS -> logs/$NAME.log"
  exit 0
fi

shift 3
source scripts/cluster/env.sh
export CUDA_VISIBLE_DEVICES=$GPUS
for d in $DATASETS; do
  echo "=== $(date '+%F %T') task1 $d"
  "$PY" code/task1/run_direct.py --dataset "$d" "$@"
  echo "=== $(date '+%F %T') task2 $d"
  "$PY" code/task2/run_task2.py --dataset "$d" "$@"
done
echo "=== $(date '+%F %T') ALL DONE"
