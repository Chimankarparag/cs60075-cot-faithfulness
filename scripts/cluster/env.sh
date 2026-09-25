# Environment for running the pipeline on the KGP GPU boxes. Sourced by run.sh
# and run_tasks12.sh; usable on its own:  source scripts/cluster/env.sh
ENV_DIR=${ENV_DIR:-$HOME/miniconda3/envs/cotfaith}
export PY=$ENV_DIR/bin/python
export CUDA_DEVICE_ORDER=PCI_BUS_ID            # same GPU numbering as nvidia-smi
export HF_TOKEN=${HF_TOKEN:-$(cat ~/.hf_token 2>/dev/null || true)}
export HF_HUB_OFFLINE=${HF_HUB_OFFLINE:-1}     # model and data are already cached
export OMP_NUM_THREADS=4 TOKENIZERS_PARALLELISM=false PYTHONUNBUFFERED=1
# The GPU boxes run Rocky Linux 9, whose system libstdc++ is older than the one
# conda-forge's ICU/sqlite need (CXXABI_1.3.15). Put the env's own libstdc++ first,
# otherwise vLLM fails while inspecting the model with "CXXABI_1.3.15 not found".
export LD_LIBRARY_PATH="$ENV_DIR/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export PATH="$ENV_DIR/bin:$PATH"
# FlashInfer's top-k/top-p sampler is compiled on first use, which needs nvcc (not
# installed here). vLLM's PyTorch sampler gives the same sampling semantics.
export VLLM_USE_FLASHINFER_SAMPLER=0
