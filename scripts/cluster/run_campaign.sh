#!/usr/bin/env bash
# Run the whole pipeline for one model, in order, detached, on a KGP GPU box:
#   Task 1 (skipped if it already has results), Task 2 (missing stages only), Task 3 on the
#   dev items (chooses the tuned vote rule), Task 3 with seeds 42, 20, 30, 40, and the seed summary.
# One log per step in logs/<model>/; every step also appends host, GPUs and timings to the
# run_info.json of its results folder.
#
# Usage, from the repo root on the GPU box:
#   scripts/cluster/run_campaign.sh <gpu-ids> <model> [extra args for every step]
# Examples:
#   scripts/cluster/run_campaign.sh 0 llama3.1-8b --tp 1
#   scripts/cluster/run_campaign.sh 0,1 qwen3-8b --tp 2
set -euo pipefail
GPUS=$1; MODEL=$2; shift 2
EXTRA=("$@")
cd "$(dirname "$0")/../.."          # repo root
source scripts/cluster/env.sh
export CUDA_VISIBLE_DEVICES=$GPUS
LOG=logs/$MODEL
mkdir -p "$LOG"
if [ "$MODEL" = "llama3.1-8b" ]; then RES=results; else RES=results/models/$MODEL; fi

campaign() {
  set -e
  step() {
    local name=$1; shift
    echo "=== $(date -Is) $(hostname) start $name"
    "$PY" "$@" --model "$MODEL" "${EXTRA[@]}" > "$LOG/$name.log" 2>&1
    echo "=== $(date -Is) done $name"
  }
  if [ -f "$RES/task1/bbh/metrics.json" ]; then echo "=== task1 already done, skipped"; else step task1 code/task1/run_direct.py; fi
  step task2 code/task2/run_task2.py
  step task3_dev code/task3/run_task3.py --split dev
  for s in 42 20 30 40; do step "task3_seed$s" code/task3/run_task3.py --seed "$s"; done
  "$PY" code/task3/seeds.py --model "$MODEL" > "$LOG/seeds.log" 2>&1
  echo "=== $(date -Is) ALL DONE"
}
export -f campaign
export PY MODEL LOG RES
setsid nohup bash -c "$(declare -p EXTRA); campaign" > "$LOG/campaign.log" 2>&1 < /dev/null &
echo "started pid $! on GPU(s) $GPUS -> $LOG/campaign.log"
