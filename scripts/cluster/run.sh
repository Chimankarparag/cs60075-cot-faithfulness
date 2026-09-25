#!/usr/bin/env bash
# Launch one pipeline script in the background on a KGP GPU box (gpu73 / gpu74).
# Those boxes have no scheduler, so the job must survive the SSH session ending.
#
# Usage, from the repo root on the GPU box:
#   scripts/cluster/run.sh <gpu-ids> <log-name> <script> [script args...]
# Examples:
#   scripts/cluster/run.sh 0,1 task1_gsm8k code/task1/run_direct.py --dataset gsm8k --tp 2
#   scripts/cluster/run.sh 1   task2_gsm8k code/task2/run_task2.py  --dataset gsm8k
#
# Check free memory first:  nvidia-smi --query-gpu=index,memory.used,memory.total --format=csv
set -euo pipefail
GPUS=$1; NAME=$2; shift 2
cd "$(dirname "$0")/../.."          # repo root
mkdir -p logs
source scripts/cluster/env.sh
export CUDA_VISIBLE_DEVICES=$GPUS
setsid nohup "$PY" "$@" > "logs/$NAME.log" 2>&1 < /dev/null &
echo "started pid $! on GPU(s) $GPUS -> logs/$NAME.log"
