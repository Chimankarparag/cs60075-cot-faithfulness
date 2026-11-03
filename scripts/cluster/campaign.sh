#!/usr/bin/env bash
# Everything for ONE model, in order, in the foreground (run_all.sh starts this detached):
#   Task 1 (skipped if it already has results)
#   Task 2 with generation seeds 20, 30, 40 (seed 20 also runs the paper-style stages)
#   Task 3 on the 96 dev items (chooses the tuned vote rule)
#   Task 3 with seeds 20, 30, 40, then the summary across seeds
# Resumable: every stage skips output that already exists. One log per step in logs/<model>/,
# progress lines in logs/<model>/campaign.log, host/GPU/timings in each results folder's run_info.json.
#
# Usage (from the repo root, CUDA_VISIBLE_DEVICES already set):
#   scripts/cluster/campaign.sh <model> [extra args for every step, e.g. --tp 1]
set -euo pipefail
MODEL=$1; shift
cd "$(dirname "$0")/../.."
source scripts/cluster/env.sh
LOG=logs/$MODEL
mkdir -p "$LOG"
if [ "$MODEL" = "llama3.1-8b" ]; then RES=results; else RES=results/models/$MODEL; fi
SEEDS=(20 30 40)
SPEC_STAGES=(cot early mistake paraphrase filler score)

step() {
  local name=$1; shift
  echo "=== $(date '+%F %T') $(hostname -s) gpu=$CUDA_VISIBLE_DEVICES start $name" | tee -a "$LOG/campaign.log"
  if "$PY" "$@" --model "$MODEL" "${EXTRA[@]}" > "$LOG/$name.log" 2>&1; then
    echo "=== $(date '+%F %T') done $name" | tee -a "$LOG/campaign.log"
  else
    echo "=== $(date '+%F %T') FAILED $name (see $LOG/$name.log)" | tee -a "$LOG/campaign.log"
    tail -5 "$LOG/$name.log" >> "$LOG/campaign.log"
    exit 1
  fi
}
EXTRA=("$@")

if [ -f "$RES/task1/bbh/metrics.json" ]; then echo "=== task1 already done, skipped" >> "$LOG/campaign.log"
else step task1 code/task1/run_direct.py; fi
for s in "${SEEDS[@]}"; do
  if [ "$s" = "${SEEDS[0]}" ]; then step "task2_seed$s" code/task2/run_task2.py --seed "$s"
  else step "task2_seed$s" code/task2/run_task2.py --seed "$s" --stages "${SPEC_STAGES[@]}"; fi
done
step task3_dev code/task3/run_task3.py --split dev
for s in "${SEEDS[@]}"; do step "task3_seed$s" code/task3/run_task3.py --seed "$s"; done
"$PY" code/task3/seeds.py --model "$MODEL" "${EXTRA[@]}" > "$LOG/seeds.log" 2>&1
echo "=== $(date '+%F %T') ALL DONE $MODEL" | tee -a "$LOG/campaign.log"
