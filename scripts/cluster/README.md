# Running on the IIT KGP CSE GPU servers

Login node: `ssh <roll-no>@10.5.18.114` (password login; `.100` may be unreachable).
GPU boxes (no scheduler): `10.5.18.73` (2x L40S 48 GB), `10.5.18.74` (2x A40 48 GB).
Home (`/home/bt3/<roll-no>`) is shared NFS, so a clone or model download is visible on every machine.

Before every run:

```bash
nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total --format=csv
export CUDA_VISIBLE_DEVICES=<a card with >= 20 GB free>
```

Long jobs must survive the SSH session:

```bash
mkdir -p logs
setsid nohup <command> > logs/<name>.log 2>&1 < /dev/null &
```

SLURM fallback (P100 16 GB, no bf16, no vLLM): partition `gpupart_p100`, request both GPUs of one node.
Launcher scripts for each task will be added here.
