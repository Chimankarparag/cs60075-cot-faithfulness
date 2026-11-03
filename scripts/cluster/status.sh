#!/usr/bin/env bash
# One short screen: which step each model is on, its last timing line, and the final summary if done.
cd "$(dirname "$0")/../.."
date '+%F %T'
for d in logs/llama3.1-8b logs/qwen3-8b; do
  [ -f "$d/campaign.log" ] || continue
  echo "## $(basename "$d")"
  tail -2 "$d/campaign.log"
  cur=$(ls -t "$d"/task*.log 2>/dev/null | head -1)
  [ -n "$cur" ] && grep -h '\[time\]\|Error\|Traceback' "$cur" | tail -1 | sed "s|^|  $(basename "$cur"): |"
done
if grep -q '^# Finished' logs/STATUS.md 2>/dev/null; then echo; sed -n '/^# Finished/,$p' logs/STATUS.md; fi
