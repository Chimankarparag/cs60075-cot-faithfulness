# Running on the IIT KGP CSE GPU servers

Login node: `ssh <roll-no>@10.5.18.114` (password login; `.100` may be unreachable).
GPU boxes (no scheduler): `10.5.18.73` (2x L40S 48 GB), `10.5.18.74` (2x A40 48 GB).
Home (`/home/bt3/<roll-no>`) is shared NFS, so a copy of the repo or a model download is visible on every machine.

| Script | Use |
| --- | --- |
| `env.sh` | Environment for the `cotfaith` conda env; `source scripts/cluster/env.sh` before running anything by hand |
| `run.sh <gpus> <log> <script> [args]` | Start one script detached (`setsid nohup`), log to `logs/<log>.log` |
| `run_tasks12.sh <gpus> <log> [args]` | Task 1 then Task 2 on BBH, detached |
| `run_task3.sh <gpus> <log> [args]` | Task 3 on BBH, detached (run Tasks 1 and 2 first; one A40 or L40S is enough, `--tp 1`) |
| `run_campaign.sh <gpus> <model> [args]` | Everything for one model, detached: Task 1 (if missing), Task 2 (missing stages), Task 3 on the dev items, Task 3 with seeds 42/20/30/40, seed summary; one log per step in `logs/<model>/` |

```bash
nvidia-smi --query-gpu=index,memory.used,memory.total --format=csv   # the cards are shared
scripts/cluster/run_tasks12.sh 0,1 full --tp 2
tail -f logs/full.log
scripts/cluster/run_campaign.sh 0 qwen3-8b --tp 1                    # all tasks for the second model
tail -f logs/qwen3-8b/campaign.log
```

A model other than Llama must be in the Hugging Face cache first (`HF_HUB_OFFLINE=1` is set by `env.sh`), e.g.
on the login node: `HF_HUB_OFFLINE=0 python -c "from huggingface_hub import snapshot_download as d;
d('Qwen/Qwen3-8B', revision='b968826d9c46dd6066d109eabc6255188de91218')"`.

Known issues handled in `env.sh`:

- `ImportError: ... CXXABI_1.3.15 not found` — Rocky Linux 9's system `libstdc++` is older than conda-forge's
  ICU needs; the env's own `lib/` is put first on `LD_LIBRARY_PATH`.
- `FileNotFoundError: 'ninja'` during vLLM warm-up — FlashInfer tries to JIT-compile its sampler, which needs
  `nvcc`; `VLLM_USE_FLASHINFER_SAMPLER=0` uses vLLM's PyTorch sampler instead.

The model needs about 16 GB for weights plus a few GB of KV cache. `model.py` sizes vLLM's memory from what is
free at start-up; if no single card has ~20 GB free, use both cards with `--tp 2`.
