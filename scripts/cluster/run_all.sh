#!/usr/bin/env bash
# ONE command for the whole project on a KGP GPU box: picks free GPUs, runs every task for the
# chosen model(s) detached, then writes the model comparison and a short status file.
#
# Usage, from the repo root on gpu73 / gpu74:
#   scripts/cluster/run_all.sh llama            # meta-llama/Llama-3.1-8B-Instruct only
#   scripts/cluster/run_all.sh qwen             # Qwen/Qwen3-8B only
#   scripts/cluster/run_all.sh both             # both: in parallel on two GPUs if two have room,
#                                               # otherwise one after the other on the best GPU
#   GPUS=0,1 scripts/cluster/run_all.sh both    # choose the GPUs yourself (one per model)
#   scripts/cluster/run_all.sh both --tp 1      # extra arguments are passed to every step
# Check progress with scripts/cluster/status.sh (one short screen); the final summary is
# logs/STATUS.md and results/comparison/models.md.
set -euo pipefail
cd "$(dirname "$0")/../.."
case "${1:-}" in
  llama) MODELS=(llama3.1-8b) ;;
  qwen)  MODELS=(qwen3-8b) ;;
  both)  MODELS=(llama3.1-8b qwen3-8b) ;;
  *) echo "usage: $0 llama|qwen|both [extra args]"; exit 2 ;;
esac
shift
EXTRA=("$@")
NEED_MB=${NEED_MB:-20000}   # an 8B model in bf16 needs ~16 GB of weights plus KV cache

if [ -n "${GPUS:-}" ]; then
  IFS=, read -r -a FREE <<< "$GPUS"
else
  # GPUs with at least NEED_MB free, most free first (the cards are shared with other users).
  mapfile -t FREE < <(nvidia-smi --query-gpu=index,memory.free --format=csv,noheader,nounits |
                      awk -F', ' -v need="$NEED_MB" '$2 >= need {print $2, $1}' | sort -nr | awk '{print $2}')
fi
if [ "${#FREE[@]}" -eq 0 ]; then
  echo "No GPU has ${NEED_MB} MB free right now:"; nvidia-smi --query-gpu=index,memory.used,memory.total --format=csv
  exit 1
fi

mkdir -p logs
STATUS=logs/STATUS.md
{ echo "# Run started $(date '+%F %T') on $(hostname -s)"; echo; echo "Models: ${MODELS[*]}; GPUs: ${FREE[*]}"; } > "$STATUS"
q() { if [ $# -gt 0 ]; then printf '%q ' "$@"; fi; }
if [ "${#MODELS[@]}" -eq 2 ] && [ "${#FREE[@]}" -ge 2 ]; then
  PLAN="CUDA_VISIBLE_DEVICES=${FREE[0]} scripts/cluster/campaign.sh ${MODELS[0]} $(q "${EXTRA[@]}") & \
        CUDA_VISIBLE_DEVICES=${FREE[1]} scripts/cluster/campaign.sh ${MODELS[1]} $(q "${EXTRA[@]}") & wait"
  echo "Running ${MODELS[0]} on GPU ${FREE[0]} and ${MODELS[1]} on GPU ${FREE[1]} in parallel" | tee -a "$STATUS"
else
  PLAN=""
  for m in "${MODELS[@]}"; do PLAN+="CUDA_VISIBLE_DEVICES=${FREE[0]} scripts/cluster/campaign.sh $m $(q "${EXTRA[@]}"); "; done
  echo "Running ${MODELS[*]} one after the other on GPU ${FREE[0]}" | tee -a "$STATUS"
fi
FINISH="source scripts/cluster/env.sh; \"\$PY\" code/analysis/compare_models.py > logs/compare.log 2>&1; \
  { echo; echo \"# Finished \$(date '+%F %T')\"; echo; grep -h 'ALL DONE\|FAILED' logs/*/campaign.log; echo; \
    sed -n '1,40p' results/comparison/models.md; } >> $STATUS"
setsid nohup bash -c "$PLAN; $FINISH" > logs/run_all.log 2>&1 < /dev/null &
echo "started (pid $!); progress: scripts/cluster/status.sh"
